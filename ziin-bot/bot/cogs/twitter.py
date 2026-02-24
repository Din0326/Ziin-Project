from __future__ import annotations

import logging
import os
import re
import typing
import xml.etree.ElementTree as ET

import discord
import requests
from bot.core.classed import Cog_Extension
from bot.services.channel_data import get_twitter_data, save_twitter_data, ensure_twitter_data
from discord.ext import commands, tasks
from discord.ext.commands import has_permissions

logger = logging.getLogger("__main__")
_DEBUG_TWITTER = os.getenv("DEBUG_TWITTER", "0") == "1"
_NITTER_BASE_URL = (os.getenv("NITTER_BASE_URL", "https://nitter.net") or "https://nitter.net").rstrip("/")
_STATUS_ID_RE = re.compile(r"/status/(\d+)")


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


def _resolve_latest_tweet(handle: str) -> tuple[str, str, str] | None:
    rss_url = f"{_NITTER_BASE_URL}/{handle}/rss"
    response = requests.get(rss_url, timeout=20, headers={"User-Agent": "ZiinBot/1.0"})
    response.raise_for_status()
    root = ET.fromstring(response.text)
    channel = root.find("channel")
    if channel is None:
        return None

    item = channel.find("item")
    if item is None:
        return None

    link = (item.findtext("link") or "").strip()
    if not link:
        return None

    title = (item.findtext("title") or "").strip()
    creator = (item.findtext("{http://purl.org/dc/elements/1.1/}creator") or "").strip()
    display_name = creator.lstrip("@") if creator else handle
    match = _STATUS_ID_RE.search(link)
    if not match:
        return None

    tweet_id = match.group(1)
    if not title:
        title = "New tweet"
    return tweet_id, link, display_name


class Twitter(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_twitter_posts.is_running():
            self.check_twitter_posts.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        ensure_twitter_data(guild.id)

    @tasks.loop(seconds=300)
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
