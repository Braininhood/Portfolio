from cs50 import SQL
from werkzeug.security import generate_password_hash, check_password_hash

# Set up the database connection
db = SQL("sqlite:///users.db")  # Make sure your SQLite database file is correctly named


def register_user(username, password):
    """Register a new user with a hashed password."""
    hashed_password = generate_password_hash(password)  # Hash the password
    try:
        # Check if the username already exists
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if existing_user:
            print("Username already taken. Please choose a different one.")
            return False  # Indicate registration failed

        # Insert the new user if username is not taken
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hashed_password)
        print(f"User {username} registered successfully.")
        return True  # Indicate registration successful
    except Exception as e:
        print(f"Error registering user: {e}")
        return False  # Indicate registration failed


def check_user(username, password):
    """Check if the username exists and verify the password."""
    try:
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        print("User found:", user)

        if user:  # Ensure the user exists
            stored_hash = user[0]['hash']  # Get the stored hash
            print("Stored hash:", stored_hash)
            print("Entered password (for debugging):", password)

            if check_password_hash(stored_hash, password):  # Verify the password
                print("Password matched")
                return True
            else:
                print("Password did not match")
        else:
            print("User not found")
    except Exception as e:
        print(f"Error during login check: {e}")

    return False


def create_tables():
    """Create necessary tables in the database."""
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            hash TEXT NOT NULL
        )
    """)
    print("Tables created (if they didn't already exist).")
