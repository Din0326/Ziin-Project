import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";

const buildInviteUrl = (serverId: string) => {
  const baseUrl = process.env.NEXTAUTH_URL ?? "http://3.137.160.188:6001";
  const params = new URLSearchParams({
    client_id: process.env.DISCORD_CLIENT_ID ?? "1474006747969617996",
    permissions: "8",
    response_type: "code",
    redirect_uri: `${baseUrl}/api/auth/callback/discord`,
    integration_type: "0",
    scope: "bot applications.commands applications.commands.permissions.update",
    guild_id: serverId,
    disable_guild_select: "true"
  });
  return `https://discord.com/oauth2/authorize?${params.toString()}`;
};

export async function GET(_: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;

  const session = await getServerSession(authOptions);
  const accessToken = session?.accessToken;
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

  const response = await fetch(`https://discord.com/api/v10/guilds/${serverId}`, {
    headers: {
      Authorization: `Bot ${botToken}`
    },
    cache: "no-store"
  });

  const inGuild = response.ok;
  return NextResponse.json({
    inGuild,
    inviteUrl: buildInviteUrl(serverId)
  });
}

