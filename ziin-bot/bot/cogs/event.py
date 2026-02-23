from bot.core.classed import Cog_Extension
from discord.ext import commands

delete_count = 0
last_audit_log_id = 0


class Event(Cog_Extension):
    pass


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Event(bot))
