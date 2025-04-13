import validators


def main():
    email = input("Email: ")
    if validate_email(email):
        print("Valid")
    else:
        print("Invalid")


def validate_email(email):
    return validators.email(email)  # Returns True if valid, None otherwise


if __name__ == "__main__":
    main()
