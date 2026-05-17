"""
CodePiece Game Engine.

Game owns the full lifecycle:
  Phase 1 - BIDDING:       handled directly by Game (4 turns)
  Phase 2 - TRUMP SELECT:  handled directly by Game (1 turn)
  Phase 3 - TRICK PLAY:    delegated to Round objects (up to 13 rounds)

RLCard-style API:
  - init_game()       -> (state, player_id)
  - step(action_str)  -> (state, player_id)
  - get_state(pid)    -> state dict
  - is_over()         -> bool
  - get_payoffs()     -> list[float]
  - get_num_actions() -> int  (63 total)
  - get_num_players() -> int  (4)
"""



import copy
import numpy as np
from typing import Tuple, Dict, List, Optional

from .dealer import Dealer
from .player import Player
from .judger import Judger
from .round import Round
from engine.utils.card import Card
from engine.utils.action_event import (
    BidAction, ChooseTrumpAction, decode_action
)
from engine.utils.move import (
    MakePassMove, MakeBidMove, ChooseTrumpMove, DealHandMove
)
from engine.utils.utils import encode_cards


class CodePieceGame:
    NUM_PLAYERS = 4
    NUM_ACTIONS = 63  # 7 bidding + 4 trump + 52 play card
    def __init__(self, allow_step_back: bool = False):
        self.allow_step_back = allow_step_back
        self.np_random = np.random.RandomState()
        self.judger: Optional[Judger] = None
        self.round: Optional[Round] = None
        self.players: List[Player] = []
        self.dealer: Optional[Dealer] = None
        
        #--- Phase ---
        self.phase: str = 'bidding'  # 'bidding', 'choose_trump', 'trick', 'game_over'
        self.current_player_id: int = 0
        
        # --- Bidding state (owned by Game) ---
        self.dealer_id: int = 0
        self.bidding_starter_id: int = 0
        self.highest_bid: Optional[int] = None
        self.highest_bidder_id: Optional[int] = None
        self.bidding_actions: List[Tuple[int, str]] = []
        self._bid_turn_count: int = 0
        
        # --- Trump / team state (owned by Game) ---
        self.trump_suit: Optional[str] = None
        self.winning_bid: Optional[int] = None
        self.bidding_team_id: Optional[int] = None
        self.defending_team_id: Optional[int] = None
        
        # --- Trick-play state (Rounds owned by Game, each Round = 1 trick) ---
        self.current_round: Optional[Round] = None
        self.completed_rounds: List[Round] = []
        self.tricks_won: Dict[int, int] = {0: 0, 1: 0}
        
        # --- History for step_back ---
        self._history: list = []
        self._move_history: list = []
        
    @property
    def tricks_completed(self) -> int:
        return len(self.completed_rounds)
    
    
    
    def configure(self, seed: Optional[int] = None):
        """Set random seed for reproducibility."""
        if seed is not None:
            self.np_random = np.random.RandomState(seed)
            
    # ================================================================
    # INIT
    # ================================================================    
    def init_game(self) -> Tuple[Dict, int]:
        """ Initialize a new game, Return (initial state, first player_id). """
        # Create players 
        self.players = [Player(i, self.np_random) for i in range(4)]

        # Create dealer and deal 13 cards each
        self.dealer = Dealer(self.np_random)
        for p in self.players:
            self.dealer.deal_cards(p, 13)
            p.sort_hand()
        
        # Determine dealer seat (random for first game)
        self.dealer_id = self.np_random.randint(0, 4)
        
        # Bidding starts left of dealer
        self.bidding_starter_id = (self.dealer_id + 1) % 4
        self.current_player_id = self.bidding_starter_id
        
        # Reset all game state
        self.phase = 'bidding'
        self.highest_bid = None
        self.highest_bidder_id = None
        self.bidding_actions = []
        self._bid_turn_count = 0
        self.trump_suit = None
        self.winning_bid = None
        self.bidding_team_id = None
        self.defending_team_id = None
        self.current_round = None
        self.completed_rounds = []
        self.tricks_won = {0: 0, 1: 0}
        self._history = []
        self._move_history = []
        
        # Create judger
        self.judger = Judger(self)
                
        state = self.get_state(self.current_player_id)
        return state, self.current_player_id
    
    # ================================================================
    # STEP  (main entry point for all actions)
    # ================================================================
    def step(self, action_str : str) -> Tuple[Dict, int]:
        """Take one game step.

        Args:
            action_str: 'pass', 'bid_8'..'bid_13', 'trump_S/H/D/C', or card like 'AS'

        Returns:
            (next_state, next_player_id)
        """
        if self.allow_step_back:
            self._save_history()
                
        if self.phase == 'bidding':
            self._step_bidding(action_str)
        elif self.phase == 'choose_trump':
            self._step_trump(action_str)
        elif self.phase == 'trick':
            self._step_trick(action_str)
        else:
            raise ValueError(f"Invalid game phase: {self.phase}")
        state = self.get_state(self.current_player_id)
        return state, self.current_player_id
    
     # ================================================================
    # BIDDING  (handled entirely by Game)
    # ================================================================
    def _step_bidding(self, action_str: str) -> None:
        """Process one bidding action."""
        #TODO: if a player can't bid higher than the current highest, they must pass.
        player = self.players[self.current_player_id]
        
        if action_str == 'pass':
            move = MakePassMove(player)
            self.biddiing_actions.append((player.player_id, 'pass'))
        else:
            bid_val = int(action_str.split('_')[1])
            bid_action = BidAction(bid_val)
            move = MakeBidMove(player, bid_action)
            self.bidding_actions.append((player.player_id, action_str))
            
            if self.highest_bid is None or bid_val > self.highest_bid:
                self.highest_bid = bid_val
                self.highest_bidder_id = player.player_id
                
        self._move_history.append(move)
        self._bid_turn_count += 1
        
        if self._bid_turn_count >= 4:
            self._finish_bidding()
        else:
            self.current_player_id = (self.current_player_id + 1) % 4
    
    def _finish_bidding(self) -> None:
        """Resolve bidding outcome."""
        if self.highest_bid is None:
            # All 4 passed → starter forced to accept default bid 7
            self.highest_bid = 7
            self.highest_bidder_id = self.bidding_starter_id
            self.bidding_actions.append((self.bidding_starter_id, 'bid_7'))

        self.winning_bid = self.highest_bid
        self.bidding_team_id = self.highest_bidder_id % 2
        self.defending_team_id = 1 - self.bidding_team_id

        # Transition to trump selection
        self.phase = 'choose_trump'
        self.current_player_id = self.highest_bidder_id


    # ================================================================
    # TRUMP SELECTION  (handled entirely by Game)
    # ================================================================
    def _step_trump(self, action_str: str) -> None:
        """Process trump selection."""
        player = self.players[self.current_player_id]
        suit = action_str.split('_')[1]
        trump_action = ChooseTrumpAction(suit)
        move = ChooseTrumpMove(player, trump_action)
        self._move_history.append(move)

        self.trump_suit = suit

        # Transition to trick play — create the first Round
        self.phase = 'trick'
        leader_id = self.highest_bidder_id
        self.current_round = Round(
            round_number=1,
            leader_id=leader_id,
            trump_suit=self.trump_suit
        )
        self.current_player_id = leader_id
        
    # ================================================================
    # TRICK PLAY  (delegated to current Round)
    # ================================================================
    def _step_trick(self, action_str: str) -> None:
        """Process a card play in the current trick (Round)."""
        player = self.players[self.current_player_id]
        rnd = self.current_round

        # Delegate card play to the Round
        rnd.play_card(player, action_str)

        if rnd.is_complete():
            # Trick finished — tally result
            winner_pid, _ = rnd.get_winner()
            winner_team = winner_pid % 2
            self.tricks_won[winner_team] += 1
            self.completed_rounds.append(rnd)

            # Check early end: defenders reach (14 - bid) tricks
            defender_target = 14 - self.winning_bid
            if self.tricks_won[self.defending_team_id] >= defender_target:
                self.phase = 'game_over'
                return

            # Check normal end: all 13 tricks played
            if self.tricks_completed >= 13:
                self.phase = 'game_over'
                return

            # Start next Round (trick)
            next_round_num = self.tricks_completed + 1
            self.current_round = Round(
                round_number=next_round_num,
                leader_id=winner_pid,
                trump_suit=self.trump_suit
            )
            self.current_player_id = winner_pid
        else:
            # Mid-trick: Round has already advanced current_player_id
            self.current_player_id = rnd.current_player_id
            

    # ================================================================
    # STATE
    # ================================================================
    def get_state(self, player_id: int) -> dict:
        """Observable state for a specific player."""
        player = self.players[player_id]

        # Current trick info
        if self.current_round is not None:
            current_trick = self.current_round.get_trick_as_tuples()
        else:
            current_trick = []

        state = {
            # Identity
            'player_id': player_id,
            'team_id': player.team_id,

            # Game info
            'phase': self.phase,
            'current_player_id': self.current_player_id,
            'dealer_id': self.dealer_id,

            # Hand (dual representation)
            'hand': [str(c) for c in player.hand],
            'hand_encoded': encode_cards(player.hand),

            # Bidding info (game-level)
            'highest_bid': self.highest_bid,
            'winning_bid': self.winning_bid,
            'bidding_actions': list(self.bidding_actions),

            # Trump & teams (game-level)
            'trump_suit': self.trump_suit,
            'bidding_team_id': self.bidding_team_id,
            'defending_team_id': self.defending_team_id,

            # Trick progress
            'current_trick': current_trick,
            'tricks_won': dict(self.tricks_won),
            'tricks_completed': self.tricks_completed,

            # Legal actions
            'legal_actions': (self.judger.get_legal_actions(player)
                              if self.phase != 'game_over' else []),
        }

        # End-game info
        if self.phase == 'game_over':
            payoffs = self.judger.compute_payoffs()
            winner_team = self._get_winner_team_id()
            state['winner_team_id'] = winner_team
            state['penalty_amount'] = (self.winning_bid if winner_team == self.bidding_team_id
                                        else 2 * self.winning_bid)
            state['payoffs'] = payoffs
        else:
            state['winner_team_id'] = None
            state['penalty_amount'] = None
            state['payoffs'] = None

        return state

    def _get_winner_team_id(self) -> Optional[int]:
        """Which team won the game."""
        if self.phase != 'game_over':
            return None
        if self.tricks_won[self.bidding_team_id] >= self.winning_bid:
            return self.bidding_team_id
        return self.defending_team_id

    # ================================================================
    # QUERIES
    # ================================================================
    def is_over(self) -> bool:
        return self.phase == 'game_over'

    def get_payoffs(self) -> List[float]:
        return self.judger.compute_payoffs()

    def get_player_id(self) -> int:
        return self.current_player_id

    @staticmethod
    def get_num_actions() -> int:
        return CodePieceGame.NUM_ACTIONS

    @staticmethod
    def get_num_players() -> int:
        return CodePieceGame.NUM_PLAYERS

    # ================================================================
    # STEP-BACK
    # ================================================================
    def _save_history(self):
        """Snapshot for step_back."""
        snapshot = {
            'phase': self.phase,
            'current_player_id': self.current_player_id,
            'highest_bid': self.highest_bid,
            'highest_bidder_id': self.highest_bidder_id,
            'bidding_actions': list(self.bidding_actions),
            '_bid_turn_count': self._bid_turn_count,
            'trump_suit': self.trump_suit,
            'winning_bid': self.winning_bid,
            'bidding_team_id': self.bidding_team_id,
            'defending_team_id': self.defending_team_id,
            'tricks_won': dict(self.tricks_won),
            'current_round': copy.deepcopy(self.current_round),
            'completed_rounds': copy.deepcopy(self.completed_rounds),
            'players_hands': [copy.deepcopy(p.hand) for p in self.players],
        }
        self._history.append(snapshot)

    def step_back(self) -> bool:
        """Restore to the previous state.  Returns True on success."""
        if not self.allow_step_back or not self._history:
            return False
        snap = self._history.pop()
        self.phase = snap['phase']
        self.current_player_id = snap['current_player_id']
        self.highest_bid = snap['highest_bid']
        self.highest_bidder_id = snap['highest_bidder_id']
        self.bidding_actions = snap['bidding_actions']
        self._bid_turn_count = snap['_bid_turn_count']
        self.trump_suit = snap['trump_suit']
        self.winning_bid = snap['winning_bid']
        self.bidding_team_id = snap['bidding_team_id']
        self.defending_team_id = snap['defending_team_id']
        self.tricks_won = snap['tricks_won']
        self.current_round = snap['current_round']
        self.completed_rounds = snap['completed_rounds']
        for i, hand in enumerate(snap['players_hands']):
            self.players[i].hand = hand
        return True



# Backward-compatible name used by tests/examples.
Game = CodePieceGame

            