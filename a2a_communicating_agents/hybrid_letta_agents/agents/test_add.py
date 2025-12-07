import pytest

from add import add


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (1, 2, 3),
        (-5, -7, -12),
        (-10, 15, 5),
        (0, 0, 0),
        (12345678901234567890, 98765432109876543210, 111111111011111111100),
    ],
)
def test_add_valid_inputs(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize("value", ["3", 4.5, [1], {"a": 1}, None])
def test_add_raises_type_error_for_non_ints(value):
    with pytest.raises(TypeError):
        add(value, 1)
    with pytest.raises(TypeError):
        add(1, value)


def test_add_rejects_bool_inputs():
    with pytest.raises(TypeError):
        add(True, 1)
    with pytest.raises(TypeError):
        add(1, False)


def test_add_handles_extreme_negatives():
    assert add(-2**62, -2**62) == -(2**63) * 2