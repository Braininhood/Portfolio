def get_height():
    while True:
        try:
            height = int(input("Height: "))
            if 1 <= height <= 8:
                return height
        except ValueError:
            pass
        print("Please enter an integer between 1 and 8.")


def print_row(spaces, bricks):
    # Print the spaces first
    print(" " * spaces, end="")
    # Then print the bricks
    print("#" * bricks)


def main():
    # Prompt the user for the pyramid's height
    height = get_height()

    # Print a pyramid of that height
    for i in range(height):
        # Calculate the number of spaces and bricks for each row
        spaces = height - i - 1
        bricks = i + 1

        # Print each row with the correct number of spaces and bricks
        print_row(spaces, bricks)


if __name__ == "__main__":
    main()
