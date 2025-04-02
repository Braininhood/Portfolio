# List of month names for easy lookup and validation
months = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def main():
    while True:
        try:
            # Prompt the user for a date
            date = input("Date: ").strip()

            # Check if the date is in MM/DD/YYYY format
            if "/" in date:
                month, day, year = date.split("/")
                month, day, year = int(month), int(day), int(year)

            # Check if the date is in Month Day, Year format
            elif " " in date and "," in date:
                month_str, day_year = date.split(" ", 1)
                day, year = day_year.split(", ")
                month = months.index(month_str) + 1
                day, year = int(day), int(year)

            else:
                raise ValueError("Invalid date format")

            # Validate day and month ranges
            if not (1 <= month <= 12) or not (1 <= day <= 31):
                raise ValueError("Invalid date values")

            # Output the date in YYYY-MM-DD format
            print(f"{year:04}-{month:02}-{day:02}")
            break

        except (ValueError, IndexError):
            # Catch any errors due to invalid input and prompt again
            print("Invalid date. Please try again.")


if __name__ == "__main__":
    main()
