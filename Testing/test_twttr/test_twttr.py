from twttr import shorten


def test_only_vowels():
    assert shorten("AEIOU") == ""
    assert shorten("aeiou") == ""


def test_no_vowels():
    assert shorten("bcdfg") == "bcdfg"
    assert shorten("BCDFG") == "BCDFG"


def test_mixed_case():
    assert shorten("Hello") == "Hll"
    assert shorten("WORLD") == "WRLD"
    assert shorten("TwItTeR") == "TwtTR"


def test_empty_string():
    assert shorten("") == ""


def test_numbers_and_symbols():
    assert shorten("1234!@#") == "1234!@#"
    assert shorten("a1e2i3o4u!") == "1234!"
