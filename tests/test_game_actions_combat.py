import unittest
from mtg_ai.card import Card
from mtg_ai.game_state import GameState, Player
from mtg_ai import game_actions as GA


def _basic_creature(name: str, power: int, toughness: int) -> Card:
    return Card(
        {
            "name": name,
            "uuid": name,
            "types": ["Creature"],
            "subtypes": ["Bear"],
            "power": str(power),
            "toughness": str(toughness),
        }
    )


class CombatPipelineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.attacker_player = Player("Alice", [])
        self.blocker_player = Player("Bob", [])
        self.game = GameState(self.attacker_player, self.blocker_player)

        # Two simple grizzly bears on each side
        self.a1 = _basic_creature("A1", 2, 2)
        self.a2 = _basic_creature("A2", 2, 2)
        self.b1 = _basic_creature("B1", 2, 2)
        self.b2 = _basic_creature("B2", 2, 2)

        # Put on battlefield, no summoning-sick state.
        self.attacker_player.battlefield.extend([self.a1, self.a2])
        self.blocker_player.battlefield.extend([self.b1, self.b2])
        for c in (self.a1, self.a2, self.b1, self.b2):
            c.summoning_sick = False

        # Shift game into DECLARE_ATTACKERS phase
        self.game.phase = "DECLARE_ATTACKERS"

    def test_full_combat_flow(self) -> None:
        # 1. declare attackers
        GA.declare_attackers(self.game, [self.a1, self.a2])
        self.assertEqual(set(self.game.attackers), {self.a1, self.a2})

        # 2. declare blockers (block B1 → A1, let A2 through)
        GA.declare_blockers(self.game, {self.a1: [self.b1]})
        self.assertEqual(self.game.blocking_assignments[self.a1], [self.b1])

        # 3. resolve damage
        GA.resolve_combat_damage(self.game)

        #   • B1 and A1 should trade and be in graveyards
        self.assertIn(self.a1, self.attacker_player.graveyard)
        self.assertIn(self.b1, self.blocker_player.graveyard)
        #   • A2 hits for 2 damage
        self.assertEqual(self.blocker_player.life_total, 18)
        #   • Combat state reset
        self.assertFalse(self.game.attackers)        # list cleared
        self.assertFalse(self.game.blocking_assignments)
