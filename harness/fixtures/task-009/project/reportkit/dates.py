"""Date parsing for CSV imports."""

from datetime import date


def parse_date(s):
    """Parse "YYYY-MM-DD", non-padded "YYYY-M-D", or "DD/MM/YYYY" into a datetime.date."""
    s = s.strip()
    if "/" in s:
        day, month, year = s.split("/")
    else:
        year, month, day = s.split("-")
    return date(int(year), int(month), int(day))
