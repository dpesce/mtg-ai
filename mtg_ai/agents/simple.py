from typing import List, Dict
from mtg_ai.agent import FullAgent
from mtg_ai.game_state import GameState
from mtg_ai.card import Card
from mtg_ai.game_actions import can_pay_mana_cost, get_attackers, auto_tap_for_cost


class NaiveAgent(FullAgent):
    """Casts first affordable creature, attacks with all, never blocks."""

    # Cast
    def choose_casts(self, game: GameState) -> List[Card]:
        player = game.get_active_player()
        for card in player.hand:
            if card.is_creature():
                # Try to make the mana pool sufficient
                auto_tap_for_cost(player, card.mana_cost or "")
                if can_pay_mana_cost(player, card.mana_cost or ""):
                    return [card]
        return []

    # Attack
    def choose_attackers(self, game: GameState) -> List[Card]:
        return get_attackers(game.get_active_player())

    # Block
    def choose_blockers(self, game: GameState) -> Dict[Card, List[Card]]:
        return {}
