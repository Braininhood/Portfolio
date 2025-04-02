import re
import sys


def main():
    print(parse(input("HTML: ")))


def parse(s):
    # Define a regular expression to match YouTube embed URLs in iframes
    pattern = r'src="https?://(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)"'

    # Use re.search to look for the URL pattern in the input string
    match = re.search(pattern, s)

    # If a match is found, return the short URL; otherwise, return None
    if match:
        video_id = match.group(1)
        return f"https://youtu.be/{video_id}"
    return None


if __name__ == "__main__":
    main()

