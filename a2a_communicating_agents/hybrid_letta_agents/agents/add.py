from __future__ import annotations

from typing import Any
import unittest


def _require_int(value: Any, name: str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an int; got {type(value).__name__}")
    return value


def add(a: int, b: int) -> int:
    """
    Add two integers and return their sum.

    Examples
    --------
    >>> add(5, 7)
    12
    >>> add(-8, 3)
    -5
    >>> add(0, 0)
    0
    >>> add(10**20, 10**20)
    200000000000000000000
    >>> add("1", 2)
    Traceback (most recent call last):
    ...
    TypeError: a must be an int; got str
    """
    return _require_int(a, "a") + _require_int(b, "b")


class TestAddHelper(unittest.TestCase):
    def test_add_positive_numbers(self) -> None:
        self.assertEqual(add(2, 3), 5)
        self.assertEqual(add(100, 250), 350)

    def test_add_negative_numbers(self) -> None:
        self.assertEqual(add(-4, -9), -13)
        self.assertEqual(add(-1, -1), -2)

    def test_add_zero_identity(self) -> None:
        self.assertEqual(add(0, 15), 15)
        self.assertEqual(add(-33, 0), -33)
        self.assertEqual(add(0, 0), 0)

    def test_add_large_numbers(self) -> None:
        self.assertEqual(add(10**40, 10**40), 2 * 10**40)
        self.assertEqual(add(-(10**50), 10**50), 0)

    def test_bool_is_treated_as_int(self) -> None:
        self.assertEqual(add(True, 4), 5)
        self.assertEqual(add(False, -3), -3)

    def test_raises_type_error_for_non_ints(self) -> None:
        with self.assertRaises(TypeError):
            add("5", 7)
        with self.assertRaises(TypeError):
            add(3.14, 2)
        with self.assertRaises(TypeError):
            add(10, None)
        with self.assertRaises(TypeError):
            add([], {})


if __name__ == "__main__":
    unittest.main()