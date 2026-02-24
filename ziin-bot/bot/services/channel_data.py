from __future__ import annotations

import json
from typing import Any, Dict

from bot.services.storage import execute, fetchall, fetchone, now_ts

DEFAULT_TWITCH_TEXT = "**{streamer}** is live now!!\n**{url}**"
DEFAULT_YOUTUBE_TEXT = "**{ytber}** upload a video!!\n**{url}**"
DEFAULT_TWITTER_TEXT = "**{xuser}** posted a new tweet!\n**{url}**"
_SCHEMA_READY = False


def build_default_twitch_data(guild_id: int) -> Dict[str, Any]:
    return {
        "id": guild_id,
        "twitch_notification_channel": None,
        "all_streamers": [],
        "online_streamers": [],
        "offline_streamers": [],
        "twitch_notification_text": DEFAULT_TWITCH_TEXT,
    }


def build_default_youtube_data(guild_id: int) -> Dict[str, Any]:
    return {
        "id": guild_id,
        "yt_youtuber": {},
        "youtube_notification_text": DEFAULT_YOUTUBE_TEXT,
        "youtube_notification_channel": None,
    }


def build_default_twitter_data(guild_id: int) -> Dict[str, Any]:
    return {
        "id": guild_id,
        "twitter_accounts": {},
        "twitter_notification_text": DEFAULT_TWITTER_TEXT,
        "twitter_notification_channel": None,
    }


def _parse_json_value(raw: Any, fallback: Any) -> Any:
    if raw is None:
        return fallback
    if isinstance(raw, (list, dict)):
        return raw
    if not isinstance(raw, str):
        return fallback
    try:
        return json.loads(raw)
    except Exception:
        return fallback


def _normalize_id_history(raw: Any) -> list[str]:
    if isinstance(raw, list):
        values = raw
    elif isinstance(raw, str) and raw:
        values = [raw]
    else:
        values = []

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            continue
        item = value.strip()
        if not item or item in seen:
            continue
        normalized.append(item)
        seen.add(item)
    return normalized


def _normalize_twitch_data(guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    default = build_default_twitch_data(guild_id)
    normalized = dict(default)
    normalized.update(data)

    if not isinstance(normalized.get("all_streamers"), list):
        normalized["all_streamers"] = []
    if not isinstance(normalized.get("online_streamers"), list):
        normalized["online_streamers"] = []
    if not isinstance(normalized.get("offline_streamers"), list):
        normalized["offline_streamers"] = []
    if not isinstance(normalized.get("twitch_notification_text"), str):
        normalized["twitch_notification_text"] = DEFAULT_TWITCH_TEXT

    channel_id = normalized.get("twitch_notification_channel")
    if channel_id in ("", 0, "0"):
        normalized["twitch_notification_channel"] = None

    return normalized


def _normalize_youtube_subscriptions(raw: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for youtuber_id, value in raw.items():
        if not isinstance(youtuber_id, str) or not youtuber_id:
            continue

        item = value if isinstance(value, dict) else {}
        name = item.get("name") if isinstance(item.get("name"), str) else youtuber_id
        video_id = item.get("videoId") if isinstance(item.get("videoId"), str) else ""
        stream_id = item.get("streamId") if isinstance(item.get("streamId"), str) else ""
        short_id = item.get("shortId") if isinstance(item.get("shortId"), str) else ""
        video_history = _normalize_id_history(item.get("videoHistory"))
        stream_history = _normalize_id_history(item.get("streamHistory"))
        short_history = _normalize_id_history(item.get("shortHistory"))

        if video_id and video_id not in video_history:
            video_history.append(video_id)
        if stream_id and stream_id not in stream_history:
            stream_history.append(stream_id)
        if short_id and short_id not in short_history:
            short_history.append(short_id)

        normalized[youtuber_id] = {
            "id": youtuber_id,
            "name": name,
            "videoId": video_id,
            "streamId": stream_id,
            "shortId": short_id,
            "videoHistory": video_history,
            "streamHistory": stream_history,
            "shortHistory": short_history,
        }

    return normalized


def _normalize_youtube_data(guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    default = build_default_youtube_data(guild_id)
    normalized = dict(default)
    normalized.update(data)

    normalized["yt_youtuber"] = _normalize_youtube_subscriptions(normalized.get("yt_youtuber"))
    if not isinstance(normalized.get("youtube_notification_text"), str):
        normalized["youtube_notification_text"] = DEFAULT_YOUTUBE_TEXT

    channel_id = normalized.get("youtube_notification_channel")
    if channel_id in ("", 0, "0"):
        normalized["youtube_notification_channel"] = None

    return normalized


def _normalize_twitter_subscriptions(raw: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}

    normalized: Dict[str, Dict[str, Any]] = {}
    for account_id, value in raw.items():
        if not isinstance(account_id, str) or not account_id:
            continue

        item = value if isinstance(value, dict) else {}
        account = account_id.strip().lower().lstrip("@")
        if not account:
            continue

        name = item.get("name") if isinstance(item.get("name"), str) else account
        tweet_id = item.get("tweetId") if isinstance(item.get("tweetId"), str) else ""
        tweet_history = _normalize_id_history(item.get("tweetHistory"))
        if tweet_id and tweet_id not in tweet_history:
            tweet_history.append(tweet_id)

        normalized[account] = {
            "id": account,
            "name": name,
            "tweetId": tweet_id,
            "tweetHistory": tweet_history,
        }

    return normalized


def _normalize_twitter_data(guild_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    default = build_default_twitter_data(guild_id)
    normalized = dict(default)
    normalized.update(data)

    normalized["twitter_accounts"] = _normalize_twitter_subscriptions(normalized.get("twitter_accounts"))
    if not isinstance(normalized.get("twitter_notification_text"), str):
        normalized["twitter_notification_text"] = DEFAULT_TWITTER_TEXT

    channel_id = normalized.get("twitter_notification_channel")
    if channel_id in ("", 0, "0"):
        normalized["twitter_notification_channel"] = None

    return normalized


def _table_columns(table: str) -> set[str]:
    return {str(row["name"]) for row in fetchall(f"PRAGMA table_info({table})")}


def _ensure_youtube_subscriptions_schema() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS youtube_subscriptions (
          server_id TEXT NOT NULL,
          youtuber_id TEXT NOT NULL,
          channel_name TEXT,
          video_id TEXT,
          stream_id TEXT,
          short_id TEXT,
          video_history TEXT NOT NULL DEFAULT '[]',
          stream_history TEXT NOT NULL DEFAULT '[]',
          short_history TEXT NOT NULL DEFAULT '[]',
          updated_at INTEGER,
          PRIMARY KEY (server_id, youtuber_id)
        )
        """
    )
    columns = _table_columns("youtube_subscriptions")
    if "video_history" not in columns:
        execute("ALTER TABLE youtube_subscriptions ADD COLUMN video_history TEXT NOT NULL DEFAULT '[]'")
    if "stream_history" not in columns:
        execute("ALTER TABLE youtube_subscriptions ADD COLUMN stream_history TEXT NOT NULL DEFAULT '[]'")
    if "short_history" not in columns:
        execute("ALTER TABLE youtube_subscriptions ADD COLUMN short_history TEXT NOT NULL DEFAULT '[]'")


def _ensure_twitter_subscriptions_schema() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS twitter_subscriptions (
          server_id TEXT NOT NULL,
          account_id TEXT NOT NULL,
          display_name TEXT,
          tweet_id TEXT,
          tweet_history TEXT NOT NULL DEFAULT '[]',
          updated_at INTEGER,
          PRIMARY KEY (server_id, account_id)
        )
        """
    )
    columns = _table_columns("twitter_subscriptions")
    if "tweet_history" not in columns:
        execute("ALTER TABLE twitter_subscriptions ADD COLUMN tweet_history TEXT NOT NULL DEFAULT '[]'")


def _ensure_twitch_table_schema() -> None:
    required = {
        "server_id",
        "twitch_notification_channel",
        "all_streamers",
        "online_streamers",
        "offline_streamers",
        "twitch_notification_text",
        "updated_at",
    }
    columns = _table_columns("twitch_data")
    if required.issubset(columns):
        return

    legacy_rows: list[tuple[str, Dict[str, Any], int | None]] = []
    if "data_json" in columns:
        for row in fetchall("SELECT server_id, data_json, updated_at FROM twitch_data"):
            try:
                old = json.loads(row["data_json"]) if row["data_json"] else {}
            except Exception:
                old = {}
            legacy_rows.append((str(row["server_id"]), old if isinstance(old, dict) else {}, row["updated_at"]))
    elif {"all_streamers_json", "online_streamers_json", "offline_streamers_json"}.issubset(columns):
        for row in fetchall(
            """
            SELECT
              server_id,
              twitch_notification_channel,
              all_streamers_json,
              online_streamers_json,
              offline_streamers_json,
              twitch_notification_text,
              updated_at
            FROM twitch_data
            """
        ):
            old = {
                "twitch_notification_channel": row["twitch_notification_channel"],
                "all_streamers": _parse_json_value(row["all_streamers_json"], []),
                "online_streamers": _parse_json_value(row["online_streamers_json"], []),
                "offline_streamers": _parse_json_value(row["offline_streamers_json"], []),
                "twitch_notification_text": row["twitch_notification_text"],
            }
            legacy_rows.append((str(row["server_id"]), old, row["updated_at"]))

    execute("DROP TABLE IF EXISTS twitch_data")
    execute(
        """
        CREATE TABLE IF NOT EXISTS twitch_data (
          server_id TEXT PRIMARY KEY,
          twitch_notification_channel TEXT,
          all_streamers TEXT NOT NULL DEFAULT '[]',
          online_streamers TEXT NOT NULL DEFAULT '[]',
          offline_streamers TEXT NOT NULL DEFAULT '[]',
          twitch_notification_text TEXT NOT NULL DEFAULT '**{streamer}** is live now!!\n**{url}**',
          updated_at INTEGER
        )
        """
    )

    for server_id, old, updated_at in legacy_rows:
        try:
            row_guild_id = int(server_id)
        except Exception:
            continue

        normalized = _normalize_twitch_data(row_guild_id, old)
        execute(
            """
            INSERT INTO twitch_data (
              server_id,
              twitch_notification_channel,
              all_streamers,
              online_streamers,
              offline_streamers,
              twitch_notification_text,
              updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                server_id,
                normalized["twitch_notification_channel"],
                json.dumps(normalized["all_streamers"], ensure_ascii=False),
                json.dumps(normalized["online_streamers"], ensure_ascii=False),
                json.dumps(normalized["offline_streamers"], ensure_ascii=False),
                normalized["twitch_notification_text"],
                updated_at or now_ts(),
            ),
        )


def _replace_youtube_subscriptions(server_id: str, items: Dict[str, Dict[str, Any]], updated_at: int) -> None:
    execute("DELETE FROM youtube_subscriptions WHERE server_id = ?", (server_id,))
    for youtuber_id, item in items.items():
        execute(
            """
            INSERT INTO youtube_subscriptions (
              server_id,
              youtuber_id,
              channel_name,
              video_id,
              stream_id,
              short_id,
              video_history,
              stream_history,
              short_history,
              updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                server_id,
                youtuber_id,
                item.get("name"),
                item.get("videoId"),
                item.get("streamId"),
                item.get("shortId"),
                json.dumps(_normalize_id_history(item.get("videoHistory")), ensure_ascii=False),
                json.dumps(_normalize_id_history(item.get("streamHistory")), ensure_ascii=False),
                json.dumps(_normalize_id_history(item.get("shortHistory")), ensure_ascii=False),
                updated_at,
            ),
        )


def _replace_twitter_subscriptions(server_id: str, items: Dict[str, Dict[str, Any]], updated_at: int) -> None:
    execute("DELETE FROM twitter_subscriptions WHERE server_id = ?", (server_id,))
    for account_id, item in items.items():
        execute(
            """
            INSERT INTO twitter_subscriptions (
              server_id,
              account_id,
              display_name,
              tweet_id,
              tweet_history,
              updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                server_id,
                account_id,
                item.get("name"),
                item.get("tweetId"),
                json.dumps(_normalize_id_history(item.get("tweetHistory")), ensure_ascii=False),
                updated_at,
            ),
        )


def _ensure_youtube_table_schema() -> None:
    _ensure_youtube_subscriptions_schema()

    required = {
        "server_id",
        "youtube_notification_text",
        "youtube_notification_channel",
        "updated_at",
    }
    columns = _table_columns("youtube_data")
    legacy_like_columns = {"data_json", "yt_youtuber", "yt_youtuber_json"}

    if required.issubset(columns) and not (legacy_like_columns & columns):
        return

    legacy_rows: list[tuple[str, Dict[str, Any], int | None]] = []
    if "data_json" in columns:
        for row in fetchall("SELECT server_id, data_json, updated_at FROM youtube_data"):
            try:
                old = json.loads(row["data_json"]) if row["data_json"] else {}
            except Exception:
                old = {}
            legacy_rows.append((str(row["server_id"]), old if isinstance(old, dict) else {}, row["updated_at"]))
    else:
        has_youtuber = "yt_youtuber" in columns
        has_youtuber_json = "yt_youtuber_json" in columns
        if has_youtuber or has_youtuber_json:
            youtuber_col = "yt_youtuber" if has_youtuber else "yt_youtuber_json"
            for row in fetchall(
                f"""
                SELECT
                  server_id,
                  {youtuber_col} AS yt_youtuber_value,
                  youtube_notification_text,
                  youtube_notification_channel,
                  updated_at
                FROM youtube_data
                """
            ):
                old = {
                    "yt_youtuber": _parse_json_value(row["yt_youtuber_value"], {}),
                    "youtube_notification_text": row["youtube_notification_text"],
                    "youtube_notification_channel": row["youtube_notification_channel"],
                }
                legacy_rows.append((str(row["server_id"]), old, row["updated_at"]))

    execute("DROP TABLE IF EXISTS youtube_data")
    execute(
        """
        CREATE TABLE IF NOT EXISTS youtube_data (
          server_id TEXT PRIMARY KEY,
          youtube_notification_text TEXT NOT NULL DEFAULT '**{ytber}** upload a video!!\n**{url}**',
          youtube_notification_channel TEXT,
          updated_at INTEGER
        )
        """
    )

    for server_id, old, updated_at in legacy_rows:
        try:
            row_guild_id = int(server_id)
        except Exception:
            continue

        normalized = _normalize_youtube_data(row_guild_id, old)
        stamp = updated_at or now_ts()

        execute(
            """
            INSERT INTO youtube_data (
              server_id,
              youtube_notification_text,
              youtube_notification_channel,
              updated_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                server_id,
                normalized["youtube_notification_text"],
                normalized["youtube_notification_channel"],
                stamp,
            ),
        )
        _replace_youtube_subscriptions(server_id, normalized["yt_youtuber"], stamp)


def _ensure_twitter_table_schema() -> None:
    _ensure_twitter_subscriptions_schema()

    required = {
        "server_id",
        "twitter_notification_text",
        "twitter_notification_channel",
        "updated_at",
    }
    columns = _table_columns("twitter_data")

    if required.issubset(columns):
        return

    execute("DROP TABLE IF EXISTS twitter_data")
    execute(
        """
        CREATE TABLE IF NOT EXISTS twitter_data (
          server_id TEXT PRIMARY KEY,
          twitter_notification_text TEXT NOT NULL DEFAULT '**{xuser}** posted a new tweet!\n**{url}**',
          twitter_notification_channel TEXT,
          updated_at INTEGER
        )
        """
    )


def _ensure_split_tables_schema() -> None:
    global _SCHEMA_READY
    if _SCHEMA_READY:
        return

    _ensure_twitch_table_schema()
    _ensure_youtube_table_schema()
    _ensure_twitter_table_schema()
    _SCHEMA_READY = True


def _row_to_twitch_data(guild_id: int, row: Any) -> Dict[str, Any]:
    raw = {
        "id": guild_id,
        "twitch_notification_channel": row["twitch_notification_channel"],
        "all_streamers": _parse_json_value(row["all_streamers"], []),
        "online_streamers": _parse_json_value(row["online_streamers"], []),
        "offline_streamers": _parse_json_value(row["offline_streamers"], []),
        "twitch_notification_text": row["twitch_notification_text"],
    }
    return _normalize_twitch_data(guild_id, raw)


def _load_youtube_subscriptions(server_id: str) -> Dict[str, Dict[str, Any]]:
    rows = fetchall(
        """
        SELECT
          youtuber_id,
          channel_name,
          video_id,
          stream_id,
          short_id,
          video_history,
          stream_history,
          short_history
        FROM youtube_subscriptions
        WHERE server_id = ?
        """,
        (server_id,),
    )

    items: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        youtuber_id = str(row["youtuber_id"])
        items[youtuber_id] = {
            "id": youtuber_id,
            "name": row["channel_name"] if isinstance(row["channel_name"], str) else youtuber_id,
            "videoId": row["video_id"] if isinstance(row["video_id"], str) else "",
            "streamId": row["stream_id"] if isinstance(row["stream_id"], str) else "",
            "shortId": row["short_id"] if isinstance(row["short_id"], str) else "",
            "videoHistory": _normalize_id_history(_parse_json_value(row["video_history"], [])),
            "streamHistory": _normalize_id_history(_parse_json_value(row["stream_history"], [])),
            "shortHistory": _normalize_id_history(_parse_json_value(row["short_history"], [])),
        }

    return items


def _row_to_youtube_data(guild_id: int, row: Any, subscriptions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    raw = {
        "id": guild_id,
        "yt_youtuber": subscriptions,
        "youtube_notification_text": row["youtube_notification_text"],
        "youtube_notification_channel": row["youtube_notification_channel"],
    }
    return _normalize_youtube_data(guild_id, raw)


def _load_twitter_subscriptions(server_id: str) -> Dict[str, Dict[str, Any]]:
    rows = fetchall(
        """
        SELECT
          account_id,
          display_name,
          tweet_id,
          tweet_history
        FROM twitter_subscriptions
        WHERE server_id = ?
        """,
        (server_id,),
    )

    items: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        account_id = str(row["account_id"]).strip().lower().lstrip("@")
        if not account_id:
            continue
        items[account_id] = {
            "id": account_id,
            "name": row["display_name"] if isinstance(row["display_name"], str) else account_id,
            "tweetId": row["tweet_id"] if isinstance(row["tweet_id"], str) else "",
            "tweetHistory": _normalize_id_history(_parse_json_value(row["tweet_history"], [])),
        }
    return items


def _row_to_twitter_data(guild_id: int, row: Any, subscriptions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    raw = {
        "id": guild_id,
        "twitter_accounts": subscriptions,
        "twitter_notification_text": row["twitter_notification_text"],
        "twitter_notification_channel": row["twitter_notification_channel"],
    }
    return _normalize_twitter_data(guild_id, raw)


def ensure_twitch_data(guild_id: int) -> Dict[str, Any]:
    _ensure_split_tables_schema()
    row = fetchone(
        """
        SELECT
          twitch_notification_channel,
          all_streamers,
          online_streamers,
          offline_streamers,
          twitch_notification_text
        FROM twitch_data
        WHERE server_id = ?
        """,
        (str(guild_id),),
    )
    if row is None:
        payload = build_default_twitch_data(guild_id)
        return save_twitch_data(guild_id, payload)

    return _row_to_twitch_data(guild_id, row)


def ensure_youtube_data(guild_id: int) -> Dict[str, Any]:
    _ensure_split_tables_schema()
    server_id = str(guild_id)
    row = fetchone(
        """
        SELECT
          youtube_notification_text,
          youtube_notification_channel
        FROM youtube_data
        WHERE server_id = ?
        """,
        (server_id,),
    )
    if row is None:
        payload = build_default_youtube_data(guild_id)
        return save_youtube_data(guild_id, payload)

    return _row_to_youtube_data(guild_id, row, _load_youtube_subscriptions(server_id))


def ensure_twitter_data(guild_id: int) -> Dict[str, Any]:
    _ensure_split_tables_schema()
    server_id = str(guild_id)
    row = fetchone(
        """
        SELECT
          twitter_notification_text,
          twitter_notification_channel
        FROM twitter_data
        WHERE server_id = ?
        """,
        (server_id,),
    )
    if row is None:
        payload = build_default_twitter_data(guild_id)
        return save_twitter_data(guild_id, payload)

    return _row_to_twitter_data(guild_id, row, _load_twitter_subscriptions(server_id))


def get_twitch_data(guild_id: int) -> Dict[str, Any]:
    return ensure_twitch_data(guild_id)


def get_youtube_data(guild_id: int) -> Dict[str, Any]:
    return ensure_youtube_data(guild_id)


def get_twitter_data(guild_id: int) -> Dict[str, Any]:
    return ensure_twitter_data(guild_id)


def save_twitch_data(guild_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_split_tables_schema()
    normalized = _normalize_twitch_data(guild_id, payload)
    execute(
        """
        INSERT INTO twitch_data (
          server_id,
          twitch_notification_channel,
          all_streamers,
          online_streamers,
          offline_streamers,
          twitch_notification_text,
          updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(server_id)
        DO UPDATE SET
          twitch_notification_channel = excluded.twitch_notification_channel,
          all_streamers = excluded.all_streamers,
          online_streamers = excluded.online_streamers,
          offline_streamers = excluded.offline_streamers,
          twitch_notification_text = excluded.twitch_notification_text,
          updated_at = excluded.updated_at
        """,
        (
            str(guild_id),
            normalized["twitch_notification_channel"],
            json.dumps(normalized["all_streamers"], ensure_ascii=False),
            json.dumps(normalized["online_streamers"], ensure_ascii=False),
            json.dumps(normalized["offline_streamers"], ensure_ascii=False),
            normalized["twitch_notification_text"],
            now_ts(),
        ),
    )
    return normalized


def save_youtube_data(guild_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_split_tables_schema()
    normalized = _normalize_youtube_data(guild_id, payload)
    stamp = now_ts()
    server_id = str(guild_id)

    execute(
        """
        INSERT INTO youtube_data (
          server_id,
          youtube_notification_text,
          youtube_notification_channel,
          updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(server_id)
        DO UPDATE SET
          youtube_notification_text = excluded.youtube_notification_text,
          youtube_notification_channel = excluded.youtube_notification_channel,
          updated_at = excluded.updated_at
        """,
        (
            server_id,
            normalized["youtube_notification_text"],
            normalized["youtube_notification_channel"],
            stamp,
        ),
    )

    _replace_youtube_subscriptions(server_id, normalized["yt_youtuber"], stamp)
    return normalized


def save_twitter_data(guild_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    _ensure_split_tables_schema()
    normalized = _normalize_twitter_data(guild_id, payload)
    stamp = now_ts()
    server_id = str(guild_id)

    execute(
        """
        INSERT INTO twitter_data (
          server_id,
          twitter_notification_text,
          twitter_notification_channel,
          updated_at
        )
        VALUES (?, ?, ?, ?)
        ON CONFLICT(server_id)
        DO UPDATE SET
          twitter_notification_text = excluded.twitter_notification_text,
          twitter_notification_channel = excluded.twitter_notification_channel,
          updated_at = excluded.updated_at
        """,
        (
            server_id,
            normalized["twitter_notification_text"],
            normalized["twitter_notification_channel"],
            stamp,
        ),
    )

    _replace_twitter_subscriptions(server_id, normalized["twitter_accounts"], stamp)
    return normalized
