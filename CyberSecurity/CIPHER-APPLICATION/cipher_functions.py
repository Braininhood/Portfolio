import string

# Encrypt or decrypt a message using the Fibonacci sequence for character shifting


def fibonacci_cipher(message, num_fib, mode='encrypt'):
    def fibonacci(n):
        fib_sequence = [0, 1]
        while len(fib_sequence) < n:
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        return fib_sequence[:n]

    fib_sequence = fibonacci(len(message))
    result_message = []

    for i, char in enumerate(message):
        shift_value = fib_sequence[i % num_fib]
        if mode == 'decrypt':
            shift_value = -shift_value

        if char.isdigit():
            new_char = (int(char) + shift_value) % 10
            result_message.append(str(new_char))

        elif char.islower():
            new_char = chr((ord(char) - ord('a') + shift_value) % 26 + ord('a'))
            result_message.append(new_char)

        elif char.isupper():
            new_char = chr((ord(char) - ord('A') + shift_value) % 26 + ord('A'))
            result_message.append(new_char)

        elif char in string.punctuation:
            special_chars = string.punctuation
            idx = (special_chars.index(char) + shift_value) % len(special_chars)
            result_message.append(special_chars[idx])

        else:
            result_message.append(char)

    return ''.join(result_message)


# Caesar cipher implementation
def caesar_cipher(message, shift_value, mode='encrypt'):
    result_message = []
    for char in message:
        if char.islower():
            base = ord('a')
            new_char = chr((ord(char) - base + (shift_value if mode ==
                           'encrypt' else -shift_value)) % 26 + base)
            result_message.append(new_char)
        elif char.isupper():
            base = ord('A')
            new_char = chr((ord(char) - base + (shift_value if mode ==
                           'encrypt' else -shift_value)) % 26 + base)
            result_message.append(new_char)
        elif char.isdigit():
            new_char = (int(char) + (shift_value if mode == 'encrypt' else -shift_value)) % 10
            result_message.append(str(new_char))
        else:
            result_message.append(char)
    return ''.join(result_message)


# Vigenère cipher implementation
def vigenere_cipher(message, keyword, mode='encrypt'):
    keyword = keyword.lower()
    result_message = []
    keyword_length = len(keyword)

    for i, char in enumerate(message):
        if char.isalpha():
            shift_value = ord(keyword[i % keyword_length]) - ord('a')
            if mode == 'decrypt':
                shift_value = -shift_value

            if char.islower():
                base = ord('a')
                new_char = chr((ord(char) - base + shift_value) % 26 + base)
                result_message.append(new_char)
            elif char.isupper():
                base = ord('A')
                new_char = chr((ord(char) - base + shift_value) % 26 + base)
                result_message.append(new_char)
        else:
            result_message.append(char)

    return ''.join(result_message)


# Atbash cipher implementation (encryption and decryption are the same)
def atbash_cipher(message):
    result_message = []
    for char in message:
        if char.islower():
            new_char = chr(ord('a') + (ord('z') - ord(char)))
            result_message.append(new_char)
        elif char.isupper():
            new_char = chr(ord('A') + (ord('Z') - ord(char)))
            result_message.append(new_char)
        else:
            result_message.append(char)
    return ''.join(result_message)
