import pytest

from add import add


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (2, 3, 5),
        (0, 0, 0),
        (-5, -7, -12),
        (-10, 5, -5),
        (5, -10, -5),
        (1_000_000_000_000, 2_000_000_000_000, 3_000_000_000_000),
    ],
)
def test_add_valid_inputs(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("1", 2),
        (1.0, 3),
        (None, 0),
        ([1], 2),
        (3, {"value": 4}),
    ],
)
def test_add_invalid_types(a, b):
    with pytest.raises(TypeError):
        add(a, b)