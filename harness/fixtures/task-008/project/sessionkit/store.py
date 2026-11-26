"""Session records. All times are integer seconds since the epoch, passed in by the caller."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SessionRecord:
    user_id: str
    created_at: int
    ttl_seconds: int

    def expires_at(self) -> int:
        return self.created_at + self.ttl_seconds
