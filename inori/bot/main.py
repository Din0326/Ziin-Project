from __future__ import annotations

import asyncio
import logging

import discord
from bot.config import BASE_DIR, load_settings
from bot.logging_conf import setup_logging
from bot.state import StateStore
from discord.ext import commands

log = logging.getLogger(__name__)


class InoriBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.message_content = True

        self.settings = load_settings()
        self.state = StateStore(self.settings.state_file)

        super().__init__(command_prefix="z!", intents=intents, help_command=None)

    async def setup_hook(self) -> None:
        extensions = [
            "bot.cogs.twitch",
            "bot.cogs.youtube",
            "bot.cogs.twitter",
        ]
        for ext in extensions:
            await self.load_extension(ext)
            log.info("Loaded extension: %s", ext)

    async def on_ready(self) -> None:
        log.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")


async def main() -> None:
    setup_logging(BASE_DIR / "logs")
    bot = InoriBot()

    if not bot.settings.token:
        raise RuntimeError("Missing DISCORD_TOKEN in inori/.env")

    await bot.start(bot.settings.token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

