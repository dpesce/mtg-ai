from typing import Callable, Dict
from .agent import FullAgent
from .game_state import GameState
from . import game_actions as GA

# Each handler gets (game, active_agent, defending_agent)
PhaseHandler = Callable[[GameState, FullAgent, FullAgent], None]

_phase_handlers: Dict[str, PhaseHandler] = {
    "UNTAP": lambda g, a, d: GA.untap_step(g),
    "UPKEEP": lambda g, a, d: GA.upkeep_step(g),
    "DRAW": lambda g, a, d: GA.draw_step(g),
    "MAIN1": lambda g, a, d: GA.precombat_main_phase(g, a),
    "BEGINNING_OF_COMBAT": lambda g, a, d: GA.beginning_of_combat(g),
    "DECLARE_ATTACKERS": lambda g, a, d: GA.declare_attackers(g, a.choose_attackers(g)),
    "DECLARE_BLOCKERS": lambda g, a, d: GA.declare_blockers(g, d.choose_blockers(g)),
    "COMBAT_DAMAGE": lambda g, a, d: GA.resolve_combat_damage(g),
    "END_OF_COMBAT": lambda g, a, d: GA.end_of_combat(g),
    "MAIN2": lambda g, a, d: GA.postcombat_main_phase(g, a),
    "ENDING": lambda g, a, d: GA.ending_phase(g),
}


def step_game(game: GameState, active_agent: FullAgent, defending_agent: FullAgent) -> None:
    """
    Advance exactly one phase for the active player using agents.
    """
    handler = _phase_handlers[game.phase]
    handler(game, active_agent, defending_agent)
    game.next_phase()
