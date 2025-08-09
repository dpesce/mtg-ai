from typing import Dict
from .card import Card
from .game_state import Player, GameState
from .agent import CastAgent
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


def auto_tap_for_cost(player: "Player", mana_cost: str) -> bool:
    """
    Greedy tap until cost met.  Returns True if successfully satisfied.
    Simplified: treats any untapped land producing one generic mana if colorless.
    """
    if can_pay_mana_cost(player, mana_cost):
        return True

    for land in [c for c in player.battlefield if c.is_land() and not c.tapped]:
        player.tap_land_for_mana(land)
        if can_pay_mana_cost(player, mana_cost):
            return True
    return False


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


def can_block(game: GameState, blocker: Card, attacker: Card) -> bool:
    if blocker.tapped or not blocker.is_creature():
        return False
    # Add more rules (e.g., flying/blocking rules) here
    return True


####################################
# phase handling


def _execute_casts(game: GameState, agent: CastAgent) -> None:
    player = game.get_active_player()
    for card in agent.choose_casts(game):
        if card not in player.hand:
            continue
        if card.mana_cost and auto_tap_for_cost(player, card.mana_cost):
            cast_creature(player, card)


def untap_step(game: GameState) -> None:
    """
    Untap permanents and clear summoning sickness for the active player.
    """
    player = game.get_active_player()
    for card in player.battlefield:
        # Untap everything
        card.tapped = False
        # Summoning sickness clears at the start of your turn
        if card.is_creature():
            card.summoning_sick = False


def upkeep_step(game: GameState) -> None:
    """
    Placeholder for future upkeep triggers. No-op for now.
    """
    return None


def draw_step(game: GameState) -> None:
    """
    Draw one card for the active player unless it's turn 1 and
    game.skip_first_draw is True.
    """
    player = game.get_active_player()
    if game.turn_number == 1 and game.skip_first_draw:
        return
    player.draw_card(game)


def precombat_main_phase(game: GameState, cast_agent: CastAgent) -> None:
    _execute_casts(game, cast_agent)


def beginning_of_combat(game: GameState) -> None:
    return None


def declare_attackers(game: GameState, attackers: list[Card]) -> None:
    player = game.get_active_player()
    legal_attackers = []

    for creature in attackers:
        if creature in player.battlefield and creature.is_creature() and not creature.tapped and not creature.summoning_sick:
            creature.tapped = True
            legal_attackers.append(creature)
        else:
            print(f"{creature.name} is not a valid attacker.")

    game.attackers = legal_attackers


def declare_blockers(game: GameState, assignments: Dict[Card, list[Card]]) -> None:
    defending_player = game.get_opponent()
    for attacker, blockers in assignments.items():
        if attacker not in game.attackers:
            raise ValueError(f"{attacker.name} is not attacking.")

        for blocker in blockers:
            if blocker not in defending_player.battlefield:
                raise ValueError(f"{blocker.name} not controlled by defender.")
            if not blocker.is_creature():
                raise ValueError(f"{blocker.name} is not a creature.")
            if blocker.tapped:
                raise ValueError(f"{blocker.name} is tapped.")
            # Prevent one blocker from blocking two attackers
            for prev in game.blocking_assignments.values():
                if blocker in prev:
                    raise ValueError(f"{blocker.name} already blocking something.")

        # Order is preserved as passed-in
        game.blocking_assignments[attacker] = list(blockers)


def resolve_combat_damage(game: GameState) -> None:
    attacker_controller = game.get_active_player()
    defender_controller = game.get_opponent()

    total_unblocked = 0

    for attacker in list(game.attackers):
        blockers = game.blocking_assignments.get(attacker, [])
        if not blockers:                 # ── unblocked
            total_unblocked += attacker.power or 0
            continue

        # --- attacker ➜ blockers (sequential lethal assignment) ---
        remaining_power = attacker.power or 0
        for blocker in blockers:
            lethal = blocker.toughness or 0
            if remaining_power >= lethal:
                defender_controller.battlefield.remove(blocker)
                blocker.zone = "graveyard"
                defender_controller.graveyard.append(blocker)
            remaining_power = max(0, remaining_power - lethal)

        # --- blockers ➜ attacker (sum of their power) -------------
        total_blocker_power = sum(b.power or 0 for b in blockers)
        if attacker.toughness is not None and total_blocker_power >= attacker.toughness:
            attacker_controller.battlefield.remove(attacker)
            attacker.zone = "graveyard"
            attacker_controller.graveyard.append(attacker)

    defender_controller.life_total -= total_unblocked
    game.attackers.clear()
    game.blocking_assignments.clear()
    game.check_winner()


def end_of_combat(game: GameState) -> None:
    return None


def postcombat_main_phase(game: GameState, cast_agent: CastAgent) -> None:
    _execute_casts(game, cast_agent)


def ending_phase(game: GameState) -> None:
    return None
