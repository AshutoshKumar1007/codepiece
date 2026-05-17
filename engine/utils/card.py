"""
Card class for representing playing cards in a standard 52-card deck.

Encoding:
  Index 0-12:  Clubs    (2C, 3C, ..., AC)
  Index 13-25: Diamonds (2D, 3D, ..., AD)
  Index 26-38: Hearts   (2H, 3H, ..., AH)
  Index 39-51: Spades   (2S, 3S, ..., AS)
"""


class Card:
    suits = ['C', 'D', 'H', 'S']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suit_to_index = {s: i for i, s in enumerate(suits)}
    rank_to_index = {r: i for i, r in enumerate(ranks)}

    def __init__(self, suit: str, rank: str):
        self.suit = suit
        self.rank = rank
        self._suit_index = Card.suit_to_index[self.suit]
        self._rank_index = Card.rank_to_index[self.rank]
        self.card_id = 13 * self._suit_index + self._rank_index
        self._str = f'{self.rank}{self.suit}'

    @staticmethod
    def card(card_id: int):
        """Get a Card from the pre-built deck by its integer id."""
        return _deck[card_id]

    @staticmethod
    def get_deck():
        """Return a copy of the full 52-card ordered deck."""
        return _deck.copy()

    @property
    def rank_index(self) -> int:
        return self._rank_index

    @property
    def suit_index(self) -> int:
        return self._suit_index

    def __eq__(self, other):
        if isinstance(other, Card):
            return self.card_id == other.card_id
        return NotImplemented

    def __hash__(self):
        return self.card_id

    def __str__(self):
        return self._str

    def __repr__(self):
        return f'{self.rank}{self.suit}'


# Canonical ordered deck: 2C..AC, 2D..AD, 2H..AH, 2S..AS
_deck = [Card(suit, rank) for suit in Card.suits for rank in Card.ranks]
