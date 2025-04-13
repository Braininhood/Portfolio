#include <cs50.h>
#include <stdio.h>

// Function prototypes
int get_height(void);
void print_row(int spaces, int bricks);

int main(void)
{
    // Prompt the user for the pyramid's height
    int height = get_height();

    // Print a pyramid of that height
    for (int i = 0; i < height; i++)
    {
        // Calculate the number of spaces and bricks for each row
        int spaces = height - i - 1;
        int bricks = i + 1;

        // Print each row with the correct number of spaces and bricks
        print_row(spaces, bricks);
    }
}

// Function to prompt the user for a valid pyramid height
int get_height(void)
{
    int height;
    do
    {
        height = get_int("Height: ");
    }
    while (height < 1 || height > 8); // Ensure the height is between 1 and 8
    return height;
}

// Function to print spaces and bricks for each row
void print_row(int spaces, int bricks)
{
    // Print the spaces first
    for (int i = 0; i < spaces; i++)
    {
        printf(" ");
    }
    // Then print the bricks
    for (int i = 0; i < bricks; i++)
    {
        printf("#");
    }
    // Move to the next line after printing the row
    printf("\n");
}
