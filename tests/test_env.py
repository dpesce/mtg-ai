import unittest
import numpy as np
from typing import Tuple, List, Optional, cast
from numpy.typing import NDArray

from mtg_ai.card import Card
from mtg_ai.env import (
    MTGEnv,
    make_default_env,
    ACTION_SIZE,
    A_PLAY_BASE,
    A_CAST_BASE,
    A_ATTACK_NONE,
    A_ATTACK_ALL,
    _legal_mask,  # import mask helper to avoid stepping
)


# --------- test helpers ---------

class StubDeck:
    def __init__(self, cards: List[Card]) -> None:
        self.cards = cards


FOREST = {"name": "Forest", "uuid": "forest", "types": ["Land"], "subtypes": ["Forest"]}
BEAR = {
    "name": "Grizzly Bears",
    "uuid": "bear",
    "types": ["Creature"],
    "manaCost": "{1}{G}",
    "power": "2",
    "toughness": "2",
}
ELVES = {  # simple {G} one-drop for casting test
    "name": "Llanowar Elves",
    "uuid": "elves",
    "types": ["Creature"],
    "manaCost": "{G}",
    "power": "1",
    "toughness": "1",
}


def make_stub_decks() -> Tuple[StubDeck, StubDeck]:
    """Return two small decks with plenty of basics + bears."""
    def deck() -> StubDeck:
        cards: List[Card] = []
        # 20 Forests, 20 Bears
        for i in range(20):
            c = Card({**FOREST, "uuid": f"F{i}"})
            cards.append(c)
        for i in range(20):
            c = Card({**BEAR, "uuid": f"B{i}"})
            cards.append(c)
        return StubDeck(cards)
    return deck(), deck()


def step_until_phase(env: MTGEnv, target: str, max_steps: int = 200) -> None:
    """Advance with PASS until the game reaches the given phase."""
    steps = 0
    while env.game is not None and env.game.phase != target and steps < max_steps:
        # PASS to move one phase forward
        _, _, term, trunc, _ = env.step(0)
        if term or trunc:
            break
        steps += 1


def current_mask(env: MTGEnv) -> NDArray[np.bool_]:
    """Return the legal-action mask for the CURRENT phase without stepping."""
    assert env.game is not None and env.p1 is not None
    mask = _legal_mask(env.game, env.p1)
    return cast(NDArray[np.bool_], mask)


# --------- tests ---------

class EnvBasicsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.env = make_default_env(make_stub_decks)

    def test_reset_shapes_and_mask(self) -> None:
        obs, info = self.env.reset()
        self.assertIsInstance(obs, np.ndarray)
        self.assertEqual(obs.shape, (48,))
        mask = cast(NDArray[np.bool_], info["legal_mask"])
        self.assertEqual(mask.shape, (ACTION_SIZE,))
        self.assertEqual(mask.dtype, np.bool_)

    def test_main1_land_mask_and_once_per_turn(self) -> None:
        self.env.reset()
        # reach MAIN1
        step_until_phase(self.env, "MAIN1")
        assert self.env.game is not None
        me = self.env.game.get_active_player()

        # find a land index in hand (Optional narrowing)
        land_idx_opt: Optional[int] = next((i for i, c in enumerate(me.hand) if c.is_land()), None)
        assert land_idx_opt is not None, "No land in opening hand; adjust stub deck if flaky."
        land_idx: int = land_idx_opt

        # Get mask WITHOUT stepping away from MAIN1
        mask = current_mask(self.env)
        self.assertTrue(mask[A_PLAY_BASE + land_idx], "Land play should be legal in MAIN1.")

        # Play it (this will advance to BEGINNING_OF_COMBAT after MAIN1 handler)
        _, _, _, _, _ = self.env.step(A_PLAY_BASE + land_idx)

        # March to MAIN2; once-per-turn rule should forbid further land plays
        step_until_phase(self.env, "MAIN2")
        mask2 = current_mask(self.env)
        self.assertFalse(mask2[A_PLAY_BASE:(A_PLAY_BASE + 10)].any(), "Second land this turn should be illegal.")

    def test_cast_creature_during_main1(self) -> None:
        self.env.reset()
        step_until_phase(self.env, "MAIN1")
        assert self.env.game is not None
        me = self.env.game.get_active_player()

        # Ensure at least one untapped Forest on battlefield
        forest = Card({**FOREST, "uuid": "F_test"})
        me.battlefield.append(forest)

        # Add a {G} creature to hand
        elves = Card(ELVES)
        me.hand.append(elves)
        elves_idx = len(me.hand) - 1

        # Mask should allow CAST at that index (no step)
        mask = current_mask(self.env)
        self.assertTrue(mask[A_CAST_BASE + elves_idx], "CAST should be legal with one untapped Forest.")

        # Take CAST action in MAIN1; env will cast during main-phase handler
        _, _, _, _, _ = self.env.step(A_CAST_BASE + elves_idx)
        # After step, card should be on battlefield, not in hand
        self.assertIn(elves, me.battlefield)
        self.assertNotIn(elves, me.hand)
        self.assertTrue(elves.summoning_sick)

    def test_attack_mask_and_attack_all_flow(self) -> None:
        self.env.reset()
        assert self.env.game is not None
        me = self.env.game.get_active_player()

        # Put a ready creature on battlefield (no summoning sickness, untapped)
        bear = Card({**BEAR, "uuid": "B_ready"})
        bear.summoning_sick = False
        bear.tapped = False
        me.battlefield.append(bear)

        # Fast-forward to DECLARE_ATTACKERS
        step_until_phase(self.env, "DECLARE_ATTACKERS")

        # Mask for current phase (no stepping!)
        mask = current_mask(self.env)
        self.assertTrue(mask[A_ATTACK_NONE])
        self.assertTrue(mask[A_ATTACK_ALL])

        # Choose ATTACK_ALL (this advances to DECLARE_BLOCKERS)
        _, _, _, _, _ = self.env.step(A_ATTACK_ALL)
        assert self.env.game is not None
        self.assertIn(bear, self.env.game.attackers)
        self.assertTrue(bear.tapped)

        # Advance through damage; attackers cleared afterward
        step_until_phase(self.env, "COMBAT_DAMAGE")
        _, _, _, _, _ = self.env.step(0)  # resolve combat damage
        assert self.env.game is not None
        self.assertFalse(self.env.game.attackers)
        self.assertFalse(self.env.game.blocking_assignments)

    def test_non_turn_mask_only_pass(self) -> None:
        self.env.reset()
        assert self.env.game is not None
        # Force it to be opponent's turn (without marching through all phases)
        self.env.game.active_player_index = 1  # Opponent is active
        # Mask snapshot for current phase
        mask = current_mask(self.env)
        # Only PASS should be possible (environment design)
        self.assertTrue(mask[0])
        self.assertFalse(mask[1:].any())


class EnvRewardSmokeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.env = make_default_env(make_stub_decks)

    def test_reward_signal_and_termination(self) -> None:
        obs, info = self.env.reset()
        _ = obs  # unused
        steps = 0
        total_reward = 0.0
        rng = np.random.default_rng(42)

        while True:
            # Use CURRENT mask without stepping
            mask = current_mask(self.env)
            legal_ids = np.flatnonzero(mask)
            assert legal_ids.size > 0, "There should always be at least PASS legal."

            # Greedy/random policy
            action = int(legal_ids[0]) if rng.random() < 0.5 else int(rng.choice(legal_ids))

            obs, reward, terminated, truncated, _ = self.env.step(action)
            total_reward += float(reward)
            steps += 1

            # Reward must be in {-1.0, 0.0, +1.0}
            self.assertIn(reward, (-1.0, 0.0, 1.0))

            if terminated or truncated or steps > 2000:
                break

        self.assertIsInstance(total_reward, float)
        self.assertGreater(steps, 0)


if __name__ == "__main__":
    unittest.main()
