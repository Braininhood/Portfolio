def get_change():
    while True:
        try:
            dollars = float(input("Change owed: "))
            if dollars >= 0:
                # Convert dollars to cents
                cents = round(dollars * 100)
                return cents
        except ValueError:
            pass
        print("Please enter a non-negative number.")


def main():
    # Prompt the user for change owed in dollars
    cents = get_change()

    # Initialize counter for the number of coins
    coins = 0

    # Calculate the number of quarters (25 cents)
    coins += cents // 25
    cents %= 25

    # Calculate the number of dimes (10 cents)
    coins += cents // 10
    cents %= 10

    # Calculate the number of nickels (5 cents)
    coins += cents // 5
    cents %= 5

    # Calculate the number of pennies (1 cent)
    coins += cents

    # Print the total number of coins used
    print(coins)


if __name__ == "__main__":
    main()
