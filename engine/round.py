"""
Round for the CodePiece game.

A Round represents a single trick: 4 players each play one card
clockwise starting from the trick leader.  After 4 cards are played
the round determines the winner.

There can be at most 13 rounds (tricks) in a game.
"""

from typing import List, Tuple, Optional
from .player import Player
from engine.utils.card import Card
from engine.utils.action_event import PlayCardAction
from engine.utils.move import PlayCardMove
from engine.utils.utils import trick_winner as compute_trick_winner, current_trick_winner


class Round:
    def __init__(self, round_number: int, leader_id: int, trump_suit: str):
        """
        Args:
            round_number: which trick this is (1-based, 1..13)
            leader_id:    player who leads this trick
            trump_suit:   the trump suit for this game ('S','H','D','C')
        """
        self.round_number = round_number
        self.trump_suit = trump_suit
        self.leader_id = leader_id
        self.current_player_id: int = leader_id

        # Cards played in this trick: list of (player_id, Card)
        self.trick_cards: List[Tuple[int, Card]] = []

        # Move history for this round
        self.move_history: List[PlayCardMove] = []

        # Resolved after 4 cards
        self._winner_id: Optional[int] = None
        self._winner_card: Optional[Card] = None

    @property
    def led_suit(self) -> Optional[str]:
        """The suit of the first card played in this trick, or None if empty."""
        if self.trick_cards:
            return self.trick_cards[0][1].suit
        return None

    @property
    def num_cards_played(self) -> int:
        return len(self.trick_cards)

    def is_complete(self) -> bool:
        """True when all 4 cards have been played."""
        return len(self.trick_cards) == 4

    def play_card(self, player: Player, card_str: str) -> None:
        """Play a card into this trick.

        Args:
            player:   the Player object whose turn it is
            card_str: string like 'AS', '7H', etc.
        """
        assert not self.is_complete(), "Round already complete"
        assert player.player_id == self.current_player_id, (
            f"Not player {player.player_id}'s turn, expected {self.current_player_id}"
        )

        card = player.get_card(card_str)
        assert card is not None, f"Player {player.player_id} does not hold {card_str}"

        # Record the play
        action = PlayCardAction(card)
        move = PlayCardMove(player, action)
        self.move_history.append(move)

        # Remove from hand, add to trick
        player.remove_card(card)
        self.trick_cards.append((player.player_id, card))

        if self.is_complete():
            # Resolve the trick winner
            self._winner_id, self._winner_card = compute_trick_winner(
                self.trick_cards, self.trump_suit
            )
        else:
            # Advance clockwise
            self.current_player_id = (self.current_player_id + 1) % 4

    def get_winner(self) -> Tuple[int, Card]:
        """Return (winner_player_id, winning_card).  Only valid after is_complete()."""
        assert self.is_complete(), "Trick not yet complete"
        return self._winner_id, self._winner_card

    @property
    def winner_team_id(self) -> Optional[int]:
        """Team that won this trick, or None if not yet resolved."""
        if self._winner_id is not None:
            return self._winner_id % 2
        return None

    def get_current_winner(self) -> Optional[Tuple[int, Card]]:
        """Who is currently winning mid-trick.  None if no cards played yet."""
        if not self.trick_cards:
            return None
        return current_trick_winner(self.trick_cards, self.trump_suit)

    def get_trick_as_tuples(self) -> List[Tuple[int, str]]:
        """Return trick cards as (player_id, card_str) for state reporting."""
        return [(pid, str(c)) for pid, c in self.trick_cards]

    def __repr__(self):
        status = "complete" if self.is_complete() else f"{self.num_cards_played}/4"
        return f"Round({self.round_number}, leader={self.leader_id}, {status})"
