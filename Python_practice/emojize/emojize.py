import emoji


def main():
    # Prompt user for input
    user_input = input("Enter text with emoji codes: ")
    # Convert and output the emojized string
    print(emoji.emojize(user_input, language="alias"))


if __name__ == "__main__":
    main()
