import random


def main():
    # Prompt user for a valid level
    while True:
        try:
            level = int(input("Level: "))
            if level > 0:
                break
        except ValueError:
            pass  # Ignore invalid input and re-prompt

    # Generate a random number between 1 and the specified level
    secret_number = random.randint(1, level)

    # Prompt user to guess the number
    while True:
        try:
            guess = int(input("Guess: "))
            if guess <= 0:
                continue
            if guess < secret_number:
                print("Too small!")
            elif guess > secret_number:
                print("Too large!")
            else:
                print("Just right!")
                break
        except ValueError:
            pass  # Ignore invalid input and re-prompt


if __name__ == "__main__":
    main()
