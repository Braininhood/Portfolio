import pytest
from jar import Jar


def test_init():
    # Test if the jar is initialized correctly with default capacity
    jar = Jar()
    assert jar.capacity == 12
    assert jar.size == 0

    # Test if the jar is initialized correctly with a custom capacity
    jar = Jar(5)
    assert jar.capacity == 5
    assert jar.size == 0

    # Test invalid capacity input
    with pytest.raises(ValueError):
        Jar(-1)
    with pytest.raises(ValueError):
        Jar("abc")


def test_str():
    jar = Jar()
    assert str(jar) == ""  # Empty jar should be represented as ""
    jar.deposit(1)
    assert str(jar) == "🍪"  # One cookie should be represented as "🍪"
    jar.deposit(11)
    assert str(jar) == "🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪🍪"  # 12 cookies


def test_deposit():
    jar = Jar(5)
    jar.deposit(3)
    assert jar.size == 3  # Should be 3 cookies in the jar
    jar.deposit(2)
    assert jar.size == 5  # Should be 5 cookies (capacity is 5)

    # Try to deposit more than capacity
    with pytest.raises(ValueError):
        jar.deposit(1)


def test_withdraw():
    jar = Jar(10)
    jar.deposit(5)
    jar.withdraw(3)
    assert jar.size == 2  # Should be 2 cookies after withdrawing 3

    # Try to withdraw more than the size
    with pytest.raises(ValueError):
        jar.withdraw(3)
