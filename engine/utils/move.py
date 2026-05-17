"""
Move objects pair a Player with an ActionEvent.
Used to record the history of actions taken during a game.
"""

from .card import Card
from .action_event import (ActionEvent, PassAction, BidAction,
                           PlayCardAction, ChooseTrumpAction)


class CodePieceMove:
    """Base interface for all moves."""
    pass


class PlayerMove(CodePieceMove):
    """A move made by a specific player."""
    def __init__(self, player, action: ActionEvent):
        super().__init__()
        self.player = player
        self.action = action


class CallMove(PlayerMove):
    """A bidding-phase move (pass or bid)."""
    def __init__(self, player, action: ActionEvent):
        super().__init__(player=player, action=action)


class DealHandMove(CodePieceMove):
    """Records the initial deal."""
    def __init__(self, dealer, shuffled_deck):
        super().__init__()
        self.dealer = dealer
        self.shuffled_deck = shuffled_deck

    def __str__(self):
        deck_text = " ".join([str(c) for c in self.shuffled_deck])
        return f'{self.dealer} deal shuffled_deck= [{deck_text}]'


class MakePassMove(CallMove):
    """A player passes during bidding."""
    def __init__(self, player):
        super().__init__(player=player, action=PassAction())

    def __str__(self):
        return f'Player {self.player.player_id} passes'


class MakeBidMove(CallMove):
    """A player places a bid."""
    def __init__(self, player, bid_action: BidAction):
        super().__init__(player=player, action=bid_action)

    def __str__(self):
        return f'Player {self.player.player_id} bids {self.action.bid_amount}' #! instead of bid_amount should use bid_hands (something like that that represents the number of hands the player is bidding to win, which is more intuitive for players)


class PlayCardMove(PlayerMove):
    """A player plays a card during a trick."""
    def __init__(self, player, action: PlayCardAction):
        super().__init__(player=player, action=action)

    @property
    def card(self):
        return self.action.card

    def __str__(self):
        return f'Player {self.player.player_id} plays {self.action}'


class ChooseTrumpMove(PlayerMove):
    """The bid winner chooses a trump suit."""
    def __init__(self, player, action: ChooseTrumpAction):
        super().__init__(player=player, action=action)

    @property
    def trump_suit(self):
        return self.action.trump_suit

    def __str__(self):
        return f'Player {self.player.player_id} chooses trump {self.action.trump_suit}'
