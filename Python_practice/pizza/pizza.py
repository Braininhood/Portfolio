import sys
import csv
from tabulate import tabulate


def read_csv(file_path):
    try:
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Get the first row as header
            data = [row for row in reader]  # Store remaining rows as data
            return header, data
    except FileNotFoundError:
        sys.exit("File does not exist")


def main():
    # Check command-line arguments
    if len(sys.argv) != 2:
        sys.exit("Usage: python pizza.py <filename.csv>")

    file_path = sys.argv[1]

    # Check file extension
    if not file_path.endswith(".csv"):
        sys.exit("Not a CSV file")

    # Read the CSV file and retrieve the header and data
    header, data = read_csv(file_path)

    # Print table using tabulate in grid format
    print(tabulate(data, headers=header, tablefmt="grid"))


if __name__ == "__main__":
    main()
