from __future__ import annotations

import discord
from discord.ext import commands


class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", with_app_command=True, description="Show help")
    async def help(self, ctx: commands.Context):
        prefix = "?"
        try:
            prefix = (await self.bot.get_prefix(ctx.message))[0] if isinstance(await self.bot.get_prefix(ctx.message), (list, tuple)) else await self.bot.get_prefix(ctx.message)
        except Exception:
            pass

        embed = discord.Embed(title="Help", description=f"Prefix: `{prefix}`  |  Slash: `/help`")
        embed.add_field(name="Tip", value=("Most commands are still prefix-based in this modernized build.\n"
                                    "You can gradually convert commands to slash or hybrid commands."), inline=False)

        # Show a few top-level commands
        shown = 0
        for cmd in self.bot.commands:
            if cmd.hidden or cmd.parent is not None:
                continue
            if cmd.name in {"load", "unload", "reload", "shutdown"}:
                continue
            embed.add_field(name=f"{prefix}{cmd.name}", value=(cmd.help or " "), inline=False)
            shown += 1
            if shown >= 8:
                break

        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
