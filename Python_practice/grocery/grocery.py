def main():
    grocery_list = {}

    # Continuously prompt the user for grocery items
    while True:
        try:
            # Prompt user for an item, stripping whitespace and making it case-insensitive
            item = input().strip().lower()

            # Update the count of the item in the grocery list
            if item in grocery_list:
                grocery_list[item] += 1
            else:
                grocery_list[item] = 1

        except EOFError:
            # Print a newline to separate cursor from next prompt after EOF
            print()
            break  # Exit loop on control-d (EOF)

    # Sort items alphabetically and print each item in uppercase with its count
    for item in sorted(grocery_list):
        print(f"{grocery_list[item]} {item.upper()}")


if __name__ == "__main__":
    main()
