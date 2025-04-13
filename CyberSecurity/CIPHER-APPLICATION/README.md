# CIPHER APPLICATION
Welcome to the Cipher Application! This web-based application allows users to encrypt and decrypt messages using various cipher techniques. Whether you're looking to send a secret message or learn about cryptography, this application provides a user-friendly interface to explore different cipher methods.

#### Video Demo: https://youtu.be/ndUT_BQAxoI
#### Description:

The Cipher Application is a web-based platform that enables users to encrypt and decrypt text messages using various well-known cipher techniques. Built as part of the CS50 course, this project demonstrates the practical application of cryptography in a user-friendly web environment. The goal of this project is to help users experiment with encryption methods while ensuring security through user authentication and session management.

This project was developed in Python using the Flask framework, with HTML, CSS, and JavaScript for the front end. It also features an SQLite database to store user credentials, ensuring password security with hashing methods.
Key Features:

    User Authentication:
        Sign Up: Users can register by creating an account with a username and password. Passwords must meet specific security criteria, including at least 8 characters, an uppercase letter, a lowercase letter, a digit, and a special character. This ensures that the user credentials are robust.
        Login: Registered users can log in to access the cipher functionalities. User sessions are securely managed, and user IDs are stored using Flask's session management system.
        Logout: Users can securely log out, which clears their session data to prevent unauthorized access.

    Ciphers Supported:
        Fibonacci Cipher: A cipher based on Fibonacci numbers where characters in the message are shifted according to the Fibonacci sequence.
        Caesar Cipher: One of the simplest and most famous ciphers, shifting each letter of the message by a fixed number of positions.
        Vigenère Cipher: A more complex cipher that uses a keyword to shift characters, providing more security than the Caesar cipher by incorporating a polyalphabetic substitution.
        Atbash Cipher: A straightforward substitution cipher where the alphabet is reversed, with A substituted for Z, B for Y, and so on.

    Each of these ciphers has both an encryption and decryption function, and users can input their message and select their cipher method to either encode or decode it. This allows the application to serve as both an educational tool and a practical encryption platform.

    Responsive Design: The application's front end is built with a responsive design that works seamlessly on both desktop and mobile browsers. This ensures a consistent user experience regardless of the device being used.

Design Choices:

One of the main design considerations for this project was user authentication. In order to keep the application secure, password hashing was implemented using the werkzeug.security module. This ensures that plain text passwords are never stored in the database, providing security in case the database is ever compromised. This decision was based on best practices in security, as storing hashed passwords is essential in modern applications.

For the cipher operations, I chose to implement multiple ciphers to give users a range of options to experiment with. Each cipher is unique and offers different levels of complexity:

    The Fibonacci cipher introduces users to a lesser-known encryption technique that is not commonly seen in most applications.
    The Caesar and Atbash ciphers were chosen for their simplicity and historical significance.
    The Vigenère cipher was included because it introduces users to a more secure, polyalphabetic cipher.

To manage session data securely, I decided to clear user sessions upon logout and also on visiting the app initially (at /home) to ensure that no session is remembered from previous visits. This prevents any accidental reuse of credentials and ensures users always begin with a fresh session.
File Structure:

    static/: This directory contains the static files for the application, including CSS for styling and JavaScript for client-side functionality.
        style.css: Defines the visual style for the application's pages, making it both aesthetically pleasing and user-friendly.
        scripts.js: Handles any front-end interactions or dynamic elements, such as form validation or UI updates.

    templates/: This directory contains the HTML templates that Flask renders for each page.
        base.html: The base layout that defines the structure of the application. Other templates extend from this file.
        home.html: The landing page template that greets users and prompts them to either log in or sign up.
        login.html: The login form template that allows users to enter their credentials.
        signup.html: The signup form template that users can use to create a new account.
        cipher.html: The page where users can input their message, choose a cipher, and encrypt or decrypt their text.

    app.py: The main application file. This file handles the routing, form submissions, and overall backend logic. It also initializes the database and manages user sessions.

    users.py: Handles the database-related functions, such as creating tables and checking user credentials.

    cipher_functions.py: Contains the logic for the various cipher operations, including encryption and decryption for each supported cipher.

    users.db: The SQLite database where user information (usernames and hashed passwords) is stored.

Contribution:

Contributions are welcome! If you'd like to contribute, please fork the repository and submit a pull request. You can also reach out with suggestions, bug reports, or requests for additional features.
License:

This project is licensed under the MIT License, allowing for open-source contribution and usage.
