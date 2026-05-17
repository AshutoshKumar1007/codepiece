"""
Judger for the CodePiece game.

Responsibilities:
  - Compute legal actions for the current player given the game/round state.
  - Compute terminal payoffs once the game is over.
"""

#TODO : implement mask based legal action representation also along side the string based one...

from typing import List, Optional, TYPE_CHECKING
import numpy as np
if TYPE_CHECKING:
    from .game import CodePieceGame
from engine.utils.card import Card
from engine.utils.action_event import (
    ChooseTrumpAction,
)
from engine.utils.action_space import (
    ACTION_DIM,
    PASS_INDEX,
    BID_START_INDEX,
    TRUMP_START_INDEX,
    CARD_START_INDEX,
    legal_actions_to_mask,
)


_TRUMP_ACTIONS = [f'trump_{s}' for s in ChooseTrumpAction.VALID_SUITS]
_BID_ACTIONS_FROM = {
    min_bid: ['pass'] + [f'bid_{b}' for b in range(min_bid, 14)]
    for min_bid in range(8, 15)
}
_TRUMP_INDICES = np.arange(TRUMP_START_INDEX, TRUMP_START_INDEX + 4)


class Judger:
    def __init__(self, game : 'CodePieceGame'):
        self.game : CodePieceGame = game

    # ----------------------------------------------------------------
    # Bidding phase legal actions
    # ----------------------------------------------------------------
    def get_legal_bid_actions(self, player) -> List[str]:
        """Return legal action strings during bidding.

        A player may:
          - 'pass'
          - 'bid_N' where N > current highest bid, and 8 <= N <= 13
        """
        g = self.game
        current_highest = g.highest_bid  # None if no bids yet
        min_bid = (current_highest + 1) if current_highest is not None else 8

        # Return a copy so callers can safely mutate if needed.
        return list(_BID_ACTIONS_FROM[max(min_bid, 8)])

    # ----------------------------------------------------------------
    # Trump selection legal actions
    # ----------------------------------------------------------------
    def get_legal_trump_actions(self) -> List[str]:
        """Return legal trump selection actions: trump_S, trump_H, trump_D, trump_C."""
        return list(_TRUMP_ACTIONS)

    # ----------------------------------------------------------------
    # Trick play legal actions (with mandatory overtake)
    # ----------------------------------------------------------------
    def _legal_play_card_ids(self, player) -> np.ndarray:
        """Return legal card ids for trick play while preserving hand order."""
        g = self.game
        rnd = g.current_round
        hand = player.hand

        if not hand:
            return np.empty(0, dtype=np.int16)

        card_ids = np.fromiter((c.card_id for c in hand), dtype=np.int16, count=len(hand))

        # Leading: all cards are legal.
        if rnd.num_cards_played == 0:
            return card_ids

        suit_idx = card_ids // 13
        rank_idx = card_ids % 13

        # Follow-suit restriction.
        led_idx = Card.suit_to_index[rnd.led_suit]
        follow_mask = suit_idx == led_idx
        if not np.any(follow_mask):
            follow_mask = np.ones(len(hand), dtype=bool)

        # Mandatory overtake when an opponent is currently winning.
        winning_player_id, winning_card = rnd.get_current_winner()
        if (winning_player_id % 2) != player.team_id:
            trump_idx = Card.suit_to_index[rnd.trump_suit]
            win_suit_idx = winning_card.suit_index
            win_rank_idx = winning_card.rank_index

            a_is_trump = suit_idx == trump_idx
            b_is_trump = (win_suit_idx == trump_idx)
            a_is_led = suit_idx == led_idx
            b_is_led = (win_suit_idx == led_idx)

            if b_is_trump:
                beating_mask = a_is_trump & (rank_idx > win_rank_idx)
            else:
                beating_mask = a_is_trump
                if b_is_led:
                    beating_mask |= (~a_is_trump) & a_is_led & (rank_idx > win_rank_idx)
                else:
                    beating_mask |= (~a_is_trump) & a_is_led

            forced_mask = follow_mask & beating_mask
            if np.any(forced_mask):
                return card_ids[forced_mask]

        return card_ids[follow_mask]

    def get_legal_play_actions(self, player) -> List[str]:
        """Return legal card-play action strings for the current trick.

        Rules applied in order:
          1. If leading the trick: any card in hand.
          2. Follow-suit: must play led suit if possible, else any card.
          3. Mandatory overtake: if opponent is currently winning AND
             you hold a card (among follow-suit legal cards) that can beat
             the current winner, you MUST play one of those beating cards.
             If teammate is winning OR you cannot beat, play any follow-suit
             legal card.
        """
        return [str(Card.card(int(cid))) for cid in self._legal_play_card_ids(player)]

    def get_legal_play_action_mask(self, player, dtype=np.int8) -> np.ndarray:
        """Return a fixed-size legal action mask during trick play."""
        mask = np.zeros(ACTION_DIM, dtype=dtype)
        legal_card_ids = self._legal_play_card_ids(player)
        if legal_card_ids.size:
            mask[CARD_START_INDEX + legal_card_ids.astype(np.int32)] = 1
        return mask

    # ----------------------------------------------------------------
    # Unified legal actions dispatcher
    # ----------------------------------------------------------------
    def get_legal_actions(self, player) -> List[str]:
        """Return legal action strings based on current game phase."""
        phase = self.game.phase
        if phase == 'bidding':
            return self.get_legal_bid_actions(player)
        elif phase == 'choose_trump':
            return self.get_legal_trump_actions()
        elif phase == 'trick':
            return self.get_legal_play_actions(player)
        else:
            return []

    def get_legal_action_mask(self, player, dtype=np.int8) -> np.ndarray:
        """Return fixed-size legal action mask aligned to the 63-action space."""
        phase = self.game.phase

        if phase == 'bidding':
            g = self.game
            current_highest = g.highest_bid
            min_bid = (current_highest + 1) if current_highest is not None else 8
            min_bid = max(min_bid, 8)

            mask = np.zeros(ACTION_DIM, dtype=dtype)
            mask[PASS_INDEX] = 1
            if min_bid <= 13:
                start = BID_START_INDEX + (min_bid - 8)
                end = BID_START_INDEX + (13 - 8) + 1
                mask[start:end] = 1
            return mask

        if phase == 'choose_trump':
            mask = np.zeros(ACTION_DIM, dtype=dtype)
            mask[_TRUMP_INDICES] = 1
            return mask

        if phase == 'trick':
            return self.get_legal_play_action_mask(player, dtype=dtype)

        return np.zeros(ACTION_DIM, dtype=dtype)

    def get_legal_actions_and_mask(self, player, dtype=np.int8):
        """Return (legal_actions, legal_action_mask) in one call."""
        legal_actions = self.get_legal_actions(player)
        return legal_actions, legal_actions_to_mask(legal_actions, dtype=dtype)

    # ----------------------------------------------------------------
    # Payoff computation
    # ----------------------------------------------------------------
    def compute_payoffs(self) -> List[float]:
        """Compute per-player payoffs at game end.

        Bidding team wins (>= bid tricks):
            bidding team: +bid,  defending team: -bid
        Defending team wins (14 - bid tricks):
            defending team: +2*bid, bidding team: -2*bid
        """
        g = self.game
        bid = g.winning_bid
        bidding_team = g.bidding_team_id
        defending_team = g.defending_team_id

        bidding_tricks = g.tricks_won.get(bidding_team, 0)

        payoffs = [0.0] * 4

        if bidding_tricks >= bid:
            # Bidding team succeeded
            for pid in range(4):
                if pid % 2 == bidding_team:
                    payoffs[pid] = float(bid)
                else:
                    payoffs[pid] = float(-bid)
        else:
            # Defending team succeeded
            for pid in range(4):
                if pid % 2 == defending_team:
                    payoffs[pid] = float(2 * bid)
                else:
                    payoffs[pid] = float(-2 * bid)

        return payoffs
