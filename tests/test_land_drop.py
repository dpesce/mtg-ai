import unittest
from mtg_ai.card import Card
from mtg_ai.game_state import GameState, Player

FOREST = {"name": "Forest", "uuid": "f1", "types": ["Land"], "subtypes": ["Forest"]}


class LandDropRuleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.p1 = Player("A", [])
        self.p2 = Player("B", [])
        self.game = GameState(self.p1, self.p2)
        self.land1 = Card(FOREST)
        self.land2 = Card(FOREST)
        self.p1.hand.extend([self.land1, self.land2])

    def test_one_land_per_turn(self) -> None:
        # First land succeeds
        self.p1.play_land(self.land1)
        self.assertIn(self.land1, self.p1.battlefield)
        # Second land should raise
        with self.assertRaises(ValueError):
            self.p1.play_land(self.land2)

    def test_counter_resets_next_turn(self) -> None:
        self.p1.play_land(self.land1)
        self.game.next_turn()          # switch to player B, then back
        self.game.next_turn()
        # Now p1 should be allowed again
        self.p1.play_land(self.land2)
        self.assertIn(self.land2, self.p1.battlefield)


if __name__ == "__main__":
    unittest.main()
