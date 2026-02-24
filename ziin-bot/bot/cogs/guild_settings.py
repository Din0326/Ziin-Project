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

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(administrator=True)
    async def setting(self, ctx: commands.Context):
        Lang, guild_tz = get_ctx_lang_tz(ctx)
        log = get_log_settings(ctx.guild.id)
        # todo 回復 網頁版的設定介面

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(administrator=True)
    async def ignore(self, ctx: commands.Context, channel: discord.TextChannel = None):
        Lang, guild_tz = get_ctx_lang_tz(ctx)
        self._debug_log(f"ignore command guild={ctx.guild.id} channel={getattr(channel, 'id', None)}")
        added = toggle_ignored_channel(ctx.guild.id, channel.id)
        if added:
            await ctx.send(Lang["ignore_add"].format(channel.mention))
            return
        await ctx.send(Lang["ignore_del"].format(channel.mention))

    @commands.hybrid_command(with_app_command=True)
    async def show(self, ctx: commands.Context):
        Lang, guild_tz = get_ctx_lang_tz(ctx)
        id_list = get_ignored_channels(ctx.guild.id)
        embed = discord.Embed(
            title=Lang["ignore_all"].format(ctx.guild.name),
            color=ctx.author.colour,
            timestamp=datetime.utcnow(),
        )
        embed.set_footer(text=f"{ctx.author}")
        if id_list != []:
            for i in id_list:
                igg_ch = self.bot.get_channel(int(i))
                embed.add_field(name=igg_ch, value=igg_ch.mention)
        else:
            embed.add_field(name=Lang["ignore_none"], value="------")
        await ctx.send(embed=embed)

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(administrator=True)
    async def setlog(self, ctx: commands.Context, info: str, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        Lang, guild_tz = get_ctx_lang_tz(ctx)
        self._debug_log(f"setlog command guild={ctx.guild.id} info={info} channel={channel.id}")
        if info == "member":
            set_log_channel(ctx.guild.id, "member", channel.id)
            await ctx.send(Lang["setlog_member"].format(channel.mention))
        if info == "msg":
            set_log_channel(ctx.guild.id, "msg", channel.id)
            await ctx.send(Lang["setlog_msg"].format(channel.mention))
        if info == "voice":
            set_log_channel(ctx.guild.id, "voice", channel.id)
            await ctx.send(Lang["setlog_voice"].format(channel.mention))
        if info == "guild":
            set_log_channel(ctx.guild.id, "guild", channel.id)
            await ctx.send(Lang["setlog_guild"].format(channel.mention))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GuildSettings(bot))

