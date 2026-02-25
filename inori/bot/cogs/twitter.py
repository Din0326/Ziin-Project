from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone

import discord
import requests
from discord.ext import commands, tasks

log = logging.getLogger(__name__)
MONITOR_HANDLE = "oginoinori23"
STATE_KEY = "twitter_last_tweet_id"


def _extract_tweets(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            tweets = data.get("tweets")
            if isinstance(tweets, list):
                return [x for x in tweets if isinstance(x, dict)]
        tweets = payload.get("tweets")
        if isinstance(tweets, list):
            return [x for x in tweets if isinstance(x, dict)]
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    return []


def _parse_time(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
    except Exception:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None


def _extract_image(tweet: dict[str, object]) -> str:
    ext = tweet.get("extendedEntities") if isinstance(tweet.get("extendedEntities"), dict) else {}
    media = ext.get("media") if isinstance(ext.get("media"), list) else []
    for item in media:
        if not isinstance(item, dict):
            continue
        value = item.get("media_url_https") or item.get("media_url")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _extract_video(tweet: dict[str, object]) -> str:
    ext = tweet.get("extendedEntities") if isinstance(tweet.get("extendedEntities"), dict) else {}
    media = ext.get("media") if isinstance(ext.get("media"), list) else []
    for item in media:
        if not isinstance(item, dict):
            continue
        mtype = str(item.get("type", "")).lower()
        if mtype not in {"video", "animated_gif"}:
            continue
        info = item.get("video_info") if isinstance(item.get("video_info"), dict) else {}
        variants = info.get("variants") if isinstance(info.get("variants"), list) else []
        mp4 = []
        for v in variants:
            if not isinstance(v, dict):
                continue
            ctype = str(v.get("content_type", "")).lower()
            url = str(v.get("url", "")).strip()
            if not url or "mp4" not in ctype:
                continue
            bitrate = v.get("bitrate")
            mp4.append((int(bitrate) if isinstance(bitrate, int) else 0, url))
        if mp4:
            mp4.sort(key=lambda x: x[0], reverse=True)
            return mp4[0][1]
    return ""


class TwitterMonitor(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_checked_utc = datetime.now(timezone.utc) - timedelta(hours=1)
        self.check_tweet.start()

    def cog_unload(self) -> None:
        self.check_tweet.cancel()

    async def _get_channel(self) -> discord.TextChannel | None:
        cid = self.bot.settings.twitter_notify_channel_id
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

    def _fetch_latest_tweet(self) -> dict | None:
        key = self.bot.settings.twitterapi_io_key
        if not key:
            raise RuntimeError("TWITTERAPI_IO_KEY missing")

        now_utc = datetime.now(timezone.utc)
        since_utc = self._last_checked_utc
        if since_utc >= now_utc:
            since_utc = now_utc - timedelta(seconds=5)

        query = (
            f"from:{MONITOR_HANDLE} "
            f"since:{since_utc.strftime('%Y-%m-%d_%H:%M:%S_UTC')} "
            f"until:{now_utc.strftime('%Y-%m-%d_%H:%M:%S_UTC')} "
            "include:nativeretweets"
        )
        response = requests.get(
            f"{self.bot.settings.twitterapi_io_base}/twitter/tweet/advanced_search",
            headers={"X-API-Key": key},
            params={"query": query, "queryType": "Latest"},
            timeout=30,
        )
        response.raise_for_status()
        self._last_checked_utc = now_utc

        tweets = _extract_tweets(response.json())
        if not tweets:
            return None
        return tweets[0]

    @tasks.loop(seconds=600)
    async def check_tweet(self) -> None:
        self.check_tweet.change_interval(seconds=max(60, self.bot.settings.twitter_poll_seconds))
        await self.bot.wait_until_ready()

        channel = await self._get_channel()
        if channel is None:
            return

        try:
            tweet = self._fetch_latest_tweet()
        except Exception as exc:
            log.warning("twitter fetch failed: %s", exc)
            return

        if not tweet:
            return

        tweet_id = str(tweet.get("id", "")).strip()
        if not tweet_id:
            return

        last_id = self.bot.state.get(STATE_KEY, "")
        if tweet_id == last_id:
            return

        author = tweet.get("author") if isinstance(tweet.get("author"), dict) else {}
        screen_name = str(author.get("userName", MONITOR_HANDLE)).strip() or MONITOR_HANDLE
        display_name = str(author.get("name", screen_name)).strip() or screen_name
        profile_image = str(author.get("profilePicture", "")).strip()
        tweet_url = str(tweet.get("url", "")).strip() or f"https://x.com/{screen_name}/status/{tweet_id}"
        text = str(tweet.get("text", "")).strip()
        text = re.sub(r"https?://t\\.co/\\S+", "", text).strip()
        created_at = str(tweet.get("createdAt", "")).strip()
        image_url = _extract_image(tweet)
        video_url = _extract_video(tweet)

        embed = discord.Embed(title=" ", url=tweet_url, description=f"\n{text}" if text else None, color=discord.Color.from_rgb(240, 171, 252))
        author_name = f"{display_name} (@{screen_name})"
        if profile_image:
            embed.set_author(name=author_name, url=f"https://x.com/{screen_name}", icon_url=profile_image)
            embed.set_thumbnail(url=profile_image)
        else:
            embed.set_author(name=author_name, url=f"https://x.com/{screen_name}")
        if image_url:
            embed.set_image(url=image_url)
        if video_url:
            embed.add_field(name="Video Link", value=f"[Watch Video]({video_url})", inline=False)
        embed.set_footer(
            text="X - Made by dinnn._o",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/X_logo_2023.svg/1200px-X_logo_2023.svg.png",
        )
        embed.timestamp = _parse_time(created_at) or datetime.now(tz=timezone(timedelta(hours=8)))

        message = f"<@&1279868417171656714> 垂耳兔在推特發文了，點進來查看一下吧 ᐡᴗ ̫ ᴗᐡ\n{tweet_url}"
        await channel.send(message, embed=embed)
        self.bot.state.set(STATE_KEY, tweet_id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TwitterMonitor(bot))
