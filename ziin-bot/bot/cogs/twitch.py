import typing
from datetime import datetime
import logging
import os

import discord
import requests
from bot.core.classed import Cog_Extension
from bot.services.channel_data import (
    ensure_twitch_data,
    ensure_youtube_data,
    get_twitch_data,
    save_twitch_data,
    get_youtube_data,
    save_youtube_data,
)
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

AUTH_URL = "https://id.twitch.tv/oauth2/token"
online_title = [{}]
logger = logging.getLogger("__main__")
_DEBUG_TWITCH = os.getenv("DEBUG_TWITCH", "0") == "1"


def _debug_twitch(message: str) -> None:
    if _DEBUG_TWITCH:
        logger.info("[twitch] %s", message)


def _fetch_access_token(client_id: str, client_secret: str) -> str | None:
    if not client_id or not client_secret:
        return None
    params = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
    }
    try:
        response = requests.post(url=AUTH_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception:
        return None


def stream_check(usr: str, guild_data: dict, client_id: str, access_token: str):
    head = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
    }
    try:
        streams_response = requests.get(
            "https://api.twitch.tv/helix/streams?user_login=" + usr,
            headers=head,
            timeout=15,
        )
        streams_response.raise_for_status()
        streams = streams_response.json().get("data", [])
    except Exception:
        return None

    if streams and isinstance(streams[0], dict) and streams[0].get("type") == "live":
        stream = streams[0]
        became_online = False
        if usr in guild_data["offline_streamers"]:
            guild_data["offline_streamers"].remove(usr)
        if usr not in guild_data["online_streamers"]:
            guild_data["online_streamers"].append(usr)
            became_online = True
            user_login = stream.get("user_login", usr)
            online_title[0][user_login] = {"title": stream.get("title", "")}
            _debug_twitch(
                f"{usr} -> ONLINE | online={guild_data['online_streamers']} | offline={guild_data['offline_streamers']}"
            )

        usr_icon = ""
        try:
            user_response = requests.get(
                f"https://api.twitch.tv/helix/users?login={usr}",
                headers=head,
                timeout=15,
            )
            user_response.raise_for_status()
            user_data = user_response.json().get("data", [])
            if user_data and isinstance(user_data[0], dict):
                usr_icon = user_data[0].get("profile_image_url", "")
        except Exception:
            usr_icon = ""

        return stream, usr_icon, became_online

    if usr in guild_data["online_streamers"]:
        guild_data["online_streamers"].remove(usr)
    online_title[0].pop(usr, None)
    if usr not in guild_data["offline_streamers"]:
        guild_data["offline_streamers"].append(usr)
    _debug_twitch(
        f"{usr} -> OFFLINE | online={guild_data['online_streamers']} | offline={guild_data['offline_streamers']}"
    )
    return None


def user_check(streamer: str, client_id: str, access_token: str):
    head = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
    }
    url = "https://api.twitch.tv/helix/users?login=" + streamer
    r = requests.get(url, headers=head, timeout=15).json().get("data", [])
    if r:
        return r[0]
    return False


class Twitch(Cog_Extension):
    def __init__(self, bot):
        super().__init__(bot)
        self._live_message_ids: dict[tuple[int, str], int] = {}
        self._live_user_icons: dict[tuple[int, str], str] = {}

    def _build_live_embed(self, r: dict, usr_icon: str) -> discord.Embed:
        title = r.get("title", "Twitch Live")
        twitch_link = "https://www.twitch.tv/" + r.get("user_login", "")
        author_name = f"{r.get('user_name', 'Streamer')} is live now!!"
        thumbnail_base = str(r.get("thumbnail_url", "")).replace("{width}x{height}", "1920x1080")
        thumbnail = f"{thumbnail_base}?ts={int(datetime.utcnow().timestamp())}" if thumbnail_base else ""

        embed = discord.Embed(title=title, url=twitch_link, timestamp=datetime.utcnow())
        embed.set_author(name=author_name, icon_url=usr_icon)
        embed.add_field(name="Game", value=(r.get("game_name") if r.get("game_name") else "---"), inline=True)
        embed.add_field(name="Viewers", value=str(r.get("viewer_count", 0)), inline=True)
        if usr_icon:
            embed.set_thumbnail(url=usr_icon)
        if thumbnail:
            embed.set_image(url=thumbnail)
        embed.set_footer(
            text="Made by dinnn._o",
            icon_url="https://static.twitchcdn.net/assets/favicon-32-e29e246c157142c94346.png",
        )
        return embed

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_online_twitch.is_running():
            self.check_online_twitch.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        ensure_twitch_data(guild.id)
        ensure_youtube_data(guild.id)

    @tasks.loop(seconds=60)
    async def check_online_twitch(self):
        client_id = self.bot.settings.twitch_client_id
        client_secret = self.bot.settings.twitch_client_secret
        access_token = _fetch_access_token(client_id, client_secret)
        if not access_token:
            return

        for guild in self.bot.guilds:
            guild_data = get_twitch_data(guild.id)
            for usr in list(guild_data["all_streamers"]):
                try:
                    result = stream_check(usr, guild_data, client_id, access_token)
                except Exception:
                    _debug_twitch(f"stream_check exception guild={guild.id} user={usr}")
                    continue

                save_twitch_data(guild.id, guild_data)
                _debug_twitch(
                    f"saved guild={guild.id} user={usr} | online={guild_data['online_streamers']} | offline={guild_data['offline_streamers']}"
                )

                key = (guild.id, usr)
                if not result:
                    if usr not in guild_data["online_streamers"]:
                        self._live_message_ids.pop(key, None)
                        self._live_user_icons.pop(key, None)
                    continue

                r, usr_icon, became_online = result
                if not isinstance(r, dict):
                    continue

                channel_id = guild_data.get("twitch_notification_channel")
                channel = self.bot.get_channel(int(channel_id)) if channel_id else None
                if not channel:
                    continue

                cached_icon = usr_icon or self._live_user_icons.get(key, "")
                embed = self._build_live_embed(r, cached_icon)

                if became_online or key not in self._live_message_ids:
                    twitch_link = "https://www.twitch.tv/" + r.get("user_login", usr)
                    text = guild_data["twitch_notification_text"].replace("{streamer}", r.get("user_name", usr)).replace("{url}", twitch_link)
                    msg = await channel.send(content=text, embed=embed)
                    self._live_message_ids[key] = msg.id
                    self._live_user_icons[key] = cached_icon
                else:
                    msg_id = self._live_message_ids.get(key)
                    if not msg_id:
                        continue
                    try:
                        msg = await channel.fetch_message(msg_id)
                        await msg.edit(embed=embed)
                    except Exception:
                        _debug_twitch(f"message edit failed guild={guild.id} user={usr} message_id={msg_id}")

    @has_permissions(manage_guild=True)
    @commands.hybrid_command(with_app_command=True)
    async def streamers(self, ctx: commands.Context, arg: str, streamer: typing.Optional[str] = None):
        c_data = get_twitch_data(ctx.guild.id)
        if arg == "online":
            await ctx.send(c_data["online_streamers"])
        if arg == "offline":
            await ctx.send(c_data["offline_streamers"])
        if arg == "all":
            await ctx.send(c_data["all_streamers"])
        if arg in ["add", "del"]:
            if streamer is not None:
                if c_data["twitch_notification_channel"] is None:
                    await ctx.send("pls setup the notification channel\nexample: !notify #channel")
                    return
                load_msg = await ctx.send("<a:load:854870818982723604> searching... <a:load:854870818982723604>")
                if arg == "add":
                    access_token = _fetch_access_token(self.bot.settings.twitch_client_id, self.bot.settings.twitch_client_secret)
                    valid_user = user_check(streamer, self.bot.settings.twitch_client_id, access_token) if access_token else False
                    if valid_user:
                        if streamer not in c_data["all_streamers"]:
                            c_data["all_streamers"].append(streamer)
                        add_text = f">>> added! Twitch > **{valid_user['login']}({valid_user['display_name']})**\nhttps://www.twitch.tv/{valid_user['login']}"
                        await ctx.send(add_text)
                    else:
                        await ctx.send(f"cant find this streamer **{streamer}**")
                    await load_msg.delete()
                if arg == "del":
                    if streamer in c_data["all_streamers"]:
                        c_data["all_streamers"].remove(streamer)
                        if streamer in c_data["online_streamers"]:
                            c_data["online_streamers"].remove(streamer)
                        if streamer in c_data["offline_streamers"]:
                            c_data["offline_streamers"].remove(streamer)
                        await ctx.send(f"deleted {streamer} in streamers list.")
                        await load_msg.delete()
                save_twitch_data(ctx.guild.id, c_data)
            else:
                await ctx.send("pls input streamer id.\nexample: **!streamers add din4ni**")

    @has_permissions(manage_guild=True)
    @commands.hybrid_command(with_app_command=True)
    async def twitch_text(self, ctx: commands.Context, *, text: str):
        c_data = get_twitch_data(ctx.guild.id)
        c_data["twitch_notification_text"] = f"{text}"
        save_twitch_data(ctx.guild.id, c_data)
        await ctx.send(f"twtich notification text\n```{text}```")

    @has_permissions(manage_guild=True)
    @commands.hybrid_command(with_app_command=True)
    async def notify(self, ctx: commands.Context, platform: str, channel: discord.TextChannel):
        if platform != "youtube" and platform != "twitch":
            await ctx.send("pls input platform(youtube/twitch)\nexample: !notify twitch #channel")
            return
        if channel is not None:
            if platform == "twitch":
                c_data = get_twitch_data(ctx.guild.id)
                c_data["twitch_notification_channel"] = channel.id
                save_twitch_data(ctx.guild.id, c_data)
            elif platform == "youtube":
                c_data = get_youtube_data(ctx.guild.id)
                c_data["youtube_notification_channel"] = channel.id
                save_youtube_data(ctx.guild.id, c_data)
            await ctx.send(f"{platform} notification channel setup to {channel.mention}")
        else:
            await ctx.send("pls mention a channel or give a channel id")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Twitch(bot))
