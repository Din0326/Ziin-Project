import { NextRequest, NextResponse } from "next/server";

const CACHE_TTL_MS = 1000 * 60 * 30;
const cache = new Map<string, { url: string; name: string; expiresAt: number }>();

const extractOgImage = (html: string): string | null => {
  const match = html.match(/<meta\s+property="og:image"\s+content="([^"]+)"/i);
  if (!match?.[1]) {
    return null;
  }
  return match[1].replace(/&amp;/g, "&");
};

const extractOgTitle = (html: string): string | null => {
  const ogMatch = html.match(/<meta\s+property="og:title"\s+content="([^"]+)"/i);
  if (ogMatch?.[1]) {
    return ogMatch[1].trim();
  }
  const titleMatch = html.match(/<title>([^<]+)<\/title>/i);
  if (titleMatch?.[1]) {
    return titleMatch[1].trim();
  }
  return null;
};

const normalizePlatform = (value: string | null): "twitch" | "youtube" | null => {
  if (value === "twitch" || value === "youtube") {
    return value;
  }
  return null;
};

const getTargetUrl = (platform: "twitch" | "youtube", id: string): string => {
  if (platform === "twitch") {
    return `https://www.twitch.tv/${encodeURIComponent(id)}`;
  }
  return `https://www.youtube.com/channel/${encodeURIComponent(id)}`;
};

const resolveTwitchAvatarFromDecapi = async (id: string): Promise<string | null> => {
  try {
    const response = await fetch(`https://decapi.me/twitch/avatar/${encodeURIComponent(id)}`, {
      method: "GET",
      redirect: "follow"
    });
    if (!response.ok) {
      return null;
    }
    const text = (await response.text()).trim();
    if (!/^https?:\/\//i.test(text)) {
      return null;
    }
    return text;
  } catch {
    return null;
  }
};

export async function GET(request: NextRequest) {
  const platform = normalizePlatform(request.nextUrl.searchParams.get("platform"));
  const id = request.nextUrl.searchParams.get("id")?.trim() ?? "";
  if (!platform || !id) {
    return NextResponse.json({ message: "Invalid parameters" }, { status: 400 });
  }

  const cacheKey = `${platform}:${id.toLowerCase()}`;
  const now = Date.now();
  const cached = cache.get(cacheKey);
  if (cached && cached.expiresAt > now) {
    return NextResponse.json({ avatarUrl: cached.url, profileName: cached.name });
  }

  try {
    let fallbackAvatarUrl: string | null = null;
    if (platform === "twitch") {
      const decapiAvatar = await resolveTwitchAvatarFromDecapi(id);
      if (decapiAvatar) {
        fallbackAvatarUrl = decapiAvatar;
      }
    }

    const response = await fetch(getTargetUrl(platform, id), {
      method: "GET",
      redirect: "follow",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
      }
    });

    if (!response.ok) {
      if (fallbackAvatarUrl) {
        cache.set(cacheKey, { url: fallbackAvatarUrl, name: id, expiresAt: now + CACHE_TTL_MS });
        return NextResponse.json({ avatarUrl: fallbackAvatarUrl, profileName: id });
      }
      return NextResponse.json({ message: "Failed to fetch profile page" }, { status: 404 });
    }

    const html = await response.text();
    const avatarUrl = extractOgImage(html) ?? fallbackAvatarUrl;
    if (!avatarUrl) {
      return NextResponse.json({ message: "Avatar not found" }, { status: 404 });
    }
    const rawName = extractOgTitle(html) ?? id;
    const profileName = rawName
      .replace(/\s*-\s*YouTube$/i, "")
      .replace(/\s*-\s*Twitch$/i, "")
      .trim();

    cache.set(cacheKey, { url: avatarUrl, name: profileName, expiresAt: now + CACHE_TTL_MS });
    return NextResponse.json({ avatarUrl, profileName });
  } catch {
    return NextResponse.json({ message: "Failed to resolve avatar" }, { status: 500 });
  }
}
