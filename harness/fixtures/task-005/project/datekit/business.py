"""Business-day arithmetic. Business days are Monday to Friday."""

from datetime import date, timedelta


def add_business_days(start: date, n: int) -> date:
    """Return the date n business days from start.

    Positive n moves forward, negative n moves backward, and weekends are skipped
    in both directions. n=0 returns start unchanged.
    """
    current = start
    remaining = abs(n)
    while remaining:
        current += timedelta(days=1)
        if current.weekday() < 5:
            remaining -= 1
    return current
