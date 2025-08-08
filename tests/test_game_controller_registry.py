from typing import List, Dict
import unittest
from mtg_ai.game_state import GameState, Player
from mtg_ai.game_controller import _phase_handlers
from mtg_ai.agent import AttackAgent, BlockAgent


class DummyAgents(AttackAgent, BlockAgent):
    """Attack with nothing, block with nothing."""

    def choose_attackers(self, game: GameState) -> List:
        return []

    def choose_blockers(self, game: GameState) -> Dict:
        return {}


class PhaseRegistryTest(unittest.TestCase):
    def test_every_phase_has_handler(self) -> None:
        phases = [
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
        missing = [ph for ph in phases if ph not in _phase_handlers]
        self.assertFalse(missing, f"Missing handlers for phases: {missing}")

    def test_handler_executes_without_error(self) -> None:
        game = GameState(Player("A", []), Player("B", []))
        agents = DummyAgents()
        for phase, handler in _phase_handlers.items():
            game.phase = phase
            # Simply verify no exceptions arise
            handler(game, agents, agents)
