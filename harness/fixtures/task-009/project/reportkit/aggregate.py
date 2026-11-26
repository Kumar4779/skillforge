"""Monthly aggregation of imported transactions."""


def monthly_totals(transactions):
    """Sum amounts by calendar month.

    `transactions` is an iterable of (date string, amount). Returns {(year, month): total}.
    """
    by_month = {}
    for tx_date, amount in transactions:
        month = tx_date[:7]  # "YYYY-MM"
        by_month[month] = by_month.get(month, 0) + amount
    return {(int(month[:4]), int(month[5:7].strip("-"))): total for month, total in by_month.items()}
