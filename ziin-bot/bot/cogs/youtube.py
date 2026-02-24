import re
import typing

import requests
from bot.core.classed import Cog_Extension
from bot.services.channel_data import get_youtube_data, save_youtube_data
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions


def _append_unique_id(bucket: list[str], value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value in bucket:
        return False
    bucket.append(value)
    return True


def yt_short_check(ytber: str, guild_data: dict):
    search_url = "https://www.youtube.com/channel/" + ytber + "/shorts"
    r = requests.get(search_url, timeout=15)
    r.raise_for_status()
    info = r.text
    if not info:
        return False, False

    short_id = re.search(r'(?<={"videoId":").*?(?=",)', info).group()
    channel_name = re.search(r'(?<="channelMetadataRenderer":{"title":").*?(?=",)', info).group()
    target = guild_data["yt_youtuber"][ytber]
    target["name"] = channel_name
    target["shortId"] = short_id
    short_history = target.setdefault("shortHistory", [])
    if not isinstance(short_history, list):
        short_history = []
        target["shortHistory"] = short_history
    is_new = _append_unique_id(short_history, short_id)
    if is_new:
        return short_id, channel_name
    return False, False


def yt_video_check(ytber: str, guild_data: dict):
    search_url = "https://www.youtube.com/channel/" + ytber + "/videos"
    r = requests.get(search_url, timeout=15)
    r.raise_for_status()
    info = r.text
    if not info:
        return False, False

    video_id = re.search(r'(?<={"videoId":").*?(?=",)', info).group()
    channel_name = re.search(r'(?<="channelMetadataRenderer":{"title":").*?(?=",)', info).group()
    target = guild_data["yt_youtuber"][ytber]
    target["name"] = channel_name
    target["videoId"] = video_id
    video_history = target.setdefault("videoHistory", [])
    if not isinstance(video_history, list):
        video_history = []
        target["videoHistory"] = video_history
    is_new = _append_unique_id(video_history, video_id)
    if is_new:
        return video_id, channel_name
    return False, False


class Youtube(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        self.check_video_youtube.start()

    @tasks.loop(seconds=300)
    async def check_video_youtube(self):
        for guild in self.bot.guilds:
            guild_data = get_youtube_data(guild.id)
            try:
                for ytber in list(guild_data["yt_youtuber"].keys()):
                    video_id, channel_name = yt_video_check(ytber, guild_data)
                    if video_id and channel_name:
                        yt_link = "https://youtu.be/" + video_id
                        text = guild_data["youtube_notification_text"].replace("{ytber}", channel_name).replace("{url}", yt_link)
                        channel_id = guild_data.get("youtube_notification_channel")
                        channel = self.bot.get_channel(channel_id) if channel_id else None
                        if channel:
                            await channel.send(text)

                    short_id, channel_name = yt_short_check(ytber, guild_data)
                    if short_id and channel_name:
                        yt_link = "https://www.youtube.com/shorts/" + short_id
                        text = guild_data["youtube_notification_text"].replace("{ytber}", channel_name).replace("{url}", yt_link)
                        channel_id = guild_data.get("youtube_notification_channel")
                        channel = self.bot.get_channel(channel_id) if channel_id else None
                        if channel:
                            await channel.send(text)
                save_youtube_data(guild.id, guild_data)
            except Exception:
                pass

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

