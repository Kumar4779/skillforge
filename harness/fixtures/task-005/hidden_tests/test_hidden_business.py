from datetime import date

from datekit import add_business_days


def test_reported_backward_case():
    assert add_business_days(date(2026, 1, 5), -1) == date(2026, 1, 2)


def test_backward_across_a_weekend():
    assert add_business_days(date(2026, 1, 12), -1) == date(2026, 1, 9)
    assert add_business_days(date(2026, 1, 13), -3) == date(2026, 1, 8)


def test_forward_across_a_weekend():
    assert add_business_days(date(2026, 1, 9), 1) == date(2026, 1, 12)


def test_zero_returns_start_unchanged():
    assert add_business_days(date(2026, 1, 7), 0) == date(2026, 1, 7)
    assert add_business_days(date(2026, 1, 10), 0) == date(2026, 1, 10)


def test_saturday_plus_one_is_monday():
    assert add_business_days(date(2026, 1, 10), 1) == date(2026, 1, 12)
