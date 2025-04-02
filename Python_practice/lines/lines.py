import sys
import os


def count_lines_of_code(file_path):
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()

            # Count lines that are not blank and not comments
            loc = sum(1 for line in lines if line.strip() and not line.lstrip().startswith("#"))
        return loc
    except FileNotFoundError:
        sys.exit("File does not exist")


def main():
    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python lines.py <filename.py>")

    file_path = sys.argv[1]

    # Check file extension
    if not file_path.endswith(".py"):
        sys.exit("Not a Python file")

    # Get the count of lines of code
    loc = count_lines_of_code(file_path)
    print(f"Lines of code: {loc}")


if __name__ == "__main__":
    main()
