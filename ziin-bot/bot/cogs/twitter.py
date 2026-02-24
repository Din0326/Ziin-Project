from __future__ import annotations

import logging
import os
import re
import traceback
import typing

import discord
import requests
from bot.core.classed import Cog_Extension
from bot.services.channel_data import get_twitter_data, save_twitter_data, ensure_twitter_data
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions
from twikit.guest import GuestClient

logger = logging.getLogger("__main__")
_DEBUG_TWITTER = os.getenv("DEBUG_TWITTER", "0") == "1"


def _debug_twitter(message: str) -> None:
    if _DEBUG_TWITTER:
        logger.info("[twitter] %s", message)


def _normalize_handle(value: str) -> str:
    raw = value.strip()
    if not raw:
        return ""

    url_match = re.search(r"(?:x\.com|twitter\.com)/([A-Za-z0-9_]{1,15})", raw, flags=re.IGNORECASE)
    if url_match:
        return url_match.group(1).lower()

    return raw.lstrip("@").lower()


def _append_unique_id(bucket: list[str], value: str) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value in bucket:
        return False
    bucket.append(value)
    return True


def _resolve_user_meta_from_syndication(handle: str) -> tuple[str, str, str] | None:
    url = f"https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={handle}"
    response = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    response.raise_for_status()
    rows = response.json()
    if not isinstance(rows, list) or not rows:
        return None

    first = rows[0] if isinstance(rows[0], dict) else None
    if not first:
        return None

    raw_id = first.get("id")
    user_id = str(raw_id).strip() if raw_id is not None else ""
    if not user_id:
        return None
    screen_name = str(first.get("screen_name") or handle).strip() or handle
    display_name = str(first.get("name") or screen_name).strip() or screen_name
    return user_id, screen_name, display_name


class Twitter(Cog_Extension):
    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self._guest: GuestClient | None = None
        self._guest_ready = False

    async def _get_guest_client(self) -> GuestClient:
        if self._guest is None:
            _debug_twitter("guest client create")
            self._guest = GuestClient()
        if not self._guest_ready:
            _debug_twitter("guest client activate start")
            await self._guest.activate()
            self._guest_ready = True
            _debug_twitter("guest client activate ok")
        return self._guest

    async def _resolve_latest_tweet(self, handle: str) -> tuple[str, str, str] | None:
        client = await self._get_guest_client()
        user_id = ""
        screen_name = handle
        display_name = handle

        try:
            _debug_twitter(f"resolve user by screen_name start handle={handle}")
            user = await client.get_user_by_screen_name(handle)
            user_id = str(user.id)
            screen_name = getattr(user, "screen_name", handle) or handle
            display_name = getattr(user, "name", handle) or handle
            _debug_twitter(
                f"resolve user by screen_name ok handle={handle} user_id={user_id} "
                f"screen_name={screen_name} display_name={display_name}"
            )
        except Exception as exc:
            _debug_twitter(f"resolve user by screen_name failed handle={handle} error={exc!r}")
            fallback = _resolve_user_meta_from_syndication(handle)
            if not fallback:
                _debug_twitter(f"syndication fallback empty handle={handle}; trying search_tweet")
                search_tweets = await client.search_tweet(f"from:{handle}", "Latest", count=1)
                if not search_tweets:
                    _debug_twitter(f"search_tweet fallback empty handle={handle}")
                    return None
                tweet = search_tweets[0]
                tweet_id = str(tweet.id)
                user = getattr(tweet, "user", None)
                screen_name = getattr(user, "screen_name", handle) or handle
                display_name = getattr(user, "name", screen_name) or screen_name
                tweet_url = f"https://x.com/{screen_name}/status/{tweet_id}"
                _debug_twitter(
                    f"search_tweet fallback ok handle={handle} tweet_id={tweet_id} "
                    f"screen_name={screen_name} display_name={display_name}"
                )
                return tweet_id, tweet_url, display_name
            user_id, screen_name, display_name = fallback
            _debug_twitter(
                f"syndication fallback ok handle={handle} user_id={user_id} "
                f"screen_name={screen_name} display_name={display_name}"
            )

        try:
            _debug_twitter(f"get_user_tweets start handle={handle} user_id={user_id}")
            tweets = await client.get_user_tweets(user_id, count=1)
            if not tweets:
                _debug_twitter(f"get_user_tweets empty handle={handle} user_id={user_id}")
                return None
            tweet = tweets[0]
            _debug_twitter(f"get_user_tweets ok handle={handle} user_id={user_id} tweet_id={tweet.id}")
        except Exception as exc:
            _debug_twitter(
                f"get_user_tweets failed handle={handle} user_id={user_id} error={exc!r}; "
                f"trying search_tweet"
            )
            search_tweets = await client.search_tweet(f"from:{screen_name}", "Latest", count=1)
            if not search_tweets:
                _debug_twitter(f"search_tweet fallback empty handle={handle} screen_name={screen_name}")
                return None
            tweet = search_tweets[0]
            _debug_twitter(
                f"search_tweet fallback ok handle={handle} screen_name={screen_name} tweet_id={tweet.id}"
            )

        tweet_id = str(tweet.id)
        tweet_url = f"https://x.com/{screen_name}/status/{tweet_id}"
        _debug_twitter(
            f"resolve latest tweet final handle={handle} tweet_id={tweet_id} "
            f"screen_name={screen_name} display_name={display_name}"
        )
        return tweet_id, tweet_url, display_name

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_twitter_posts.is_running():
            self.check_twitter_posts.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        ensure_twitter_data(guild.id)

    @tasks.loop(seconds=60)
    async def check_twitter_posts(self):
        for guild in self.bot.guilds:
            guild_data = get_twitter_data(guild.id)
            channel_id = guild_data.get("twitter_notification_channel")
            channel = self.bot.get_channel(int(channel_id)) if channel_id else None
            accounts = guild_data.get("twitter_accounts", {})
            if not isinstance(accounts, dict):
                accounts = {}
                guild_data["twitter_accounts"] = accounts

            for handle in list(accounts.keys()):
                item = accounts.get(handle)
                if not isinstance(item, dict):
                    continue
                try:
                    latest = await self._resolve_latest_tweet(handle)
                except Exception as exc:
                    _debug_twitter(f"fetch failed guild={guild.id} handle={handle} error={exc}")
                    if _DEBUG_TWITTER:
                        _debug_twitter(f"fetch traceback guild={guild.id} handle={handle}\n{traceback.format_exc()}")
                    self._guest_ready = False
                    continue

                if not latest:
                    continue

                tweet_id, tweet_url, display_name = latest
                history = item.setdefault("tweetHistory", [])
                if not isinstance(history, list):
                    history = []
                    item["tweetHistory"] = history

                is_new = _append_unique_id(history, tweet_id)
                if not is_new:
                    continue

                item["tweetId"] = tweet_id
                item["name"] = display_name or handle

                if channel is None:
                    _debug_twitter(f"guild={guild.id} handle={handle} new={tweet_id} but no notify channel")
                    continue

                text = (
                    guild_data.get("twitter_notification_text", "**{xuser}** posted a new tweet!\n**{url}**")
                    .replace("{xuser}", item["name"])
                    .replace("{url}", tweet_url)
                )
                try:
                    await channel.send(text)
                    _debug_twitter(f"sent guild={guild.id} handle={handle} tweet={tweet_id}")
                except Exception as exc:
                    _debug_twitter(f"send failed guild={guild.id} handle={handle} error={exc}")

            save_twitter_data(guild.id, guild_data)

    @has_permissions(manage_guild=True)
    @commands.hybrid_command(with_app_command=True)
    async def xusers(self, ctx: commands.Context, arg: str, account: typing.Optional[str] = None):
        c_data = get_twitter_data(ctx.guild.id)
        accounts = c_data.setdefault("twitter_accounts", {})
        if not isinstance(accounts, dict):
            accounts = {}
            c_data["twitter_accounts"] = accounts

        if arg == "all":
            await ctx.send(list(accounts.keys()))
            return

        if arg in {"add", "del"}:
            if not account:
                await ctx.send("pls input x handle. example: !xusers add @elonmusk")
                return
            handle = _normalize_handle(account)
            if not handle:
                await ctx.send("invalid handle")
                return

            if arg == "add":
                if handle not in accounts:
                    accounts[handle] = {
                        "id": handle,
                        "name": handle,
                        "tweetId": "",
                        "tweetHistory": [],
                    }
                save_twitter_data(ctx.guild.id, c_data)
                await ctx.send(f"added x account: **{handle}**")
                return

            if handle in accounts:
                del accounts[handle]
            save_twitter_data(ctx.guild.id, c_data)
            await ctx.send(f"deleted x account: **{handle}**")

    @has_permissions(manage_guild=True)
    @commands.hybrid_command(with_app_command=True)
    async def twitter_text(self, ctx: commands.Context, *, text: str):
        c_data = get_twitter_data(ctx.guild.id)
        c_data["twitter_notification_text"] = text
        save_twitter_data(ctx.guild.id, c_data)
        await ctx.send(f"twitter notification text\n```{text}```")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Twitter(bot))
