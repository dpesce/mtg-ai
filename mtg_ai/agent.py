from typing import Protocol, List, Dict
from .card import Card
from .game_state import GameState


class AttackAgent(Protocol):
    def choose_attackers(self, game: GameState) -> List[Card]:
        ...


class BlockAgent(Protocol):
    def choose_blockers(self, game: GameState) -> Dict[Card, list[Card]]:
        ...


class CastAgent(Protocol):
    def choose_casts(self, game: GameState) -> List[Card]:
        """
        Return cards (in hand) to attempt to cast this main phase,
        in the order you want them cast.
        """
        ...


class FullAgent(AttackAgent, BlockAgent, CastAgent, Protocol):
    """Implements all decision types needed by the game controller."""
    ...
