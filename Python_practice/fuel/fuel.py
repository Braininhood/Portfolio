def get_fuel_level():
    while True:
        try:
            # Prompt the user for input in X/Y format
            fraction = input("Fraction (X/Y): ")
            # Split the input to get X and Y as integers
            x, y = fraction.split("/")
            x = int(x)
            y = int(y)

            # Check for division by zero or if X is greater than Y
            if y == 0:
                raise ZeroDivisionError
            if x > y:
                raise ValueError

            # Calculate the percentage
            percentage = round((x / y) * 100)

            # Output based on the calculated percentage
            if percentage <= 1:
                return "E"
            elif percentage >= 99:
                return "F"
            else:
                return f"{percentage}%"

        except (ValueError, ZeroDivisionError):
            # If input is invalid, loop and prompt again
            print("Invalid input. Please enter a valid fraction.")


# Main program execution
if __name__ == "__main__":
    print(get_fuel_level())
