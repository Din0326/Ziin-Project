import { NextRequest, NextResponse } from "next/server";

const CACHE_TTL_MS = 1000 * 60 * 30;
const cache = new Map<string, { url: string; name: string; expiresAt: number }>();
let twitchTokenCache: { token: string; expiresAt: number } | null = null;

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

const getTwitchAppAccessToken = async (): Promise<string | null> => {
  const now = Date.now();
  if (twitchTokenCache && twitchTokenCache.expiresAt > now + 60_000) {
    return twitchTokenCache.token;
  }

  const clientId = process.env.TWITCH_CLIENT_ID;
  const clientSecret = process.env.TWITCH_CLIENT_SECRET;
  if (!clientId || !clientSecret) {
    return null;
  }

  try {
    const tokenResponse = await fetch("https://id.twitch.tv/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        client_id: clientId,
        client_secret: clientSecret,
        grant_type: "client_credentials"
      }).toString()
    });
    if (!tokenResponse.ok) {
      return null;
    }

    const tokenData = (await tokenResponse.json()) as { access_token?: unknown; expires_in?: unknown };
    if (typeof tokenData.access_token !== "string" || !tokenData.access_token) {
      return null;
    }

    const expiresInSec = typeof tokenData.expires_in === "number" ? tokenData.expires_in : 3600;
    twitchTokenCache = {
      token: tokenData.access_token,
      expiresAt: now + expiresInSec * 1000
    };
    return tokenData.access_token;
  } catch {
    return null;
  }
};

const resolveTwitchProfileFromApi = async (
  id: string
): Promise<{ avatarUrl: string; profileName: string } | null> => {
  const token = await getTwitchAppAccessToken();
  const clientId = process.env.TWITCH_CLIENT_ID;
  if (!token || !clientId) {
    return null;
  }

  try {
    const response = await fetch(`https://api.twitch.tv/helix/users?login=${encodeURIComponent(id)}`, {
      method: "GET",
      headers: {
        "Client-ID": clientId,
        Authorization: `Bearer ${token}`
      }
    });
    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as {
      data?: Array<{ profile_image_url?: unknown; display_name?: unknown; login?: unknown }>;
    };
    const first = Array.isArray(data.data) ? data.data[0] : undefined;
    if (!first || typeof first.profile_image_url !== "string" || !first.profile_image_url) {
      return null;
    }

    const display =
      typeof first.display_name === "string" && first.display_name.trim()
        ? first.display_name.trim()
        : typeof first.login === "string" && first.login.trim()
          ? first.login.trim()
          : id;
    return { avatarUrl: first.profile_image_url, profileName: display };
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
      const twitchProfile = await resolveTwitchProfileFromApi(id);
      if (twitchProfile) {
        cache.set(cacheKey, { url: twitchProfile.avatarUrl, name: twitchProfile.profileName, expiresAt: now + CACHE_TTL_MS });
        return NextResponse.json(twitchProfile);
      }

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
    const safeProfileName = profileName.toLowerCase() === "twitch" ? id : profileName;

    cache.set(cacheKey, { url: avatarUrl, name: safeProfileName, expiresAt: now + CACHE_TTL_MS });
    return NextResponse.json({ avatarUrl, profileName: safeProfileName });
  } catch {
    return NextResponse.json({ message: "Failed to resolve avatar" }, { status: 500 });
  }
}
