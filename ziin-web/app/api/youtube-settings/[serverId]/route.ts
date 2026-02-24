import { NextRequest, NextResponse } from "next/server";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getYouTubeSettings, upsertYouTubeSettings } from "@/lib/local-db";
import { getDiscordAccessToken } from "@/lib/server-auth";

const canManageServer = async (accessToken: string, serverId: string) => {
  const result = await fetchDiscordGuilds(accessToken);
  if (!result.ok) {
    return false;
  }

  const guild = result.guilds.find((item) => item.id === serverId);
  if (!guild) {
    return false;
  }

  return hasManagePermission(guild.permissions);
};

const getAuthorizedSession = async (request: NextRequest, serverId: string) => {
  const accessToken = await getDiscordAccessToken(request);
  if (!accessToken) {
    return { ok: false as const, response: NextResponse.json({ message: "Unauthorized" }, { status: 401 }) };
  }

  const allowed = await canManageServer(accessToken, serverId);
  if (!allowed) {
    return { ok: false as const, response: NextResponse.json({ message: "Forbidden" }, { status: 403 }) };
  }

  return { ok: true as const };
};

export async function GET(request: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;
  const auth = await getAuthorizedSession(request, serverId);
  if (!auth.ok) {
    return auth.response;
  }

  const settings = await getYouTubeSettings(serverId);
  return NextResponse.json({
    settings: {
      youtubeNotificationChannel: settings.YouTubeNotificationChannel,
      youtubeNotificationText: settings.YouTubeNotificationText,
      youtubers: settings.YouTubers
    }
  });
}

export async function PUT(request: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;
  const auth = await getAuthorizedSession(request, serverId);
  if (!auth.ok) {
    return auth.response;
  }

  const payload = (await request.json()) as {
    youtubeNotificationChannel?: unknown;
    youtubeNotificationText?: unknown;
    youtubers?: unknown;
  };

  const updateData: {
    YouTubeNotificationChannel?: string | null;
    YouTubeNotificationText?: string;
    YouTubers?: Array<{
      id: string;
      name: string;
      videoId: string;
      streamId: string;
      shortId: string;
      videoHistory: string[];
      streamHistory: string[];
      shortHistory: string[];
    }>;
  } = {};

  if (payload.youtubeNotificationChannel === null || typeof payload.youtubeNotificationChannel === "string") {
    updateData.YouTubeNotificationChannel =
      payload.youtubeNotificationChannel === null ? null : payload.youtubeNotificationChannel.trim();
  }
  if (typeof payload.youtubeNotificationText === "string") {
    updateData.YouTubeNotificationText = payload.youtubeNotificationText;
  }
  if (Array.isArray(payload.youtubers)) {
    updateData.YouTubers = payload.youtubers
      .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
      .map((item) => ({
        id: typeof item.id === "string" ? item.id : "",
        name: typeof item.name === "string" ? item.name : "",
        videoId: typeof item.videoId === "string" ? item.videoId : "",
        streamId: typeof item.streamId === "string" ? item.streamId : "",
        shortId: typeof item.shortId === "string" ? item.shortId : "",
        videoHistory: Array.isArray(item.videoHistory)
          ? item.videoHistory.filter((value): value is string => typeof value === "string")
          : [],
        streamHistory: Array.isArray(item.streamHistory)
          ? item.streamHistory.filter((value): value is string => typeof value === "string")
          : [],
        shortHistory: Array.isArray(item.shortHistory)
          ? item.shortHistory.filter((value): value is string => typeof value === "string")
          : []
      }))
      .filter((item) => item.id.trim().length > 0);
  }

  if (Object.keys(updateData).length === 0) {
    return NextResponse.json({ message: "No valid fields to update" }, { status: 400 });
  }

  await upsertYouTubeSettings(serverId, updateData);
  return NextResponse.json({ ok: true });
}
