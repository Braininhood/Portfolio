#include <cs50.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Function prototypes
bool only_digits(string s);
char rotate(char c, int key);

int main(int argc, string argv[])
{
    // Check if the program is executed with exactly one command-line argument
    if (argc != 2)
    {
        printf("Usage: ./caesar key\n");
        return 1;
    }

    // Check if the key contains only digits
    if (!only_digits(argv[1]))
    {
        printf("Usage: ./caesar key\n");
        return 1;
    }

    // Convert key from string to int
    int key = atoi(argv[1]);

    // Prompt the user for plaintext
    string plaintext = get_string("plaintext:  ");

    // Print ciphertext
    printf("ciphertext: ");

    // Rotate each character of the plaintext by the key
    for (int i = 0, n = strlen(plaintext); i < n; i++)
    {
        printf("%c", rotate(plaintext[i], key));
    }

    // Print a newline at the end
    printf("\n");

    return 0;
}

// Function to check if a string contains only digits
bool only_digits(string s)
{
    for (int i = 0, n = strlen(s); i < n; i++)
    {
        if (!isdigit(s[i]))
        {
            return false;
        }
    }
    return true;
}

// Function to rotate a character by a key
char rotate(char c, int key)
{
    if (isupper(c))
    {
        // Rotate uppercase letters
        return (c - 'A' + key) % 26 + 'A';
    }
    else if (islower(c))
    {
        // Rotate lowercase letters
        return (c - 'a' + key) % 26 + 'a';
    }
    else
    {
        // Return non-alphabetical characters unchanged
        return c;
    }
}
