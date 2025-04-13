def check_luhn(number):
    """Function to implement Luhn's Algorithm to check if a credit card number is valid."""
    sum = 0
    is_second = False

    while number > 0:
        digit = number % 10

        # If it's the second digit from the right, multiply by 2
        if is_second:
            digit *= 2
            if digit > 9:
                digit -= 9  # Add the digits of the product

        sum += digit
        number //= 10
        is_second = not is_second

    # Return true if the total modulo 10 is congruent to 0
    return (sum % 10) == 0


def get_length(number):
    """Function to get the length of the credit card number."""
    length = 0
    while number != 0:
        number //= 10
        length += 1
    return length


def is_valid_length(number):
    """Function to check if the card has a valid length (13, 15, or 16 digits)."""
    length = get_length(number)
    return length == 13 or length == 15 or length == 16


def print_card_type(number):
    """Function to print the type of card based on the first digits and length."""
    length = get_length(number)
    start_digits = number

    # Get the first 2 digits
    while start_digits >= 100:
        start_digits //= 10

    # Determine the card type based on the starting digits and length
    if (start_digits == 34 or start_digits == 37) and length == 15:
        print("AMEX")
    elif 51 <= start_digits <= 55 and length == 16:
        print("MASTERCARD")
    elif (start_digits // 10 == 4) and (length == 13 or length == 16):
        print("VISA")
    else:
        print("INVALID")


def main():
    # Prompt user for a credit card number
    card_number = int(input("Number: "))

    # Check if the number passes Luhn's algorithm and is of valid length
    if check_luhn(card_number) and is_valid_length(card_number):
        print_card_type(card_number)
    else:
        print("INVALID")


if __name__ == "__main__":
    main()
