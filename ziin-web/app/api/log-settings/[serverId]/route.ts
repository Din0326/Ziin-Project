import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getLogSettings, upsertLogSettings } from "@/lib/local-db";

const logFieldMap = {
  memberAdd: "MemberAdd",
  memberKick: "MemberKick",
  memberNickUpdate: "MemberNickUpdate",
  memberRemove: "MemberRemove",
  memberUnban: "MemberUnban",
  memberUpdate: "MemberUpdate",
  roleCreate: "RoleCreate",
  roleDelete: "RoleDelete",
  roleUpdate: "RoleUpdate",
  channelCreate: "channelCreate",
  channelDelete: "channelDelete",
  guildUpdate: "guildUpdate",
  messageDelete: "messageDelete",
  messageDeleteBulk: "messageDeleteBulk",
  messageUpdate: "messageUpdate",
  voiceChannelJoin: "voiceChannelJoin",
  voiceChannelLeave: "voiceChannelLeave",
  voiceChannelSwitch: "voiceChannelSwitch",
  voiceStateUpdate: "voiceStateUpdate"
} as const;

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

  const data = await getLogSettings(serverId);
  if (!data) {
    return NextResponse.json({ settings: null });
  }

  const settings = Object.fromEntries(
    Object.entries(logFieldMap).map(([key, fieldName]) => {
      const value = data[fieldName];
      if (typeof value === "boolean") {
        return [key, value];
      }
      return [key, false];
    })
  );

  return NextResponse.json({ settings });
}

export async function PUT(request: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;
  const auth = await getAuthorizedSession(serverId);
  if (!auth.ok) {
    return auth.response;
  }

  const payload = (await request.json()) as {
    settings?: Record<string, unknown>;
  };

  if (!payload.settings || typeof payload.settings !== "object") {
    return NextResponse.json({ message: "No valid fields to update" }, { status: 400 });
  }

  const updateData: Record<string, boolean> = {};
  for (const [key, fieldName] of Object.entries(logFieldMap)) {
    const value = payload.settings[key];
    if (typeof value === "boolean") {
      updateData[fieldName] = value;
    }
  }

  if (Object.keys(updateData).length === 0) {
    return NextResponse.json({ message: "No valid fields to update" }, { status: 400 });
  }

  await upsertLogSettings(serverId, updateData);

  return NextResponse.json({ ok: true });
}
