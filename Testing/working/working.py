import re
import sys


def main():
    try:
        print(convert(input("Hours: ")))
    except ValueError:
        sys.exit("ValueError")


def convert(s):
    # Define a regex pattern to match the specified 12-hour time formats
    pattern = r"^(\d{1,2})(?::(\d{2}))? (AM|PM) to (\d{1,2})(?::(\d{2}))? (AM|PM)$"
    match = re.match(pattern, s)

    # Raise a ValueError if the input format is incorrect
    if not match:
        raise ValueError

    # Extract the matched groups
    start_hour, start_minute, start_period, end_hour, end_minute, end_period = match.groups()

    # Convert start and end times to 24-hour format, or raise ValueError for invalid times
    start_time_24 = convert_to_24_hour(start_hour, start_minute or "00", start_period)
    end_time_24 = convert_to_24_hour(end_hour, end_minute or "00", end_period)

    return f"{start_time_24} to {end_time_24}"


def convert_to_24_hour(hour, minute, period):
    # Validate the hour and minute values
    hour = int(hour)
    minute = int(minute)

    if hour < 1 or hour > 12 or minute < 0 or minute >= 60:
        raise ValueError

    # Convert the hour based on the AM/PM period
    if period == "AM":
        hour = 0 if hour == 12 else hour
    elif period == "PM":
        hour = 12 if hour == 12 else hour + 12

    return f"{hour:02}:{minute:02}"


if __name__ == "__main__":
    main()
