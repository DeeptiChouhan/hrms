"""Date helpers for leave automation (sandwich / weekend scenarios)."""

from __future__ import annotations

from datetime import date, timedelta


def next_weekend_sandwich_pair(
    *,
    from_date: date | None = None,
    min_lead_days: int = 1,
) -> tuple[date, date]:
    """
    Next Friday + Monday pair with Sat–Sun between them.

    Used for sandwich leave: full-day leave on Friday, then full-day leave on
    Monday so weekend days are sandwiched (policy must allow sandwich on weekends).
    """
    cursor = (from_date or date.today()) + timedelta(days=min_lead_days)
    while cursor.weekday() != 4:  # Friday
        cursor += timedelta(days=1)
    friday = cursor
    monday = friday + timedelta(days=3)
    return friday, monday
