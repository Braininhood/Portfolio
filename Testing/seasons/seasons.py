from datetime import date
import inflect
import sys


def main():
    # Prompt user for their birthdate
    birthdate = input("Enter your birthdate (YYYY-MM-DD): ")

    # Validate and parse the date
    try:
        birthdate = date.fromisoformat(birthdate)  # Convert input to a date object
    except ValueError:
        # Exit with status 1 on invalid date format
        print("Invalid date format.")
        sys.exit(1)

    # Get the current date
    today = date.today()

    # Calculate the difference in days
    days_lived = (today - birthdate).days

    # Convert days lived to minutes
    minutes_lived = days_lived * 24 * 60

    # Use inflect to convert the number to words without "and"
    p = inflect.engine()
    minutes_words = p.number_to_words(minutes_lived, andword="")

    # Capitalize and add "minutes" at the end
    result = f"{minutes_words} minutes"
    print(result.capitalize())  # Capitalize the result


if __name__ == "__main__":
    main()
