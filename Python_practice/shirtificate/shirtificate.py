from fpdf import FPDF
from PIL import Image

# Create a subclass of FPDF to include a custom header
class PDF(FPDF):
    def header(self):
        # Set font for the header
        self.set_font("Helvetica", "B", 24)
        # Title: CS50 Shirtificate (centered horizontally)
        self.cell(0, 10, "CS50 Shirtificate", align="C", new_y="NEXT")  # Fixed line break
        self.ln(10)  # Line break before the image

# Create an instance of the PDF class
pdf = PDF(orientation='P', unit='mm', format='A4')
pdf.add_page()

# Prompt the user for their name
name = input("Enter your name: ")

# Get image dimensions using PIL (Pillow)
shirt_image_path = "shirtificate.png"
with Image.open(shirt_image_path) as img:
    img_width, img_height = img.size

# Add the shirt image, centered horizontally
pdf.image(shirt_image_path, x=(pdf.w - img_width * 0.75) / 2, y=pdf.get_y(), w=pdf.epw * 0.75)  # Scale the image to 75% of the page width

# Set font for the name
pdf.set_font("Helvetica", "B", 30)

# Set the color of the text to white (RGB: 255, 255, 255)
pdf.set_text_color(255, 255, 255)

# Add the user's name on top of the shirt, centered horizontally
pdf.set_y(pdf.get_y() - 140)  # Adjust the position to be on top of the shirt
pdf.cell(0, 10, f"{name} took CS50", align="C")

# Output the PDF to a file
pdf.output("shirtificate.pdf")

print("Shirtificate generated: shirtificate.pdf")
