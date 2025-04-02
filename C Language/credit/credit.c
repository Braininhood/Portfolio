#include <cs50.h>
#include <stdio.h>

bool check_luhn(long number);
int get_length(long number);
bool is_valid_length(long number);
void print_card_type(long number);

int main(void)
{
    // Prompt user for a credit card number
    long card_number = get_long("Number: ");

    // Check if the number passes Luhn's algorithm and is of valid length
    if (check_luhn(card_number) && is_valid_length(card_number))
    {
        print_card_type(card_number);
    }
    else
    {
        printf("INVALID\n");
    }
}

// Function to implement Luhn's Algorithm to check if a credit card number is valid
bool check_luhn(long number)
{
    int sum = 0;
    int digit;
    bool is_second = false;

    // Loop through all digits starting from the last
    while (number > 0)
    {
        digit = number % 10;

        // If it's the second digit from the right, multiply by 2
        if (is_second)
        {
            digit *= 2;
            if (digit > 9)
            {
                digit -= 9; // Add the digits of the product
            }
        }

        sum += digit;
        number /= 10;
        is_second = !is_second;
    }

    // Return true if the total modulo 10 is congruent to 0
    return (sum % 10) == 0;
}

// Function to get the length of the credit card number
int get_length(long number)
{
    int length = 0;
    while (number != 0)
    {
        number /= 10;
        length++;
    }
    return length;
}

// Function to check if the card has a valid length (13, 15, or 16 digits)
bool is_valid_length(long number)
{
    int length = get_length(number);
    return (length == 13 || length == 15 || length == 16);
}

// Function to print the type of card based on the first digits and length
void print_card_type(long number)
{
    int length = get_length(number);
    long start_digits = number;

    // Get the first 2 digits
    while (start_digits > 100)
    {
        start_digits /= 10;
    }

    // Determine the card type based on the starting digits and length
    if ((start_digits == 34 || start_digits == 37) && length == 15)
    {
        printf("AMEX\n");
    }
    else if (start_digits >= 51 && start_digits <= 55 && length == 16)
    {
        printf("MASTERCARD\n");
    }
    else if ((start_digits / 10 == 4) && (length == 13 || length == 16))
    {
        printf("VISA\n");
    }
    else
    {
        printf("INVALID\n");
    }
}
