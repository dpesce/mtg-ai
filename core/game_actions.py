from typing import Dict
from core.card import Card
from core.game_state import Player, GameState
import re


def parse_mana_cost(mana_cost: str) -> Dict[str, int]:
    """
    Example: '{2}{R}{R}' => {'R': 2, 'generic': 2}
    """
    pattern = r"\{(.*?)\}"
    symbols = re.findall(pattern, mana_cost or "")
    mana = {"generic": 0}
    for symbol in symbols:
        if symbol.isdigit():
            mana["generic"] += int(symbol)
        else:
            mana[symbol] = mana.get(symbol, 0) + 1
    return mana


def can_pay_mana_cost(player: Player, mana_cost: str) -> bool:
    required = parse_mana_cost(mana_cost)
    pool = player.mana_pool.copy()

    # Pay colored mana
    for color, amount in required.items():
        if color == "generic":
            continue
        if pool.get(color, 0) < amount:
            return False
        pool[color] -= amount

    # Sum remaining pool for generic payment
    remaining = sum(pool.values())
    return remaining >= required.get("generic", 0)


def cast_creature(player: Player, card: Card) -> bool:
    if card not in player.hand or not card.is_creature():
        return False

    if card.mana_cost is not None:

        # Player must tap lands manually to build mana pool
        if not can_pay_mana_cost(player, card.mana_cost):
            return False

        # Pay colored mana
        cost = parse_mana_cost(card.mana_cost)
        for color, amount in cost.items():
            if color == "generic":
                continue
            player.mana_pool[color] -= amount

        # Pay generic using leftover mana
        generic = cost.get("generic", 0)
        for color in list(player.mana_pool.keys()):
            while generic > 0 and player.mana_pool[color] > 0:
                player.mana_pool[color] -= 1
                generic -= 1

    # Move to battlefield
    player.hand.remove(card)
    card.zone = "battlefield"
    card.tapped = False
    card.summoning_sick = True
    player.battlefield.append(card)
    return True


def count_untapped_lands(player: Player) -> int:
    return sum(1 for card in player.battlefield if card.is_land() and not card.tapped)


def get_attackers(player: Player) -> list:
    return [
        card
        for card in player.battlefield
        if card.is_creature() and not card.summoning_sick and not card.tapped
    ]


def attack(game: GameState, attacking_creatures: list[Card]) -> None:
    player = game.get_active_player()
    opponent = game.get_opponent()

    total_damage = 0
    for creature in attacking_creatures:
        if creature in player.battlefield and not creature.tapped and not creature.summoning_sick:
            creature.tapped = True
            if creature.power is not None:
                total_damage += creature.power

    opponent.life_total -= total_damage
    print(
        f"{player.name} attacks with {len(attacking_creatures)} creature(s) for {total_damage} damage!"
    )
    game.check_winner()
