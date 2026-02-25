import typing
from datetime import datetime, timedelta
from typing import Optional

import discord
from bot.core.classed import Cog_Extension
from bot.services.guild_settings import update_guild_settings
from bot.utils.i18n import t_ctx
from discord import app_commands
from discord import Member
from discord.ext import commands
from discord.ext.commands import (Greedy, bot_has_permissions,
                                  has_guild_permissions, has_permissions)


class Admin(Cog_Extension):
    @commands.hybrid_command(
        with_app_command=True,
        aliases=["改名", "暱稱"],
        description="修改成員暱稱",
        help="修改指定成員的伺服器暱稱。\n用法：nick <成員> <新暱稱>"
    )
    @app_commands.describe(member="要修改的成員", nick="新的暱稱")
    @has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, member: discord.Member, *, nick: str):
        await member.edit(nick=nick)
        await ctx.send(t_ctx(ctx, "nick_change", member.mention, nick))

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["禁言"],
        description="禁言成員",
        help="將指定成員設為語音禁言。\n用法：mute <成員> [原因]"
    )
    @app_commands.describe(member="要禁言的成員", reason="禁言原因（可省略）")
    @has_guild_permissions(mute_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
        await member.edit(mute=True, reason=reason)
        await ctx.send(t_ctx(ctx, "member_mute", member.mention))

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["解除禁言"],
        description="解除成員禁言",
        help="解除指定成員的語音禁言。\n用法：unmute <成員> [原因]"
    )
    @app_commands.describe(member="要解除禁言的成員", reason="解除原因（可省略）")
    @has_guild_permissions(mute_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
        await member.edit(reason=reason, mute=False)
        await ctx.send(t_ctx(ctx, "member_unmute", member.mention))

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["封鎖", "封禁"],
        description="封鎖成員",
        help="封鎖指定成員。\n用法：ban <成員> [原因]"
    )
    @app_commands.describe(member="要封鎖的成員", reason="封鎖原因（可省略）")
    @has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: typing.Optional[str] = None):
        await member.ban(reason=reason)
        await ctx.send(t_ctx(ctx, "member_ban", member.mention))

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["解封", "解除封鎖"],
        description="解除成員封鎖",
        help="依使用者 ID 解除封鎖。\n用法：unban <使用者ID> [原因]"
    )
    @app_commands.describe(target="要解除封鎖的使用者 ID", reason="解除原因（可省略）")
    @has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, target: int, *, reason: typing.Optional[str] = None):
        user = self.bot.get_user(target)
        await ctx.guild.unban(user, reason=reason)
        await ctx.send(t_ctx(ctx, "member_unban", user.name, user.discriminator))

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["踢出"],
        description="踢出成員",
        help="將指定成員踢出伺服器。\n用法：kick <成員> [原因]"
    )
    @app_commands.describe(target="要踢出的成員", reason="踢出原因（可省略）")
    @has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, target: discord.Member, *, reason: typing.Optional[str] = None):
        await target.kick(reason=reason)
        await ctx.send(t_ctx(ctx, "member_kick", target.mention))

    @commands.hybrid_command(
        with_app_command=True,
        aliases=["清除", "清訊息"],
        description="批次刪除訊息",
        help="刪除近期訊息，可指定清除數量與成員。\n用法：clear [數量] [@成員 ...]"
    )
    @app_commands.describe(
        limit="最多刪除數量（1~500，預設 1）",
        targets="只刪除這些成員的訊息（可省略）"
    )
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
