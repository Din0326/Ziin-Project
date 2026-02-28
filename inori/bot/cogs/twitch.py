from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import discord
import requests
from discord.ext import commands, tasks

log = logging.getLogger(__name__)
MONITOR_LOGIN = "inori0017"


class TwitchMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._token: str | None = None
        self._token_expire_at: datetime | None = None
        self._live_message_id: int | None = None
        self._current_stream_id: str | None = None
        self.check_stream.start()

    def cog_unload(self) -> None:
        self.check_stream.cancel()

    async def _get_channel(self) -> discord.TextChannel | None:
        cid = self.bot.settings.twitch_notify_channel_id
        if not cid:
            return None
        channel = self.bot.get_channel(cid)
        if isinstance(channel, discord.TextChannel):
            return channel
        try:
            fetched = await self.bot.fetch_channel(cid)
        except Exception:
            return None
        return fetched if isinstance(fetched, discord.TextChannel) else None

    def _get_app_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._token and self._token_expire_at and now < self._token_expire_at:
            return self._token

        client_id = self.bot.settings.twitch_client_id
        client_secret = self.bot.settings.twitch_client_secret
        if not client_id or not client_secret:
            raise RuntimeError("TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET missing")

        resp = requests.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        self._token_expire_at = now + timedelta(seconds=max(60, expires_in - 60))
        return self._token

    def _fetch_live_stream(self) -> dict | None:
        token = self._get_app_token()
        client_id = self.bot.settings.twitch_client_id
        resp = requests.get(
            "https://api.twitch.tv/helix/streams",
            params={"user_login": MONITOR_LOGIN},
            headers={
                "Client-ID": client_id,
                "Authorization": f"Bearer {token}",
            },
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        rows = payload.get("data")
        if isinstance(rows, list) and rows:
            return rows[0]
        return None

    def _build_live_embed(self, stream: dict) -> tuple[discord.Embed, str]:
        user_login = str(stream.get("user_login", MONITOR_LOGIN)).strip() or MONITOR_LOGIN
        title = str(stream.get("title", "Twitch Live")).strip() or "Twitch Live"
        url = f"https://www.twitch.tv/{user_login}"
        thumbnail_base = str(stream.get("thumbnail_url", "")).replace("{width}", "1920").replace("{height}", "1080")
        thumbnail = f"{thumbnail_base}?ts={int(datetime.now(timezone.utc).timestamp())}" if thumbnail_base else ""

        embed = discord.Embed(title=title, url=url, color=discord.Color.from_rgb(145, 70, 255), timestamp=datetime.utcnow())
        embed.set_author(name=f"{stream.get('user_name', 'Streamer')} is live now!!")
        embed.add_field(name="Game", value=str(stream.get("game_name", "")).strip() or "---", inline=True)
        embed.add_field(name="Viewers", value=str(stream.get("viewer_count", 0)), inline=True)
        if thumbnail:
            embed.set_image(url=thumbnail)
        embed.set_footer(
            text="Made by dinnn._o",
            icon_url="https://static.twitchcdn.net/assets/favicon-32-e29e246c157142c94346.png",
        )
        return embed, url

    @tasks.loop(seconds=60)
    async def check_stream(self) -> None:
        self.check_stream.change_interval(seconds=max(30, self.bot.settings.twitch_poll_seconds))
        await self.bot.wait_until_ready()

        channel = await self._get_channel()
        if channel is None:
            return

        try:
            stream = self._fetch_live_stream()
        except Exception as exc:
            log.warning("twitch fetch failed: %s", exc)
            return

        if not stream:
            self._live_message_id = None
            self._current_stream_id = None
            return

        stream_id = str(stream.get("id", "")).strip()
        if not stream_id:
            return

        embed, url = self._build_live_embed(stream)
        is_new_live = stream_id != self._current_stream_id

        if is_new_live or not self._live_message_id:
            msg = await channel.send(f"<@&1279866353519558767> is live now!\n{url}", embed=embed)
            self._live_message_id = msg.id
            self._current_stream_id = stream_id
            return

        try:
            msg = await channel.fetch_message(self._live_message_id)
            await msg.edit(embed=embed)
        except Exception as exc:
            log.warning("twitch message edit failed: %s", exc)
            msg = await channel.send(f"<@&1279866353519558767> is live now!\n{url}", embed=embed)
            self._live_message_id = msg.id
            self._current_stream_id = stream_id


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TwitchMonitor(bot))