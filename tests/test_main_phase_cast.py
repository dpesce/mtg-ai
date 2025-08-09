import unittest
from mtg_ai.card import Card
from mtg_ai.game_state import GameState, Player
from mtg_ai.game_controller import step_game
from mtg_ai.agents.simple import NaiveAgent

BEAR = {
    "name": "Bear",
    "uuid": "bear",
    "types": ["Creature"],
    "manaCost": "{1}{G}",
    "power": "2",
    "toughness": "2",
}
FOREST = {"name": "Forest", "uuid": "F", "types": ["Land"], "subtypes": ["Forest"]}


class MainPhaseCastingIntegration(unittest.TestCase):
    def test_creature_cast_and_summoning_sick(self) -> None:
        # --- set up players & game ---
        p1, p2 = Player("A", []), Player("B", [])
        game = GameState(p1, p2)

        bear = Card(BEAR)
        forest1 = Card(FOREST)
        forest2 = Card(FOREST)

        # Bear starts in hand; two forests already untapped on battlefield
        p1.hand.append(bear)
        p1.battlefield.extend([forest1, forest2])

        atk = NaiveAgent()
        dfn = NaiveAgent()

        # --- simulate MAIN1 only ---
        game.phase = "MAIN1"
        step_game(game, atk, dfn)          # controller will invoke casting

        # --- checks ---
        self.assertIn(bear, p1.battlefield)
        self.assertTrue(bear.summoning_sick)   # can’t attack this turn


if __name__ == "__main__":
    unittest.main()
