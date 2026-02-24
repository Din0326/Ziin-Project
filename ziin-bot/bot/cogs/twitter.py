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
    direct_candidates: list[object] = []
    if isinstance(payload, dict):
        direct_candidates.extend(
            [
                payload.get("tweets"),
                payload.get("data"),
                _get_nested(payload, "result", "tweets"),
                payload.get("result"),
                _get_nested(payload, "timeline", "tweets"),
            ]
        )
    elif isinstance(payload, list):
        direct_candidates.append(payload)
    else:
        return []

    for candidate in direct_candidates:
        if isinstance(candidate, list):
            rows = [item for item in candidate if isinstance(item, dict)]
            if rows:
                return rows

    matches: list[dict[str, object]] = []

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            normalized = node.get("tweet")
            if isinstance(normalized, dict):
                node = normalized

            if any(key in node for key in ("id", "tweetId", "rest_id")):
                matches.append(node)
                return

            for value in node.values():
                _walk(value)
            return

        if isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(payload)
    return matches


def _extract_first_image_url(tweet: dict[str, object]) -> str:
    media = tweet.get("media")
    if isinstance(media, list):
        for item in media:
            if isinstance(item, dict):
                value = item.get("url") or item.get("mediaUrl") or item.get("media_url_https") or item.get("media_url")
                if isinstance(value, str) and value.strip():
                    return value.strip()

    photos = tweet.get("photos")
    if isinstance(photos, list):
        for item in photos:
            if isinstance(item, dict):
                value = item.get("url")
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return ""


def _extract_first_video_url(tweet: dict[str, object]) -> str:
    media = tweet.get("media")
    if isinstance(media, list):
        for item in media:
            if not isinstance(item, dict):
                continue

            direct = item.get("videoUrl") or item.get("video_url")
            if isinstance(direct, str) and direct.strip():
                return direct.strip()

            variants = item.get("variants")
            if isinstance(variants, list):
                for variant in variants:
                    if not isinstance(variant, dict):
                        continue
                    content_type = variant.get("content_type") or variant.get("contentType")
                    if isinstance(content_type, str) and "mp4" not in content_type.lower():
                        continue
                    url = variant.get("url")
                    if isinstance(url, str) and url.strip():
                        return url.strip()

            url = item.get("url")
            media_type = item.get("type")
            if isinstance(media_type, str) and media_type.lower() in {"video", "animated_gif"}:
                if isinstance(url, str) and url.strip():
                    return url.strip()

    video = tweet.get("video")
    if isinstance(video, dict):
        direct = video.get("url")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
    return ""


def _resolve_latest_tweet(handle: str) -> dict[str, str] | None:
    if not _TWITTERAPI_IO_KEY:
        raise RuntimeError("TWITTERAPI_IO_KEY is missing")

    url = f"{_TWITTERAPI_IO_BASE}/twitter/user/last_tweets"
    headers = {"x-api-key": _TWITTERAPI_IO_KEY}
    params = {"userName": handle, "includeReplies": "true"}

    _debug_twitter(f"twitterapi request start handle={handle}")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()
    tweets = _extract_tweets(payload)
    if not tweets:
        if isinstance(payload, dict):
            _debug_twitter(f"twitterapi payload keys handle={handle} keys={list(payload.keys())}")
        _debug_twitter(f"twitterapi empty tweets handle={handle}")
        return None

    first_raw = tweets[0]
    first = first_raw.get("tweet") if isinstance(first_raw.get("tweet"), dict) else first_raw
    tweet_id_raw = first.get("id") or first.get("tweetId") or first.get("rest_id") or first.get("tweet_id")
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
    tweet_text_raw = first.get("text") or first.get("fullText") or first.get("full_text")
    tweet_text = str(tweet_text_raw).strip() if tweet_text_raw is not None else ""
    created_at_raw = first.get("createdAt") or first.get("created_at")
    created_at = str(created_at_raw).strip() if created_at_raw is not None else ""
    image_url = _extract_first_image_url(first)
    video_url = _extract_first_video_url(first)

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
    return {
        "tweet_id": tweet_id,
        "tweet_url": tweet_url,
        "display_name": display_name,
        "screen_name": screen_name,
        "text": tweet_text,
        "created_at": created_at,
        "image_url": image_url,
        "video_url": video_url,
    }


class Twitter(Cog_Extension):
    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_twitter_posts.is_running():
            self.check_twitter_posts.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        ensure_twitter_data(guild.id)

    @tasks.loop(seconds=600)
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

                tweet_id = latest["tweet_id"]
                tweet_url = latest["tweet_url"]
                display_name = latest["display_name"]
                screen_name = latest["screen_name"]
                tweet_text = latest["text"]
                created_at = latest["created_at"]
                image_url = latest["image_url"]
                video_url = latest["video_url"]
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
                    guild_data.get("twitter_notification_text", "{xuser} 發文了，點進來看一下吧")
                    .replace("{xuser}", item["name"])
                    .replace("{url}", tweet_url)
                )
                embed = discord.Embed(
                    title=f"{display_name} (@{screen_name})",
                    url=tweet_url,
                    description=tweet_text or None,
                    color=discord.Color.from_rgb(240, 171, 252),
                )
                if image_url and not video_url:
                    embed.set_image(url=image_url)
                if video_url:
                    embed.add_field(name="影片", value=video_url, inline=False)
                embed.set_footer(text="X · Made by Ziin Bot")
                parsed_time = discord.utils.parse_time(created_at) if created_at else None
                embed.timestamp = parsed_time or discord.utils.utcnow()
                try:
                    message_parts = [text, tweet_url]
                    if video_url:
                        message_parts.append(video_url)
                    await channel.send("\n".join(message_parts), embed=embed)
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
