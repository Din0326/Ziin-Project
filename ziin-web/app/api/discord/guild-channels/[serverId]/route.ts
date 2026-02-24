import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";

type DiscordChannel = {
  id: string;
  name: string;
  type: number;
  parent_id: string | null;
  position: number;
};

const isLoggableTextChannel = (type: number) => type === 0 || type === 5;

const getAuthorizedSession = async (serverId: string) => {
  const session = await getServerSession(authOptions);
  const accessToken = session?.accessToken;
  if (!accessToken) {
    return { ok: false as const, response: NextResponse.json({ message: "Unauthorized" }, { status: 401 }) };
  }

  const result = await fetchDiscordGuilds(accessToken);
  if (!result.ok) {
    return { ok: false as const, response: NextResponse.json({ message: "Forbidden" }, { status: 403 }) };
  }

  const guild = result.guilds.find((item) => item.id === serverId);
  if (!guild || !hasManagePermission(guild.permissions)) {
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

  const botToken = process.env.DISCORD_TOKEN;
  if (!botToken) {
    return NextResponse.json({ message: "Bot token missing" }, { status: 500 });
  }

  const response = await fetch(`https://discord.com/api/v10/guilds/${serverId}/channels`, {
    headers: {
      Authorization: `Bot ${botToken}`
    },
    cache: "no-store"
  });

  if (!response.ok) {
    return NextResponse.json({ message: "Failed to fetch channels" }, { status: response.status });
  }

  const channels = (await response.json()) as DiscordChannel[];
  const textChannels = channels
    .filter((channel) => isLoggableTextChannel(channel.type))
    .sort((a, b) => a.position - b.position)
    .map((channel) => ({
      id: channel.id,
      name: channel.name,
      type: channel.type,
      parentId: channel.parent_id
    }));

  return NextResponse.json({ channels: textChannels });
}

