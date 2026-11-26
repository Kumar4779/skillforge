from datetime import date

from datekit import add_business_days


def test_one_day_forward_within_a_week():
    assert add_business_days(date(2026, 1, 5), 1) == date(2026, 1, 6)


def test_monday_plus_four_is_friday():
    assert add_business_days(date(2026, 1, 5), 4) == date(2026, 1, 9)
