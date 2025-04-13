class Jar:
    def __init__(self, capacity=12):
        # Validate the capacity
        if not isinstance(capacity, int) or capacity < 0:
            raise ValueError("Capacity must be a non-negative integer.")
        self._capacity = capacity
        self._size = 0

    def __str__(self):
        # Return a string with the appropriate number of cookies represented as 🍪
        return "🍪" * self._size

    def deposit(self, n):
        # Add n cookies to the jar, checking if it exceeds capacity
        if self._size + n > self._capacity:
            raise ValueError("Too many cookies!")
        self._size += n

    def withdraw(self, n):
        # Remove n cookies from the jar, checking if there are enough cookies
        if self._size < n:
            raise ValueError("Not enough cookies!")
        self._size -= n

    @property
    def capacity(self):
        # Return the capacity of the jar
        return self._capacity

    @property
    def size(self):
        # Return the current size (number of cookies in the jar)
        return self._size
