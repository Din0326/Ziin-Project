from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from bot.services.guild_settings import get_guild_settings
from bot.utils.timezone import parse_utc_offset_hours

BASE_DIR = Path(__file__).resolve().parents[2]
I18N_DIR = BASE_DIR / "data" / "i18n"

EN = json.loads((I18N_DIR / "en.json").read_text(encoding="utf-8-sig"))
TW = json.loads((I18N_DIR / "zh_tw.json").read_text(encoding="utf-8-sig"))


@dataclass(frozen=True)
class GuildContext:
    language: str
    timezone: int
    lang_pack: Dict[str, Any]
    settings: Dict[str, Any]


def _parse_timezone(value: Any, default: int = 0) -> int:
    return parse_utc_offset_hours(value, default=default)


def get_lang_pack(language: str | None) -> Dict[str, Any]:
    return TW if language == "zh-TW" else EN


def get_guild_context(guild_id: int) -> GuildContext:
    settings = get_guild_settings(guild_id)
    language = settings.get("Language") or "English"
    timezone = _parse_timezone(settings.get("TimeZone"), default=0)
    lang_pack = get_lang_pack(language)
    return GuildContext(language=language, timezone=timezone, lang_pack=lang_pack, settings=settings)


def get_ctx_lang_tz(ctx) -> tuple[Dict[str, Any], int]:
    context = get_guild_context(ctx.guild.id)
    return context.lang_pack, context.timezone


def get_ctx_lang(ctx) -> Dict[str, Any]:
    return get_guild_context(ctx.guild.id).lang_pack
