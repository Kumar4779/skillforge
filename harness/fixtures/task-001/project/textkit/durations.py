"""Parse compact duration strings such as "1h30m" into seconds."""

import re

_DURATION = re.compile(r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$")


def parse_duration(s: str) -> int:
    """Convert a duration string like "1h30m" or "45s" to a number of seconds."""
    text = s.strip()
    match = _DURATION.match(text)
    if not text or match is None:
        raise ValueError(f"invalid duration: {s!r}")
    hours, minutes, seconds = (int(group) if group else 0 for group in match.groups())
    return hours * 3600 + minutes * 60
