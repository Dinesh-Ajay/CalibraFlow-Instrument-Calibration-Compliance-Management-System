from datetime import datetime, timedelta, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def calculate_next_due_date(last_date: datetime, interval_days: int) -> datetime:
    return last_date + timedelta(days=interval_days)


def is_overdue(due_date: Optional[datetime], current_date: Optional[datetime] = None) -> bool:
    if due_date is None:
        return False
    if current_date is None:
        current_date = utcnow()
    if due_date.tzinfo is not None and current_date.tzinfo is None:
        current_date = current_date.replace(tzinfo=timezone.utc)
    elif due_date.tzinfo is None and current_date.tzinfo is not None:
        due_date = due_date.replace(tzinfo=timezone.utc)
    return current_date > due_date


def days_until_due(due_date: Optional[datetime], current_date: Optional[datetime] = None) -> Optional[int]:
    if due_date is None:
        return None
    if current_date is None:
        current_date = utcnow()
    if due_date.tzinfo is not None and current_date.tzinfo is None:
        current_date = current_date.replace(tzinfo=timezone.utc)
    elif due_date.tzinfo is None and current_date.tzinfo is not None:
        due_date = due_date.replace(tzinfo=timezone.utc)
    return (due_date - current_date).days
