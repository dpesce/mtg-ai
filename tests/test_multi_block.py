import unittest
from mtg_ai.card import Card
from mtg_ai.game_state import GameState, Player
from mtg_ai import game_actions as GA


def creature(name: str, p: int, t: int) -> Card:
    return Card({"name": name, "uuid": name, "types": ["Creature"],
                 "power": str(p), "toughness": str(t)})


class MultiBlockTest(unittest.TestCase):
    def setUp(self) -> None:
        self.pA, self.pB = Player("A", []), Player("B", [])
        self.game = GameState(self.pA, self.pB)
        # attacker 4/4, blockers two 2/2s
        self.atk = creature("Att4", 4, 4)
        self.blk1 = creature("Blk1", 2, 2)
        self.blk2 = creature("Blk2", 2, 2)
        for c in (self.atk, self.blk1, self.blk2):
            c.summoning_sick = False
        self.pA.battlefield.append(self.atk)
        self.pB.battlefield.extend([self.blk1, self.blk2])
        self.game.phase = "DECLARE_ATTACKERS"

    def test_two_blockers_destroy_attacker(self) -> None:
        GA.declare_attackers(self.game, [self.atk])
        GA.declare_blockers(self.game, {self.atk: [self.blk1, self.blk2]})
        GA.resolve_combat_damage(self.game)

        # All three creatures die
        self.assertIn(self.atk, self.pA.graveyard)
        self.assertIn(self.blk1, self.pB.graveyard)
        self.assertIn(self.blk2, self.pB.graveyard)
        # No life loss
        self.assertEqual(self.pB.life_total, 20)


if __name__ == "__main__":
    unittest.main()
