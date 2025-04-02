def main():
    fraction = input("Fraction (X/Y): ")
    try:
        percentage = convert(fraction)
        print(gauge(percentage))
    except (ValueError, ZeroDivisionError) as e:
        print(f"Error: {e}")


def convert(fraction: str) -> int:
    """Converts a fraction in X/Y format to a percentage."""
    try:
        x, y = fraction.split("/")
        x = int(x)
        y = int(y)

        if y == 0:
            raise ZeroDivisionError("Denominator cannot be zero.")
        if x > y:
            raise ValueError("Numerator cannot be greater than denominator.")

        # Calculate and return the percentage rounded to the nearest integer
        return round((x / y) * 100)
    except ValueError:
        raise ValueError("Invalid input. Both numerator and denominator must be integers.")


def gauge(percentage: int) -> str:
    """Returns a string representing the fuel gauge."""
    if percentage <= 1:
        return "E"
    elif percentage >= 99:
        return "F"
    else:
        return f"{percentage}%"


if __name__ == "__main__":
    main()
