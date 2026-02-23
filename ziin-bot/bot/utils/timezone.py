from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
import zoneinfo


def to_local_time(dt: datetime, tz_value: Any) -> datetime:
    base = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    try:
        offset_hours = int(str(tz_value).strip())
        return base + timedelta(hours=offset_hours)
    except Exception:
        pass

    try:
        tz = zoneinfo.ZoneInfo(str(tz_value).strip())
        return base.astimezone(tz)
    except Exception:
        return base


def format_local_time(dt: datetime, tz_value: Any, fmt: str) -> str:
    return to_local_time(dt, tz_value).strftime(fmt)
