#include "bmp.h"
#include <getopt.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

// Function prototypes
void grayscale(int height, int width, RGBTRIPLE image[height][width]);
void reflect(int height, int width, RGBTRIPLE image[height][width]);
void blur(int height, int width, RGBTRIPLE image[height][width]);
void edges(int height, int width, RGBTRIPLE image[height][width]);

// Convert image to grayscale
void grayscale(int height, int width, RGBTRIPLE image[height][width])
{
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            // Calculate the average of the red, green, and blue values
            BYTE red = image[i][j].rgbtRed;
            BYTE green = image[i][j].rgbtGreen;
            BYTE blue = image[i][j].rgbtBlue;

            // Calculate the average, rounding
            BYTE average = round((red + green + blue) / 3.0);

            // Set each color to the average value
            image[i][j].rgbtRed = average;
            image[i][j].rgbtGreen = average;
            image[i][j].rgbtBlue = average;
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
            // Swap pixels horizontally
            RGBTRIPLE temp = image[i][j];
            image[i][j] = image[i][width - j - 1];
            image[i][width - j - 1] = temp;
        }
    }
}

// Blur image
void blur(int height, int width, RGBTRIPLE image[height][width])
{
    // Create a copy of the original image
    RGBTRIPLE copy[height][width];

    // Iterate over each pixel
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            int red = 0, green = 0, blue = 0, count = 0;

            // Check surrounding pixels
            for (int di = -1; di <= 1; di++)
            {
                for (int dj = -1; dj <= 1; dj++)
                {
                    int new_i = i + di;
                    int new_j = j + dj;

                    // Check if the new pixel is within bounds
                    if (new_i >= 0 && new_i < height && new_j >= 0 && new_j < width)
                    {
                        red += image[new_i][new_j].rgbtRed;
                        green += image[new_i][new_j].rgbtGreen;
                        blue += image[new_i][new_j].rgbtBlue;
                        count++;
                    }
                }
            }

            // Calculate average color values
            copy[i][j].rgbtRed = round((float) red / count);
            copy[i][j].rgbtGreen = round((float) green / count);
            copy[i][j].rgbtBlue = round((float) blue / count);
        }
    }

    // Copy blurred values back to the original image
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            image[i][j] = copy[i][j];
        }
    }
}

// Detect edges
void edges(int height, int width, RGBTRIPLE image[height][width])
{
    // Create a copy of the original image
    RGBTRIPLE copy[height][width];

    // Sobel operator kernels
    int Gx[3][3] = {{-1, 0, 1}, {-2, 0, 2}, {-1, 0, 1}};

    int Gy[3][3] = {{1, 2, 1}, {0, 0, 0}, {-1, -2, -1}};

    // Iterate over each pixel, excluding the border pixels
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            int redX = 0, greenX = 0, blueX = 0;
            int redY = 0, greenY = 0, blueY = 0;

            // Apply the Sobel operator
            for (int di = -1; di <= 1; di++)
            {
                for (int dj = -1; dj <= 1; dj++)
                {
                    int new_i = i + di;
                    int new_j = j + dj;

                    // Check if the new pixel is within bounds
                    if (new_i >= 0 && new_i < height && new_j >= 0 && new_j < width)
                    {
                        redX += image[new_i][new_j].rgbtRed * Gx[di + 1][dj + 1];
                        greenX += image[new_i][new_j].rgbtGreen * Gx[di + 1][dj + 1];
                        blueX += image[new_i][new_j].rgbtBlue * Gx[di + 1][dj + 1];

                        redY += image[new_i][new_j].rgbtRed * Gy[di + 1][dj + 1];
                        greenY += image[new_i][new_j].rgbtGreen * Gy[di + 1][dj + 1];
                        blueY += image[new_i][new_j].rgbtBlue * Gy[di + 1][dj + 1];
                    }
                }
            }

            // Calculate the magnitude of the gradient
            int red = round(sqrt(redX * redX + redY * redY));
            int green = round(sqrt(greenX * greenX + greenY * greenY));
            int blue = round(sqrt(blueX * blueX + blueY * blueY));

            // Clamp values to [0, 255]
            copy[i][j].rgbtRed = fmin(255, red);
            copy[i][j].rgbtGreen = fmin(255, green);
            copy[i][j].rgbtBlue = fmin(255, blue);
        }
    }

    // Copy edge-detected values back to the original image
    for (int i = 0; i < height; i++)
    {
        for (int j = 0; j < width; j++)
        {
            image[i][j] = copy[i][j];
        }
    }
}
