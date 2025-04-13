import sys
import os
from PIL import Image, ImageOps


def main():
    # Check command-line arguments
    if len(sys.argv) != 3:
        sys.exit("Usage: python shirt.py input.jpg output.jpg")

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Check that both input and output have valid extensions
    valid_extensions = ('.jpg', '.jpeg', '.png')
    if not (input_path.lower().endswith(valid_extensions) and output_path.lower().endswith(valid_extensions)):
        sys.exit("Input and output files must be in .jpg, .jpeg, or .png format")

    # Ensure that input and output have the same file extension
    if os.path.splitext(input_path)[1].lower() != os.path.splitext(output_path)[1].lower():
        sys.exit("Input and output files must have the same file extension")

    # Attempt to open the input image and the shirt overlay
    try:
        with Image.open(input_path) as photo:
            with Image.open("shirt.png") as shirt:
                # Resize and crop the input photo to match the shirt's dimensions
                photo = ImageOps.fit(photo, shirt.size)

                # Overlay the shirt onto the resized photo
                photo.paste(shirt, shirt)

                # Save the output
                photo.save(output_path)
    except FileNotFoundError:
        sys.exit("Input file does not exist")


if __name__ == "__main__":
    main()
