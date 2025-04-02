from numb3rs import validate


def test_valid_ips():
    # Test several valid IP addresses
    assert validate("127.0.0.1") == True
    assert validate("192.168.1.1") == True
    assert validate("255.255.255.255") == True
    assert validate("0.0.0.0") == True


def test_invalid_ips():
    # Test out-of-range numbers and incorrect formats
    assert validate("275.3.6.28") == False
    assert validate("256.256.256.256") == False
    assert validate("192.168.1.256") == False
    assert validate("123.456.78.90") == False
    assert validate("1.2.3.1000") == False


def test_non_numeric():
    # Test non-numeric strings and empty input
    assert validate("cat") == False
    assert validate("abc.def.ghi.jkl") == False
    assert validate("") == False


def test_partial_ips():
    # Test incomplete IP addresses
    assert validate("192.168.1") == False
    assert validate("10.0") == False
    assert validate("127") == False
