
from typing import List, Tuple, Optional
import numpy as np

from .card import Card


def encode_cards(cards: List[Card]) -> np.ndarray:
    """Encode a list of cards as a 52-dimensional binary vector.

    Index layout: 0-12 Clubs, 13-25 Diamonds, 26-38 Hearts, 39-51 Spades.
    """
    
    plane = np.zeros(52, dtype=int)
    for card in cards:
        plane[card.card_id] = 1
    return plane



def card_beats(card_a: Card, card_b: Card, led_suit: str, trump_suit: str) -> bool:
    """Return True if card_a beats card_b.

    Rules:
      - Trump beats non-trump.
      - Among same suit, higher rank wins.
      - Off-suit non-trump never beats anything (it's a discard).
    """
    a_is_trump = (card_a.suit == trump_suit)
    b_is_trump = (card_b.suit == trump_suit)

    # If both trump, compare rank
    if a_is_trump and b_is_trump:
        return card_a.rank_index > card_b.rank_index

    # Trump beats non-trump
    if a_is_trump and not b_is_trump:
        return True
    if not a_is_trump and b_is_trump:
        return False

    # Neither is trump: only led-suit cards matter
    a_is_led = (card_a.suit == led_suit)
    b_is_led = (card_b.suit == led_suit)

    if a_is_led and b_is_led:
        return card_a.rank_index > card_b.rank_index
    if a_is_led and not b_is_led:
        return True
    if not a_is_led and b_is_led:
        return False

    # Both off-suit, non-trump -> card_a cannot beat card_b
    return False


def trick_winner(trick: List[Tuple[int, Card]], trump_suit: str) -> Tuple[int, Card]:
    """Determine the winner of a completed 4-card trick.

    Args:
        trick: list of (player_id, card) tuples in play order
        trump_suit: the current trump suit

    Returns:
        (winning_player_id, winning_card)
    """
    led_suit = trick[0][1].suit
    best_player_id, best_card = trick[0]

    for player_id, card in trick[1:]:
        if card_beats(card, best_card, led_suit, trump_suit):
            best_player_id = player_id
            best_card = card

    return best_player_id, best_card


def current_trick_winner(trick: List[Tuple[int, Card]], trump_suit: str) -> Tuple[int, Card]:
    """Determine who is currently winning a partially played trick.
    Same logic as trick_winner but works on 1-3 cards too.
    """
    if not trick:
        raise ValueError("Cannot determine winner of empty trick")
    led_suit = trick[0][1].suit
    best_player_id, best_card = trick[0]
    for player_id, card in trick[1:]:
        if card_beats(card, best_card, led_suit, trump_suit):
            best_player_id = player_id
            best_card = card
    return best_player_id, best_card
