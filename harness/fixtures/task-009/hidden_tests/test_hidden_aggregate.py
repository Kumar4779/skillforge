from reportkit import monthly_totals


def test_padded_and_non_padded_dates_in_the_same_month_sum_together():
    assert monthly_totals([("2026-01-05", 10), ("2026-1-20", 5), ("2026-1-5", 1)]) == {(2026, 1): 16}


def test_same_month_in_different_years_stays_separate():
    assert monthly_totals([("2025-03-01", 1), ("2026-03-01", 2), ("2026-3-9", 4)]) == {(2025, 3): 1, (2026, 3): 6}


def test_dd_mm_yyyy_lands_in_its_true_month():
    assert monthly_totals([("15/02/2026", 7), ("2026-02-01", 3)]) == {(2026, 2): 10}


def test_december_january_boundary_across_years():
    transactions = [("2025-12-31", 4), ("31/12/2025", 1), ("2026-01-01", 6), ("2026-1-2", 1)]
    assert monthly_totals(transactions) == {(2025, 12): 5, (2026, 1): 7}
