import { NextRequest, NextResponse } from "next/server";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getDiscordAccessToken } from "@/lib/server-auth";

type DiscordRole = {
  id: string;
  name: string;
  position: number;
  managed?: boolean;
};

const getAuthorizedSession = async (request: NextRequest, serverId: string) => {
  const accessToken = await getDiscordAccessToken(request);
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

export async function GET(request: NextRequest, context: { params: Promise<{ serverId: string }> }) {
  const { serverId } = await context.params;
  const auth = await getAuthorizedSession(request, serverId);
  if (!auth.ok) {
    return auth.response;
  }

  const botToken = process.env.DISCORD_TOKEN;
  if (!botToken) {
    return NextResponse.json({ message: "Bot token missing" }, { status: 500 });
  }

  const response = await fetch(`https://discord.com/api/v10/guilds/${serverId}/roles`, {
    headers: {
      Authorization: `Bot ${botToken}`
    },
    cache: "no-store"
  });

  if (!response.ok) {
    return NextResponse.json({ message: "Failed to fetch roles" }, { status: response.status });
  }

  const roles = (await response.json()) as DiscordRole[];
  const filteredRoles = roles
    .filter((role) => role.name !== "@everyone")
    .sort((a, b) => b.position - a.position)
    .map((role) => ({
      id: role.id,
      name: role.name,
      managed: role.managed === true
    }));

  return NextResponse.json({ roles: filteredRoles });
}
