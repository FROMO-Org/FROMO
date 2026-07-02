from datetime import UTC, datetime

def utc_now_naive() -> datetime:
    """Return current UTC time as naive datetime for Postgres timestamp columns."""
    return datetime.now(UTC).replace(tzinfo=None)

def to_naive_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)