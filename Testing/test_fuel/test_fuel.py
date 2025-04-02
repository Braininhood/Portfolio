import pytest
from fuel import convert, gauge

def test_convert_valid():
    assert convert("1/4") == 25
    assert convert("1/2") == 50
    assert convert("3/4") == 75
    assert convert("0/10") == 0
    assert convert("5/5") == 100

def test_convert_invalid():
    with pytest.raises(ValueError):
        convert("2/1")  # X is greater than Y
    with pytest.raises(ZeroDivisionError):
        convert("1/0")  # Division by zero
    with pytest.raises(ValueError):
        convert("A/B")  # Non-integer input
    with pytest.raises(ValueError):
        convert("1/X")  # Non-integer input
    with pytest.raises(ValueError):
        convert("1/2/3")  # Too many values

def test_gauge():
    assert gauge(0) == "E"
    assert gauge(1) == "E"
    assert gauge(50) == "50%"
    assert gauge(99) == "F"
    assert gauge(100) == "F"

