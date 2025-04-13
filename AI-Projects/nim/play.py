#from nim import train, play

#ai = train(10000)
#play(ai)

from nim import train, Nim
import random
import time


def play(ai, human_player=None):
    """
    Play a game of Nim against the AI.
    `human_player` can be set to 0 or 1 to specify whether
    the human player moves first or second.
    """

    # If no player order set, choose human's order randomly
    if human_player is None:
        human_player = random.randint(0, 1)

    # Create a new game
    game = Nim()

    # Game loop
    while True:
        # Print contents of piles
        print("\nPiles:")
        for i, pile in enumerate(game.piles):
            print(f"Pile {i}: {pile}")
        print()

        # Compute available actions
        available_actions = Nim.available_actions(game.piles)
        time.sleep(1)

        # Let the human make a move
        if game.player == human_player:
            print("Your Turn")
            while True:
                try:
                    pile = int(input("Choose Pile: "))
                    count = int(input("Choose Count: "))
                    if (pile, count) in available_actions:
                        break
                    else:
                        print("Invalid move, try again.")
                except ValueError:
                    print("Invalid input. Enter numbers only.")

        # AI makes a move
        else:
            print("AI's Turn")
            pile, count = ai.choose_action(game.piles, epsilon=False)
            print(f"AI chose to take {count} from pile {pile}.")

        # Make move
        game.move((pile, count))

        # Check for winner
        if game.winner is not None:
            print("\nGAME OVER")
            winner = "Human" if game.winner == human_player else "AI"
            print(f"Winner is {winner}")
            return


# Train AI and play against it
ai = train(10000)
play(ai)
