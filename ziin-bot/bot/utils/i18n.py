from __future__ import annotations

from typing import Any, Dict

from bot.utils.guild_context import EN, TW, get_guild_context


def get_lang_for_guild(guild_id: int | None) -> Dict[str, Any]:
    """Return language dict for a guild; defaults to zh_tw then en."""
    if guild_id is None:
        return TW or EN or {}

    try:
        return get_guild_context(guild_id).lang_pack
    except Exception:
        return TW or EN or {}


def t_lang(lang_pack: Dict[str, Any], key: str, *fmt_args: Any, **fmt_kwargs: Any) -> str:
    """Translate by key from a language pack with EN fallback."""
    template = lang_pack.get(key)
    if template is None:
        template = EN.get(key)
    if template is None:
        return key
    if not isinstance(template, str):
        return str(template)

    if not fmt_args and not fmt_kwargs:
        return template
    try:
        return template.format(*fmt_args, **fmt_kwargs)
    except Exception:
        return template


def t_guild(guild_id: int | None, key: str, *fmt_args: Any, **fmt_kwargs: Any) -> str:
    return t_lang(get_lang_for_guild(guild_id), key, *fmt_args, **fmt_kwargs)


def t_ctx(ctx, key: str, *fmt_args: Any, **fmt_kwargs: Any) -> str:
    guild_id = ctx.guild.id if getattr(ctx, "guild", None) else None
    return t_guild(guild_id, key, *fmt_args, **fmt_kwargs)
