from __future__ import annotations

import logging

import discord
import requests
from discord.ext import commands, tasks

log = logging.getLogger(__name__)
MONITOR_CHANNEL_ID = "UCX3p0efXtm3hl_3O1LP2l9w"
STATE_KEY = "youtube_last_video_id"


class YouTubeMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_upload.start()

    def cog_unload(self) -> None:
        self.check_upload.cancel()

    async def _get_channel(self) -> discord.TextChannel | None:
        cid = self.bot.settings.youtube_notify_channel_id
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

    def _fetch_latest_video(self) -> dict | None:
        key = self.bot.settings.youtube_api_key
        if not key:
            raise RuntimeError("YOUTUBE_API_KEY missing")

        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "channelId": MONITOR_CHANNEL_ID,
                "order": "date",
                "type": "video",
                "maxResults": 1,
                "key": key,
            },
            timeout=20,
        )
        resp.raise_for_status()
        payload = resp.json()
        items = payload.get("items")
        if isinstance(items, list) and items:
            return items[0]
        return None

    @tasks.loop(seconds=300)
    async def check_upload(self) -> None:
        self.check_upload.change_interval(seconds=max(60, self.bot.settings.youtube_poll_seconds))
        await self.bot.wait_until_ready()

        channel = await self._get_channel()
        if channel is None:
            return

        try:
            item = self._fetch_latest_video()
        except Exception as exc:
            log.warning("youtube fetch failed: %s", exc)
            return

        if not item:
            return

        id_obj = item.get("id") if isinstance(item.get("id"), dict) else {}
        video_id = str(id_obj.get("videoId", "")).strip()
        if not video_id:
            return

        last_id = self.bot.state.get(STATE_KEY, "")
        if video_id == last_id:
            return

        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        title = str(snippet.get("title", "New YouTube video")).strip() or "New YouTube video"
        channel_title = str(snippet.get("channelTitle", "YouTube")).strip() or "YouTube"
        thumbs = snippet.get("thumbnails") if isinstance(snippet.get("thumbnails"), dict) else {}
        high = thumbs.get("high") if isinstance(thumbs.get("high"), dict) else {}
        thumb_url = str(high.get("url", "")).strip()
        url = f"https://www.youtube.com/watch?v={video_id}"

        embed = discord.Embed(title=title, url=url, color=discord.Color.red())
        embed.set_author(name=channel_title, url=f"https://www.youtube.com/channel/{MONITOR_CHANNEL_ID}")
        if thumb_url:
            embed.set_image(url=thumb_url)
        embed.set_footer(text="Made by dinnn._o")
        await channel.send(f"<@&279868417171656714> ʏᴏᴜᴛᴜʙᴇ上新片了，機玩一下祝你上廁所天天有衛生紙│ ˙ᵕ˙ )꜆🧻\n{url}", embed=embed)
        self.bot.state.set(STATE_KEY, video_id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(YouTubeMonitor(bot))
