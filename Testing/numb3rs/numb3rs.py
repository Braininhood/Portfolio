import re
import sys


def main():
    print(validate(input("IPv4 Address: ")))


def validate(ip):
    # Define a regular expression pattern to match valid IPv4 addresses
    pattern = r"^(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\." \
              r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\." \
              r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\." \
              r"(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$"

    # Use re.fullmatch to ensure the entire string matches the pattern
    return bool(re.fullmatch(pattern, ip))


if __name__ == "__main__":
    main()
