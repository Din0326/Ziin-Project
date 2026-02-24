import { NextRequest, NextResponse } from "next/server";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getDiscordAccessToken } from "@/lib/server-auth";

let cachedBotClientId: string | null = null;

const resolveBotClientId = async (botToken: string): Promise<string | null> => {
  const fromEnv =
    process.env.DISCORD_BOT_ID ?? process.env.DISCORD_APPLICATION_ID ?? process.env.DISCORD_CLIENT_ID ?? null;
  if (fromEnv) {
    return fromEnv;
  }
  if (cachedBotClientId) {
    return cachedBotClientId;
  }

  try {
    const response = await fetch("https://discord.com/api/v10/users/@me", {
      headers: { Authorization: `Bot ${botToken}` },
      cache: "no-store"
    });
    if (!response.ok) {
      return null;
    }

    const data = (await response.json()) as { id?: unknown };
    if (typeof data.id === "string" && data.id) {
      cachedBotClientId = data.id;
      return data.id;
    }
  } catch {
    return null;
  }

  return null;
};

const buildInviteUrl = (serverId: string, clientId: string) => {
  const params = new URLSearchParams({
    client_id: clientId,
    permissions: "8",
    scope: "bot applications.commands",
    guild_id: serverId,
    disable_guild_select: "true"
  });

  return `https://discord.com/oauth2/authorize?${params.toString()}`;
};

export async function GET(request: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;

  const accessToken = await getDiscordAccessToken(request);
  if (!accessToken) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const guildResult = await fetchDiscordGuilds(accessToken);
  if (!guildResult.ok) {
    return NextResponse.json({ message: "Forbidden" }, { status: 403 });
  }

  const guild = guildResult.guilds.find((item) => item.id === serverId);
  if (!guild || !hasManagePermission(guild.permissions)) {
    return NextResponse.json({ message: "Forbidden" }, { status: 403 });
  }

  const botToken = process.env.DISCORD_TOKEN;
  if (!botToken) {
    return NextResponse.json({ message: "Bot token missing" }, { status: 500 });
  }
  const botClientId = await resolveBotClientId(botToken);
  if (!botClientId) {
    return NextResponse.json({ message: "Bot client id missing" }, { status: 500 });
  }

  const response = await fetch(`https://discord.com/api/v10/guilds/${serverId}`, {
    headers: {
      Authorization: `Bot ${botToken}`
    },
    cache: "no-store"
  });

  const inGuild = response.ok;
  return NextResponse.json({
    inGuild,
    inviteUrl: buildInviteUrl(serverId, botClientId)
  });
}
