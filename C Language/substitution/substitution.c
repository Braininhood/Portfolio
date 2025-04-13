#include <cs50.h>
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Function prototypes
bool is_valid_key(string key);
char substitute(char c, string key);

int main(int argc, string argv[])
{
    // Check if the program is executed with exactly one command-line argument
    if (argc != 2)
    {
        printf("Usage: ./substitution key\n");
        return 1;
    }

    // Validate the key
    string key = argv[1];
    if (!is_valid_key(key))
    {
        printf("Key must contain 26 unique alphabetic characters.\n");
        return 1;
    }

    // Prompt the user for plaintext
    string plaintext = get_string("plaintext:  ");

    // Print the ciphertext
    printf("ciphertext: ");

    // Substitute each character in the plaintext
    for (int i = 0, n = strlen(plaintext); i < n; i++)
    {
        printf("%c", substitute(plaintext[i], key));
    }

    // Print a newline at the end
    printf("\n");

    return 0;
}

// Function to validate the key
bool is_valid_key(string key)
{
    // Check if the key length is 26
    if (strlen(key) != 26)
    {
        return false;
    }

    bool letters[26] = {false}; // Array to track unique letters

    // Check if each character is a letter and unique
    for (int i = 0; i < 26; i++)
    {
        char c = tolower(key[i]);

        // Ensure the character is alphabetic and hasn't been used before
        if (!isalpha(c) || letters[c - 'a'])
        {
            return false;
        }

        letters[c - 'a'] = true;
    }

    return true;
}

// Function to substitute a character using the key
char substitute(char c, string key)
{
    // If uppercase letter, map to corresponding uppercase letter in the key
    if (isupper(c))
    {
        return toupper(key[c - 'A']);
    }
    // If lowercase letter, map to corresponding lowercase letter in the key
    else if (islower(c))
    {
        return tolower(key[c - 'a']);
    }
    // Return non-alphabetic characters unchanged
    else
    {
        return c;
    }
}
