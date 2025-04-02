#include <cs50.h>
#include <stdio.h>

int main(void)
{
    // Prompt the user for change owed in cents
    int cents;
    do
    {
        cents = get_int("Change owed: ");
    }
    while (cents < 0); // Ensure the input is non-negative

    // Initialize counter for the number of coins
    int coins = 0;

    // Calculate the number of quarters (25 cents)
    coins += cents / 25;
    cents %= 25;

    // Calculate the number of dimes (10 cents)
    coins += cents / 10;
    cents %= 10;

    // Calculate the number of nickels (5 cents)
    coins += cents / 5;
    cents %= 5;

    // Calculate the number of pennies (1 cent)
    coins += cents;

    // Print the total number of coins used
    printf("%d\n", coins);
}
