import { NextRequest, NextResponse } from "next/server";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getDiscordAccessToken } from "@/lib/server-auth";
import { getTwitterSettings, upsertTwitterSettings } from "@/lib/local-db";

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

  const settings = await getTwitterSettings(serverId);
  return NextResponse.json({
    settings: {
      twitterNotificationChannel: settings.TwitterNotificationChannel,
      twitterNotificationText: settings.TwitterNotificationText,
      xusers: settings.XUsers
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
    twitterNotificationChannel?: unknown;
    twitterNotificationText?: unknown;
    xusers?: unknown;
  };

  const updateData: {
    TwitterNotificationChannel?: string | null;
    TwitterNotificationText?: string;
    XUsers?: Array<{
      id: string;
      name: string;
      tweetId: string;
      tweetHistory: string[];
    }>;
  } = {};

  if (payload.twitterNotificationChannel === null || typeof payload.twitterNotificationChannel === "string") {
    updateData.TwitterNotificationChannel =
      payload.twitterNotificationChannel === null ? null : payload.twitterNotificationChannel.trim();
  }
  if (typeof payload.twitterNotificationText === "string") {
    updateData.TwitterNotificationText = payload.twitterNotificationText;
  }
  if (Array.isArray(payload.xusers)) {
    updateData.XUsers = payload.xusers
      .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
      .map((item) => ({
        id: typeof item.id === "string" ? item.id : "",
        name: typeof item.name === "string" ? item.name : "",
        tweetId: typeof item.tweetId === "string" ? item.tweetId : "",
        tweetHistory: Array.isArray(item.tweetHistory)
          ? item.tweetHistory.filter((value): value is string => typeof value === "string")
          : []
      }))
      .filter((item) => item.id.trim().length > 0);
  }

  if (Object.keys(updateData).length === 0) {
    return NextResponse.json({ message: "No valid fields to update" }, { status: 400 });
  }

  await upsertTwitterSettings(serverId, updateData);
  return NextResponse.json({ ok: true });
}
