import unittest
from core.card import Card
from core.game_state import Player, GameState
from core.game_actions import (
    cast_creature,
    parse_mana_cost,
    can_pay_mana_cost,
    get_attackers,
    attack,
)

# Sample MTGJSON-style cards
LAND_DATA = {
    "name": "Forest",
    "uuid": "f-001",
    "types": ["Land"],
    "subtypes": ["Forest"],
}

CREATURE_DATA = {
    "name": "Grizzly Bears",
    "uuid": "g-001",
    "types": ["Creature"],
    "subtypes": ["Bear"],
    "manaCost": "{1}{G}",
    "convertedManaCost": 2,
    "power": "2",
    "toughness": "2",
    "colors": ["Green"],
}


class TestMagicGameLogic(unittest.TestCase):
    def setUp(self) -> None:
        self.land = Card(LAND_DATA)
        self.creature = Card(CREATURE_DATA)

        self.player = Player("TestPlayer", [])
        self.player.hand = [self.creature.copy()]
        self.player.battlefield = [self.land.copy(), self.land.copy()]
        self.player.reset_mana_pool()

        self.opponent = Player("Opponent", [])

    def test_card_copy_is_unique(self) -> None:
        c1 = self.creature.copy()
        c2 = self.creature.copy()
        self.assertNotEqual(id(c1), id(c2))
        c1.tapped = True
        self.assertFalse(c2.tapped)

    def test_tap_land_adds_correct_mana(self) -> None:
        self.assertTrue(self.player.tap_land_for_mana(self.player.battlefield[0]))
        self.assertEqual(self.player.mana_pool["G"], 1)

    def test_tap_plains_adds_white_mana(self) -> None:
        land_data = {
            "name": "Plains",
            "uuid": "f-001",
            "types": ["Land"],
            "subtypes": ["Plains"],
        }
        land = Card(land_data)
        result = self.player.tap_land_for_mana(land)
        self.assertTrue(result)
        self.assertEqual(self.player.mana_pool["W"], 1)
        self.assertTrue(land.tapped)

    def test_tap_island_adds_blue_mana(self) -> None:
        land_data = {
            "name": "Island",
            "uuid": "f-001",
            "types": ["Land"],
            "subtypes": ["Island"],
        }
        land = Card(land_data)
        result = self.player.tap_land_for_mana(land)
        self.assertTrue(result)
        self.assertEqual(self.player.mana_pool["U"], 1)
        self.assertTrue(land.tapped)

    def test_tap_swamp_adds_black_mana(self) -> None:
        land_data = {
            "name": "Swamp",
            "uuid": "f-001",
            "types": ["Land"],
            "subtypes": ["Swamp"],
        }
        land = Card(land_data)
        result = self.player.tap_land_for_mana(land)
        self.assertTrue(result)
        self.assertEqual(self.player.mana_pool["B"], 1)
        self.assertTrue(land.tapped)

    def test_tap_mountain_adds_red_mana(self) -> None:
        land_data = {
            "name": "Mountain",
            "uuid": "f-001",
            "types": ["Land"],
            "subtypes": ["Mountain"],
        }
        land = Card(land_data)
        result = self.player.tap_land_for_mana(land)
        self.assertTrue(result)
        self.assertEqual(self.player.mana_pool["R"], 1)
        self.assertTrue(land.tapped)

    def test_tap_forest_adds_green_mana(self) -> None:
        land_data = {
            "name": "Forest",
            "uuid": "f-001",
            "types": ["Land"],
            "subtypes": ["Forest"],
        }
        land = Card(land_data)
        result = self.player.tap_land_for_mana(land)
        self.assertTrue(result)
        self.assertEqual(self.player.mana_pool["G"], 1)
        self.assertTrue(land.tapped)

    def test_tap_land_already_tapped(self) -> None:
        card = self.land
        card.tapped = True
        result = self.player.tap_land_for_mana(card)
        self.assertFalse(result)
        self.assertEqual(self.player.mana_pool["G"], 0)

    def test_tap_non_land_card(self) -> None:
        card = self.creature
        result = self.player.tap_land_for_mana(card)
        self.assertFalse(result)
        self.assertEqual(sum(self.player.mana_pool.values()), 0)

    def test_parse_mana_cost(self) -> None:
        cost = parse_mana_cost("{2}{G}{G}")
        self.assertEqual(cost["G"], 2)
        self.assertEqual(cost["generic"], 2)

    def test_can_pay_mana_cost(self) -> None:
        # Tap both lands first
        for land in self.player.battlefield:
            self.player.tap_land_for_mana(land)
        self.assertTrue(can_pay_mana_cost(self.player, "{1}{G}"))

    def test_cast_creature_pays_correct_mana(self) -> None:
        # Tap lands
        for land in self.player.battlefield:
            self.player.tap_land_for_mana(land)
        success = cast_creature(self.player, self.player.hand[0])
        self.assertTrue(success)
        self.assertEqual(len(self.player.battlefield), 3)  # 2 lands + 1 creature
        self.assertEqual(len(self.player.hand), 0)

    def test_summoning_sickness_prevents_attack(self) -> None:
        # Play creature and test summoning sickness
        for land in self.player.battlefield:
            self.player.tap_land_for_mana(land)
        cast_creature(self.player, self.player.hand[0])
        attackers = get_attackers(self.player)
        self.assertEqual(len(attackers), 0)

        # Remove summoning sickness
        for card in self.player.battlefield:
            card.summoning_sick = False
        attackers = get_attackers(self.player)
        self.assertEqual(len(attackers), 1)

    def test_attack_damage_applies(self) -> None:
        self.opponent.life_total = 20
        game = GameState(self.player, self.opponent)

        # Play creature and remove sickness
        for land in self.player.battlefield:
            self.player.tap_land_for_mana(land)
        cast_creature(self.player, self.player.hand[0])
        for card in self.player.battlefield:
            if card.is_creature():
                card.summoning_sick = False

        game.attackers = get_attackers(self.player)
        attack(game)

        self.assertEqual(self.opponent.life_total, 18)  # Grizzly Bears does 2

    def test_turn_progression(self) -> None:
        game = GameState(self.player, self.opponent)
        game.phase = "ENDING"
        current_turn = game.turn_number
        game.next_phase()
        self.assertEqual(game.turn_number, current_turn + 1)
        self.assertEqual(game.phase, "BEGINNING")

    def test_play_land_moves_card(self) -> None:
        land = self.land.copy()
        self.player.hand.append(land)
        self.player.play_land(land)
        self.assertIn(land, self.player.battlefield)
        self.assertNotIn(land, self.player.hand)

    def test_draw_card_adds_to_hand(self) -> None:
        self.player.library = [self.creature.copy()]
        self.player.hand = []
        game = GameState(self.player, self.opponent)
        self.player.draw_card(game)
        self.assertEqual(len(self.player.hand), 1)
        self.assertEqual(len(self.player.library), 0)

    def test_draw_card_empty_library(self) -> None:
        self.player.library = []
        self.player.hand = []
        game = GameState(self.player, self.opponent)
        self.player.draw_card(game)
        self.assertEqual(len(self.player.hand), 0)

    def test_get_active_and_opponent(self) -> None:
        game = GameState(self.player, self.opponent)
        self.assertEqual(game.get_active_player(), self.player)
        self.assertEqual(game.get_opponent(), self.opponent)

    def test_check_winner_sets_winner_correctly(self) -> None:
        game = GameState(self.player, self.opponent)
        self.player.life_total = 0
        game.check_winner()
        self.assertEqual(game.winner, self.opponent)

    def test_board_state_returns_string(self) -> None:
        game = GameState(self.player, self.opponent)
        board_output = game.board_state()
        self.assertIsInstance(board_output, str)
        self.assertIn("Turn", board_output)

    def test_game_state_repr(self) -> None:
        game = GameState(self.player, self.opponent)
        self.assertIn("Turn", repr(game))

    def test_milling_causes_game_loss(self) -> None:
        self.player.library = []
        self.player.hand = []
        game = GameState(self.player, self.opponent)
        self.player.draw_card(game)
        self.assertIs(game.winner, self.opponent)


if __name__ == "__main__":
    unittest.main()
