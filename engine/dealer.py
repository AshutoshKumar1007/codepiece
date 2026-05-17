"""
Dealer for the CodePiece game.
Responsible for shuffling a 52-card deck and dealing cards to players.
"""

from typing import List
from engine.utils.card import Card


class Dealer:
    def __init__(self, np_random):
        self.np_random = np_random
        self.deck: List[Card] = Card.get_deck()
        self.np_random.shuffle(self.deck)
        self.stock: List[Card] = self.deck.copy()

    def deal_cards(self, player, num: int) -> None:
        """Deal `num` cards from stock to `player`."""
        for _ in range(num):
            if self.stock:
                card = self.stock.pop()
                player.hand.append(card)
