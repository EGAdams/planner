from add import add
import pytest


@pytest.mark.parametrize(
    "a,b,expected",
    [
        (2, 3, 5),
        (-4, -6, -10),
        (0, 0, 0),
        (-7, 7, 0),
        (10**12, 10**12, 2 * 10**12),
    ],
)
def test_add_valid_inputs(a, b, expected):
    assert add(a, b) == expected


@pytest.mark.parametrize(
    "a,b",
    [
        (1.5, 2),
        ("1", 2),
        (None, 5),
        ([1], 2),
        (3, "4"),
        (3, None),
    ],
)
def test_add_rejects_non_ints(a, b):
    with pytest.raises(TypeError):
        add(a, b)