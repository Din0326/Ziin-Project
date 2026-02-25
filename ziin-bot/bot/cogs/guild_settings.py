from datetime import datetime

import logging
import os

import discord
from bot.core.classed import Cog_Extension
from bot.services.guild_settings import (ensure_guild_defaults,
                                         get_ignored_channels,
                                         get_log_settings, set_log_channel,
                                         toggle_ignored_channel)
from bot.utils.guild_context import get_ctx_lang_tz
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import has_permissions


class GuildSettings(Cog_Extension):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self._defaults_bootstrapped = False
        self._debug = os.getenv("DEBUG_GUILD_SETTINGS", "0") == "1"
        self._logger = logging.getLogger("__main__")

    def _debug_log(self, message: str) -> None:
        if self._debug:
            self._logger.info("[guild_settings_cog] %s", message)

    @commands.Cog.listener()
    async def on_ready(self):
        if self._defaults_bootstrapped:
            self._debug_log("on_ready skipped: defaults already bootstrapped")
            return
        self._debug_log(f"on_ready start: guild_count={len(self.bot.guilds)}")
        for guild in self.bot.guilds:
            self._debug_log(f"on_ready ensure defaults guild={guild.id} name={guild.name}")
            ensure_guild_defaults(guild)
        self._defaults_bootstrapped = True
        self._debug_log("on_ready done")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        join = self.bot.get_channel(766318401441628210)
        self._debug_log(f"on_guild_join guild={guild.id} name={guild.name}")
        info_created, log_created = ensure_guild_defaults(guild)

        if join is not None:
            await join.send(
                f"Name: {guild.name}\nID: {guild.id}\nDatabase Ready (Guild created={info_created}, Logsetting created={log_created})"
            )

    @commands.Cog.listener()
    async def on_guild_leave(self, guild: discord.Guild):
        join = self.bot.get_channel(766318401441628210)
        await join.send(f"Name: {guild.name}\nID: {guild.id}\nLeave Guild!")

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["設定", "伺服器設定", "紀錄設定"],
        description="查看伺服器紀錄設定與網頁設定入口",
        help=(
            "顯示目前伺服器的訊息/成員/語音/伺服器紀錄狀態，並提供網頁設定按鈕。\n"
            "用法：setting"
        ),
    )
    @has_permissions(administrator=True)
    async def setting(self, ctx: commands.Context):
        Lang, _ = get_ctx_lang_tz(ctx)
        log = get_log_settings(ctx.guild.id)
        base_url = (os.getenv("WEB_DASHBOARD_URL") or os.getenv("NEXTAUTH_URL") or "http://localhost:6001").rstrip("/")
        dashboard_url = base_url if base_url.endswith("/dashboard") else f"{base_url}/dashboard"
        dashboard_url = f"{dashboard_url}?server={ctx.guild.id}"

        def _state_text(value: str) -> str:
            return "ON" if str(value).lower() == "on" else "OFF"

        embed = discord.Embed(
            title=Lang.get("set_title", "紀錄顯示設定"),
            description=f"網頁設定介面：{dashboard_url}",
            color=ctx.author.colour,
            timestamp=datetime.utcnow(),
        )
        embed.add_field(name="訊息", value=_state_text(log.get("msg")), inline=True)
        embed.add_field(name="成員", value=_state_text(log.get("member")), inline=True)
        embed.add_field(name="語音", value=_state_text(log.get("voice")), inline=True)
        embed.add_field(name="伺服器", value=_state_text(log.get("guild")), inline=True)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="開啟網頁設定", url=dashboard_url))
        await ctx.send(embed=embed, view=view)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildSettings(bot))
