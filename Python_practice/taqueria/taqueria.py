# Menu dictionary with item prices
menu = {
    "Baja Taco": 4.25,
    "Burrito": 7.50,
    "Bowl": 8.50,
    "Nachos": 11.00,
    "Quesadilla": 8.50,
    "Super Burrito": 8.50,
    "Super Quesadilla": 9.50,
    "Taco": 3.00,
    "Tortilla Salad": 8.00
}


def main():
    total = 0.0  # Initialize total cost

    while True:
        try:
            # Prompt user for an item, stripping whitespace and titlecasing it
            item = input("Item: ").strip().title()

            # Check if the item is in the menu
            if item in menu:
                # Add the item's price to the total
                total += menu[item]
                # Print the current total cost, formatted to two decimal places
                print(f"Total: ${total:.2f}")

        except EOFError:
            # Print a newline to separate cursor from next prompt
            print()
            break  # Exit loop on control-d (EOF)


if __name__ == "__main__":
    main()
