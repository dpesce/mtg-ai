from typing import List, Dict, Optional
from .card import Card
import random

phases = [
    "UNTAP",
    "UPKEEP",
    "DRAW",
    "MAIN1",
    "BEGINNING_OF_COMBAT",
    "DECLARE_ATTACKERS",
    "DECLARE_BLOCKERS",
    "COMBAT_DAMAGE",
    "END_OF_COMBAT",
    "MAIN2",
    "ENDING",
]

phase_step_map = {
    "UNTAP": "Untap step",
    "UPKEEP": "Upkeep step",
    "DRAW": "Draw step",
    "MAIN1": "Precombat main phase",
    "BEGINNING_OF_COMBAT": "Beginning of combat",
    "DECLARE_ATTACKERS": "Declare attackers",
    "DECLARE_BLOCKERS": "Declare blockers",
    "COMBAT_DAMAGE": "Combat damage",
    "END_OF_COMBAT": "End of combat",
    "MAIN2": "Postcombat main phase",
    "ENDING": "Ending phase",
}


class Player:
    def __init__(self, name: str, deck: List[Card]):
        self.name = name
        self.life_total: int = 20
        self.library: List[Card] = deck.copy()
        self.hand: List[Card] = []
        self.battlefield: List[Card] = []
        self.graveyard: List[Card] = []
        self.exile: List[Card] = []
        self.mana_pool: Dict[str, int] = {
            "W": 0,  # White
            "U": 0,  # Blue
            "B": 0,  # Black
            "R": 0,  # Red
            "G": 0,  # Green
            "C": 0,  # Colorless
        }
        self.lands_played_this_turn: int = 0

    def draw_card(self, game: "GameState") -> None:
        if not self.library:
            game.winner = game.get_opponent()
            return
        card = self.library.pop(0)
        card.zone = "hand"
        self.hand.append(card)

    def play_land(self, card: Card) -> None:
        if card not in self.hand or not card.is_land():
            return

        if self.lands_played_this_turn >= 1:
            raise ValueError(f"{self.name} has already played a land this turn.")

        self.hand.remove(card)
        card.zone = "battlefield"
        self.battlefield.append(card)
        self.lands_played_this_turn += 1

    def tap_land_for_mana(self, land: Card) -> bool:
        if land.tapped or not land.is_land():
            return False

        # Simplified land types -> mana mapping
        if "Plains" in land.subtypes:
            self.mana_pool["W"] += 1
        elif "Island" in land.subtypes:
            self.mana_pool["U"] += 1
        elif "Swamp" in land.subtypes:
            self.mana_pool["B"] += 1
        elif "Mountain" in land.subtypes:
            self.mana_pool["R"] += 1
        elif "Forest" in land.subtypes:
            self.mana_pool["G"] += 1
        else:
            self.mana_pool["C"] += 1  # Generic colorless fallback

        land.tapped = True
        return True

    def reset_mana_pool(self) -> None:
        for color in self.mana_pool:
            self.mana_pool[color] = 0

    def __repr__(self) -> str:
        return f"<Player {self.name}: {self.life_total} Life>"


class GameState:
    def __init__(self, player1: Player, player2: Player, line_length: int = 80):
        self.players = [player1, player2]
        self.active_player_index = 0
        self.turn_number = 1
        self.phase = "UNTAP"
        self.stack: List = []
        self.line_length = line_length

        self.skip_first_draw: bool = True
        self.winner: Optional[Player] = None

        self.attackers: List[Card] = []
        self.blocking_assignments: Dict[Card, list[Card]] = {}

    def shuffle_library(self, player: "Player", *, seed: Optional[int] = None) -> None:
        """
        Shuffle a single player's library in-place.
        If `seed` is provided, shuffling is deterministic (useful for tests).
        """
        rng = random.Random(seed) if seed is not None else random
        rng.shuffle(player.library)

    def shuffle_both_libraries(
        self,
        *,
        seed_active: Optional[int] = None,
        seed_opponent: Optional[int] = None,
    ) -> None:
        """
        Convenience: shuffle both players' libraries.
        Seeds allow deterministic but independent shuffles if desired.
        """
        self.shuffle_library(self.players[0], seed=seed_active)
        self.shuffle_library(self.players[1], seed=seed_opponent)

    def start_game(
        self,
        opening_hand_size: int = 7,
        skip_first_draw: bool = True,
        *,
        shuffle_active_seed: Optional[int] = None,
        shuffle_opponent_seed: Optional[int] = None,
    ) -> None:
        """
        Prepare game start: shuffle libraries, draw opening hands, and set phase to BEGINNING.
        The active player at turn 1 skips their beginning-phase draw if `skip_first_draw` is True.
        """
        # Shuffle each player's library (single-player shuffle, called twice)
        self.shuffle_both_libraries(
            seed_active=shuffle_active_seed,
            seed_opponent=shuffle_opponent_seed,
        )

        # Draw opening hands
        for _ in range(opening_hand_size):
            self.players[0].draw_card(self)
            self.players[1].draw_card(self)

        self.skip_first_draw = skip_first_draw
        self.phase = "UNTAP"

    def next_phase(self) -> None:
        for player in self.players:
            player.reset_mana_pool()
        idx = phases.index(self.phase)
        if idx < len(phases) - 1:
            self.phase = phases[idx + 1]
        else:
            # End of turn → next player's UNTAP
            self.phase = "UNTAP"
            self.next_turn()

    def next_turn(self) -> None:
        self.turn_number += 1
        self.active_player_index = 1 - self.active_player_index
        player = self.get_active_player()
        player.lands_played_this_turn = 0

    def get_active_player(self) -> Player:
        return self.players[self.active_player_index]

    def get_opponent(self) -> Player:
        return self.players[1 - self.active_player_index]

    def is_game_over(self) -> bool:
        return self.winner is not None

    def check_winner(self) -> None:
        if self.players[self.active_player_index].life_total <= 0:
            self.winner = self.players[1 - self.active_player_index]
        elif self.players[1 - self.active_player_index].life_total <= 0:
            self.winner = self.players[self.active_player_index]

    def board_state(self) -> str:

        p1 = self.get_active_player()
        p2 = self.get_opponent()

        ########################
        # Player 1's field

        strout = "*" * self.line_length + "\n"
        strout += (
            (f"* Turn {self.turn_number} | Phase: {self.phase}").ljust(self.line_length - 1)
            + "*"
            + "\n"
        )
        strout += "* " + "-" * (self.line_length - 4) + " *" + "\n"
        strout += (f"* Active player: {p1.name}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (f"* Life total: {p1.life_total}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (f"* Cards in hand: {len(p1.hand)}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (f"* Cards in library: {len(p1.library)}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (
            (f"* Cards in graveyard: {len(p1.graveyard)}").ljust(self.line_length - 1) + "*" + "\n"
        )
        strout += (f"* Cards in exile: {len(p1.hand)}").ljust(self.line_length - 1) + "*" + "\n"
        strout += "* " + "-" * (self.line_length - 4) + " *" + "\n"
        strout += (
            (f"* Cards on battlefield: {len(p1.battlefield)}").ljust(self.line_length - 1)
            + "*"
            + "\n"
        )

        strout += "* ".ljust(self.line_length - 1) + "*" + "\n"

        strland = "* "
        strcrea = "* "
        for card in p1.battlefield:
            if "Land" in card.types:
                strland += card.name[0]
                if card.tapped:
                    strland += "(T)"
                strland += " "
            if "Creature" in card.types:
                strcrea += card.name[0]
                if card.tapped:
                    strcrea += "(T)"
                strcrea += " "
        strland = strland.ljust(self.line_length - 1) + "*" + "\n"
        strcrea = strcrea.ljust(self.line_length - 1) + "*" + "\n"
        strout += strland
        strout += "* ".ljust(self.line_length - 1) + "*" + "\n"
        strout += strcrea
        strout += "* ".ljust(self.line_length - 1) + "*" + "\n"
        strout += "*" * self.line_length + "\n"

        ########################
        # Player 2's field

        strout += (f"* Opposing player: {p2.name}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (f"* Life total: {p2.life_total}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (f"* Cards in hand: {len(p2.hand)}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (f"* Cards in library: {len(p2.library)}").ljust(self.line_length - 1) + "*" + "\n"
        strout += (
            (f"* Cards in graveyard: {len(p2.graveyard)}").ljust(self.line_length - 1) + "*" + "\n"
        )
        strout += (f"* Cards in exile: {len(p2.hand)}").ljust(self.line_length - 1) + "*" + "\n"
        strout += "* " + "-" * (self.line_length - 4) + " *" + "\n"
        strout += (
            (f"* Cards on battlefield: {len(p2.battlefield)}").ljust(self.line_length - 1)
            + "*"
            + "\n"
        )

        strout += "* ".ljust(self.line_length - 1) + "*" + "\n"

        strland = "* "
        strcrea = "* "
        for card in p2.battlefield:
            if "Land" in card.types:
                strland += card.name[0]
                if card.tapped:
                    strland += "(T)"
                strland += " "
            if "Creature" in card.types:
                strcrea += card.name[0]
                if card.tapped:
                    strcrea += "(T)"
                strcrea += " "
        strland = strland.ljust(self.line_length - 1) + "*" + "\n"
        strcrea = strcrea.ljust(self.line_length - 1) + "*" + "\n"
        strout += strland
        strout += "* ".ljust(self.line_length - 1) + "*" + "\n"
        strout += strcrea
        strout += "* ".ljust(self.line_length - 1) + "*" + "\n"
        strout += "*" * self.line_length + "\n"

        return strout

    def __repr__(self) -> str:
        p1, p2 = self.players
        return f"Turn {self.turn_number} | Phase: {phase_step_map[self.phase]} | {p1.name}: {p1.life_total} Life, {p2.name}: {p2.life_total} Life"
