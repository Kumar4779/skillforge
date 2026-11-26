"""Create and check login sessions. Times are integer seconds since the epoch; there is no wall clock."""

from sessionkit.store import SessionRecord


def create_session(user_id, now, ttl_minutes=60):
    """Start a session for `user_id` at time `now` that lasts `ttl_minutes` minutes."""
    return SessionRecord(user_id=user_id, created_at=now, ttl_seconds=ttl_minutes)


def is_valid(session, now):
    """Return True if `session` has not expired at time `now`."""
    return now < session.expires_at()
