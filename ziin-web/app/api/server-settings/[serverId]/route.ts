import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { getServerSettings, upsertServerSettings } from "@/lib/local-db";

type DiscordGuild = {
  id: string;
  permissions: string;
};

const ADMINISTRATOR_PERMISSION = BigInt(0x8);
const MANAGE_GUILD_PERMISSION = BigInt(0x20);

const hasManagePermission = (permissions: string) => {
  const bits = BigInt(permissions);
  return (
    (bits & ADMINISTRATOR_PERMISSION) !== BigInt(0) || (bits & MANAGE_GUILD_PERMISSION) !== BigInt(0)
  );
};

const canManageServer = async (accessToken: string, serverId: string) => {
  const response = await fetch("https://discord.com/api/users/@me/guilds", {
    headers: {
      Authorization: `Bearer ${accessToken}`
    },
    cache: "no-store"
  });

  if (!response.ok) {
    return false;
  }

  const guilds = (await response.json()) as DiscordGuild[];
  const guild = guilds.find((item) => item.id === serverId);
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

  const data = await getServerSettings(serverId);
  if (!data) {
    return NextResponse.json({ settings: null });
  }

  return NextResponse.json({
    settings: {
      prefix: data.Prefix ?? "",
      timezone: data.TimeZone ?? null,
      language: data.Language ?? null
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
    prefix?: unknown;
    timezone?: unknown;
    language?: unknown;
  };

  const updateData: { Prefix?: string; TimeZone?: string; Language?: string } = {};

  if (typeof payload.prefix === "string") {
    updateData.Prefix = payload.prefix.trim().slice(0, 32);
  }
  if (typeof payload.timezone === "string") {
    updateData.TimeZone = payload.timezone;
  }
  if (typeof payload.language === "string") {
    updateData.Language = payload.language;
  }

  if (Object.keys(updateData).length === 0) {
    return NextResponse.json({ message: "No valid fields to update" }, { status: 400 });
  }

  await upsertServerSettings(serverId, updateData);

  return NextResponse.json({ ok: true });
}
