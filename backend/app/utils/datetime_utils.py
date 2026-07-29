import calendar
from datetime import date, datetime, timezone, timedelta

KST = timezone(timedelta(hours=9), name="Asia/Seoul")


def now_kst() -> datetime:
    """Return the current datetime in KST (UTC+9)."""
    return datetime.now(tz=KST)


def today_kst() -> date:
    """KST 기준 오늘 날짜를 반환한다."""
    return now_kst().date()


def add_months(base: date, months: int) -> date:
    """달력 기준으로 개월을 더한다. 말일 초과 시 해당 월의 말일로 보정한다."""
    total = base.month - 1 + months
    year = base.year + total // 12
    month = total % 12 + 1
    day = min(base.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def to_kst(dt: datetime) -> datetime:
    """Convert any datetime to KST. Naive datetimes are assumed to be UTC."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(KST)
