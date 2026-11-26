from reportkit import monthly_totals


def test_sums_within_a_month():
    assert monthly_totals([("2026-01-05", 10), ("2026-01-20", 5)]) == {(2026, 1): 15}


def test_separates_months():
    assert monthly_totals([("2026-01-31", 1), ("2026-02-01", 2)]) == {(2026, 1): 1, (2026, 2): 2}
