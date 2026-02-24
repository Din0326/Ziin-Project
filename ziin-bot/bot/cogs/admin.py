import typing
from datetime import datetime, timedelta
from typing import Optional

import discord
from bot.core.classed import Cog_Extension
from bot.services.guild_settings import update_guild_settings
from bot.utils.i18n import t_ctx
from discord import Member
from discord.ext import commands
from discord.ext.commands import (Greedy, bot_has_permissions,
                                  has_guild_permissions, has_permissions)


class Admin(Cog_Extension):
    @commands.hybrid_command(with_app_command=True)
    @has_permissions(administrator=True)
    async def prefix(self, ctx: commands.Context, *, new_prefix: str):
        if len(new_prefix) <= 3:
            update_guild_settings(ctx.guild.id, {"Prefix": new_prefix})
            await ctx.send(t_ctx(ctx, "prefix_new", new_prefix))
        else:
            await ctx.send(t_ctx(ctx, "prefix_max"))

    @commands.hybrid_command(aliases=["lang"], with_app_command=True)
    @has_permissions(administrator=True)
    async def language(self, ctx: commands.Context, *, lang: str):
        if lang.lower() == "chinese" or lang == "銝剜?":
            update_guild_settings(ctx.guild.id, {"Language": "zh-TW"})
            await ctx.send(t_ctx(ctx, "language_set_zh"))
        elif lang.lower() in {"english", "en"} or lang == "?望?":
            update_guild_settings(ctx.guild.id, {"Language": "English"})
            await ctx.send(t_ctx(ctx, "language_set_en"))

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(administrator=True)
    async def timezone(self, ctx: commands.Context, *, utc_time: int):
        if 12 >= utc_time >= -12:
            update_guild_settings(ctx.guild.id, {"TimeZone": utc_time})
            if utc_time >= 0:
                await ctx.send(t_ctx(ctx, "tz_set_more0", utc_time))
            else:
                await ctx.send(t_ctx(ctx, "tz_set_less0", utc_time))
        else:
            await ctx.send(t_ctx(ctx, "tz_error"))

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nick: str):
        await member.edit(nick=nick)
        await ctx.send(t_ctx(ctx, "nick_change", member.mention, nick))

    @commands.hybrid_command(with_app_command=True)
    @has_guild_permissions(mute_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
        await member.edit(mute=True, reason=reason)
        await ctx.send(t_ctx(ctx, "member_mute", member.mention))

    @commands.hybrid_command(with_app_command=True)
    @has_guild_permissions(mute_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
        await member.edit(reason=reason, mute=False)
        await ctx.send(t_ctx(ctx, "member_unmute", member.mention))

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
        await member.ban(reason=reason)
        await ctx.send(t_ctx(ctx, "member_ban", member.mention))

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, target: int, *, reason: typing.Optional[str] = None):
        user = self.bot.get_user(target)
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(t_ctx(ctx, "member_unban", user.name, user.discriminator))

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, target: discord.Member, *, reason: typing.Optional[str] = None):
        await target.kick(reason=reason)
        await ctx.send(t_ctx(ctx, "member_kick", target.mention))

    @commands.hybrid_command(with_app_command=True)
    @has_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    async def clear(self, ctx: commands.Context, limit: Optional[int], targets: Greedy[Member]):
        def _check(message):
            return not len(targets) or message.author in targets

        limit = limit or 1
        if 0 < limit <= 500:
            async with ctx.channel.typing():
                await ctx.message.delete()
                deleted = await ctx.channel.purge(
                    limit=limit,
                    after=datetime.utcnow() - timedelta(days=14),
                    check=_check,
                )
                await ctx.send(t_ctx(ctx, "message_clear", len(deleted)), delete_after=5)
        else:
            await ctx.send(t_ctx(ctx, "message_clear_limit"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Admin(bot))
