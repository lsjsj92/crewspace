from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9), name="Asia/Seoul")


def now_kst() -> datetime:
    """Return the current datetime in KST (UTC+9)."""
    return datetime.now(tz=KST)


def to_kst(dt: datetime) -> datetime:
    """Convert any datetime to KST. Naive datetimes are assumed to be UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST)
