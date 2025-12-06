import pytest

from add import add


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 2, 3),
        (10, 0, 10),
        (0, 0, 0),
        (-5, -7, -12),
        (-3, 9, 6),
        (9, -3, 6),
        (2_147_483_600, 100, 2_147_483_700),
        (-2_147_483_600, -100, -2_147_483_700),
    ],
)
def test_add_valid_inputs(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize("bad_a", [None, 1.0, "1", [1], (1,), {1}, object()])
def test_add_invalid_first_operand(bad_a):
    with pytest.raises(TypeError):
        add(bad_a, 1)


@pytest.mark.parametrize("bad_b", [None, 2.5, "b", [2], (2,), {2: 2}, object()])
def test_add_invalid_second_operand(bad_b):
    with pytest.raises(TypeError):
        add(1, bad_b)


def test_add_invalid_both_operands():
    with pytest.raises(TypeError):
        add("3", 4.0)