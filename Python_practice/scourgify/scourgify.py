import sys
import csv


def main():
    # Check for correct number of command-line arguments
    if len(sys.argv) != 3:
        sys.exit("Usage: python scourgify.py input.csv output.csv")

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    try:
        # Open and read the input CSV file
        with open(input_file, "r") as csvfile:
            reader = csv.DictReader(csvfile)

            # Prepare to write to the output CSV file
            with open(output_file, "w", newline='') as outfile:
                fieldnames = ["first", "last", "house"]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames)

                writer.writeheader()

                # Process each row in the input file
                for row in reader:
                    # Split the "name" field into last and first names
                    last, first = row["name"].split(", ")
                    # Write to the new file with the separated names
                    writer.writerow({"first": first, "last": last, "house": row["house"]})

    except FileNotFoundError:
        sys.exit(f"Could not read {input_file}")


if __name__ == "__main__":
    main()
