from __future__ import annotations

import logging

import discord
from bot.core.error_reporting import (DebugInfoView, build_report,
                                      send_auto_report)
from bot.utils.i18n import get_lang_for_guild
from bot.utils.respond import respond
from discord import app_commands
from discord.ext import commands

log = logging.getLogger(__name__)


def _nice_permission_list(perms: list[str]) -> str:
    # Turn ['manage_guild', 'ban_members'] into 'Manage Guild, Ban Members'
    return ", ".join(p.replace("_", " ").title() for p in perms)


async def _send_error(
    target: commands.Context | discord.Interaction,
    *,
    title: str,
    description: str,
    ephemeral: bool = True,
    view: discord.ui.View | None = None,
):
    embed = discord.Embed(title=title, description=description, color=discord.Color.red())
    try:
        await respond(target, embed=embed, ephemeral=ephemeral, view=view)
    except discord.HTTPException:
        # last resort
        await respond(target, content=f"{title}\n{description}", ephemeral=ephemeral, view=view)


def setup_error_handlers(bot: commands.Bot) -> None:
    """Attach global error handlers for both prefix and slash/hybrid commands."""

    @bot.event
    async def on_command_error(ctx: commands.Context, error: commands.CommandError):
        # If a command has its own local error handler, don't double-handle.
        if hasattr(ctx.command, "on_error"):
            return

        # Ignore unknown commands (common for prefix bots)
        if isinstance(error, commands.CommandNotFound):
            return

        guild_id = ctx.guild.id if ctx.guild else None
        lang = get_lang_for_guild(guild_id)

        # Whether to send user-facing errors as ephemeral messages (where supported)
        eph = getattr(getattr(bot, 'settings', None), 'error_report_ephemeral', True)
        
        # Unwrap original errors
        if isinstance(error, commands.CommandInvokeError) and error.original:
            original = error.original
        else:
            original = error

        # Cooldown
        if isinstance(original, commands.CommandOnCooldown):
            msg = lang.get("error_delay") or "You're doing that too fast. Try again in {0:.1f}s."
            return await _send_error(
                ctx,
                title="⏳ 冷卻中 / Cooldown",
                description=msg.format(original.retry_after),
                ephemeral=eph,
            )

        # Missing args
        if isinstance(original, commands.MissingRequiredArgument):
            usage = f"{ctx.prefix}{ctx.command.qualified_name} {ctx.command.signature}".strip()
            return await _send_error(
                ctx,
                title="⚠️ 參數不足 / Missing argument",
                description=f"少了：`{original.param.name}`\n用法：`{usage}`",
                ephemeral=eph,
            )

        # Permissions
        if isinstance(original, commands.MissingPermissions):
            need = _nice_permission_list(list(original.missing_permissions))
            return await _send_error(
                ctx,
                title="🚫 權限不足 / Missing permissions",
                description=f"你需要這些權限：{need}",
                ephemeral=eph,
            )

        if isinstance(original, commands.BotMissingPermissions):
            need = _nice_permission_list(list(original.missing_permissions))
            return await _send_error(
                ctx,
                title="🚫 我缺權限 / Bot missing permissions",
                description=f"我需要這些權限才能做：{need}",
                ephemeral=eph,
            )

        if isinstance(original, commands.NoPrivateMessage):
            return await _send_error(
                ctx,
                title="🚫 無法在私訊使用",
                description="這個指令只能在伺服器內使用。",
                ephemeral=eph,
            )

        if isinstance(original, commands.CheckFailure):
            return await _send_error(
                ctx,
                title="🚫 無法使用此指令",
                description="你不符合使用條件或缺少權限。",
                ephemeral=eph,
            )

        if isinstance(original, commands.BadArgument):
            return await _send_error(
                ctx,
                title="⚠️ 參數格式錯誤",
                description="你輸入的參數格式不正確，請檢查後再試一次。",
                ephemeral=eph,
            )

        # Fallback: log stack + show short message
        log.exception("Unhandled command error: %s", error)

        report = build_report(error=original, bot=bot, ctx=ctx)
        # auto send to admin channel (if configured)
        await send_auto_report(
            bot=bot,
            report=report,
            channel_id=getattr(getattr(bot, "settings", None), "error_report_channel_id", None),
        )
        view = DebugInfoView(
            report=report,
            send_to_channel_id=getattr(getattr(bot, "settings", None), "error_report_channel_id", None),
        )
        return await _send_error(
            ctx,
            title="💥 發生未預期的錯誤",
            description=report.user_message,
            ephemeral=eph,
            view=view,
        )

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
        guild_id = interaction.guild.id if interaction.guild else None
        lang = get_lang_for_guild(guild_id)

        eph = getattr(getattr(bot, 'settings', None), 'error_report_ephemeral', True)

        # Unwrap invoke error
        original: Exception = getattr(error, "original", error)

        # Interaction already responded: respond() handles followup automatically.

        # Cooldown (app_commands)
        if isinstance(original, app_commands.CommandOnCooldown):
            msg = lang.get("error_delay") or "You're doing that too fast. Try again in {0:.1f}s."
            return await _send_error(
                interaction,
                title="⏳ 冷卻中 / Cooldown",
                description=msg.format(original.retry_after),
                ephemeral=eph,
            )

        # Missing permissions (user)
        if isinstance(original, app_commands.MissingPermissions):
            need = _nice_permission_list(list(original.missing_permissions))
            return await _send_error(
                interaction,
                title="🚫 權限不足 / Missing permissions",
                description=f"你需要這些權限：{need}",
                ephemeral=eph,
            )

        # Missing permissions (bot)
        if isinstance(original, app_commands.BotMissingPermissions):
            need = _nice_permission_list(list(original.missing_permissions))
            return await _send_error(
                interaction,
                title="🚫 我缺權限 / Bot missing permissions",
                description=f"我需要這些權限才能做：{need}",
                ephemeral=eph,
            )

        # Checks
        if isinstance(original, app_commands.CheckFailure):
            return await _send_error(
                interaction,
                title="🚫 無法使用此指令",
                description="你不符合使用條件或缺少權限。",
                ephemeral=eph,
            )

        # Transformer / bad input
        if isinstance(original, (app_commands.TransformerError, app_commands.AppCommandError)):
            # Some input errors are subclasses of AppCommandError; keep message friendly.
            # If Discord already provides a nice error, we avoid leaking internals.
            pass

        if isinstance(original, discord.InteractionResponded):
            # Should be rare; respond() already handles, but keep safe.
            return

        # Timeout / unknown interaction can appear as NotFound (webhook expired)
        if isinstance(original, discord.NotFound):
            # Can't reply anymore; just log.
            log.warning("Interaction expired / not found: %s", original)
            return

        # Fallback
        log.exception("Unhandled app command error: %s", error)

        report = build_report(error=original, bot=bot, interaction=interaction)
        await send_auto_report(
            bot=bot,
            report=report,
            channel_id=getattr(getattr(bot, "settings", None), "error_report_channel_id", None),
        )
        view = DebugInfoView(
            report=report,
            send_to_channel_id=getattr(getattr(bot, "settings", None), "error_report_channel_id", None),
        )
        return await _send_error(
            interaction,
            title="💥 發生未預期的錯誤",
            description=report.user_message,
            ephemeral=eph,
            view=view,
        )
