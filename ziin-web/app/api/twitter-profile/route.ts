import { NextRequest, NextResponse } from "next/server";

const CACHE_TTL_MS = 1000 * 60 * 30;
const cache = new Map<string, { profileName: string; handle: string; expiresAt: number }>();

const normalizeHandle = (value: string): string => {
  const input = value.trim();
  if (!input) {
    return "";
  }
  const match = input.match(/(?:x\.com|twitter\.com)\/([A-Za-z0-9_]{1,15})/i);
  const raw = match?.[1] ?? input.replace(/^@+/, "");
  return raw.trim().replace(/^@+/, "");
};

export async function GET(request: NextRequest) {
  const rawHandle = request.nextUrl.searchParams.get("handle") ?? "";
  const normalized = normalizeHandle(rawHandle);
  if (!normalized) {
    return NextResponse.json({ message: "Invalid handle" }, { status: 400 });
  }

  const cacheKey = normalized.toLowerCase();
  const now = Date.now();
  const cached = cache.get(cacheKey);
  if (cached && cached.expiresAt > now) {
    return NextResponse.json({ profileName: cached.profileName, handle: cached.handle });
  }

  try {
    const response = await fetch(
      `https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names=${encodeURIComponent(normalized)}`,
      {
        method: "GET",
        redirect: "follow",
        headers: {
          "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
      }
    );
    if (response.ok) {
      const result = (await response.json()) as Array<{ name?: unknown; screen_name?: unknown }>;
      const first = Array.isArray(result) ? result[0] : undefined;
      if (first) {
        const handle =
          typeof first.screen_name === "string" && first.screen_name.trim() ? first.screen_name.trim() : normalized;
        const profileName =
          typeof first.name === "string" && first.name.trim() ? first.name.trim() : handle;

        cache.set(cacheKey, { profileName, handle, expiresAt: now + CACHE_TTL_MS });
        return NextResponse.json({ profileName, handle });
      }
    }

    const profileResponse = await fetch(`https://x.com/${encodeURIComponent(normalized)}`, {
      method: "GET",
      redirect: "follow",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
      }
    });
    if (!profileResponse.ok) {
      return NextResponse.json({ message: "Failed to resolve profile" }, { status: 404 });
    }

    const html = await profileResponse.text();
    const titleMatch = html.match(/<title>([^<]+)<\/title>/i);
    const title = titleMatch?.[1]?.trim() ?? "";
    const patternMatch = title.match(/^\s*(.*?)\s*\(@([A-Za-z0-9_]{1,15})\)/);
    if (!patternMatch) {
      return NextResponse.json({ message: "Profile not found" }, { status: 404 });
    }

    const profileName = patternMatch[1]?.trim() || normalized;
    const handle = patternMatch[2]?.trim() || normalized;

    cache.set(cacheKey, { profileName, handle, expiresAt: now + CACHE_TTL_MS });
    return NextResponse.json({ profileName, handle });
  } catch {
    return NextResponse.json({ message: "Failed to resolve profile" }, { status: 500 });
  }
}
