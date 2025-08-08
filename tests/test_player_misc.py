import unittest
from mtg_ai.card import Card
from mtg_ai.game_state import Player, GameState


def _dummy_card():
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
