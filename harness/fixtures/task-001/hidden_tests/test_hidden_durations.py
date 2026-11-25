import pytest

from textkit import parse_duration


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("45s", 45),
        ("2m", 120),
        ("1h30m", 5400),
        ("1h15s", 3615),
        ("0s", 0),
    ],
)
def test_parse_duration(text, expected):
    assert parse_duration(text) == expected
