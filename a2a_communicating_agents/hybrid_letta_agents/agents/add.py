from __future__ import annotations


def add(a: int, b: int) -> int:
    if not _is_strict_int(a):
        raise TypeError(f"a must be int, got {type(a).__name__}")
    if not _is_strict_int(b):
        raise TypeError(f"b must be int, got {type(b).__name__}")
    return a + b


def _is_strict_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _run_tests() -> None:
    assert add(2, 3) == 5
    assert add(-4, -6) == -10
    assert add(0, 0) == 0
    assert add(-3, 7) == 4
    assert add(10**50, 10**50) == 2 * 10**50

    invalid_cases = [
        (1.0, 2),
        (1, 2.0),
        ("1", 2),
        (1, None),
        (True, 1),
        (1, False),
    ]
    for args in invalid_cases:
        try:
            add(*args)
        except TypeError:
            continue
        raise AssertionError(f"Expected TypeError for args={args}")


if __name__ == "__main__":
    _run_tests()