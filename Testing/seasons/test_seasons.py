import pytest
from datetime import date
import inflect  # Make sure inflect is imported here
from seasons import main

# Test valid date input


def test_valid_date(monkeypatch, capsys):
    # Mock user input to simulate a specific date
    monkeypatch.setattr('builtins.input', lambda _: "2000-01-01")

    # Run the main function and capture the output
    main()

    # Manually calculate minutes for a 24-year-old born on 2000-01-01
    birthdate = date(2000, 1, 1)
    today = date.today()
    days_lived = (today - birthdate).days
    expected_minutes = days_lived * 24 * 60
    p = inflect.engine()  # Create the inflect engine
    expected_output = p.number_to_words(expected_minutes, andword="").capitalize() + " minutes"

    # Capture and check the printed output
    captured = capsys.readouterr()
    assert captured.out.strip() == expected_output

# Test invalid date format (wrong format)


def test_invalid_date_format(monkeypatch):
    # Simulate wrong format input
    monkeypatch.setattr('builtins.input', lambda _: "01/01/2000")

    with pytest.raises(SystemExit):
        main()  # Run main function which will exit

# Test leap year


def test_leap_year(monkeypatch, capsys):
    # Testing with a leap year birthdate (2020-02-29)
    monkeypatch.setattr('builtins.input', lambda _: "2020-02-29")

    # Run the main function and capture the output
    main()

    # Manually calculate minutes for a person born on 2020-02-29 (leap year)
    birthdate = date(2020, 2, 29)
    today = date.today()
    days_lived = (today - birthdate).days
    expected_minutes = days_lived * 24 * 60
    p = inflect.engine()  # Create the inflect engine
    expected_output = p.number_to_words(expected_minutes, andword="").capitalize() + " minutes"

    # Capture and check the printed output
    captured = capsys.readouterr()
    assert captured.out.strip() == expected_output
