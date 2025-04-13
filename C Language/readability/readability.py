import re
import math

# Function to count the number of letters in the text


def count_letters(text):
    letters = 0
    for char in text:
        if char.isalpha():
            letters += 1
    return letters


# Function to count the number of words in the text
def count_words(text):
    words = len(text.split())
    return words


# Function to count the number of sentences in the text
def count_sentences(text):
    sentences = 0
    for char in text:
        if char in ['.', '!', '?']:
            sentences += 1
    return sentences


def main():
    # Prompt the user for some text
    text = input("Text: ")

    # Count the number of letters, words, and sentences in the text
    letters = count_letters(text)
    words = count_words(text)
    sentences = count_sentences(text)

    # Compute the Coleman-Liau index
    L = (letters / words) * 100
    S = (sentences / words) * 100
    index = 0.0588 * L - 0.296 * S - 15.8

    # Round the index to the nearest integer
    grade = round(index)

    # Output the grade level
    if grade < 1:
        print("Before Grade 1")
    elif grade >= 16:
        print("Grade 16+")
    else:
        print(f"Grade {grade}")


if __name__ == "__main__":
    main()
