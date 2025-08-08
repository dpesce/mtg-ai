import unittest
from mtg_ai.card import Card
from mtg_ai.game_state import Player
from mtg_ai import game_actions as GA


CREATURE_DATA = {
    "name": "Bear",
    "uuid": "bear-001",
    "types": ["Creature"],
    "subtypes": ["Bear"],
    "manaCost": "{1}{G}",
    "convertedManaCost": 2,
    "power": "2",
    "toughness": "2",
    "colors": ["Green"],
}

FOREST = {
    "name": "Forest",
    "uuid": "forest-001",
    "types": ["Land"],
    "subtypes": ["Forest"],
}


class ManaPaymentTest(unittest.TestCase):
    def test_parse_mana_cost(self) -> None:
        cost = GA.parse_mana_cost("{2}{G}{G}")
        self.assertEqual(cost, {"generic": 2, "G": 2})

    def test_can_pay_and_cast(self) -> None:
        p = Player("Caster", [])
        bear = Card(CREATURE_DATA)
        forest1, forest2 = Card(FOREST), Card(FOREST)
        p.hand.append(bear)
        p.battlefield.extend([forest1, forest2])

        # tap both lands
        p.tap_land_for_mana(forest1)
        p.tap_land_for_mana(forest2)

        self.assertTrue(GA.can_pay_mana_cost(p, "{1}{G}"))
        self.assertTrue(GA.cast_creature(p, bear))
        self.assertIn(bear, p.battlefield)
        # mana pool should be empty after cast
        self.assertEqual(sum(p.mana_pool.values()), 0)
