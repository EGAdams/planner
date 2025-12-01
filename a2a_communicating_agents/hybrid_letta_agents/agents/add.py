"""Utility helper that adds two integers with strict type validation."""


def add(a: int, b: int) -> int:
    if type(a) is not int:
        raise TypeError(f"Expected int for parameter 'a', got {type(a).__name__}")
    if type(b) is not int:
        raise TypeError(f"Expected int for parameter 'b', got {type(b).__name__}")
    return a + b


def _run_tests() -> None:
    assert add(5, 7) == 12
    assert add(-3, -9) == -12
    assert add(0, 0) == 0
    assert add(-5, 5) == 0
    assert add(2_147_483_647, 1) == 2_147_483_648

    for args in [(1.5, 2), (1, "2"), (True, 3)]:
        try:
            add(*args)  # type: ignore[arg-type]
        except TypeError:
            pass
        else:
            raise AssertionError(f"TypeError not raised for args={args}")


if __name__ == "__main__":
    _run_tests()