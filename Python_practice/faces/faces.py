
def convert(text):
    """Convert emoticons to emoji."""
    text = text.replace(":)", "🙂")
    text = text.replace(":(", "🙁")
    return text


def main():
    # Prompt user for input
    user_input = input("Please enter your text: ")

    # Convert emoticons to emoji and print result
    print(convert(user_input))


# Call main function
if __name__ == "__main__":
    main()
