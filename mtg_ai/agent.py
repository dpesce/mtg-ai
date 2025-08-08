
from typing import Protocol, List, Dict
from .card import Card
from .game_state import GameState


class AttackAgent(Protocol):
    def choose_attackers(self, game: GameState) -> List[Card]:
        ...


class BlockAgent(Protocol):
    def choose_blockers(self, game: GameState) -> Dict[Card, Card]:
        ...
