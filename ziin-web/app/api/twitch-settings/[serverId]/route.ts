import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getTwitchSettings, upsertTwitchSettings } from "@/lib/local-db";

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

const getAuthorizedSession = async (serverId: string) => {
  const session = await getServerSession(authOptions);
  const accessToken = session?.accessToken;
  if (!accessToken) {
    return { ok: false as const, response: NextResponse.json({ message: "Unauthorized" }, { status: 401 }) };
  }

  const allowed = await canManageServer(accessToken, serverId);
  if (!allowed) {
    return { ok: false as const, response: NextResponse.json({ message: "Forbidden" }, { status: 403 }) };
  }

  return { ok: true as const };
};

export async function GET(_: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;
  const auth = await getAuthorizedSession(serverId);
  if (!auth.ok) {
    return auth.response;
  }

  const settings = await getTwitchSettings(serverId);
  return NextResponse.json({
    settings: {
      twitchNotificationChannel: settings.TwitchNotificationChannel,
      twitchNotificationText: settings.TwitchNotificationText,
      allStreamers: settings.AllStreamers,
      onlineStreamers: settings.OnlineStreamers,
      offlineStreamers: settings.OfflineStreamers
    }
  });
}

export async function PUT(request: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;
  const auth = await getAuthorizedSession(serverId);
  if (!auth.ok) {
    return auth.response;
  }

  const payload = (await request.json()) as {
    twitchNotificationChannel?: unknown;
    twitchNotificationText?: unknown;
    allStreamers?: unknown;
    onlineStreamers?: unknown;
    offlineStreamers?: unknown;
  };

  const updateData: {
    TwitchNotificationChannel?: string | null;
    TwitchNotificationText?: string;
    AllStreamers?: string[];
    OnlineStreamers?: string[];
    OfflineStreamers?: string[];
  } = {};

  if (payload.twitchNotificationChannel === null || typeof payload.twitchNotificationChannel === "string") {
    updateData.TwitchNotificationChannel =
      payload.twitchNotificationChannel === null ? null : payload.twitchNotificationChannel.trim();
  }
  if (typeof payload.twitchNotificationText === "string") {
    updateData.TwitchNotificationText = payload.twitchNotificationText;
  }
  if (Array.isArray(payload.allStreamers)) {
    updateData.AllStreamers = payload.allStreamers.filter((item): item is string => typeof item === "string");
  }
  if (Array.isArray(payload.onlineStreamers)) {
    updateData.OnlineStreamers = payload.onlineStreamers.filter((item): item is string => typeof item === "string");
  }
  if (Array.isArray(payload.offlineStreamers)) {
    updateData.OfflineStreamers = payload.offlineStreamers.filter((item): item is string => typeof item === "string");
  }

  if (Object.keys(updateData).length === 0) {
    return NextResponse.json({ message: "No valid fields to update" }, { status: 400 });
  }

  await upsertTwitchSettings(serverId, updateData);
  return NextResponse.json({ ok: true });
}
