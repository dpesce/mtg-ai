from typing import Dict
from .card import Card
from .game_state import Player, GameState
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


def attack(game: GameState) -> None:
    player = game.get_active_player()
    opponent = game.get_opponent()

    total_damage = 0
    unblocked_attackers = set(game.attackers)

    # Tap attackers
    for attacker in game.attackers:
        attacker.tapped = True

    # Handle blocking
    for blocker, attacker in game.blocking_assignments.items():
        if blocker.toughness is None or attacker.power is None:
            continue  # Skip edge cases

        # Simple 1v1 blocker: attacker and blocker destroy each other if power ≥ toughness
        if attacker.power >= blocker.toughness:
            opponent.battlefield.remove(blocker)
            blocker.zone = "graveyard"
            opponent.graveyard.append(blocker)
        if (blocker.power is not None) and (attacker.toughness is not None) and blocker.power >= attacker.toughness:
            player.battlefield.remove(attacker)
            attacker.zone = "graveyard"
            player.graveyard.append(attacker)

        # Remove from unblocked list
        unblocked_attackers.discard(attacker)

    # Deal damage from unblocked attackers
    for attacker in unblocked_attackers:
        if attacker.power:
            total_damage += attacker.power

    opponent.life_total -= total_damage
    print(f"{player.name} deals {total_damage} unblocked damage to {opponent.name}!")
    game.check_winner()

    # Cleanup
    game.attackers = []
    game.blocking_assignments = {}


def declare_attackers(game: GameState, attackers: list[Card]) -> None:
    player = game.get_active_player()
    legal_attackers = []

    for creature in attackers:
        if creature in player.battlefield and creature.is_creature() and not creature.tapped and not creature.summoning_sick:
            legal_attackers.append(creature)
        else:
            print(f"{creature.name} is not a valid attacker.")

    game.attackers = legal_attackers


def can_block(game: GameState, blocker: Card, attacker: Card) -> bool:
    if blocker.tapped or not blocker.is_creature():
        return False
    # Add more rules (e.g., flying/blocking rules) here
    return True


def declare_blockers(game: GameState, blocking_assignments: Dict[Card, Card]) -> None:
    defending_player_index = 1 - game.active_player_index
    defending_player = game.players[defending_player_index]

    for blocker, attacker in blocking_assignments.items():
        if blocker not in defending_player.battlefield:
            raise ValueError(f"{blocker.name} is not controlled by the defending player.")
        if not blocker.is_creature():
            raise ValueError(f"{blocker.name} is not a creature and can't block.")
        if blocker.tapped:
            raise ValueError(f"{blocker.name} is tapped and can't block.")
        if attacker not in game.attackers:
            raise ValueError(f"{attacker.name} is not attacking.")

        # Add additional combat rules here (e.g., flying/evasion)

        game.blocking_assignments[blocker] = attacker

####################################
# phase handlers


def beginning_phase(game: GameState) -> None:
    return None


def main_phase(game: GameState) -> None:
    return None


def beginning_of_combat(game: GameState) -> None:
    return None


# def declare_attackers(game: GameState) -> None:
#     return None


# def declare_blockers(game: GameState) -> None:
#     return None


def resolve_combat_damage(game: GameState) -> None:
    return None


def end_of_combat(game: GameState) -> None:
    return None


def ending_phase(game: GameState) -> None:
    return None
