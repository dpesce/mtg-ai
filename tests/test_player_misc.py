import unittest
from mtg_ai.card import Card
from mtg_ai.game_state import Player, GameState


def _dummy_card() -> Card:
    return Card({"name": "X", "uuid": "1", "types": ["Creature"], "power": "1", "toughness": "1"})


class PlayerUtilityTest(unittest.TestCase):
    def test_draw_card_empty_library_causes_loss(self) -> None:
        p1, p2 = Player("A", []), Player("B", [])
        game = GameState(p1, p2)
        p1.draw_card(game)
        self.assertIs(game.winner, p2)

    def test_reset_mana_pool(self) -> None:
        p = Player("Mana", [])
        p.mana_pool["G"] = 3
        p.reset_mana_pool()
        self.assertTrue(all(v == 0 for v in p.mana_pool.values()))

    def test_starting_player_skips_first_draw(self) -> None:
        p1, p2 = Player("A", []), Player("B", [])
        game = GameState(p1, p2)
        # give each a 1-card library so a draw would change hand size
        p1.library = [Card({"name": "X", "uuid": "x", "types": ["Creature"], "power": "1", "toughness": "1"})]
        p2.library = []
        game.start_game(opening_hand_size=0, skip_first_draw=True)

        # UNTAP
        from mtg_ai.game_controller import step_game
        from mtg_ai.agents.simple import NaiveAgent
        a = NaiveAgent()
        step_game(game, a, a)  # UNTAP -> UPKEEP
        step_game(game, a, a)  # UPKEEP -> DRAW
        step_game(game, a, a)  # DRAW (skipped) -> MAIN1

        self.assertEqual(len(p1.hand), 0)  # no draw because skip_first_draw
