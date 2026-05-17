"""
Tray determines the dealer seat from a board_id.
Dealer rotates: board 1 -> player 0, board 2 -> player 1, etc.
"""


class Tray:
    def __init__(self, board_id: int):
        if board_id <= 0:
            raise ValueError(f"Tray: invalid board id {board_id}")
        self.board_id = board_id

    @property
    def dealer_id(self):
        return (self.board_id - 1) % 4
