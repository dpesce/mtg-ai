from typing import Callable, Dict
from .agent import AttackAgent, BlockAgent
from .game_state import GameState
from . import game_actions as GA

PhaseHandler = Callable[[GameState, AttackAgent, BlockAgent], None]

_phase_handlers: Dict[str, PhaseHandler] = {
    "BEGINNING": lambda g, a, b: GA.beginning_phase(g),
    "MAIN1": lambda g, a, b: GA.main_phase(g),
    "BEGINNING_OF_COMBAT": lambda g, a, b: GA.beginning_of_combat(g),
    "DECLARE_ATTACKERS": lambda g, a, b: GA.declare_attackers(g, a.choose_attackers(g)),
    "DECLARE_BLOCKERS": lambda g, a, b: GA.declare_blockers(g, b.choose_blockers(g)),
    "COMBAT_DAMAGE": lambda g, a, b: GA.resolve_combat_damage(g),
    "END_OF_COMBAT": lambda g, a, b: GA.end_of_combat(g),
    "MAIN2": lambda g, a, b: GA.main_phase(g),
    "ENDING": lambda g, a, b: GA.ending_phase(g),
}


def step_game(
    game: GameState,
    attack_agent: AttackAgent,
    block_agent: BlockAgent
) -> None:
    handler = _phase_handlers.get(game.phase)
    if handler:
        handler(game, attack_agent, block_agent)
    game.next_phase()
