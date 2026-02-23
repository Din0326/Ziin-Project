from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]  # project root
DATA_DIR = BASE_DIR / "data"
I18N_DIR = DATA_DIR / "i18n"
SECRETS_DIR = BASE_DIR / "secrets"

@dataclass(frozen=True)
class Settings:
    # Discord
    token: str
    default_prefix: str = "z!"
    sync_commands: bool = False

    # Error reporting
    error_report_channel_id: Optional[int] = None
    error_report_show_ids: bool = True
    error_report_ephemeral: bool = True

    # Local DB
    local_db_path: Path = DATA_DIR / "local.db"

    # External APIs
    twitch_client_id: str = ""
    twitch_client_secret: str = ""
    youtube_api_key: str = ""

    # Misc
    timezone_default: str = "Asia/Taipei"


def load_settings() -> Settings:
    """Load settings from .env."""
    load_dotenv(BASE_DIR / ".env")

    token = os.getenv("DISCORD_TOKEN") or ""
    prefix = os.getenv("DISCORD_PREFIX") or "z!"
    sync_commands = (os.getenv("SYNC_COMMANDS") or "").strip() in {"1", "true", "True", "yes", "YES"}

    err_channel = os.getenv("ERROR_REPORT_CHANNEL_ID") or ""
    try:
        err_channel_id = int(err_channel) if err_channel.strip() else None
    except ValueError:
        err_channel_id = None

    err_show_ids = (os.getenv("ERROR_REPORT_SHOW_IDS") or "1").strip() not in {"0","false","False","no","NO"}
    err_ephemeral = (os.getenv("ERROR_REPORT_EPHEMERAL") or "1").strip() not in {"0","false","False","no","NO"}

    local_db_path_env = os.getenv("LOCAL_DB_PATH")
    local_db_path = Path(local_db_path_env) if local_db_path_env else (DATA_DIR / "local.db")
    twitch_client_id = os.getenv("TWITCH_CLIENT_ID") or ""
    twitch_client_secret = os.getenv("TWITCH_CLIENT_SECRET") or ""
    youtube_api_key = os.getenv("YOUTUBE_API_KEY") or ""

    return Settings(
        token=token,
        default_prefix=prefix,
        sync_commands=sync_commands,
        error_report_channel_id=err_channel_id,
        error_report_show_ids=err_show_ids,
        error_report_ephemeral=err_ephemeral,
        local_db_path=local_db_path,
        twitch_client_id=twitch_client_id,
        twitch_client_secret=twitch_client_secret,
        youtube_api_key=youtube_api_key,
    )
