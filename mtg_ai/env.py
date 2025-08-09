from __future__ import annotations

import numpy as np
import gymnasium as gym
from typing import Any, Dict, Tuple, List, Optional, Callable, Protocol
from numpy.typing import NDArray

from .game_state import GameState, Player
from .game_controller import step_game
from .card import Card
from .agent import FullAgent
from . import game_actions as GA
from .agents.simple import NaiveAgent  # opponent baseline


# =========================
# Constants / action layout
# =========================

MAX_HAND = 10  # number of addressable hand slots for play/cast actions

# Discrete action IDs:
# 0                      -> PASS
# 1..MAX_HAND            -> PLAY_LAND at hand index (i-1)
# 1+MAX_HAND..2*MAX_HAND -> CAST_CREATURE at hand index (i-1-MAX_HAND)
# 2*MAX_HAND+1           -> ATTACK_NONE
# 2*MAX_HAND+2           -> ATTACK_ALL
ACTION_SIZE = 2 * MAX_HAND + 3

A_PASS = 0
A_PLAY_BASE = 1
A_CAST_BASE = 1 + MAX_HAND
A_ATTACK_NONE = 1 + 2 * MAX_HAND
A_ATTACK_ALL = 2 + 2 * MAX_HAND

# Phase names we care about
PHASES = [
    "UNTAP",
    "UPKEEP",
    "DRAW",
    "MAIN1",
    "BEGINNING_OF_COMBAT",
    "DECLARE_ATTACKERS",
    "DECLARE_BLOCKERS",
    "COMBAT_DAMAGE",
    "END_OF_COMBAT",
    "MAIN2",
    "ENDING",
]
PHASE_INDEX: Dict[str, int] = {p: i for i, p in enumerate(PHASES)}


# =========================
# Deck builder typing (no import of Deck class needed)
# =========================


class HasCards(Protocol):
    cards: List[Card]


DeckBuilderFn = Callable[[], Tuple[HasCards, HasCards]]


# =========================
# Learner Agent Proxy
# =========================


class LearnerProxy(FullAgent):
    """
    A tiny adapter that returns the choices specified by the environment's
    last action. If no choice was specified for a phase, it returns defaults
    (no casts; no attackers; no blocks).
    """

    def __init__(self) -> None:
        # set by env before calling step_game
        self.pending_cast_card: Optional[Card] = None
        self.pending_attackers: Optional[List[Card]] = None
        # (blockers omitted for baseline; returns {})

    def clear(self) -> None:
        self.pending_cast_card = None
        self.pending_attackers = None

    # -- FullAgent API --
    def choose_casts(self, game: GameState) -> List[Card]:
        if self.pending_cast_card is not None:
            card = self.pending_cast_card
            self.pending_cast_card = None
            if card in game.get_active_player().hand:
                return [card]
        return []

    def choose_attackers(self, game: GameState) -> List[Card]:
        if self.pending_attackers is not None:
            attackers = self.pending_attackers
            self.pending_attackers = None
            return attackers
        return []

    def choose_blockers(self, game: GameState) -> Dict[Card, List[Card]]:
        return {}


# =========================
# Minimal observation encoder
# =========================


def _cmc_from_cost(card: Card) -> int:
    if not getattr(card, "mana_cost", None):
        return 0
    cost = GA.parse_mana_cost(card.mana_cost or "")
    return int(cost.get("generic", 0) + sum(v for k, v in cost.items() if k != "generic"))


def _count_hand_buckets(player: Player) -> List[int]:
    lands = sum(1 for c in player.hand if c.is_land())
    c1 = c2 = c3 = c4p = 0
    for c in player.hand:
        if not c.is_creature():
            continue
        cmc = _cmc_from_cost(c)
        if cmc <= 1:
            c1 += 1
        elif cmc == 2:
            c2 += 1
        elif cmc == 3:
            c3 += 1
        else:
            c4p += 1
    return [lands, c1, c2, c3, c4p]


def _battlefield_counts(player: Player) -> List[int]:
    untapped_lands = sum(1 for c in player.battlefield if c.is_land() and not c.tapped)
    tapped_lands = sum(1 for c in player.battlefield if c.is_land() and c.tapped)
    ready_crea = sum(1 for c in player.battlefield if c.is_creature() and not c.summoning_sick and not c.tapped)
    sick_crea = sum(1 for c in player.battlefield if c.is_creature() and c.summoning_sick)
    other_crea = sum(1 for c in player.battlefield if c.is_creature()) - ready_crea - sick_crea
    ready_power = sum((c.power or 0) for c in player.battlefield if c.is_creature() and not c.summoning_sick and not c.tapped)
    return [untapped_lands, tapped_lands, ready_crea, sick_crea, other_crea, ready_power]


def _onehot_phase(phase: str) -> NDArray[np.float32]:
    vec: NDArray[np.float32] = np.zeros(len(PHASES), dtype=np.float32)
    idx = PHASE_INDEX.get(phase, None)
    if idx is not None:
        vec[idx] = 1.0
    return vec


def _encode_obs(game: GameState, pov: Player) -> NDArray[np.float32]:
    me = pov
    opp = game.get_opponent() if game.get_active_player() is me else game.get_active_player()
    phase_vec = _onehot_phase(game.phase)

    me_life = np.array([me.life_total / 20.0], dtype=np.float32)
    me_landplayed = np.array([float(me.lands_played_this_turn >= 1)], dtype=np.float32)
    me_pool = np.array([me.mana_pool[c] for c in ("W", "U", "B", "R", "G", "C")], dtype=np.float32) / 10.0
    me_hand = np.array(_count_hand_buckets(me), dtype=np.float32) / 10.0
    me_bf = np.array(_battlefield_counts(me), dtype=np.float32) / 10.0
    me_sizes = np.array([len(me.library) / 60.0, len(me.graveyard) / 60.0], dtype=np.float32)

    opp_life = np.array([opp.life_total / 20.0], dtype=np.float32)
    opp_pool = np.array([opp.mana_pool[c] for c in ("W", "U", "B", "R", "G", "C")], dtype=np.float32) / 10.0
    opp_sizes = np.array([len(opp.library) / 60.0, len(opp.hand) / 10.0, len(opp.graveyard) / 60.0], dtype=np.float32)
    opp_bf = np.array(_battlefield_counts(opp), dtype=np.float32) / 10.0

    obs = np.concatenate([
        phase_vec,            # 11
        me_life,              # 1
        me_landplayed,        # 1
        me_pool,              # 6
        me_hand,              # 5
        me_bf,                # 6
        me_sizes,             # 2
        opp_life,             # 1
        opp_pool,             # 6
        opp_sizes,            # 3
        opp_bf,               # 6
    ], dtype=np.float32)
    # mypy sees np.concatenate as Any; cast to concrete type
    from typing import cast as _cast
    return _cast(NDArray[np.float32], obs)


# =========================
# Legal action mask (no side-effects)
# =========================


def _untapped_land_counts(player: Player) -> Dict[str, int]:
    counts: Dict[str, int] = {"W": 0, "U": 0, "B": 0, "R": 0, "G": 0, "C": 0}
    for c in player.battlefield:
        if c.is_land() and not c.tapped:
            if "Plains" in c.subtypes:
                counts["W"] += 1
            elif "Island" in c.subtypes:
                counts["U"] += 1
            elif "Swamp" in c.subtypes:
                counts["B"] += 1
            elif "Mountain" in c.subtypes:
                counts["R"] += 1
            elif "Forest" in c.subtypes:
                counts["G"] += 1
            else:
                counts["C"] += 1
    return counts


def _can_auto_tap_to_pay_without_mutation(player: Player, card: Card) -> bool:
    if not card.is_creature():
        return False
    cost = GA.parse_mana_cost(card.mana_cost or "")
    pool = _untapped_land_counts(player)
    for color, amt in cost.items():
        if color == "generic":
            continue
        if pool.get(color, 0) < amt:
            return False
        pool[color] -= amt
    total_remaining = sum(pool.values())
    return total_remaining >= cost.get("generic", 0)


def _legal_mask(game: GameState, pov: Player) -> NDArray[np.bool_]:
    mask: NDArray[np.bool_] = np.zeros(ACTION_SIZE, dtype=np.bool_)
    mask[A_PASS] = True

    my_turn = (game.get_active_player() is pov)
    if not my_turn:
        return mask

    phase = game.phase

    if phase in ("MAIN1", "MAIN2"):
        if pov.lands_played_this_turn < 1:
            for i in range(min(len(pov.hand), MAX_HAND)):
                if pov.hand[i].is_land():
                    mask[A_PLAY_BASE + i] = True

        for i in range(min(len(pov.hand), MAX_HAND)):
            card = pov.hand[i]
            if card.is_creature() and _can_auto_tap_to_pay_without_mutation(pov, card):
                mask[A_CAST_BASE + i] = True

    elif phase == "DECLARE_ATTACKERS":
        ready = GA.get_attackers(pov)
        if ready:
            mask[A_ATTACK_NONE] = True
            mask[A_ATTACK_ALL] = True
        else:
            mask[A_ATTACK_NONE] = True

    # DECLARE_BLOCKERS and other phases: PASS only
    return mask


# =========================
# Environment
# =========================


class MTGEnv(gym.Env):
    """
    One-learner-vs-Naive agent environment.
    Each env.step() advances exactly one phase via game_controller.step_game().
    The learner can meaningfully act during:
      • MAIN1 / MAIN2: play a land; cast one creature
      • DECLARE_ATTACKERS: attack-none / attack-all
    All other phases: PASS.
    """
    metadata = {"render_modes": []}

    def __init__(self, deck_builder_fn: DeckBuilderFn, max_steps: int = 400):
        """
        deck_builder_fn: () -> Tuple[DeckLike, DeckLike]
            A callable returning two objects with .cards: List[Card]
        """
        super().__init__()
        self.deck_builder_fn: DeckBuilderFn = deck_builder_fn
        self.max_steps: int = max_steps
        self.step_count: int = 0

        # 48-dim observation (see encoder)
        self.observation_space = gym.spaces.Box(low=-1.0, high=1.0, shape=(48,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(ACTION_SIZE)

        self.learner_proxy = LearnerProxy()
        self.opponent = NaiveAgent()

        self.game: Optional[GameState] = None
        self.p1: Optional[Player] = None  # learner
        self.p2: Optional[Player] = None  # opponent

    def reset(
        self,
        seed: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Tuple[NDArray[np.float32], Dict[str, Any]]:
        super().reset(seed=seed)
        deckA, deckB = self.deck_builder_fn()
        self.p1 = Player("Learner", deckA.cards)
        self.p2 = Player("Opponent", deckB.cards)
        self.game = GameState(self.p1, self.p2)
        self.game.start_game(
            opening_hand_size=7,
            skip_first_draw=True,
            shuffle_active_seed=101,
            shuffle_opponent_seed=202,
        )
        self.step_count = 0
        self.learner_proxy.clear()

        obs = _encode_obs(self.game, self.p1)
        info: Dict[str, Any] = {"legal_mask": _legal_mask(self.game, self.p1)}
        return obs, info

    def step(
        self, action: int
    ) -> Tuple[NDArray[np.float32], float, bool, bool, Dict[str, Any]]:
        assert self.game is not None and self.p1 is not None and self.p2 is not None

        self._apply_action_intent(action)

        # Choose agents for this phase
        if self.game.get_active_player() is self.p1:
            active_agent: FullAgent = self.learner_proxy
            defending_agent: FullAgent = self.opponent
        else:
            active_agent = self.opponent
            defending_agent = self.learner_proxy  # proxy defends with {}

        step_game(self.game, active_agent, defending_agent)
        self.learner_proxy.clear()

        self.step_count += 1
        terminated = self.game.is_game_over()
        truncated = self.step_count >= self.max_steps

        reward = 0.0
        if terminated:
            reward = 1.0 if self.game.winner is self.p1 else -1.0

        obs = _encode_obs(self.game, self.p1)
        info: Dict[str, Any] = {"legal_mask": _legal_mask(self.game, self.p1)}
        return obs, reward, terminated, truncated, info

    # -------------------------
    # Internal helpers
    # -------------------------

    def _apply_action_intent(self, action: int) -> None:
        g = self.game
        assert g is not None and self.p1 is not None

        if g.get_active_player() is not self.p1:
            return

        phase = g.phase
        me = self.p1

        if action == A_PASS:
            return

        if phase in ("MAIN1", "MAIN2"):
            if A_PLAY_BASE <= action < A_CAST_BASE:
                idx = action - A_PLAY_BASE
                if 0 <= idx < len(me.hand) and me.hand[idx].is_land() and me.lands_played_this_turn < 1:
                    try:
                        me.play_land(me.hand[idx])
                    except Exception:
                        pass
                return
            if A_CAST_BASE <= action < A_ATTACK_NONE:
                idx = action - A_CAST_BASE
                if 0 <= idx < len(me.hand):
                    card = me.hand[idx]
                    if card.is_creature() and _can_auto_tap_to_pay_without_mutation(me, card):
                        self.learner_proxy.pending_cast_card = card
                return

        if phase == "DECLARE_ATTACKERS":
            if action == A_ATTACK_NONE:
                self.learner_proxy.pending_attackers = []
            elif action == A_ATTACK_ALL:
                self.learner_proxy.pending_attackers = GA.get_attackers(me)
            return
        # DECLARE_BLOCKERS and other phases: ignore (PASS)


def make_default_env(deck_builder_fn: DeckBuilderFn, max_steps: int = 400) -> MTGEnv:
    return MTGEnv(deck_builder_fn=deck_builder_fn, max_steps=max_steps)
