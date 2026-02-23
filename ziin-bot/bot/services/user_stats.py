from __future__ import annotations

from typing import Any, Dict, Optional

from bot.services.storage import execute, fetchone, now_ts


def _server(user_id: int, guild_id: int) -> tuple[str, str]:
    return str(user_id), str(guild_id)


def get_user_doc(user_id: int, guild_id: int, doc_id: str) -> Optional[Dict[str, Any]]:
    if doc_id == "guild":
        return get_user_guild_stats(user_id, guild_id)
    try:
        channel_id = int(doc_id)
    except ValueError:
        return None
    return get_user_voice_channel_stats(user_id, guild_id, channel_id)


def get_user_guild_stats(user_id: int, guild_id: int) -> Dict[str, Any]:
    uid, sid = _server(user_id, guild_id)
    row = fetchone(
        "SELECT * FROM user_guild_stats WHERE user_id = ? AND server_id = ?",
        (uid, sid),
    )
    if row is None:
        return {}
    return {
        "total": float(row["total_hours"] or 0),
        "last_message": row["last_message"],
        "stream_start_time": row["stream_start_time"],
        "stream_end_time": row["stream_end_time"],
        "stream_total_time": int(row["stream_total_time"] or 0),
    }


def get_user_voice_channel_stats(user_id: int, guild_id: int, channel_id: int) -> Optional[Dict[str, Any]]:
    uid, sid = _server(user_id, guild_id)
    row = fetchone(
        "SELECT join_time, leave_time FROM user_voice_channel_stats WHERE user_id = ? AND server_id = ? AND channel_id = ?",
        (uid, sid, str(channel_id)),
    )
    if row is None:
        return None
    return {"Join": row["join_time"], "Leave": row["leave_time"]}


def _ensure_user_guild_row(user_id: int, guild_id: int) -> None:
    uid, sid = _server(user_id, guild_id)
    execute(
        """
        INSERT OR IGNORE INTO user_guild_stats (
            user_id, server_id, total_msg, voice_total_seconds,
            stream_total_seconds, last_voice_join_at,
            total_hours, last_message, stream_start_time, stream_end_time,
            stream_total_time, updated_at
        ) VALUES (?, ?, 0, 0, 0, NULL, 0, NULL, NULL, NULL, 0, ?)
        """,
        (uid, sid, now_ts()),
    )


def _ensure_voice_channel_row(user_id: int, guild_id: int, channel_id: int) -> None:
    uid, sid = _server(user_id, guild_id)
    execute(
        """
        INSERT OR IGNORE INTO user_voice_channel_stats (
            user_id, server_id, channel_id, voice_seconds,
            last_join_at, join_time, leave_time, updated_at
        ) VALUES (?, ?, ?, 0, NULL, NULL, NULL, ?)
        """,
        (uid, sid, str(channel_id), now_ts()),
    )


def upsert_user_guild_last_message(user_id: int, guild_id: int, last_message: str) -> None:
    _ensure_user_guild_row(user_id, guild_id)
    uid, sid = _server(user_id, guild_id)
    execute(
        "UPDATE user_guild_stats SET last_message = ?, updated_at = ? WHERE user_id = ? AND server_id = ?",
        (last_message, now_ts(), uid, sid),
    )


def upsert_user_voice_join(user_id: int, guild_id: int, channel_id: int, join_time: str) -> None:
    _ensure_voice_channel_row(user_id, guild_id, channel_id)
    uid, sid = _server(user_id, guild_id)
    execute(
        """
        UPDATE user_voice_channel_stats
        SET join_time = ?, last_join_at = ?, updated_at = ?
        WHERE user_id = ? AND server_id = ? AND channel_id = ?
        """,
        (join_time, now_ts(), now_ts(), uid, sid, str(channel_id)),
    )


def upsert_user_voice_leave(user_id: int, guild_id: int, channel_id: int, leave_time: str) -> None:
    _ensure_voice_channel_row(user_id, guild_id, channel_id)
    uid, sid = _server(user_id, guild_id)
    execute(
        """
        UPDATE user_voice_channel_stats
        SET leave_time = ?, updated_at = ?
        WHERE user_id = ? AND server_id = ? AND channel_id = ?
        """,
        (leave_time, now_ts(), uid, sid, str(channel_id)),
    )


def add_user_voice_total_hours(user_id: int, guild_id: int, hours: float) -> float:
    _ensure_user_guild_row(user_id, guild_id)
    uid, sid = _server(user_id, guild_id)
    row = fetchone(
        "SELECT total_hours, voice_total_seconds FROM user_guild_stats WHERE user_id = ? AND server_id = ?",
        (uid, sid),
    )
    current_hours = float(row["total_hours"] or 0)
    current_seconds = int(row["voice_total_seconds"] or 0)

    total_hours = round(current_hours + float(hours), 1)
    total_seconds = current_seconds + int(float(hours) * 3600)

    execute(
        """
        UPDATE user_guild_stats
        SET total_hours = ?, voice_total_seconds = ?, updated_at = ?
        WHERE user_id = ? AND server_id = ?
        """,
        (total_hours, total_seconds, now_ts(), uid, sid),
    )
    return total_hours


def upsert_stream_start(user_id: int, guild_id: int, start_time: str) -> None:
    _ensure_user_guild_row(user_id, guild_id)
    uid, sid = _server(user_id, guild_id)
    execute(
        """
        UPDATE user_guild_stats
        SET stream_start_time = ?, stream_end_time = '', updated_at = ?
        WHERE user_id = ? AND server_id = ?
        """,
        (start_time, now_ts(), uid, sid),
    )


def upsert_stream_end(user_id: int, guild_id: int, end_time: str) -> None:
    _ensure_user_guild_row(user_id, guild_id)
    uid, sid = _server(user_id, guild_id)
    execute(
        "UPDATE user_guild_stats SET stream_end_time = ?, updated_at = ? WHERE user_id = ? AND server_id = ?",
        (end_time, now_ts(), uid, sid),
    )


def add_stream_total_seconds(user_id: int, guild_id: int, seconds: int) -> int:
    _ensure_user_guild_row(user_id, guild_id)
    uid, sid = _server(user_id, guild_id)
    row = fetchone(
        "SELECT stream_total_time, stream_total_seconds FROM user_guild_stats WHERE user_id = ? AND server_id = ?",
        (uid, sid),
    )
    old_time = int(row["stream_total_time"] or 0)
    old_seconds = int(row["stream_total_seconds"] or 0)

    total = old_time + int(seconds)
    total_seconds = old_seconds + int(seconds)

    execute(
        """
        UPDATE user_guild_stats
        SET stream_total_time = ?, stream_total_seconds = ?, updated_at = ?
        WHERE user_id = ? AND server_id = ?
        """,
        (total, total_seconds, now_ts(), uid, sid),
    )
    return total
