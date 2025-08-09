from mtg_ai.game_state import GameState, Player
from mtg_ai.game_controller import step_game
from mtg_ai.agents import NaiveAgent
from mtg_ai.deck_builder import load_deck_from_file
from pathlib import Path

###############################################


def run_demo() -> None:
    # Build decks (sample lists under decks/)
    deckA = load_deck_from_file(Path("decks/mono_green.txt"))
    deckB = load_deck_from_file(Path("decks/mono_red.txt"))

    # Players
    p1 = Player("Alice", deckA.cards)
    p2 = Player("Bob", deckB.cards)
    game = GameState(p1, p2)

    # Agents
    agent1 = NaiveAgent()
    agent2 = NaiveAgent()

    # Start of game: shuffle, draw opening hands, set phase to BEGINNING,
    # and skip starting player’s first draw by default.
    game.start_game()

    # Main loop
    while not game.is_game_over():
        active_agent = agent1 if game.get_active_player() is p1 else agent2
        defending_agent = agent2 if active_agent is agent1 else agent1
        step_game(game, active_agent, defending_agent)

    print("Winner:", game.winner.name)

# def run_demo():
#     deckA = load_deck_from_file(Path("decks/mono_green.txt"))
#     deckB = load_deck_from_file(Path("decks/mono_green.txt"))
#     p1, p2 = Player("Alice", deckA.cards), Player("Bob", deckB.cards)
#     game = GameState(p1, p2)
#     agent = NaiveAgent()

#     while not game.is_game_over():
#         step_game(game, agent)

#     print("Winner:", game.winner.name)

# def run_demo():
#     p1, p2 = Player("Alice", []), Player("Bob", [])
#     game = GameState(p1, p2)
#     agent1, agent2 = NaiveAgent(), NaiveAgent()

#     while not game.is_game_over():
#         current_agent = agent1 if game.get_active_player() is p1 else agent2
#         step_game(game, current_agent)

#     print("Winner:", game.winner.name)

# def run_demo() -> None:

#     ###############################################
#     # load card pool

#     with open("./cards/AllPrintings.json") as f:
#         all_data = json.load(f)

#     ###############################################
#     # temporary functions to load a simple deck

#     fire_elemental = Card(all_data["data"]['FDN']['cards'][537])
#     mountain = Card(all_data["data"]['FDN']['cards'][287])

#     def load_simple_deck():
#         creatures = [fire_elemental.copy() for _ in range(40)]
#         lands = [mountain.copy() for _ in range(20)]
#         return(creatures + lands)

#     ###############################################

#     # load decks
#     deck1 = load_simple_deck()
#     deck2 = load_simple_deck()

#     p1 = Player("Alice", deck1)
#     p2 = Player("Bob", deck2)
#     game = GameState(p1, p2)

#     # Draw opening hands
#     for _ in range(7):
#         p1.draw_card(game)
#         p2.draw_card(game)

#     while not game.is_game_over():
#         player = game.get_active_player()
#         # print(game)

#         if game.phase == "BEGINNING":
#             game.next_phase()

#         elif game.phase == "MAIN1":
            
#             # Try to play a land (only 1 per turn for now)
#             for card in player.hand:
#                 if card.is_land():
#                     player.play_land(card)
#                     print(f"{player.name} plays {card.name}")
#                     break

#             # Tap lands to generate mana
#             for card in player.battlefield:
#                 if card.is_land() and not card.tapped:
#                     player.tap_land_for_mana(card)

#             # Try casting creatures after mana is in the pool
#             for card in player.hand:
#                 if cast_creature(player, card):
#                     print(f"{player.name} casts {card.name}")
#                     break

#             game.next_phase()

#         elif game.phase == "COMBAT":
#             attackers = get_attackers(player)
#             if attackers:
#                 resolve_combat_damage(game)
#             game.next_phase()

#         elif game.phase == "MAIN2":
#             game.next_phase()

#         elif game.phase == "ENDING":
#             print(game.board_state())
#             game.next_phase()

#     if game.winner:
#         print(f"Game over! Winner: {game.winner.name}")

###############################################

if __name__ == "__main__":
    run_demo()

