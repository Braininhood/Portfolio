import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from math import prod, pow
import random
import string
import re
import pyperclip  # Import pyperclip for clipboard functionality


class FibonacciHelper:
    @staticmethod
    def generate_fibonacci(n):
        fib_sequence = [0, 1]
        while len(fib_sequence) < n:
            fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
        return fib_sequence[:n]

    @staticmethod
    def map_to_fibonacci(text):
        fib_seq = FibonacciHelper.generate_fibonacci(len(text))
        return {char: fib_seq[i] for i, char in enumerate(text)}


class MeanCalculator:
    @staticmethod
    def harmonic_mean(numbers):
        non_zero_numbers = [num for num in numbers if num != 0]
        return len(non_zero_numbers) / sum(1 / num for num in non_zero_numbers)

    @staticmethod
    def geometric_mean(numbers):
        product = prod(numbers)
        return pow(product, 1 / len(numbers))

    @staticmethod
    def proportional_mean(hm, gm):
        return (hm + gm) / 2


class OTPGenerator:
    @staticmethod
    def enforce_min_percentage(otp, required_chars, total_length, percentage):
        required_count = max(1, round(total_length * percentage))
        current_count = sum(1 for char in otp if char in required_chars)
        while current_count < required_count:
            replace_index = random.randint(0, total_length - 1)
            if otp[replace_index] not in required_chars:
                otp = otp[:replace_index] + random.choice(required_chars) + otp[replace_index+1:]
                current_count += 1
        return otp

    @staticmethod
    def generate_otp_from_pm(pm_digits, otp_length, option, login, password):
        otp = ''
        characters = pm_digits

        if option == 1:
            otp = ''.join(random.choices(pm_digits, k=otp_length))
        elif option == 2:
            lowercase_letters = ''.join([char.lower()
                                        for char in login + password if char.isalpha()])
            characters += lowercase_letters
            otp = ''.join(random.choices(characters, k=otp_length))
        elif option == 3:
            letters = ''.join([char for char in login + password if char.isalpha()])
            characters += letters
            otp = ''.join(random.choices(characters, k=otp_length))
            otp = OTPGenerator.enforce_min_percentage(otp, string.ascii_uppercase, otp_length, 0.25)
        elif option == 4:
            letters = ''.join([char for char in login + password if char.isalpha()])
            special_chars_in_login_password = ''.join(
                [char for char in login + password if char in string.punctuation])

            if len(special_chars_in_login_password) < 2:
                special_chars = ''.join(random.choices(string.punctuation, k=2))
            else:
                special_chars = special_chars_in_login_password

            characters += letters + special_chars
            otp = ''.join(random.choices(characters, k=otp_length))
            otp = OTPGenerator.enforce_min_percentage(otp, string.ascii_uppercase, otp_length, 0.25)
            otp = OTPGenerator.enforce_min_percentage(otp, string.punctuation, otp_length, 0.25)

        return otp


class User:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_fibonacci_mapping(self):
        login_fib = FibonacciHelper.map_to_fibonacci(self.login)
        password_fib = FibonacciHelper.map_to_fibonacci(self.password)
        datetime_fib = FibonacciHelper.map_to_fibonacci(self.formatted_time)
        return list(login_fib.values()) + list(password_fib.values()) + list(datetime_fib.values())

    def extract_digits_from_pm(self, pm):
        return ''.join([char for char in str(pm) if char.isdigit()])


class OTPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OTP Generator")

        # Login and Password Input
        tk.Label(root, text="Enter Login:").pack()
        self.login_entry = tk.Entry(root)
        self.login_entry.pack()

        tk.Label(root, text="Enter Password:").pack()
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.pack()

        # OTP Length Input
        tk.Label(root, text="OTP Length:").pack()
        self.otp_length_entry = tk.Entry(root)
        self.otp_length_entry.pack()

        # OTP Option Input
        tk.Label(root, text="OTP Options:").pack()
        self.option_var = tk.StringVar(value="1")
        options_frame = tk.Frame(root)
        options_frame.pack()
        tk.Radiobutton(options_frame, text="1 - Only numbers",
                       variable=self.option_var, value="1").pack(anchor="w")
        tk.Radiobutton(options_frame, text="2 - Numbers and lowercase letters",
                       variable=self.option_var, value="2").pack(anchor="w")
        tk.Radiobutton(options_frame, text="3 - Numbers, lowercase and uppercase letters",
                       variable=self.option_var, value="3").pack(anchor="w")
        tk.Radiobutton(options_frame, text="4 - Numbers, lowercase and uppercase letters, special characters",
                       variable=self.option_var, value="4").pack(anchor="w")

        # Generate Button and Result Label
        tk.Button(root, text="Generate OTP", command=self.generate_otp).pack()
        self.result_label = tk.Label(root, text="Generated OTP will appear here")
        self.result_label.pack()

    def generate_otp(self):
        login = self.login_entry.get()
        password = self.password_entry.get()

        # Check if login, password are provided
        if not login or not password:
            messagebox.showerror("Error", "Please enter login and password.")
            return

        try:
            otp_length = int(self.otp_length_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for OTP length.")
            return

        try:
            otp_option = int(self.option_var.get())
        except ValueError:
            messagebox.showerror("Error", "Please select a valid OTP option.")
            return

        # Proceed with OTP generation if all checks pass
        user = User(login, password)
        all_fib_numbers = user.get_fibonacci_mapping()
        non_zero_fib_numbers = [num for num in all_fib_numbers if num != 0]
        hm = MeanCalculator.harmonic_mean(non_zero_fib_numbers)
        gm = MeanCalculator.geometric_mean(non_zero_fib_numbers)
        pm = MeanCalculator.proportional_mean(hm, gm)
        pm_digits = user.extract_digits_from_pm(pm)

        if len(pm_digits) == 0:
            messagebox.showerror("Error", "No digits available from proportional mean.")
        else:
            otp_password = OTPGenerator.generate_otp_from_pm(
                pm_digits, otp_length, otp_option, login, password)
            self.result_label.config(text=f"Your OTP password is: {otp_password}")

            # Copy the OTP to the clipboard
            pyperclip.copy(otp_password)
            messagebox.showinfo("Success", "OTP copied to clipboard!")


def run():
    root = tk.Tk()
    app = OTPApp(root)
    root.mainloop()


if __name__ == "__main__":
    run()
