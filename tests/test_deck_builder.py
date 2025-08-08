import unittest
from mtg_ai.deck_builder import load_deck_from_lines

DECKLIST = [
    "60 Forest",
]


class DeckBuilderTest(unittest.TestCase):
    def test_single_card_type(self) -> None:
        deck = load_deck_from_lines(DECKLIST, deck_name="MonoG")
        self.assertEqual(len(deck.cards), 60)
        self.assertEqual({c.name for c in deck.cards}, {"Forest"})
        # Ensure copies are unique
        self.assertNotEqual(id(deck.cards[0]), id(deck.cards[1]))


if __name__ == "__main__":
    unittest.main()
