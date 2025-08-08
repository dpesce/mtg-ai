
from typing import Protocol, List, Dict
from .card import Card
from .game_state import GameState


class AttackAgent(Protocol):
    def choose_attackers(self, game: GameState) -> List[Card]:
        ...


class BlockAgent(Protocol):
    def choose_blockers(self, game: GameState) -> Dict[Card, list[Card]]:
        ...


# simple dummy agent that never blocks
class NoBlockAgent(BlockAgent):
    def choose_blockers(self, game: GameState) -> Dict[Card, list[Card]]:
        return {}


class OnePerAttackerAgent(BlockAgent):
    def choose_blockers(self, game: GameState) -> Dict[Card, list[Card]]:
        # block first attacker with first untapped creature
        blockers = {}
        defender = game.get_opponent()
        attackers = game.attackers
        avail = [c for c in defender.battlefield if not c.tapped]
        for atk, blk in zip(attackers, avail):
            blockers[atk] = [blk]       # note list wrapper
        return blockers
