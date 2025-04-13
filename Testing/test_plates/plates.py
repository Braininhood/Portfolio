def main():
    plate = input("Plate: ")
    if is_valid(plate):
        print("Valid")
    else:
        print("Invalid")


def is_valid(s: str) -> bool:
    return (
        check_length(s)
        and starts_with_letters(s)
        and numbers_at_end(s)
        and no_punctuation(s)
    )


def check_length(s: str) -> bool:
    """Check if the plate length is between 2 and 6 characters."""
    return 2 <= len(s) <= 6


def starts_with_letters(s: str) -> bool:
    """Check if the plate starts with at least two letters."""
    return s[:2].isalpha()


def numbers_at_end(s: str) -> bool:
    """Check if numbers appear only at the end and the first number is not '0'."""
    has_number = False
    for i, char in enumerate(s):
        if char.isdigit():
            # Ensure all following characters are digits
            if not has_number and char == '0':
                return False  # First number cannot be '0'
            has_number = True
        elif has_number:
            return False  # Letters found after numbers
    return True


def no_punctuation(s: str) -> bool:
    """Check that the plate contains only letters and numbers (no punctuation)."""
    return s.isalnum()


if __name__ == "__main__":
    main()
