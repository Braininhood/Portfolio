import pytest
from working import convert


def test_valid_conversion():
    # Test standard AM to PM conversion
    assert convert("9:00 AM to 5:00 PM") == "09:00 to 17:00"
    assert convert("9 AM to 5 PM") == "09:00 to 17:00"
    assert convert("10 AM to 8:50 PM") == "10:00 to 20:50"
    assert convert("10:30 PM to 8 AM") == "22:30 to 08:00"


def test_edge_cases():
    # Test cases around midnight and noon
    assert convert("12:00 AM to 12:00 PM") == "00:00 to 12:00"
    assert convert("12 PM to 12 AM") == "12:00 to 00:00"
    assert convert("11:59 AM to 12:01 PM") == "11:59 to 12:01"
    assert convert("12:01 AM to 11:59 PM") == "00:01 to 23:59"


def test_invalid_formats():
    # Invalid formats should raise a ValueError
    with pytest.raises(ValueError):
        convert("9:60 AM to 5:60 PM")  # Invalid minutes
    with pytest.raises(ValueError):
        convert("9 AM - 5 PM")  # Incorrect separator
    with pytest.raises(ValueError):
        convert("09:00 to 17:00")  # 24-hour format mixed in
    with pytest.raises(ValueError):
        convert("13:00 AM to 1:00 PM")  # Invalid hour in 12-hour format


def test_missing_minutes():
    # Valid cases without minutes should convert correctly
    assert convert("9 AM to 5 PM") == "09:00 to 17:00"
    assert convert("12 PM to 12 AM") == "12:00 to 00:00"
    assert convert("1 PM to 2 AM") == "13:00 to 02:00"


def test_varied_spacing():
    # Valid inputs with varied spacing between time and AM/PM
    with pytest.raises(ValueError):
        convert("9:00AM to 5:00PM")  # No space before "AM"/"PM"
    with pytest.raises(ValueError):
        convert("10AM to 8PM")  # No space before "AM"/"PM"
