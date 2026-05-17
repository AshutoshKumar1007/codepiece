"""
Action events for the CodePiece game.

Phases and their actions:
  Bidding:        PassAction, BidAction(8..13)  [BidAction(7) only as forced default]
  Trump Select:   ChooseTrumpAction(S/H/D/C)
  Trick Play:     PlayCardAction(card)
"""

from .card import Card


class ActionEvent:
    """Base class for all game actions."""

    def __eq__(self, other):
        if isinstance(other, ActionEvent):
            return str(self) == str(other)
        return NotImplemented

    def __hash__(self):
        return hash(str(self))


class PassAction(ActionEvent):
    """Pass during the bidding phase."""

    action_id = 'pass'

    def __str__(self):
        return 'pass'

    def __repr__(self):
        return 'PassAction()'


class BidAction(ActionEvent):
    """Place a bid during the bidding phase.
    Regular bids: 8-13.  Bid 7 is the forced default when all four players pass.
    """

    MIN_BID = 7
    MAX_BID = 13

    def __init__(self, bid_amount: int):
        if not (self.MIN_BID <= bid_amount <= self.MAX_BID): 
            raise ValueError(f"Bid must be {self.MIN_BID}-{self.MAX_BID}, got {bid_amount}")
        self.bid_amount = bid_amount

    @property
    def action_id(self):
        return f'bid_{self.bid_amount}'

    def __str__(self):
        return f'bid_{self.bid_amount}'

    def __repr__(self):
        return f'BidAction({self.bid_amount})'


class ChooseTrumpAction(ActionEvent):
    """Choose a trump suit after winning the bid."""

    VALID_SUITS = ['S', 'H', 'D', 'C']

    def __init__(self, trump_suit: str):
        if trump_suit not in self.VALID_SUITS:
            raise ValueError(f"Trump must be one of {self.VALID_SUITS}, got {trump_suit}")
        self.trump_suit = trump_suit

    @property
    def action_id(self):
        return f'trump_{self.trump_suit}'

    def __str__(self):
        return f'trump_{self.trump_suit}'

    def __repr__(self):
        return f'ChooseTrumpAction({self.trump_suit})'


class PlayCardAction(ActionEvent):
    """Play a card during the trick phase."""

    def __init__(self, card: Card):
        self.card = card

    @property
    def action_id(self):
        return str(self.card)

    def __str__(self):
        return str(self.card)

    def __repr__(self):
        return f'PlayCardAction({self.card})'


# ============================================================
# Pre-built lookup tables
# ============================================================

BID_ACTIONS = {i: BidAction(i) for i in range(BidAction.MIN_BID, BidAction.MAX_BID + 1)}
TRUMP_ACTIONS = {s: ChooseTrumpAction(s) for s in ChooseTrumpAction.VALID_SUITS}
PLAY_CARD_ACTIONS = {str(c): PlayCardAction(c) for c in Card.get_deck()}

# Master string -> ActionEvent map
ACTION_LOOKUP = {}
ACTION_LOOKUP['pass'] = PassAction()
for _a in BID_ACTIONS.values():
    ACTION_LOOKUP[str(_a)] = _a
for _a in TRUMP_ACTIONS.values():
    ACTION_LOOKUP[str(_a)] = _a
for _a in PLAY_CARD_ACTIONS.values():
    ACTION_LOOKUP[str(_a)] = _a


def decode_action(action_str: str) -> ActionEvent:
    """Convert an action string to its ActionEvent object."""
    if action_str in ACTION_LOOKUP:
        return ACTION_LOOKUP[action_str]
    raise ValueError(f"Unknown action: {action_str}")
