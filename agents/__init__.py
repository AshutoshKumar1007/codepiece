"""
Agents for the CodePiece game engine.

BaseAgent      - abstract interface every agent must implement
RandomAgent    - picks uniformly at random from legal actions
HeuristicAgent - bids on hand strength; plays the highest-valued legal card
HumanAgent     - prompts for input (CLI or routed to GUI callback)
"""

import numpy as np
from typing import List, Optional, Callable


class BaseAgent:
    """Interface that all CodePiece agents must implement."""

    def __init__(self, player_id: int):
        self.player_id = player_id

    def step(self, state: dict) -> str:
        """Given a game state dict, return an action string."""
        raise NotImplementedError

    def eval_step(self, state: dict) -> str:
        """Evaluation-mode step (no exploration). Defaults to step()."""
        return self.step(state)

    @property
    def name(self) -> str:
        return self.__class__.__name__


# ---------------------------------------------------------------------------
# RandomAgent
# ---------------------------------------------------------------------------

class RandomAgent(BaseAgent):
    """Selects uniformly at random from legal actions."""

    def __init__(self, player_id: int, seed: Optional[int] = None):
        super().__init__(player_id)
        self.rng = np.random.RandomState(seed)

    def step(self, state: dict) -> str:
        legal = state['legal_actions']
        return legal[self.rng.randint(len(legal))]

    @property
    def name(self) -> str:
        return f"Random-{self.player_id}"


# ---------------------------------------------------------------------------
# HeuristicAgent
# ---------------------------------------------------------------------------

_RANK_VALUE = {r: i for i, r in enumerate('23456789TJQKA')}
_HCP        = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}


class HeuristicAgent(BaseAgent):
    """Heuristic agent for CodePiece:

    * Bidding   – estimates hand strength via HCP and bids accordingly.
    * Trump     – picks the suit with the highest aggregate rank-value.
    * Trick     – always plays the highest-valued legal card (trump > plain).
    """

    def __init__(self, player_id: int):
        super().__init__(player_id)

    def step(self, state: dict) -> str:
        phase = state['phase']
        if phase == 'bidding':
            return self._bid(state)
        if phase == 'choose_trump':
            return self._choose_trump(state)
        if phase == 'trick':
            return self._play_card(state)
        raise ValueError(f"HeuristicAgent.step called in unknown phase: {phase}")

    def _bid(self, state: dict) -> str:
        hand  = state['hand']
        legal = state['legal_actions']

        hcp = sum(_HCP.get(c[0], 0) for c in hand)
        bids = sorted(int(a.split('_')[1]) for a in legal if a.startswith('bid_'))

        if not bids or hcp < 4:
            return 'pass'

        target = min(8 + max(0, (hcp - 4) // 2), 13)
        chosen = min(bids, key=lambda b: abs(b - target))
        return f"bid_{chosen}"

    def _choose_trump(self, state: dict) -> str:
        hand = state['hand']
        suit_score: dict = {}
        for cs in hand:
            s = cs[1]
            suit_score[s] = suit_score.get(s, 0) + _RANK_VALUE.get(cs[0], 0) + 2
        best = max('SHDC', key=lambda s: suit_score.get(s, 0))
        return f"trump_{best}"

    def _play_card(self, state: dict) -> str:
        legal = state['legal_actions']
        trump = state.get('trump_suit', '')

        def card_value(cs: str) -> int:
            rank, suit = cs[0], cs[1]
            v = _RANK_VALUE.get(rank, 0)
            if suit == trump:
                v += 100
            return v

        return max(legal, key=card_value)

    @property
    def name(self) -> str:
        return f"Heuristic-{self.player_id}"


# ---------------------------------------------------------------------------
# HumanAgent
# ---------------------------------------------------------------------------

class HumanAgent(BaseAgent):
    """Agent that gets actions from a human player.

    In CLI mode : prints state and prompts for input.
    In GUI mode : set_gui_callback() attaches a function that the GUI uses
                  to deliver the chosen action back to the agent.
                  Signature: callback(state) -> action_str
    """

    def __init__(self, player_id: int):
        super().__init__(player_id)
        self._gui_callback: Optional[Callable] = None

    def set_gui_callback(self, callback: Callable) -> None:
        """Attach a GUI callback.  The callback receives the state dict
        and must return the chosen action string."""
        self._gui_callback = callback

    def step(self, state: dict) -> str:
        if self._gui_callback is not None:
            return self._gui_callback(state)
        return self._cli_step(state)

    def _cli_step(self, state: dict) -> str:
        phase = state['phase']
        legal = state['legal_actions']
        hand  = state['hand']

        print(f"\n{'='*50}")
        print(f"Player {self.player_id} (Team {state['team_id']}) — Phase: {phase}")

        if phase == 'trick':
            trick = state['current_trick']
            trump = state['trump_suit']
            print(f"  Trump: {trump}  |  Tricks won: {state['tricks_won']}")
            if trick:
                trick_str = ", ".join(f"P{pid}:{c}" for pid, c in trick)
                print(f"  Current trick: [{trick_str}]")
            else:
                print("  You lead this trick.")

        if phase == 'bidding':
            hb = state['highest_bid']
            print(f"  Current highest bid: {hb}" if hb else "  No bids yet.")

        print(f"  Your hand  : {' '.join(hand)}")
        print(f"  Legal moves: {' '.join(legal)}")

        while True:
            choice = input("  > Your action: ").strip()
            if choice in legal:
                return choice
            print(f"  Invalid. Choose from: {legal}")

    @property
    def name(self) -> str:
        return f"Human-{self.player_id}"
