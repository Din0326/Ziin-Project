from __future__ import annotations

import asyncio
import logging
from typing import Iterable

import discord
from bot.config import BASE_DIR, load_settings
from bot.core.errors import setup_error_handlers
from bot.logging_conf import setup_logging
from bot.services.guild_settings import get_guild_settings
from bot.services.storage import init_storage
from discord.ext import commands

log = logging.getLogger(__name__)


def iter_cog_extensions() -> Iterable[str]:
    cogs_dir = BASE_DIR / "bot" / "cogs"
    for path in cogs_dir.glob("*.py"):
        if path.name.startswith("_"):
            continue
        yield f"bot.cogs.{path.stem}"


class ZiinBot(commands.Bot):
    VERSION = "2.0.0"

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # needed for prefix commands
        intents.members = True
        intents.guilds = True
        intents.presences = True

        self.settings = load_settings()

        super().__init__(
            command_prefix=self._dynamic_prefix,
            intents=intents,
            help_command=None,
            allowed_mentions=discord.AllowedMentions(everyone=False, roles=False, users=True),
        )

    async def _dynamic_prefix(self, bot: commands.Bot, message: discord.Message):
        from bot.services.storage import is_storage_ready

        if message.guild is None:
            return self.settings.default_prefix

        if not is_storage_ready():
            return self.settings.default_prefix

        try:
            data = get_guild_settings(message.guild.id)
            return data.get("Prefix") or self.settings.default_prefix
        except Exception:
            return self.settings.default_prefix

    async def setup_hook(self) -> None:
        # Local SQLite DB init
        init_storage(self.settings.local_db_path)

        # Load cogs
        for ext in iter_cog_extensions():
            try:
                await self.load_extension(ext)
                log.info("Loaded extension: %s", ext)
            except Exception:
                log.exception("Failed to load extension: %s", ext)

        # Sync slash commands (optional, controlled by env SYNC_COMMANDS=1)
        if self.settings.sync_commands:
            try:
                synced = await self.tree.sync()
                log.info("Synced %d app commands.", len(synced))
            except Exception:
                log.exception("App command sync failed.")

    async def on_ready(self) -> None:
        log.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")
        await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.playing, name=f"??{self.settings.default_prefix}help ??/help")
        )


async def main() -> None:
    setup_logging(BASE_DIR / "logs")
    log.info("BOOT_MARKER main_file=%s base_dir=%s", __file__, BASE_DIR)
    bot = ZiinBot()
    log.info("BOOT_MARKER local_db_path=%s", bot.settings.local_db_path)
    setup_error_handlers(bot)

    if not bot.settings.token:
        raise RuntimeError(
            "Missing DISCORD_TOKEN. Create a .env file with DISCORD_TOKEN=... "
            "before starting the bot."
        )

    await bot.start(bot.settings.token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


