from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Tuple

import discord
from bot.services.storage import execute, fetchall, fetchone, now_ts
from bot.utils.timezone import parse_utc_offset_hours

logger = logging.getLogger("__main__")
_DEBUG_GUILD_SETTINGS = os.getenv("DEBUG_GUILD_SETTINGS", "0") == "1"


def _debug_gs(message: str) -> None:
    if _DEBUG_GUILD_SETTINGS:
        logger.info("[guild_settings] %s", message)


def _normalize_timezone_value(value: Any, default: str | None = None) -> str | None:
    if value is None:
        return default

    raw = str(value).strip()
    if not raw:
        return default

    return str(parse_utc_offset_hours(raw, default=0))


def build_default_guild_info(guild: discord.Guild) -> Dict[str, Any]:
    return {
        "Name": guild.name,
        "ID": guild.id,
        "Language": "English",
        "TimeZone": None,
        "Prefix": "z!",
        "admin_msg_id": None,
        "basic_msg_id": None,
        "logger_msg_id": None,
        "setting_msg_id": None,
        "setting_user_id": None,
        "use_msg_id": None,
        "use_user_id": None,
        "guild_log_id": None,
        "member_log_id": None,
        "message_log_id": None,
        "voice_log_id": None,
        "ignore_channel": [],
    }


def build_default_log_settings(guild: discord.Guild) -> Dict[str, Any]:
    return {
        "-Name": guild.name,
        "-ID": guild.id,
        "guildUpdate": "off",
        "messageUpdate": "off",
        "messageDelete": "off",
        "RoleCreate": "off",
        "RoleDelete": "off",
        "RoleUpdate": "off",
        "MemberUpdate": "off",
        "MemberAdd": "off",
        "MemberKick": "off",
        "MemberUnban": "off",
        "MemberRemove": "off",
        "MemberNickUpdate": "off",
        "channelCreate": "off",
        "channelDelete": "off",
        "channelUpdate": "off",
        "voiceChannelJoin": "off",
        "voiceChannelLeave": "off",
        "voiceStateUpdate": "off",
        "voiceChannelSwitch": "off",
        "messageDeleteBulk": "off",
    }


def _row_to_guild_settings(row) -> Dict[str, Any]:
    if row is None:
        return {}
    ignore_raw = row["ignore_channels_json"] or "[]"
    try:
        ignore_list = json.loads(ignore_raw)
        if not isinstance(ignore_list, list):
            ignore_list = []
    except Exception:
        ignore_list = []

    return {
        "Name": row["name"] or "",
        "ID": int(row["server_id"]),
        "Language": row["language"] or "English",
        "TimeZone": _normalize_timezone_value(row["timezone"], default=None),
        "Prefix": row["prefix"] or "z!",
        "guild_log_id": int(row["guild_log_id"]) if row["guild_log_id"] else None,
        "member_log_id": int(row["member_log_id"]) if row["member_log_id"] else None,
        "message_log_id": int(row["message_log_id"]) if row["message_log_id"] else None,
        "voice_log_id": int(row["voice_log_id"]) if row["voice_log_id"] else None,
        "setting_msg_id": int(row["setting_msg_id"]) if row["setting_msg_id"] else None,
        "setting_user_id": int(row["setting_user_id"]) if row["setting_user_id"] else None,
        "use_msg_id": int(row["use_msg_id"]) if row["use_msg_id"] else None,
        "use_user_id": int(row["use_user_id"]) if row["use_user_id"] else None,
        "ignore_channel": [str(v) for v in ignore_list],
    }


def ensure_guild_defaults(guild: discord.Guild) -> Tuple[bool, bool]:
    server_id = str(guild.id)
    _debug_gs(f"ensure defaults start guild={guild.id} name={guild.name}")
    current = fetchone("SELECT * FROM guild_settings WHERE server_id = ?", (server_id,))
    if current is None:
        _debug_gs(f"guild_settings missing, insert default guild={guild.id}")
        execute(
            """
            INSERT INTO guild_settings (
                server_id, name, prefix, language, timezone,
                guild_log_id, member_log_id, message_log_id, voice_log_id,
                setting_msg_id, setting_user_id, use_msg_id, use_user_id,
                ignore_channels_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '[]', ?)
            """,
            (server_id, guild.name, "z!", "English", None, now_ts()),
        )
        info_created = True
    else:
        info_created = False
        if not current["name"]:
            _debug_gs(f"guild name empty, update name guild={guild.id}")
            execute(
                "UPDATE guild_settings SET name = ?, updated_at = ? WHERE server_id = ?",
                (guild.name, now_ts(), server_id),
            )

    default_logs = build_default_log_settings(guild)
    existing = fetchall("SELECT field_name FROM log_settings WHERE server_id = ?", (server_id,))
    existing_keys = {row["field_name"] for row in existing}
    missing = [(k, v) for k, v in default_logs.items() if not k.startswith("-") and k not in existing_keys]
    _debug_gs(f"log settings existing={len(existing_keys)} missing={len(missing)} guild={guild.id}")

    if not existing:
        log_created = True
    else:
        log_created = False

    for field_name, status in missing:
        _debug_gs(f"insert default log setting guild={guild.id} field={field_name} status={status}")
        execute(
            "INSERT OR IGNORE INTO log_settings (server_id, field_name, enabled, updated_at) VALUES (?, ?, ?, ?)",
            (server_id, field_name, 1 if status == "on" else 0, now_ts()),
        )

    _debug_gs(f"ensure defaults done guild={guild.id} info_created={info_created} log_created={log_created}")
    return info_created, log_created


def get_guild_settings(guild_id: int) -> Dict[str, Any]:
    _debug_gs(f"get_guild_settings guild={guild_id}")
    row = fetchone("SELECT * FROM guild_settings WHERE server_id = ?", (str(guild_id),))
    _debug_gs(f"get_guild_settings found={row is not None} guild={guild_id}")
    return _row_to_guild_settings(row)


def get_language(guild_id: int, default: str = "English") -> str:
    data = get_guild_settings(guild_id)
    return data.get("Language") or default


def update_guild_settings(guild_id: int, fields: Dict[str, Any]) -> None:
    if not fields:
        _debug_gs(f"update_guild_settings skipped empty fields guild={guild_id}")
        return

    column_map = {
        "Name": "name",
        "Prefix": "prefix",
        "Language": "language",
        "TimeZone": "timezone",
        "guild_log_id": "guild_log_id",
        "member_log_id": "member_log_id",
        "message_log_id": "message_log_id",
        "voice_log_id": "voice_log_id",
        "setting_msg_id": "setting_msg_id",
        "setting_user_id": "setting_user_id",
        "use_msg_id": "use_msg_id",
        "use_user_id": "use_user_id",
        "ignore_channel": "ignore_channels_json",
    }

    updates: list[str] = []
    params: list[Any] = []
    for key, value in fields.items():
        column = column_map.get(key)
        if not column:
            continue
        if key == "ignore_channel":
            value = json.dumps(value if isinstance(value, list) else [], ensure_ascii=False)
        if key == "TimeZone":
            value = _normalize_timezone_value(value, default=None)
        updates.append(f"{column} = ?")
        params.append(str(value) if value is not None and column.endswith("_id") else value)

    if not updates:
        _debug_gs(f"update_guild_settings skipped unknown fields guild={guild_id} fields={list(fields.keys())}")
        return

    updates.append("updated_at = ?")
    params.append(now_ts())
    params.append(str(guild_id))
    _debug_gs(
        f"update_guild_settings guild={guild_id} columns={[u.split(' = ')[0] for u in updates if u != 'updated_at = ?']}"
    )
    execute(f"UPDATE guild_settings SET {', '.join(updates)} WHERE server_id = ?", params)
    _debug_gs(f"update_guild_settings committed guild={guild_id}")


def get_log_settings(guild_id: int) -> Dict[str, Any]:
    rows = fetchall("SELECT field_name, enabled FROM log_settings WHERE server_id = ?", (str(guild_id),))
    data = {row["field_name"]: ("on" if int(row["enabled"]) == 1 else "off") for row in rows}

    if not data:
        return {}

    # fill missing keys with default off/on by default template when guild is available later
    return data


def update_log_settings(guild_id: int, fields: Dict[str, Any]) -> None:
    if not fields:
        _debug_gs(f"update_log_settings skipped empty fields guild={guild_id}")
        return

    server_id = str(guild_id)
    for field_name, value in fields.items():
        enabled = 1 if value in (True, 1, "1", "on", "ON", "true", "True") else 0
        _debug_gs(f"update_log_settings guild={guild_id} field={field_name} enabled={enabled}")
        execute(
            """
            INSERT INTO log_settings (server_id, field_name, enabled, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(server_id, field_name)
            DO UPDATE SET enabled = excluded.enabled, updated_at = excluded.updated_at
            """,
            (server_id, field_name, enabled, now_ts()),
        )


def set_setting_message_context(guild_id: int, message_id: int, user_id: int) -> None:
    update_guild_settings(
        guild_id,
        {
            "setting_msg_id": message_id,
            "setting_user_id": user_id,
        },
    )


def get_ignored_channels(guild_id: int) -> List[str]:
    data = get_guild_settings(guild_id)
    ignore_channel = data.get("ignore_channel")
    if isinstance(ignore_channel, list):
        return [str(item) for item in ignore_channel]
    return []


def toggle_ignored_channel(guild_id: int, channel_id: int) -> bool:
    channel_id_str = str(channel_id)
    id_list = get_ignored_channels(guild_id)
    if channel_id_str not in id_list:
        id_list.append(channel_id_str)
        update_guild_settings(guild_id, {"ignore_channel": id_list})
        _debug_gs(f"toggle_ignored_channel added guild={guild_id} channel={channel_id}")
        return True
    id_list = [item for item in id_list if item != channel_id_str]
    update_guild_settings(guild_id, {"ignore_channel": id_list})
    _debug_gs(f"toggle_ignored_channel removed guild={guild_id} channel={channel_id}")
    return False


def set_log_channel(guild_id: int, log_kind: str, channel_id: int) -> None:
    field_map = {
        "member": "member_log_id",
        "msg": "message_log_id",
        "voice": "voice_log_id",
        "guild": "guild_log_id",
    }
    field_name = field_map.get(log_kind)
    if field_name is None:
        _debug_gs(f"set_log_channel ignored unknown kind guild={guild_id} kind={log_kind}")
        return
    _debug_gs(f"set_log_channel guild={guild_id} kind={log_kind} channel={channel_id}")
    update_guild_settings(guild_id, {field_name: channel_id})

