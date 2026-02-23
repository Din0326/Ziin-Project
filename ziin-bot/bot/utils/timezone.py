from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
import zoneinfo


_UTC_OFFSET_RE = re.compile(r"(?:^|\s)(?:UTC|GMT)\s*([+-])\s*(\d{1,2})(?::?(\d{2}))?(?:\s|$)")


def _extract_zone_name(raw: str) -> str | None:
    # Prefer direct IANA values first, then try to pick one from labels like "UTC+8 Asia/Taipei".
    candidates = [raw]
    candidates.extend(token for token in raw.split() if "/" in token)
    for candidate in candidates:
        try:
            zoneinfo.ZoneInfo(candidate)
            return candidate
        except Exception:
            continue
    return None


def parse_utc_offset_hours(tz_value: Any, default: int = 0) -> int:
    if tz_value is None:
        return default

    raw = str(tz_value).strip()
    if not raw:
        return default

    try:
        return int(raw)
    except Exception:
        pass

    zone_name = _extract_zone_name(raw)
    if zone_name:
        try:
            offset = datetime.now(tz=zoneinfo.ZoneInfo(zone_name)).utcoffset()
            if offset is not None:
                return int(offset.total_seconds() // 3600)
        except Exception:
            pass

    match = _UTC_OFFSET_RE.search(raw)
    if match:
        sign = -1 if match.group(1) == "-" else 1
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        return sign * int(hours + minutes / 60)

    return default


def to_local_time(dt: datetime, tz_value: Any) -> datetime:
    base = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

    if tz_value is None:
        return base

    raw = str(tz_value).strip()
    if not raw:
        return base

    try:
        offset_hours = int(raw)
        return base + timedelta(hours=offset_hours)
    except Exception:
        pass

    zone_name = _extract_zone_name(raw)
    if zone_name:
        try:
            return base.astimezone(zoneinfo.ZoneInfo(zone_name))
        except Exception:
            pass

    match = _UTC_OFFSET_RE.search(raw)
    if match:
        sign = -1 if match.group(1) == "-" else 1
        hours = int(match.group(2) or 0)
        minutes = int(match.group(3) or 0)
        return base + timedelta(hours=sign * hours, minutes=sign * minutes)

    return base


def format_local_time(dt: datetime, tz_value: Any, fmt: str) -> str:
    return to_local_time(dt, tz_value).strftime(fmt)
