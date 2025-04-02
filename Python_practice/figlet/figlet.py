import sys
import random
from pyfiglet import Figlet


def main():
    figlet = Figlet()

    # Check if arguments are provided
    if len(sys.argv) == 1:
        # No font specified, choose a random font
        font = random.choice(figlet.getFonts())
    elif len(sys.argv) == 3 and sys.argv[1] in ("-f", "--font"):
        # Font specified by the user
        font = sys.argv[2]
        # Check if the font is valid
        if font not in figlet.getFonts():
            sys.exit("Error: Invalid font name")
    else:
        # Invalid usage
        sys.exit("Usage: figlet.py or figlet.py -f <fontname>")

    # Set the font for the Figlet instance
    figlet.setFont(font=font)

    # Prompt the user for input
    user_input = input("Enter text: ")

    # Render the text with the chosen font and output it
    print(figlet.renderText(user_input))


if __name__ == "__main__":
    main()
