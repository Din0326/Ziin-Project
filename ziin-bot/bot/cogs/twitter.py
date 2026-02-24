from __future__ import annotations

import logging
import os
import re
import traceback
import typing

import discord
import requests
from bot.core.classed import Cog_Extension
from bot.services.channel_data import ensure_twitter_data, get_twitter_data, save_twitter_data
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

logger = logging.getLogger("__main__")
_DEBUG_TWITTER = os.getenv("DEBUG_TWITTER", "0") == "1"
_TWITTERAPI_IO_BASE = (os.getenv("TWITTERAPI_IO_BASE", "https://api.twitterapi.io") or "https://api.twitterapi.io").rstrip("/")
_TWITTERAPI_IO_KEY = (os.getenv("TWITTERAPI_IO_KEY", "") or "").strip()


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


def _get_nested(data: object, *path: str) -> object:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _extract_tweets(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    candidates = [
        payload.get("tweets"),
        payload.get("data"),
        _get_nested(payload, "result", "tweets"),
        payload.get("result"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
    return []


def _resolve_latest_tweet(handle: str) -> tuple[str, str, str] | None:
    if not _TWITTERAPI_IO_KEY:
        raise RuntimeError("TWITTERAPI_IO_KEY is missing")

    url = f"{_TWITTERAPI_IO_BASE}/twitter/user/last_tweets"
    headers = {"x-api-key": _TWITTERAPI_IO_KEY}
    params = {"userName": handle, "includeReplies": "false"}

    _debug_twitter(f"twitterapi request start handle={handle}")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()
    tweets = _extract_tweets(payload)
    if not tweets:
        _debug_twitter(f"twitterapi empty tweets handle={handle}")
        return None

    first = tweets[0]
    tweet_id_raw = first.get("id") or first.get("tweetId") or first.get("rest_id")
    tweet_id = str(tweet_id_raw).strip() if tweet_id_raw is not None else ""

    author = first.get("author") if isinstance(first.get("author"), dict) else {}
    screen_name_raw = (
        author.get("userName")
        or author.get("username")
        or first.get("userName")
        or first.get("screenName")
        or handle
    )
    screen_name = str(screen_name_raw).strip() or handle

    display_name_raw = author.get("name") or author.get("displayName") or first.get("name") or screen_name
    display_name = str(display_name_raw).strip() or screen_name

    tweet_url_raw = first.get("url") or first.get("tweetUrl") or first.get("permanentUrl")
    tweet_url = str(tweet_url_raw).strip() if tweet_url_raw is not None else ""

    if not tweet_id and tweet_url:
        match = re.search(r"/status/(\d+)", tweet_url)
        if match:
            tweet_id = match.group(1)

    if not tweet_id:
        _debug_twitter(f"twitterapi missing tweet id handle={handle}")
        return None

    if not tweet_url:
        tweet_url = f"https://x.com/{screen_name}/status/{tweet_id}"

    _debug_twitter(
        f"twitterapi resolve ok handle={handle} tweet_id={tweet_id} screen_name={screen_name} display_name={display_name}"
    )
    return tweet_id, tweet_url, display_name


class Twitter(Cog_Extension):
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
                    latest = _resolve_latest_tweet(handle)
                except Exception as exc:
                    _debug_twitter(f"fetch failed guild={guild.id} handle={handle} error={exc}")
                    if _DEBUG_TWITTER:
                        _debug_twitter(f"fetch traceback guild={guild.id} handle={handle}\n{traceback.format_exc()}")
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
