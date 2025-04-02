def main():
    # Prompt the user for time
    time = input("Time: ").strip()
    # Convert time to float hours
    hours = convert(time)

    # Determine which meal time it is, if any
    if 7 <= hours <= 8:
        print("breakfast time")
    elif 12 <= hours <= 13:
        print("lunch time")
    elif 18 <= hours <= 19:
        print("dinner time")

def convert(time):
    # Check if the time is in 12-hour format
    if "a.m." in time or "p.m." in time:
        time, period = time.split()
        hours, minutes = time.split(":")
        hours = int(hours)
        minutes = int(minutes)

        # Convert to 24-hour format if PM
        if period.lower() == "p.m." and hours != 12:
            hours += 12
        elif period.lower() == "a.m." and hours == 12:
            hours = 0
    else:
        # 24-hour format
        hours, minutes = time.split(":")
        hours = int(hours)
        minutes = int(minutes)

    # Convert hours and minutes to float
    return hours + minutes / 60

if __name__ == "__main__":
    main()
