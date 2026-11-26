"""Helpers for inclusive integer ranges, such as day numbers in a schedule."""


def overlaps(a_start, a_end, b_start, b_end):
    """Return True if the inclusive ranges [a_start, a_end] and [b_start, b_end] share any value."""
    return a_start < b_end and b_start < a_end
