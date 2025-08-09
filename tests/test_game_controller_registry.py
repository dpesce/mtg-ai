from typing import List, Dict
import unittest

from mtg_ai.game_state import GameState, Player
from mtg_ai.game_controller import _phase_handlers
from mtg_ai.agent import FullAgent


class DummyAgent(FullAgent):
    """Does absolutely nothing in any decision branch."""

    # --- CastAgent ---
    def choose_casts(self, game: GameState) -> List:
        return []

    # --- AttackAgent ---
    def choose_attackers(self, game: GameState) -> List:
        return []

    # --- BlockAgent ---
    def choose_blockers(self, game: GameState) -> Dict:
        return {}


class PhaseRegistryTest(unittest.TestCase):
    def test_every_phase_has_handler(self) -> None:
        expected_phases = [
            "BEGINNING",
            "MAIN1",
            "BEGINNING_OF_COMBAT",
            "DECLARE_ATTACKERS",
            "DECLARE_BLOCKERS",
            "COMBAT_DAMAGE",
            "END_OF_COMBAT",
            "MAIN2",
            "ENDING",
        ]
        missing = [ph for ph in expected_phases if ph not in _phase_handlers]
        self.assertFalse(missing, f"Missing handlers for phases: {missing}")

    def test_handler_executes_without_error(self) -> None:
        """Call each handler once to ensure type-compatible invocation."""
        game = GameState(Player("A", []), Player("B", []))
        atk = DummyAgent()
        dfn = DummyAgent()

        for phase, handler in _phase_handlers.items():
            game.phase = phase
            # Should run without raising
            handler(game, atk, dfn)


if __name__ == "__main__":
    unittest.main()
