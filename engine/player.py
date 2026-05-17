"""
Player for the CodePiece game.
Each player has an id (0-3), belongs to a team, and holds a hand of cards.
Teams: 0 = players {0,2}, 1 = players {1,3}.
"""

from typing import List, Optional
from engine.utils.card import Card

class Player:
    def __init__(self, player_id: int, np_random):
        if not (0 <= player_id <= 3):
            raise ValueError("player_id must be 0-3")
        self.player_id = player_id
        self.np_random = np_random
        self.hand: List[Card] = []

    @property
    def team_id(self) -> int:
        """Team 0: players 0,2.  Team 1: players 1,3."""
        return self.player_id % 2

    def sort_hand(self) -> None:
        """Sort hand by suit (C,D,H,S) then rank (2..A)."""
        self.hand.sort(key=lambda c: (c.suit_index, c.rank_index))

    def get_card(self, card_str: str) -> Optional[Card]:
        """Find a card in hand by its string representation (e.g. 'AS')."""
        if len(card_str) != 2:
            return None

        rank = card_str[0]
        suit = card_str[1]
        if suit not in Card.suit_to_index or rank not in Card.rank_to_index:
            return None

        target_id = 13 * Card.suit_to_index[suit] + Card.rank_to_index[rank]
        for card in self.hand:
            if card.card_id == target_id:
                return card
        return None

    def remove_card(self, card: Card) -> None:
        """Remove a specific card from hand."""
        self.hand.remove(card)

    def cards_of_suit(self, suit: str) -> List[Card]:
        """Return all cards in hand of a given suit."""
        return [c for c in self.hand if c.suit == suit]

    def __str__(self):
        return f'Player {self.player_id}'

    def __repr__(self):
        return f'Player({self.player_id})'
