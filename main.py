import json
from mtg_ai.card import Card
from mtg_ai.game_state import Player, GameState
from mtg_ai.game_actions import cast_creature, attack, get_attackers

###############################################

def run_demo() -> None:

    ###############################################
    # load card pool

    with open("./cards/AllPrintings.json") as f:
        all_data = json.load(f)
        
    ###############################################
    # temporary functions to load a simple deck

    fire_elemental = Card(all_data["data"]['FDN']['cards'][537])
    mountain = Card(all_data["data"]['FDN']['cards'][287])

    def load_simple_deck():
        creatures = [fire_elemental.copy() for _ in range(40)]
        lands = [mountain.copy() for _ in range(20)]
        return(creatures + lands)

    ###############################################

    # load decks
    deck1 = load_simple_deck()
    deck2 = load_simple_deck()

    p1 = Player("Alice", deck1)
    p2 = Player("Bob", deck2)
    game = GameState(p1, p2)

    # Draw opening hands
    for _ in range(7):
        p1.draw_card(game)
        p2.draw_card(game)

    while not game.is_game_over():
        player = game.get_active_player()
        # print(game)

        if game.phase == "BEGINNING":
            game.next_phase()

        elif game.phase == "MAIN1":
            
            # Try to play a land (only 1 per turn for now)
            for card in player.hand:
                if card.is_land():
                    player.play_land(card)
                    print(f"{player.name} plays {card.name}")
                    break

            # Tap lands to generate mana
            for card in player.battlefield:
                if card.is_land() and not card.tapped:
                    player.tap_land_for_mana(card)

            # Try casting creatures after mana is in the pool
            for card in player.hand:
                if cast_creature(player, card):
                    print(f"{player.name} casts {card.name}")
                    break

            game.next_phase()

        elif game.phase == "COMBAT":
            attackers = get_attackers(player)
            if attackers:
                attack(game, attackers)
            game.next_phase()

        elif game.phase == "MAIN2":
            game.next_phase()

        elif game.phase == "ENDING":
            print(game.board_state())
            game.next_phase()

    if game.winner:
        print(f"Game over! Winner: {game.winner.name}")

###############################################

if __name__ == "__main__":
    run_demo()

