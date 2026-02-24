import { NextRequest, NextResponse } from "next/server";

const CHANNEL_ID_PATTERN = /^UC[\w-]{22}$/;

const extractChannelIdFromHtml = (html: string): string | null => {
  const patterns = [
    /"channelId":"(UC[\w-]{22})"/,
    /<meta\s+itemprop="channelId"\s+content="(UC[\w-]{22})"/i,
    /https:\/\/www\.youtube\.com\/channel\/(UC[\w-]{22})/i
  ];

  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match?.[1]) {
      return match[1];
    }
  }

  return null;
};

const extractChannelNameFromHtml = (html: string): string | null => {
  const patterns = [
    /<meta\s+property="og:title"\s+content="([^"]+)"/i,
    /<title>([^<]+)<\/title>/i
  ];

  for (const pattern of patterns) {
    const match = html.match(pattern);
    if (match?.[1]) {
      return match[1].replace(/\s*-\s*YouTube\s*$/i, "").trim();
    }
  }

  return null;
};

const normalizeInputToUrl = (input: string): URL | null => {
  const trimmed = input.trim();
  if (!trimmed) {
    return null;
  }

  const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `https://${trimmed}`;
  try {
    return new URL(withProtocol);
  } catch {
    return null;
  }
};

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as { input?: unknown };
  const rawInput = typeof payload.input === "string" ? payload.input.trim() : "";

  if (!rawInput) {
    return NextResponse.json({ message: "Input is required" }, { status: 400 });
  }

  if (CHANNEL_ID_PATTERN.test(rawInput)) {
    return NextResponse.json({ channelId: rawInput, channelName: rawInput });
  }

  const url = normalizeInputToUrl(rawInput);
  if (!url) {
    return NextResponse.json({ message: "Invalid URL" }, { status: 400 });
  }

  const host = url.hostname.toLowerCase();
  if (!host.includes("youtube.com") && !host.includes("youtu.be")) {
    return NextResponse.json({ message: "URL must be from YouTube" }, { status: 400 });
  }

  const pathMatch = url.pathname.match(/\/channel\/(UC[\w-]{22})/i);
  if (pathMatch?.[1]) {
    return NextResponse.json({ channelId: pathMatch[1], channelName: pathMatch[1] });
  }

  try {
    const response = await fetch(url.toString(), {
      method: "GET",
      redirect: "follow",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
      }
    });

    if (!response.ok) {
      return NextResponse.json({ message: "Unable to resolve channel URL" }, { status: 400 });
    }

    const html = await response.text();
    const channelId = extractChannelIdFromHtml(html);
    if (!channelId) {
      return NextResponse.json({ message: "Cannot resolve channel ID from URL" }, { status: 400 });
    }

    const channelName = extractChannelNameFromHtml(html) ?? channelId;
    return NextResponse.json({ channelId, channelName });
  } catch {
    return NextResponse.json({ message: "Failed to resolve YouTube URL" }, { status: 500 });
  }
}
