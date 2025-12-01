import pytest

from add import add


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (0, 0, 0),
        (1, 2, 3),
        (-5, 10, 5),
        (123456, 654321, 777777),
        (-7, -3, -10),
    ],
)
def test_add_basic_pairs(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b"),
    [
        (10**50, 10**50),
        (-(10**80), 10**80 - 1),
        (2**120, -(2**119)),
    ],
)
def test_add_large_magnitude_numbers(a, b):
    assert add(a, b) == a + b  # Ensures arbitrary-precision behavior matches Python


@pytest.mark.parametrize(
    ("value",),
    [
        (0,),
        (42,),
        (-999,),
    ],
)
def test_add_identity_with_zero(value):
    assert add(value, 0) == value
    assert add(0, value) == value


def test_add_treats_bools_as_ints():
    assert add(True, 2) == 3
    assert add(False, -5) == -5


def test_add_is_commutative_for_integers():
    pairs = [(-3, 7), (0, 15), (20, -4), (2**16, -2**15)]
    for a, b in pairs:
        assert add(a, b) == add(b, a)


def test_add_raises_type_error_for_incompatible_types():
    with pytest.raises(TypeError):
        add("5", 3)