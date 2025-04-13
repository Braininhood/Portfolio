import csv
import sys


def main():
    # Check for command-line usage
    if len(sys.argv) != 3:
        print("Usage: python dna.py database.csv sequence.txt")
        sys.exit(1)

    # Read database file into a variable
    database = []
    with open(sys.argv[1], "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            # Convert counts of STRs from strings to integers
            for key in row:
                if key != 'name':
                    row[key] = int(row[key])
            database.append(row)

    # Read DNA sequence file into a variable
    with open(sys.argv[2], "r") as file:
        dna_sequence = file.read()

    # Find longest match of each STR in DNA sequence
    str_counts = {}
    str_names = reader.fieldnames[1:]  # All STR names (except the 'name' field)

    for str_name in str_names:
        str_counts[str_name] = longest_match(dna_sequence, str_name)

    # Check database for matching profiles
    for person in database:
        match = True
        for str_name in str_names:
            if person[str_name] != str_counts[str_name]:
                match = False
                break
        if match:
            print(person['name'])
            return

    print("No match")


def longest_match(sequence, subsequence):
    """Returns length of longest run of subsequence in sequence."""

    longest_run = 0
    subsequence_length = len(subsequence)
    sequence_length = len(sequence)

    for i in range(sequence_length):
        count = 0

        while True:
            start = i + count * subsequence_length
            end = start + subsequence_length

            if sequence[start:end] == subsequence:
                count += 1
            else:
                break

        longest_run = max(longest_run, count)

    return longest_run


if __name__ == "__main__":
    main()
