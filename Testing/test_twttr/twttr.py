def main():
    text = input("Input: ")
    print("Output:", shorten(text))

def shorten(word):
    vowels = "AEIOUaeiou"
    result = ""
    for c in word:
        if c not in vowels:
            result += c
    return result

if __name__ == "__main__":
    main()
