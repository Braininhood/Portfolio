#include "helpers.h"
#include <math.h>

// Convert image to grayscale
void grayscale(int height, int width, RGBTRIPLE image[height][width])
{
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            // Calculate the average of the red, green, and blue values
            uint8_t average =
                round((image[i][j].rgbtRed + image[i][j].rgbtGreen + image[i][j].rgbtBlue) / 3.0);

            // Assign the average to all color channels
            image[i][j].rgbtRed = average;
            image[i][j].rgbtGreen = average;
            image[i][j].rgbtBlue = average;
        }
    }
}

// Convert image to sepia
void sepia(int height, int width, RGBTRIPLE image[height][width])
{
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            // Store original values
            uint8_t originalRed = image[i][j].rgbtRed;
            uint8_t originalGreen = image[i][j].rgbtGreen;
            uint8_t originalBlue = image[i][j].rgbtBlue;

            // Calculate new values for sepia filter
            int sepiaRed =
                round(0.393 * originalRed + 0.769 * originalGreen + 0.189 * originalBlue);
            int sepiaGreen =
                round(0.349 * originalRed + 0.686 * originalGreen + 0.168 * originalBlue);
            int sepiaBlue =
                round(0.272 * originalRed + 0.534 * originalGreen + 0.131 * originalBlue);

            // Ensure the new values don't exceed 255
            image[i][j].rgbtRed = (sepiaRed > 255) ? 255 : sepiaRed;
            image[i][j].rgbtGreen = (sepiaGreen > 255) ? 255 : sepiaGreen;
            image[i][j].rgbtBlue = (sepiaBlue > 255) ? 255 : sepiaBlue;
        }
    }
}

// Reflect image horizontally
void reflect(int height, int width, RGBTRIPLE image[height][width])
{
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width / 2; j++)
        {
            // Swap the pixels horizontally
            RGBTRIPLE temp = image[i][j];
            image[i][j] = image[i][width - 1 - j];
            image[i][width - 1 - j] = temp;
        }
    }
}

// Blur image
void blur(int height, int width, RGBTRIPLE image[height][width])
{
    // Create a temporary copy of the image to store the new blurred values
    RGBTRIPLE temp[height][width];

    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            int redSum = 0, greenSum = 0, blueSum = 0;
            int count = 0;

            // Iterate over the surrounding pixels (including itself)
            for (int di = -1; di <= 1; di++)
            {
                for (int dj = -1; dj <= 1; dj++)
                {
                    int newRow = i + di;
                    int newCol = j + dj;

                    // Ensure the surrounding pixel is within bounds
                    if (newRow >= 0 && newRow < height && newCol >= 0 && newCol < width)
                    {
                        redSum += image[newRow][newCol].rgbtRed;
                        greenSum += image[newRow][newCol].rgbtGreen;
                        blueSum += image[newRow][newCol].rgbtBlue;
                        count++;
                    }
                }
            }

            // Compute the average color values for blur
            temp[i][j].rgbtRed = round(redSum / (float) count);
            temp[i][j].rgbtGreen = round(greenSum / (float) count);
            temp[i][j].rgbtBlue = round(blueSum / (float) count);
        }
    }

    // Copy the blurred values from temp back to the original image
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            image[i][j] = temp[i][j];
        }
    }
}
