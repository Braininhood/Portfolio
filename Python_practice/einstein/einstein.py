# Speed of light in meters per second
c = 300000000


def main():
    # Prompt the user for mass in kilograms
    mass = int(input("Enter mass in kilograms: "))

    # Calculate energy using E = mc^2
    energy = mass * c**2

    # Output the energy in Joules
    print(energy)


# Call main function
if __name__ == "__main__":
    main()
