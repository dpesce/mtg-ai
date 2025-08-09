import unittest
from typing import List

from mtg_ai.card import Card
from mtg_ai.game_state import GameState, Player


def make_deck(n: int) -> List[Card]:
    """Create a deterministic list of simple vanilla creatures."""
    return [
        Card(
            {
                "name": f"C{i}",
                "uuid": f"c{i}",
                "types": ["Creature"],
                "power": "1",
                "toughness": "1",
            }
        )
        for i in range(n)
    ]


class ShuffleDeterminismTest(unittest.TestCase):
    def test_shuffle_single_player_is_deterministic_with_seed(self) -> None:
        """
        Shuffling two equal libraries with the same seed should yield identical orders.
        Also verify the order actually changed from the original (i.e., it really shuffled).
        """
        # Two separate players with identical starting decks
        deckA1 = make_deck(10)
        deckA2 = make_deck(10)

        p1 = Player("A1", deckA1)
        p1_clone = Player("A2", deckA2)

        game = GameState(p1, Player("B", []))
        game_clone = GameState(p1_clone, Player("B2", []))

        # Track original (unshuffled) order for sanity check
        original_order = [c.uuid for c in deckA1]

        seed = 123
        game.shuffle_library(p1, seed=seed)
        game_clone.shuffle_library(p1_clone, seed=seed)

        order1 = [c.uuid for c in p1.library]
        order2 = [c.uuid for c in p1_clone.library]

        # Determinism: same seed -> same order
        self.assertEqual(order1, order2)

        # Ensure we actually shuffled (i.e., order changed)
        self.assertNotEqual(order1, original_order)

    def test_shuffle_only_affects_target_player(self) -> None:
        """
        Shuffling P1's library must not mutate P2's library.
        """
        deckA = make_deck(5)
        deckB = make_deck(5)

        p1 = Player("A", deckA)
        p2 = Player("B", deckB)

        game = GameState(p1, p2)

        before_p2 = [c.uuid for c in p2.library]
        game.shuffle_library(p1, seed=7)
        after_p2 = [c.uuid for c in p2.library]

        self.assertEqual(before_p2, after_p2)

    def test_shuffle_both_libraries_deterministic_and_independent(self) -> None:
        """
        Shuffling both players' libraries with fixed (but different) seeds:
        - yields the same order across repeated runs (deterministic)
        - produces different orders for P1 vs P2 (independent seeds)
        - changes the order from the original, unshuffled list
        """
        # Game A
        deckA1 = make_deck(12)
        deckB1 = make_deck(12)
        p1a = Player("A1", deckA1)
        p2a = Player("B1", deckB1)
        gameA = GameState(p1a, p2a)

        # Original orders before shuffle (for change check)
        orig_p1 = [c.uuid for c in p1a.library]
        orig_p2 = [c.uuid for c in p2a.library]

        # Game B (fresh copy to test determinism)
        deckA2 = make_deck(12)
        deckB2 = make_deck(12)
        p1b = Player("A2", deckA2)
        p2b = Player("B2", deckB2)
        gameB = GameState(p1b, p2b)

        seed_active = 101
        seed_opponent = 202

        # Shuffle both libraries in both games with the same seeds
        gameA.shuffle_both_libraries(seed_active=seed_active, seed_opponent=seed_opponent)
        gameB.shuffle_both_libraries(seed_active=seed_active, seed_opponent=seed_opponent)

        p1a_order = [c.uuid for c in p1a.library]
        p2a_order = [c.uuid for c in p2a.library]
        p1b_order = [c.uuid for c in p1b.library]
        p2b_order = [c.uuid for c in p2b.library]

        # Determinism: same seeds → same orders across Game A and Game B
        self.assertEqual(p1a_order, p1b_order)
        self.assertEqual(p2a_order, p2b_order)

        # Independence: different seeds for P1 vs P2 → different orders (overwhelmingly likely)
        self.assertNotEqual(p1a_order, p2a_order)

        # Actual shuffle happened (order changed from original for each player)
        self.assertNotEqual(p1a_order, orig_p1)
        self.assertNotEqual(p2a_order, orig_p2)


if __name__ == "__main__":
    unittest.main()
