from typing import Callable, Dict
from .agent import FullAgent
from .game_state import GameState
from . import game_actions as GA

PhaseHandler = Callable[[GameState, FullAgent], None]

_phase_handlers: Dict[str, PhaseHandler] = {
    "BEGINNING": lambda g, agent: GA.beginning_phase(g),
    "MAIN1": lambda g, agent: GA.precombat_main_phase(g, agent),
    "BEGINNING_OF_COMBAT": lambda g, agent: GA.beginning_of_combat(g),
    "DECLARE_ATTACKERS": lambda g, agent: GA.declare_attackers(g, agent.choose_attackers(g)),
    "DECLARE_BLOCKERS": lambda g, agent: GA.declare_blockers(g, agent.choose_blockers(g)),
    "COMBAT_DAMAGE": lambda g, agent: GA.resolve_combat_damage(g),
    "END_OF_COMBAT": lambda g, agent: GA.end_of_combat(g),
    "MAIN2": lambda g, agent: GA.postcombat_main_phase(g, agent),
    "ENDING": lambda g, agent: GA.ending_phase(g),
}


def step_game(game: GameState, active_agent: FullAgent) -> None:
    """
    Drive exactly one phase for the active player using its agent.
    """
    _phase_handlers[game.phase](game, active_agent)
    game.next_phase()
