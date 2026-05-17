from collections import OrderedDict
from typing import Dict, Optional

import numpy as np

from envs.env import Env
from engine.game import CodePieceGame
from engine.utils.action_space import (
    ACTION_DIM,
    CARD_START_INDEX,
    action_to_index,
    index_to_action,
)


class CodePieceEnv(Env):
    """RL environment wrapper for the CodePiece game engine.

    The environment preserves an RLCard-like API while using engine-native
    transitions and legal-action generation.
    """

    def __init__(
        self,
        config,
        payoff_delegate: Optional["CodepiecePayoffDelegate"] = None,
        state_extractor: Optional["CodepieceStateExtractor"] = None,
    ):
        self.name = "codepiece"
        self.default_game_config = {}
        self.game = CodePieceGame()

        self.codepiecePayoffDelegate = payoff_delegate or DefaultCodepiecePayoffDelegate()
        self.codepieceStateExtractor = state_extractor or DefaultCodepieceStateExtractor()

        super().__init__(config=config)

        state_shape_size = self.codepieceStateExtractor.get_state_shape_size()
        self.state_shape = [[1, state_shape_size] for _ in range(self.num_players)]
        self.action_shape = [None for _ in range(self.num_players)]

    def _extract_state(self, state):
        """Convert engine state to agent-facing structured state."""
        return self.codepieceStateExtractor.extract_state(state)

    def _decode_action(self, action_id):
        """Decode fixed action id to engine action string."""
        return index_to_action(action_id)

    def _get_legal_actions(self):
        """Return legal action ids for the current player as an OrderedDict."""
        state = self.game.get_state(self.get_player_id())
        return self.codepieceStateExtractor.get_legal_actions(state)

    def get_payoffs(self):
        """Get final game payoffs for all players."""
        return self.codepiecePayoffDelegate.get_payoffs(self.game)

    def get_perfect_information(self):
        """Expose engine perfect-information view for CTDE/debugging."""
        return self.codepieceStateExtractor.get_perfect_information(self.game)


class CodepiecePayoffDelegate(object):
    def get_payoffs(self, game: CodePieceGame):
        """Get player payoffs from a terminal game state."""
        raise NotImplementedError


class DefaultCodepiecePayoffDelegate(CodepiecePayoffDelegate):
    def get_payoffs(self, game: CodePieceGame):
        return game.get_payoffs()


class CodepieceStateExtractor(object):
    def get_state_shape_size(self) -> int:
        raise NotImplementedError

    def extract_state(self, state: Dict):
        """Extract agent-facing observation dictionary from raw engine state."""
        raise NotImplementedError

    @staticmethod
    def get_legal_actions(state: Dict):
        """Get legal action ids for current state as OrderedDict."""
        legal_actions = state.get("legal_actions", [])
        legal_actions_ids = OrderedDict()
        for action_str in legal_actions:
            legal_actions_ids[action_to_index(action_str)] = None
        return legal_actions_ids

    @staticmethod
    def get_perfect_information(game: CodePieceGame):
        return game.get_perfect_information()


class DefaultCodepieceStateExtractor(CodepieceStateExtractor):
    # 52 hand + 52 current trick + 52 played cards + 63 legal mask
    # + 4 phase one-hot + 6 scalar features + 4 trump one-hot
    OBS_VECTOR_SIZE = 233

    _PHASE_TO_INDEX = {
        "bidding": 0,
        "choose_trump": 1,
        "trick": 2,
        "game_over": 3,
    }

    _SUIT_TO_INDEX = {
        "C": 0,
        "D": 1,
        "H": 2,
        "S": 3,
    }

    def get_state_shape_size(self) -> int:
        return self.OBS_VECTOR_SIZE

    def extract_state(self, state: Dict):
        """Build a compact observation compatible with fixed-size RL models."""
        obs = np.zeros(self.OBS_VECTOR_SIZE, dtype=np.float32)

        hand_encoded = np.asarray(state["hand_encoded"], dtype=np.float32)
        obs[0:52] = hand_encoded

        # Encode cards currently in trick.
        for _, card_str in state.get("current_trick", []):
            card_id = action_to_index(card_str) - CARD_START_INDEX
            if 0 <= card_id < 52:
                obs[52 + card_id] = 1.0

        # Encode played cards as complement of cards in hand and active trick.
        obs[104:156] = np.clip(1.0 - obs[0:52] - obs[52:104], 0.0, 1.0)

        legal_action_mask = np.zeros(ACTION_DIM, dtype=np.float32)
        for action_str in state.get("legal_actions", []):
            legal_action_mask[action_to_index(action_str)] = 1.0
        obs[156:219] = legal_action_mask

        # Phase one-hot.
        phase_idx = self._PHASE_TO_INDEX.get(state.get("phase"), 0)
        obs[219 + phase_idx] = 1.0

        # Scalar/global features.
        obs[223] = float(state.get("player_id", 0)) / 3.0
        obs[224] = float(state.get("team_id", 0))
        obs[225] = float((state.get("current_player_id", 0) == state.get("player_id", -1)))
        obs[226] = float(state.get("highest_bid") or 0) / 13.0
        obs[227] = float(state.get("winning_bid") or 0) / 13.0
        obs[228] = float(state.get("tricks_completed", 0)) / 13.0

        trump = state.get("trump_suit")
        if trump in self._SUIT_TO_INDEX:
            obs[229 + self._SUIT_TO_INDEX[trump]] = 1.0

        extracted_state = {
            "obs": obs,
            "legal_actions": self.get_legal_actions(state),
            "raw_obs": state,
            "raw_legal_actions": list(state.get("legal_actions", [])),
            "action_mask": legal_action_mask,
        }
        return extracted_state
