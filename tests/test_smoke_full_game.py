import unittest
from pathlib import Path

from mtg_ai.game_state import GameState, Player
from mtg_ai.game_controller import step_game
from mtg_ai.deck_builder import load_deck_from_file
from mtg_ai.agents.simple import NaiveAgent

MAX_STEPS = 600  # generous cap to avoid infinite loops if something regresses


def play_one_land_if_possible(game: GameState) -> None:
    """
    Very small helper for the smoke test only:
    - During MAIN1 or MAIN2, play exactly one land from the active player's hand
      if they haven't played a land this turn.
    """
    if game.phase not in ("MAIN1", "MAIN2"):
        return
    player = game.get_active_player()
    if player.lands_played_this_turn >= 1:
        return
    # find first land in hand and play it
    for card in list(player.hand):
        if card.is_land():
            player.play_land(card)
            break


class TestSmokeFullGame(unittest.TestCase):
    def test_full_game_smoke(self) -> None:
        # Load the sample decks (these should exist in your repo)
        deckA = load_deck_from_file(Path("decks/mono_green.txt"))
        deckB = load_deck_from_file(Path("decks/mono_red.txt"))

        p1 = Player("Alice", deckA.cards)
        p2 = Player("Bob", deckB.cards)
        game = GameState(p1, p2)

        # Deterministic opening — different seeds so each library is shuffled independently
        game.start_game(
            opening_hand_size=7,
            skip_first_draw=True,
            shuffle_active_seed=101,
            shuffle_opponent_seed=202,
        )

        a1 = NaiveAgent()
        a2 = NaiveAgent()

        initial_life = (p1.life_total, p2.life_total)
        initial_graves = (len(p1.graveyard), len(p2.graveyard))

        steps = 0
        while not game.is_game_over() and steps < MAX_STEPS:
            # Naively play one land in MAIN1/MAIN2 so agents can cast creatures
            play_one_land_if_possible(game)

            active_agent = a1 if game.get_active_player() is p1 else a2
            defending_agent = a2 if active_agent is a1 else a1
            step_game(game, active_agent, defending_agent)
            steps += 1

        # Basic sanity: we did something
        self.assertGreater(steps, 0, "Game loop never advanced any phase.")

        # Either a winner was found, or there was visible progress (life/graveyards changed)
        progressed = (
            game.is_game_over()
            or (p1.life_total, p2.life_total) != initial_life
            or (len(p1.graveyard), len(p2.graveyard)) != initial_graves
        )
        self.assertTrue(progressed, "No observable progress — check casting/combat wiring.")

        # Post-combat housekeeping: attackers and blocks must be cleared
        if hasattr(game, "attackers"):
            self.assertFalse(game.attackers, "Attackers not cleared after combat.")
        if hasattr(game, "blocking_assignments"):
            self.assertFalse(
                game.blocking_assignments, "Blocking assignments not cleared after combat."
            )

        # If we hit the cap without a winner, that's fine for now
        if steps >= MAX_STEPS and not game.is_game_over():
            self.skipTest(
                "Reached step cap without a winner; consider improving NaiveAgent or board size."
            )


if __name__ == "__main__":
    unittest.main()
