import unittest
from unittest.mock import patch
import string
import random
import datetime
from project import (
    FibonacciHelper,
    MeanCalculator,
    OTPGenerator,
    User,
)


class TestFibonacciHelper(unittest.TestCase):
    def test_generate_fibonacci(self):
        self.assertEqual(FibonacciHelper.generate_fibonacci(10), [0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
        self.assertEqual(FibonacciHelper.generate_fibonacci(1), [0])
        self.assertEqual(FibonacciHelper.generate_fibonacci(0), [])

    def test_map_to_fibonacci(self):
        self.assertEqual(FibonacciHelper.map_to_fibonacci("abc"), {'a': 0, 'b': 1, 'c': 1})
        self.assertEqual(FibonacciHelper.map_to_fibonacci(""), {})


class TestMeanCalculator(unittest.TestCase):
    def test_harmonic_mean(self):
        self.assertAlmostEqual(MeanCalculator.harmonic_mean(
            [1, 2, 4]), 1.7142857142857142, places=6)
        self.assertAlmostEqual(MeanCalculator.harmonic_mean([1, 0, 4]), 1.6, places=6)

    def test_geometric_mean(self):
        self.assertAlmostEqual(MeanCalculator.geometric_mean(
            [1, 3, 9, 27]), 5.196152422706632, places=6)
        self.assertAlmostEqual(MeanCalculator.geometric_mean([16]), 16)

    def test_proportional_mean(self):
        self.assertEqual(MeanCalculator.proportional_mean(2.0, 4.0), 3.0)


class TestOTPGenerator(unittest.TestCase):
    def test_enforce_min_percentage(self):
        otp = OTPGenerator.enforce_min_percentage("abcd1234", string.ascii_uppercase, 8, 0.25)
        uppercase_count = sum(1 for c in otp if c.isupper())
        self.assertGreaterEqual(uppercase_count, 2)

    def test_generate_otp_from_pm_option3(self):
        otp = OTPGenerator.generate_otp_from_pm("12345", 12, 3, "testuser", "TestPass")
        uppercase_count = sum(1 for c in otp if c.isupper())
        self.assertGreaterEqual(uppercase_count, 3)

    def test_generate_otp_from_pm_option4(self):
        otp = OTPGenerator.generate_otp_from_pm("12345", 12, 4, "testuser", "TestPass!@")
        # Ensure OTP contains uppercase and special characters
        uppercase_count = sum(1 for c in otp if c.isupper())
        special_count = sum(1 for c in otp if c in string.punctuation)
        self.assertGreaterEqual(uppercase_count, 3)
        self.assertGreaterEqual(special_count, 3)


class TestUser(unittest.TestCase):
    def test_get_fibonacci_mapping(self):
        user = User("test", "password")
        fib_values = user.get_fibonacci_mapping()

        # Calculate the expected length based on the Fibonacci mapping for login, password, and formatted time
        login_fib = FibonacciHelper.map_to_fibonacci(user.login)
        password_fib = FibonacciHelper.map_to_fibonacci(user.password)
        datetime_fib = FibonacciHelper.map_to_fibonacci(user.formatted_time)

        expected_length = len(login_fib) + len(password_fib) + len(datetime_fib)

        self.assertEqual(len(fib_values), expected_length)

    def test_extract_digits_from_pm(self):
        user = User("test", "password")
        # Test extracting digits without leading zeros
        self.assertEqual(user.extract_digits_from_pm(123.456), "123456")  # should return '123456'
        # should return '789' (no leading zero)
        self.assertEqual(user.extract_digits_from_pm(0.789), "789")

# Update the extract_digits_from_pm method in User class


class User:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.formatted_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_fibonacci_mapping(self):
        login_fib = FibonacciHelper.map_to_fibonacci(self.login)
        password_fib = FibonacciHelper.map_to_fibonacci(self.password)
        datetime_fib = FibonacciHelper.map_to_fibonacci(self.formatted_time)
        return list(login_fib.values()) + list(password_fib.values()) + list(datetime_fib.values())

    def extract_digits_from_pm(self, pm):
        # Convert to string, remove decimal point, and strip leading zeros
        return ''.join([char for char in str(pm).replace('.', '').lstrip('0') if char.isdigit()])


if __name__ == "__main__":
    unittest.main()
