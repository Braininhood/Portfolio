import inflect


def main():
    # Initialize the inflect engine
    p = inflect.engine()

    # Collect names until the end of input
    names = []
    print("Enter names (Ctrl-D to finish):")
    try:
        while True:
            name = input()
            names.append(name)
    except EOFError:
        pass

    # Create the formatted string with the names list
    farewell = f"Adieu, adieu, to {p.join(names)}"

    # Output the farewell message
    print(farewell)


if __name__ == "__main__":
    main()
