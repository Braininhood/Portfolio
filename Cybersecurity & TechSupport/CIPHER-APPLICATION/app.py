import re
from flask import Flask, render_template, request, redirect, session, url_for, flash
from users import register_user, check_user, create_tables
from cipher_functions import fibonacci_cipher, caesar_cipher, vigenere_cipher, atbash_cipher

app = Flask(__name__)
app.secret_key = "Global"  # Change this to a strong secret key

# Create tables at startup
create_tables()


@app.route("/")
def index():
    """Render the index/home page and clear session."""
    session.clear()  # Clear the session at startup
    return redirect(url_for("home"))  # Redirect to the home page defined at /home


@app.route("/home")
def home():
    """Render the home page."""
    return render_template("home.html")  # Ensure you have a home.html file


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password").strip()  # Trim whitespace
        if check_user(username, password):  # Pass both username and password
            session["user_id"] = username  # Store user information in session
            return redirect("/cipher")
        flash("Invalid credentials", "error")  # Show error message
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check if the password meets the required criteria
        if not validate_password(password):
            flash("Password must be at least 8 characters long and include an uppercase letter, a lowercase letter, a digit, and a special character.", "error")
            return render_template("signup.html")

        if register_user(username, password):  # Check if registration was successful
            return redirect(url_for("login"))  # Redirect to login page after signup
        flash("Username already taken. Please choose a different one.", "error")  # Show error message

    return render_template("signup.html")


def validate_password(password):
    """Check if the password is valid based on the specified criteria."""
    if (len(password) < 8 or
        not re.search(r"[A-Z]", password) or  # At least one uppercase letter
        not re.search(r"[a-z]", password) or  # At least one lowercase letter
        not re.search(r"[0-9]", password) or  # At least one digit
            not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)):  # At least one special character
        return False
    return True


@app.route("/cipher", methods=["GET", "POST"])
def cipher():
    result = ""

    if request.method == "POST":
        message = request.form.get("message").strip()  # Trim whitespace
        cipher_choice = request.form.get("cipher_choice")
        action = request.form.get("action")

        if not message:
            result = "Message cannot be empty."
            return render_template("cipher.html", result=result)

        # Limit the message to a maximum of 1000 words
        if len(message.split()) > 1000:
            result = "Message cannot exceed 1000 words."
            return render_template("cipher.html", result=result)

        try:
            if action == "encrypt":
                if cipher_choice == 'f':  # Fibonacci Cipher
                    num_fib = int(request.form.get("num_fib", 1))
                    result = fibonacci_cipher(message, num_fib, mode='encrypt')
                elif cipher_choice == 'c':  # Caesar Cipher
                    shift_value = int(request.form.get("shift_value", 1))
                    result = caesar_cipher(message, shift_value, mode='encrypt')
                elif cipher_choice == 'v':  # Vigenère Cipher
                    keyword = request.form.get("keyword", "")
                    result = vigenere_cipher(message, keyword, mode='encrypt')
                elif cipher_choice == 'a':  # Atbash Cipher
                    result = atbash_cipher(message)
                else:
                    result = "Invalid cipher choice."

            elif action == "decrypt":
                if cipher_choice == 'f':  # Fibonacci Cipher
                    num_fib = int(request.form.get("num_fib", 1))
                    result = fibonacci_cipher(message, num_fib, mode='decrypt')
                elif cipher_choice == 'c':  # Caesar Cipher
                    shift_value = int(request.form.get("shift_value", 1))
                    result = caesar_cipher(message, shift_value, mode='decrypt')
                elif cipher_choice == 'v':  # Vigenère Cipher
                    keyword = request.form.get("keyword", "")
                    result = vigenere_cipher(message, keyword, mode='decrypt')
                elif cipher_choice == 'a':  # Atbash Cipher
                    result = atbash_cipher(message)  # Atbash is reversible
                else:
                    result = "Invalid cipher choice."
        except Exception as e:
            result = f"An error occurred: {str(e)}"

        return render_template("cipher.html", result=result)

    return render_template("cipher.html")


@app.route("/logout", methods=["POST"])
def logout():
    """Log out the user."""
    session.clear()  # Clear the session
    flash("You have been logged out.", "success")  # Optional: Flash a logout message
    return redirect(url_for("home"))  # Redirect to the home page


if __name__ == "__main__":
    app.run(debug=True)
