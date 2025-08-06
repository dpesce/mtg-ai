from typing import List, Dict, Optional
from core.card import Card
import random

phases = ["BEGINNING", "MAIN1", "COMBAT", "MAIN2", "ENDING"]


class Player:
    def __init__(self, name: str, deck: List[Card]):
        self.name = name
        self.life_total: int = 20
        self.library: List[Card] = deck.copy()
        random.shuffle(self.library)
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

    def draw_card(self, game: "GameState") -> None:
        if not self.library:
            game.winner = game.get_opponent()
            return
        card = self.library.pop(0)
        card.zone = "hand"
        self.hand.append(card)

    def play_land(self, card: Card) -> None:
        if card in self.hand and card.is_land():
            self.hand.remove(card)
            card.zone = "battlefield"
            self.battlefield.append(card)

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
    def __init__(self, player1: Player, player2: Player, linelength: int = 80):
        self.players = [player1, player2]
        self.active_player_index = 0
        self.turn_number = 1
        self.phase = "BEGINNING"
        self.stack: List = []
        self.linelength = linelength

        self.winner: Optional[Player] = None

    def next_phase(self) -> None:
        for player in self.players:
            player.reset_mana_pool()
        idx = phases.index(self.phase)
        if idx < len(phases) - 1:
            self.phase = phases[idx + 1]
        else:
            self.phase = "BEGINNING"
            self.next_turn()

    def next_turn(self) -> None:
        self.turn_number += 1
        self.active_player_index = 1 - self.active_player_index
        player = self.get_active_player()
        player.draw_card(self)

        # Reset summoning sickness and untap cards
        for card in player.battlefield:
            if card.is_creature():
                card.summoning_sick = False
            card.tapped = False

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

        strout = "*" * self.linelength + "\n"
        strout += (
            (f"* Turn {self.turn_number} | Phase: {self.phase}").ljust(self.linelength - 1)
            + "*"
            + "\n"
        )
        strout += "* " + "-" * (self.linelength - 4) + " *" + "\n"
        strout += (f"* Active player: {p1.name}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (f"* Life total: {p1.life_total}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (f"* Cards in hand: {len(p1.hand)}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (f"* Cards in library: {len(p1.library)}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (
            (f"* Cards in graveyard: {len(p1.graveyard)}").ljust(self.linelength - 1) + "*" + "\n"
        )
        strout += (f"* Cards in exile: {len(p1.hand)}").ljust(self.linelength - 1) + "*" + "\n"
        strout += "* " + "-" * (self.linelength - 4) + " *" + "\n"
        strout += (
            (f"* Cards on battlefield: {len(p1.battlefield)}").ljust(self.linelength - 1)
            + "*"
            + "\n"
        )

        strout += "* ".ljust(self.linelength - 1) + "*" + "\n"

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
        strland = strland.ljust(self.linelength - 1) + "*" + "\n"
        strcrea = strcrea.ljust(self.linelength - 1) + "*" + "\n"
        strout += strland
        strout += "* ".ljust(self.linelength - 1) + "*" + "\n"
        strout += strcrea
        strout += "* ".ljust(self.linelength - 1) + "*" + "\n"
        strout += "*" * self.linelength + "\n"

        ########################
        # Player 2's field

        strout += (f"* Opposing player: {p2.name}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (f"* Life total: {p2.life_total}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (f"* Cards in hand: {len(p2.hand)}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (f"* Cards in library: {len(p2.library)}").ljust(self.linelength - 1) + "*" + "\n"
        strout += (
            (f"* Cards in graveyard: {len(p2.graveyard)}").ljust(self.linelength - 1) + "*" + "\n"
        )
        strout += (f"* Cards in exile: {len(p2.hand)}").ljust(self.linelength - 1) + "*" + "\n"
        strout += "* " + "-" * (self.linelength - 4) + " *" + "\n"
        strout += (
            (f"* Cards on battlefield: {len(p2.battlefield)}").ljust(self.linelength - 1)
            + "*"
            + "\n"
        )

        strout += "* ".ljust(self.linelength - 1) + "*" + "\n"

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
        strland = strland.ljust(self.linelength - 1) + "*" + "\n"
        strcrea = strcrea.ljust(self.linelength - 1) + "*" + "\n"
        strout += strland
        strout += "* ".ljust(self.linelength - 1) + "*" + "\n"
        strout += strcrea
        strout += "* ".ljust(self.linelength - 1) + "*" + "\n"
        strout += "*" * self.linelength + "\n"

        return strout

    def __repr__(self) -> str:
        p1, p2 = self.players
        return f"Turn {self.turn_number} | Phase: {self.phase} | {p1.name}: {p1.life_total} Life, {p2.name}: {p2.life_total} Life"
