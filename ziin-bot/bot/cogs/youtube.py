import logging
import os
import re
import typing

import requests
from bot.core.classed import Cog_Extension
from bot.services.channel_data import get_youtube_data, save_youtube_data
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

logger = logging.getLogger("__main__")
_DEBUG_YOUTUBE = os.getenv("DEBUG_YOUTUBE", "0") == "1"

_YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"
_DURATION_RE = re.compile(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?")


def _debug_youtube(message: str) -> None:
    if _DEBUG_YOUTUBE:
        logger.info("[youtube] %s", message)


def _append_unique_id(bucket: list[str], value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value in bucket:
        return False
    bucket.append(value)
    return True


def _parse_duration_seconds(raw: str) -> int:
    if not isinstance(raw, str):
        return 0
    match = _DURATION_RE.fullmatch(raw)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


class Youtube(Cog_Extension):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self._uploads_playlist_cache: dict[str, str] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_video_youtube.is_running():
            self.check_video_youtube.start()

    def _resolve_notification_channel(self, channel_id):
        if channel_id is None:
            return None
        try:
            return self.bot.get_channel(int(channel_id))
        except Exception:
            return None

    def _youtube_get(self, endpoint: str, params: dict[str, str], api_key: str) -> dict:
        response = requests.get(
            f"{_YOUTUBE_API_BASE}/{endpoint}",
            params={**params, "key": api_key},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return {}
        return data

    def _get_uploads_playlist_id(self, channel_id: str, api_key: str) -> str | None:
        cached = self._uploads_playlist_cache.get(channel_id)
        if cached:
            return cached

        data = self._youtube_get(
            "channels",
            {
                "part": "contentDetails",
                "id": channel_id,
                "maxResults": "1",
            },
            api_key,
        )
        items = data.get("items")
        if not isinstance(items, list) or not items:
            return None

        item = items[0] if isinstance(items[0], dict) else {}
        uploads = (
            item.get("contentDetails", {})
            .get("relatedPlaylists", {})
            .get("uploads")
            if isinstance(item.get("contentDetails"), dict)
            else None
        )
        if not isinstance(uploads, str) or not uploads:
            return None

        self._uploads_playlist_cache[channel_id] = uploads
        return uploads

    def _get_latest_upload_video_id(self, uploads_playlist_id: str, api_key: str) -> str | None:
        data = self._youtube_get(
            "playlistItems",
            {
                "part": "snippet",
                "playlistId": uploads_playlist_id,
                "maxResults": "1",
            },
            api_key,
        )
        items = data.get("items")
        if not isinstance(items, list) or not items:
            return None

        item = items[0] if isinstance(items[0], dict) else {}
        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        resource = snippet.get("resourceId") if isinstance(snippet.get("resourceId"), dict) else {}
        video_id = resource.get("videoId")
        if not isinstance(video_id, str) or not video_id:
            return None
        return video_id

    def _get_video_meta(self, video_id: str, api_key: str) -> tuple[str, str]:
        data = self._youtube_get(
            "videos",
            {
                "part": "snippet,contentDetails,liveStreamingDetails",
                "id": video_id,
                "maxResults": "1",
            },
            api_key,
        )
        items = data.get("items")
        if not isinstance(items, list) or not items:
            return "video", ""

        item = items[0] if isinstance(items[0], dict) else {}
        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        content = item.get("contentDetails") if isinstance(item.get("contentDetails"), dict) else {}

        channel_name = snippet.get("channelTitle") if isinstance(snippet.get("channelTitle"), str) else ""
        duration_sec = _parse_duration_seconds(content.get("duration") if isinstance(content.get("duration"), str) else "")

        if isinstance(item.get("liveStreamingDetails"), dict):
            return "stream", channel_name
        if 0 < duration_sec <= 60:
            return "short", channel_name
        return "video", channel_name

    def _record_video_id(self, target: dict, video_kind: str, video_id: str) -> bool:
        history_key = "videoHistory"
        current_id_key = "videoId"
        if video_kind == "short":
            history_key = "shortHistory"
            current_id_key = "shortId"
        elif video_kind == "stream":
            history_key = "streamHistory"
            current_id_key = "streamId"

        history = target.setdefault(history_key, [])
        if not isinstance(history, list):
            history = []
            target[history_key] = history

        is_new = _append_unique_id(history, video_id)
        if is_new:
            target[current_id_key] = video_id
        return is_new

    @tasks.loop(seconds=300)
    async def check_video_youtube(self):
        api_key = self.bot.settings.youtube_api_key
        if not api_key:
            _debug_youtube("skip check: missing YOUTUBE_API_KEY")
            return

        for guild in self.bot.guilds:
            guild_data = get_youtube_data(guild.id)
            channel = self._resolve_notification_channel(guild_data.get("youtube_notification_channel"))
            if channel is None:
                _debug_youtube(
                    f"guild={guild.id} has no valid notification channel ({guild_data.get('youtube_notification_channel')})"
                )

            for channel_id in list(guild_data["yt_youtuber"].keys()):
                try:
                    uploads_playlist_id = self._get_uploads_playlist_id(channel_id, api_key)
                    if not uploads_playlist_id:
                        _debug_youtube(f"guild={guild.id} channel={channel_id}: uploads playlist not found")
                        continue

                    latest_video_id = self._get_latest_upload_video_id(uploads_playlist_id, api_key)
                    if not latest_video_id:
                        _debug_youtube(f"guild={guild.id} channel={channel_id}: latest video not found")
                        continue

                    target = guild_data["yt_youtuber"][channel_id]
                    video_kind, api_channel_name = self._get_video_meta(latest_video_id, api_key)
                    channel_name = api_channel_name or target.get("name") or channel_id
                    target["name"] = channel_name

                    if not self._record_video_id(target, video_kind, latest_video_id):
                        continue

                    if channel is None:
                        _debug_youtube(
                            f"guild={guild.id} channel={channel_id} new {video_kind}={latest_video_id} but no notify channel"
                        )
                        continue

                    yt_link = (
                        f"https://www.youtube.com/shorts/{latest_video_id}"
                        if video_kind == "short"
                        else f"https://youtu.be/{latest_video_id}"
                    )
                    text = guild_data["youtube_notification_text"].replace("{ytber}", channel_name).replace("{url}", yt_link)
                    await channel.send(text)
                    _debug_youtube(
                        f"sent guild={guild.id} channel={channel_id} kind={video_kind} id={latest_video_id}"
                    )
                except Exception as exc:
                    _debug_youtube(f"check failed guild={guild.id} channel={channel_id} error={exc}")

            save_youtube_data(guild.id, guild_data)

    @has_permissions(manage_guild=True)
    @commands.hybrid_command(with_app_command=True)
    async def youtubers(self, ctx: commands.Context, arg: str, youtuber: typing.Optional[str] = None):
        c_data = get_youtube_data(ctx.guild.id)
        if arg == "all":
            ytber_list = []
            for ytber in c_data["yt_youtuber"].keys():
                ytber_list.append(c_data["yt_youtuber"][ytber]["name"])
            await ctx.send(ytber_list)

        if arg in ["add", "del"]:
            if youtuber is not None:
                if c_data["youtube_notification_channel"] is None:
                    await ctx.send("pls setup the notification channel\nexample: !notify #channel")
                    return
                load_msg = await ctx.send("<a:load:854870818982723604> searching... <a:load:854870818982723604>")
                if arg == "add":
                    api_key = self.bot.settings.youtube_api_key
                    if not api_key:
                        await ctx.send("missing YOUTUBE_API_KEY in .env")
                        await load_msg.delete()
                        return
                    search_url = (
                        "https://www.googleapis.com/youtube/v3/search?part=snippet&channelId="
                        + youtuber
                        + "&maxResults=1&order=date&key="
                        + api_key
                    )
                    r = requests.get(search_url, timeout=15)
                    r.raise_for_status()
                    info = r.json()
                    if info and info.get("items"):
                        ytb_name = info["items"][0]["snippet"]["channelTitle"]
                        video_id = info["items"][0]["id"].get("videoId") or ""
                        c_data["yt_youtuber"][youtuber] = {
                            "id": youtuber,
                            "name": ytb_name,
                            "videoId": video_id,
                            "streamId": video_id,
                            "shortId": video_id,
                            "videoHistory": [video_id] if video_id else [],
                            "streamHistory": [video_id] if video_id else [],
                            "shortHistory": [video_id] if video_id else [],
                        }
                        await ctx.send(f"å·²é???**{ytb_name}** Youtube?šçŸ¥.")
                    await load_msg.delete()

                if arg == "del":
                    if youtuber in c_data["yt_youtuber"]:
                        ytb_name = c_data["yt_youtuber"][youtuber]["name"]
                        del c_data["yt_youtuber"][youtuber]
                        await ctx.send(f"å·²é???**{ytb_name}** Youtube?šçŸ¥.")
                    await load_msg.delete()

                save_youtube_data(ctx.guild.id, c_data)
            else:
                await ctx.send("pls input streamer id.\nexample: **!youtubers add din4ni**")

    @has_permissions(manage_guild=True)
    @commands.hybrid_command(with_app_command=True)
    async def youtube_text(self, ctx: commands.Context, *, text: str):
        c_data = get_youtube_data(ctx.guild.id)
        c_data["youtube_notification_text"] = f"{text}"
        save_youtube_data(ctx.guild.id, c_data)
        await ctx.send(f"youtube notification text\n```{text}```")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Youtube(bot))
