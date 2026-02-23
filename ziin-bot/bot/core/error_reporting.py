from __future__ import annotations

import io
import logging
import re
import traceback
from dataclasses import dataclass
from datetime import datetime

import discord
from discord.errors import InteractionResponded, NotFound
from discord.ext import commands

log = logging.getLogger(__name__)

_SENSITIVE_RE = re.compile(r"(?i)\b(token|secret|api[_-]?key|password|passwd|authorization)\b\s*[:=]\s*([^\s]+)")
_LONG_HEX_RE = re.compile(r"\b[a-fA-F0-9]{32,}\b")


def make_error_id(prefix: str = "ZIIN") -> str:
    # 6 hex chars gives 16^6 ~= 16M combinations; good enough for a bot.
    import secrets
    return f"{prefix}-{secrets.token_hex(3).upper()}"


def sanitize(text: str, *, max_len: int = 3500) -> str:
    if not text:
        return ""
    # mask common key=value patterns
    text = _SENSITIVE_RE.sub(lambda m: f"{m.group(1)}=***", text)
    # mask very long hex strings (tokens, hashes)
    text = _LONG_HEX_RE.sub("***", text)
    # hard truncate
    if len(text) > max_len:
        text = text[: max_len - 20] + "\n... (truncated)"
    return text


def _now_local_str(tz_name: str | None = None) -> str:
    # Use system tz if tz_name isn't provided; keep ISO-like readability.
    try:
        if tz_name:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(tz_name)
            return datetime.now(tz=tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        pass
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@dataclass(frozen=True)
class ErrorReport:
    error_id: str
    user_message: str
    debug_text: str
    traceback_text: str


def build_report(
    *,
    error: BaseException,
    bot: commands.Bot,
    ctx: commands.Context | None = None,
    interaction: discord.Interaction | None = None,
) -> ErrorReport:
    settings = getattr(bot, "settings", None)
    tz_name = getattr(settings, "timezone_default", None) if settings else None

    error_id = make_error_id()
    when = _now_local_str(tz_name)

    guild = None
    channel = None
    user = None
    cmd_name = None
    raw_content = None

    if interaction is not None:
        guild = interaction.guild
        channel = interaction.channel
        user = interaction.user
        cmd = getattr(interaction, "command", None)
        cmd_name = getattr(cmd, "qualified_name", None) or getattr(cmd, "name", None) or "unknown"
        # best-effort args
        try:
            ns = getattr(interaction, "namespace", None)
            if ns is not None:
                raw_content = str(ns)
        except Exception:
            raw_content = None

    if ctx is not None:
        guild = ctx.guild
        channel = ctx.channel
        user = ctx.author
        cmd_name = ctx.command.qualified_name if ctx.command else "unknown"
        try:
            raw_content = ctx.message.content
        except Exception:
            raw_content = None

    show_ids = bool(getattr(settings, "error_report_show_ids", True)) if settings else True

    guild_part = f"{guild.name} ({guild.id})" if (guild and show_ids) else (guild.name if guild else "DM")
    chan_part = f"{getattr(channel, 'name', 'unknown')} ({getattr(channel, 'id', 'n/a')})" if (channel and show_ids) else (getattr(channel, "name", "unknown") if channel else "DM")
    user_part = f"{user} ({user.id})" if (user and show_ids) else (str(user) if user else "unknown")

    debug_lines = [
        f"Error Code: {error_id}",
        f"When: {when}",
        f"Guild: {guild_part}",
        f"Channel: {chan_part}",
        f"User: {user_part}",
        f"Command: {cmd_name}",
    ]
    if raw_content:
        debug_lines.append(f"Input: {raw_content}")

    exc_name = type(error).__name__
    debug_lines.append(f"Exception: {exc_name}: {error}")

    tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    tb_s = sanitize(tb, max_len=12000)

    debug_text = sanitize("\n".join(debug_lines), max_len=3500)

    user_message = (
        "我剛剛遇到一個錯誤，暫時處理不了這個指令。\n"
        f"錯誤代碼：`{error_id}`\n"
        "你可以把除錯資訊複製貼給管理員。"
    )

    return ErrorReport(
        error_id=error_id,
        user_message=user_message,
        debug_text=debug_text,
        traceback_text=tb_s,
    )


class DebugInfoView(discord.ui.View):
    def __init__(self, *, report: ErrorReport, send_to_channel_id: int | None = None, timeout: float = 180.0):
        super().__init__(timeout=timeout)
        self.report = report
        self.send_to_channel_id = send_to_channel_id

    @discord.ui.button(label="📋 複製除錯資訊", style=discord.ButtonStyle.secondary)
    async def copy_debug(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore[override]
        try:
            # 先 ack，避免 3 秒規則爆炸
            await interaction.response.defer(ephemeral=True)
        except (InteractionResponded, NotFound):
            # 已回覆或互動已失效，就別硬回 response
            pass
        # Ephemeral reply containing a code block the user can copy.
        text = self.report.debug_text
        if len(text) > 1900:
            text = text[:1900] + "\n... (truncated)"

        try:
            await interaction.followup.send(f"```\n{text}\n```", ephemeral=True)
        except NotFound:
            # 互動真的過期了，就不做任何事（或寫 log）
            return

    @discord.ui.button(label="🆘 回報給管理員", style=discord.ButtonStyle.primary)
    async def report_admin(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore[override]
        # 先 ack，避免 3 秒規則爆炸
        try:
            await interaction.response.defer(ephemeral=True)
        except (InteractionResponded, NotFound):
            pass

        if not self.send_to_channel_id:
            try:
                await interaction.followup.send("目前沒有設定回報頻道。", ephemeral=True)
            except NotFound:
                pass
            return

        channel = interaction.client.get_channel(self.send_to_channel_id)
        if channel is None:
            try:
                channel = await interaction.client.fetch_channel(self.send_to_channel_id)
            except Exception:
                channel = None

        if channel is None or not isinstance(channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
            try:
                await interaction.followup.send("找不到回報頻道或沒有權限。", ephemeral=True)
            except NotFound:
                pass
            return

        embed = discord.Embed(
            title="🧾 Bot Error Report",
            description=f"Error ID: `{self.report.error_id}`",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Debug", value=f"```\n{self.report.debug_text[:900]}\n```", inline=False)

        fp = io.BytesIO(self.report.traceback_text.encode("utf-8"))
        file = discord.File(fp, filename=f"{self.report.error_id}.txt")

        try:
            await channel.send(embed=embed, file=file)
            await interaction.followup.send("已回報給管理員 ✅", ephemeral=True)
        except Exception:
            log.exception("Failed sending error report to channel %s", self.send_to_channel_id)
            try:
                await interaction.followup.send("回報失敗（可能缺少權限）。", ephemeral=True)
            except NotFound:
                pass


async def send_auto_report(
    *,
    bot: commands.Bot,
    report: ErrorReport,
    channel_id: int | None,
) -> None:
    if not channel_id:
        return

    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except Exception:
            channel = None

    if channel is None or not isinstance(channel, (discord.TextChannel, discord.Thread, discord.DMChannel)):
        return

    embed = discord.Embed(
        title="🧾 Bot Error (Auto)",
        description=f"Error ID: `{report.error_id}`",
        color=discord.Color.red(),
    )
    embed.add_field(name="Debug", value=f"```\n{report.debug_text[:900]}\n```", inline=False)

    fp = io.BytesIO(report.traceback_text.encode("utf-8"))
    file = discord.File(fp, filename=f"{report.error_id}.txt")

    try:
        await channel.send(embed=embed, file=file)
    except Exception:
        log.exception("Failed auto-reporting error to channel %s", channel_id)
