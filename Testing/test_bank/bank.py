def main():
    # Prompt the user for a greeting
    greeting = input("Greeting: ")
    # Get the corresponding value based on the greeting
    print(f"${value(greeting)}")


def value(greeting: str) -> int:
    # Normalize the greeting to lower case for case-insensitive comparison
    greeting = greeting.lower()

    if greeting.startswith("hello"):
        return 0
    elif greeting.startswith("h"):
        return 20
    else:
        return 100


if __name__ == "__main__":
    main()
