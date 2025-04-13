def remove_vowels(text):
    vowels = "AEIOUaeiou"
    result = ""
    for c in text:
        if c not in vowels:
            result += c
    return result


# Prompt user for input
text = input("Input: ")
# Output the text without vowels
print("Output:", remove_vowels(text))
