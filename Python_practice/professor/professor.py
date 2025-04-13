import random


def main():
    level = get_level()
    score = 0  # Initialize the user's score

    for _ in range(10):  # Generate 10 problems
        x = generate_integer(level)
        y = generate_integer(level)
        correct_answer = x + y

        # Print the math problem
        print(f"{x} + {y} = ", end="")

        for attempt in range(3):  # Allow up to 3 attempts
            try:
                user_answer = int(input())
                if user_answer == correct_answer:
                    score += 1  # Increment score for a correct answer
                    break
                else:
                    print("EEE")  # Indicate incorrect answer
            except ValueError:
                print("EEE")  # Indicate non-integer input

            if attempt == 2:  # If 3 attempts are exhausted
                print(f"{correct_answer}")  # Show the correct answer

    # Output final score
    print(score)  # Output just the score, without any additional text


def get_level():
    while True:
        try:
            level = int(input("Level: "))
            if level in [1, 2, 3]:
                return level
        except ValueError:
            pass  # Ignore invalid input and re-prompt


def generate_integer(level):
    if level == 1:
        return random.randint(0, 9)  # 1-digit integer
    elif level == 2:
        return random.randint(10, 99)  # 2-digit integer
    elif level == 3:
        return random.randint(100, 999)  # 3-digit integer
    else:
        raise ValueError  # Raise an error for invalid level


if __name__ == "__main__":
    main()
