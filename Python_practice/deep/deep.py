# Prompt the user for their answer
answer = input("What is the answer to the Great Question of Life, the Universe, and Everything? ")

# Check if the answer matches any accepted forms (case-insensitively)
if answer.strip().lower() in ["42", "forty-two", "forty two"]:
    print("Yes")
else:
    print("No")
