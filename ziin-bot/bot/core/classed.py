from __future__ import annotations

from discord.ext import commands


class CogExtension(commands.Cog):
    """Base class for all cogs.

    Keeps a reference to the bot instance and provides a single place
    to add shared helpers later.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot


# Backward-compatible alias
Cog_Extension = CogExtension
