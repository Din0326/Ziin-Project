from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import discord
import requests
from discord.ext import commands, tasks

log = logging.getLogger(__name__)
MONITOR_LOGIN = "inori0017"
STATE_KEY = "twitch_last_stream_id"


class TwitchMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._token: str | None = None
        self._token_expire_at: datetime | None = None
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
            return

        stream_id = str(stream.get("id", "")).strip()
        if not stream_id:
            return

        last_id = self.bot.state.get(STATE_KEY, "")
        if stream_id == last_id:
            return

        title = str(stream.get("title", "Twitch Live")).strip() or "Twitch Live"
        thumb = str(stream.get("thumbnail_url", "")).replace("{width}", "1280").replace("{height}", "720")
        url = f"https://www.twitch.tv/{MONITOR_LOGIN}"

        embed = discord.Embed(title=title, url=url, color=discord.Color.from_rgb(145, 70, 255))
        if thumb:
            embed.set_image(url=thumb)
        embed.set_footer(
            text="Made by dinnn._o",
            icon_url="https://static.twitchcdn.net/assets/favicon-32-e29e246c157142c94346.png",
        )
        await channel.send(f"<@&1279866353519558767> 垂耳兔睡醒祈床嚕ദ്ദി₍ᐢ. ̫.ᐢ₎\n{url}", embed=embed)
        self.bot.state.set(STATE_KEY, stream_id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TwitchMonitor(bot))
