"""
Fixed action-space mapping utilities for CodePiece.

Action layout (size = 63):
  0: pass
  1..6: bid_8..bid_13
  7..10: trump_S, trump_H, trump_D, trump_C
  11..62: cards in Card.card_id order (2C..AS)
"""

from typing import Iterable, List

import numpy as np

from .card import Card


PASS_INDEX = 0
BID_START_INDEX = 1
TRUMP_START_INDEX = 7
CARD_START_INDEX = 11
ACTION_DIM = 63

_TRUMP_ORDER = ["S", "H", "D", "C"]
_INDEX_TO_ACTION: List[str] = [""] * ACTION_DIM
_INDEX_TO_ACTION[PASS_INDEX] = "pass"
for bid in range(8, 14):
    _INDEX_TO_ACTION[BID_START_INDEX + (bid - 8)] = f"bid_{bid}"
for i, suit in enumerate(_TRUMP_ORDER):
    _INDEX_TO_ACTION[TRUMP_START_INDEX + i] = f"trump_{suit}"
for c in Card.get_deck():
    _INDEX_TO_ACTION[CARD_START_INDEX + c.card_id] = str(c)

_ACTION_TO_INDEX = {a: i for i, a in enumerate(_INDEX_TO_ACTION)}


def action_to_index(action: str) -> int:
    """Return fixed action index for an action string."""
    if action not in _ACTION_TO_INDEX:
        raise ValueError(f"Unknown action string: {action}")
    return _ACTION_TO_INDEX[action]


def index_to_action(index: int) -> str:
    """Return action string for fixed action index."""
    if index < 0 or index >= ACTION_DIM:
        raise ValueError(f"Action index out of range: {index}")
    return _INDEX_TO_ACTION[index]


def legal_actions_to_mask(legal_actions: Iterable[str], dtype=np.int8) -> np.ndarray:
    """Convert legal action strings to a fixed-size binary action mask."""
    mask = np.zeros(ACTION_DIM, dtype=dtype)
    for action in legal_actions:
        mask[action_to_index(action)] = 1
    return mask


def mask_to_legal_actions(mask: np.ndarray) -> List[str]:
    """Convert a binary mask to the corresponding legal action strings."""
    if mask.shape != (ACTION_DIM,):
        raise ValueError(f"Mask must have shape ({ACTION_DIM},), got {mask.shape}")
    return [_INDEX_TO_ACTION[i] for i in np.flatnonzero(mask)]
