#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define BLOCK_SIZE 512   // Size of the block to read
#define FILE_NAME_SIZE 8 // "###.jpg" + null terminator

int main(int argc, char *argv[])
{
    // Accept a single command-line argument
    if (argc != 2)
    {
        printf("Usage: ./recover FILE\n");
        return 1;
    }

    // Open the memory card
    FILE *card = fopen(argv[1], "r");
    if (card == NULL)
    {
        printf("Could not open %s\n", argv[1]);
        return 1;
    }

    // Create a buffer for a block of data
    uint8_t buffer[BLOCK_SIZE];
    FILE *img = NULL;
    int jpeg_count = 0;

    // While there's still data left to read from the memory card
    while (fread(buffer, 1, BLOCK_SIZE, card) == BLOCK_SIZE)
    {
        // Check for JPEG signature
        if (buffer[0] == 0xff && buffer[1] == 0xd8 && buffer[2] == 0xff &&
            (buffer[3] & 0xf0) == 0xe0)
        {
            // If a JPEG file is already open, close it
            if (img != NULL)
            {
                fclose(img);
            }

            // Create a new JPEG file
            char filename[FILE_NAME_SIZE];
            sprintf(filename, "%03d.jpg", jpeg_count);
            img = fopen(filename, "w");
            if (img == NULL)
            {
                printf("Could not create %s\n", filename);
                return 1;
            }
            jpeg_count++;
        }

        // If a JPEG file is open, write the block to it
        if (img != NULL)
        {
            fwrite(buffer, 1, BLOCK_SIZE, img);
        }
    }

    // Close any remaining file
    if (img != NULL)
    {
        fclose(img);
    }

    // Close the memory card
    fclose(card);

    return 0;
}
