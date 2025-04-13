import pytest
from plates import is_valid

def test_valid_plates():
    assert is_valid("AB123") == True
    assert is_valid("CDE45") == True
    assert is_valid("XYZ123") == True
    assert is_valid("AB") == True

def test_invalid_length():
    assert is_valid("A") == False  # Too short
    assert is_valid("A1") == False  # Too short
    assert is_valid("ABCDEFG") == False  # Too long

def test_invalid_start():
    assert is_valid("1A23") == False  # Does not start with letters
    assert is_valid("1B") == False  # Does not start with letters

def test_invalid_numbers():
    assert is_valid("ABC0") == False  # Number starts with '0'
    assert is_valid("AB12C34") == False  # Letters after numbers
    assert is_valid("AB12C") == False  # Letters after numbers

def test_invalid_characters():
    assert is_valid("AB@123") == False  # Contains punctuation
    assert is_valid("AB-123") == False  # Contains punctuation
    assert is_valid("A B123") == False  # Contains space

def test_valid_numbers_at_end():
    assert is_valid("AB123") == True  # Valid case with numbers at the end
    assert is_valid("CD4567") == True  # Valid case with numbers at the end

