from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _to_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    return int(raw)


@dataclass(frozen=True)
class Settings:
    token: str
    twitch_notify_channel_id: int
    youtube_notify_channel_id: int
    twitter_notify_channel_id: int
    twitch_client_id: str
    twitch_client_secret: str
    youtube_api_key: str
    twitterapi_io_key: str
    twitterapi_io_base: str
    twitch_poll_seconds: int
    youtube_poll_seconds: int
    twitter_poll_seconds: int
    state_file: Path


def load_settings() -> Settings:
    return Settings(
        token=os.getenv("DISCORD_TOKEN", "").strip(),
        twitch_notify_channel_id=_to_int("TWITCH_NOTIFY_CHANNEL_ID", 0),
        youtube_notify_channel_id=_to_int("YOUTUBE_NOTIFY_CHANNEL_ID", 0),
        twitter_notify_channel_id=_to_int("TWITTER_NOTIFY_CHANNEL_ID", 0),
        twitch_client_id=os.getenv("TWITCH_CLIENT_ID", "").strip(),
        twitch_client_secret=os.getenv("TWITCH_CLIENT_SECRET", "").strip(),
        youtube_api_key=os.getenv("YOUTUBE_API_KEY", "").strip(),
        twitterapi_io_key=os.getenv("TWITTERAPI_IO_KEY", "").strip(),
        twitterapi_io_base=(os.getenv("TWITTERAPI_IO_BASE", "https://api.twitterapi.io") or "https://api.twitterapi.io").rstrip("/"),
        twitch_poll_seconds=_to_int("TWITCH_POLL_SECONDS", 60),
        youtube_poll_seconds=_to_int("YOUTUBE_POLL_SECONDS", 300),
        twitter_poll_seconds=_to_int("TWITTER_POLL_SECONDS", 600),
        state_file=BASE_DIR / "data" / "state.json",
    )

