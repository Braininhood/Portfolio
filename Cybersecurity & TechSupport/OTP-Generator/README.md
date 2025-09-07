# OTP Generator with Fibonacci Mapping and Proportional Mean Calculation
#### Video Demo: https://youtu.be/0uLdrnheyS8
#### Description:

This project is a secure One-Time Password (OTP) generator implemented in Python using the Tkinter library for a user-friendly graphical interface. The application creates OTPs based on a combination of mathematical methods, including Fibonacci sequence mapping and proportional mean calculations, enhancing both uniqueness and unpredictability in generated passwords.

### Key Features
1. **Fibonacci Sequence Mapping**: Each character in the user's login and password, as well as the current timestamp, is mapped to values from a Fibonacci sequence. This adds a layer of complexity to the password generation process.
2. **Proportional Mean Calculation**: The program calculates the harmonic and geometric means of non-zero values from the Fibonacci mapping and derives a proportional mean (PM) value. This PM is essential for producing digits that contribute to the OTP.
3. **Multiple OTP Options**: Users can select from four OTP generation modes:
   - **Option 1**: Numbers only
   - **Option 2**: Numbers and lowercase letters
   - **Option 3**: Numbers, lowercase, and uppercase letters, with enforced uppercase inclusion
   - **Option 4**: Numbers, lowercase and uppercase letters, and special characters, with a minimum inclusion of uppercase letters and special characters

### Files Included
- `project.py`: Main application file containing all logic for OTP generation and GUI interaction.
- `FibonacciHelper`: A helper class for generating Fibonacci sequences and mapping text characters to Fibonacci values.
- `MeanCalculator`: Provides methods to calculate harmonic mean, geometric mean, and proportional mean.
- `OTPGenerator`: Contains methods for enforcing minimum character types and generating OTP based on user selections.
- `User`: Class for handling user input and mapping user credentials to Fibonacci values.

### Project Design Choices
The OTP generation method was designed with security and usability in mind. By combining mathematical functions with user-specific inputs, each OTP is tailored and secure. The proportional mean calculation is used as a distinctive method to generate numbers without directly relying on random generation, adding a mathematical foundation for unique OTPs.

The Fibonacci sequence is leveraged here not only as a creative choice but as an additional layer to map user credentials to OTP values, making it harder to predict the generated OTP. Each OTP is copied directly to the clipboard to enhance convenience for the user.

### Usage Instructions
1. **Run the Application**: Execute `OTPApp.py` to launch the OTP generator.
2. **Enter Login and Password**: Users input their credentials and select the desired OTP length.
3. **Choose OTP Options**: Select the preferred OTP format from the radio button options.
4. **Generate OTP**: Click "Generate OTP" to see the result. The OTP will also be copied to the clipboard for easy access.

### Design and Security Considerations
In designing this OTP generator, priority was given to ensuring the security and complexity of generated passwords while maintaining ease of use. The design choices around Fibonacci mapping, mean calculations, and character enforcement ensure the OTP is both unpredictable and compliant with security standards for password composition.

This README aims to provide an overview of the functionality, code structure, and design rationale behind the OTP generator application. For additional support or questions, please refer to the video demo or the project documentation.
