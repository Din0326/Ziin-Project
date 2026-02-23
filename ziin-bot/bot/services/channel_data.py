from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from bot.services.storage import execute, fetchone, now_ts

DEFAULT_TWITCH_TEXT = "**{streamer}** is live now!!\n**{url}**"
DEFAULT_YOUTUBE_TEXT = "**{ytber}** upload a video!!\n**{url}**"


def build_default_channel_data(guild_id: int) -> Dict[str, Any]:
    return {
        "id": guild_id,
        "twitch_notification_channel": None,
        "all_streamers": [],
        "online_streamers": [],
        "offline_streamers": [],
        "twitch_notification_text": DEFAULT_TWITCH_TEXT,
        "yt_youtuber": {},
        "youtube_notification_text": DEFAULT_YOUTUBE_TEXT,
        "youtube_notification_channel": None,
    }


def _normalize_data(guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    default = build_default_channel_data(guild_id)
    normalized = dict(default)
    normalized.update(data)
    if normalized.get("twitch_notification_channel") is None and data.get("notification_channel") is not None:
        normalized["twitch_notification_channel"] = data.get("notification_channel")
    return normalized


def ensure_channel_data(guild_id: int) -> Dict[str, Any]:
    row = fetchone("SELECT data_json FROM channel_data WHERE server_id = ?", (str(guild_id),))
    if row is None:
        payload = build_default_channel_data(guild_id)
        execute(
            "INSERT INTO channel_data (server_id, data_json, updated_at) VALUES (?, ?, ?)",
            (str(guild_id), json.dumps(payload, ensure_ascii=False), now_ts()),
        )
        return payload

    data = json.loads(row["data_json"])
    normalized = _normalize_data(guild_id, data)
    if normalized != data:
        save_channel_data(guild_id, normalized)
    return normalized


def get_channel_data(guild_id: int) -> Dict[str, Any]:
    return ensure_channel_data(guild_id)


def save_channel_data(guild_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    normalized = _normalize_data(guild_id, payload)
    execute(
        """
        INSERT INTO channel_data (server_id, data_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(server_id)
        DO UPDATE SET data_json = excluded.data_json, updated_at = excluded.updated_at
        """,
        (str(guild_id), json.dumps(normalized, ensure_ascii=False), now_ts()),
    )
    return normalized


def import_legacy_channeldata(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return 0

    imported = 0
    for guild_id, payload in raw.items():
        try:
            gid = int(guild_id)
        except (TypeError, ValueError):
            continue
        exists = fetchone("SELECT 1 FROM channel_data WHERE server_id = ?", (str(gid),))
        if exists is not None:
            continue
        save_channel_data(gid, payload if isinstance(payload, dict) else {})
        imported += 1
    return imported
