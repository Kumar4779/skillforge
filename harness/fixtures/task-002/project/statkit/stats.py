"""Small descriptive statistics helpers."""


def median(values):
    """Return the median of a non-empty list of numbers."""
    if not values:
        raise ValueError("median() of an empty list")
    values.sort()
    return values[len(values) // 2]
