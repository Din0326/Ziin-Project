import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";

type DiscordGuild = {
  id: string;
  name: string;
  icon: string | null;
  owner: boolean;
  permissions: string;
};

const ADMINISTRATOR_PERMISSION = BigInt(0x8);
const MANAGE_GUILD_PERMISSION = BigInt(0x20);
const ZERO_BIGINT = BigInt(0);

export async function GET() {
  const session = await getServerSession(authOptions);
  const accessToken = session?.accessToken;

  if (!accessToken) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const response = await fetch("https://discord.com/api/users/@me/guilds", {
    headers: {
      Authorization: `Bearer ${accessToken}`
    },
    cache: "no-store"
  });

  if (!response.ok) {
    return NextResponse.json({ message: "Failed to fetch guilds" }, { status: response.status });
  }

  const guilds = (await response.json()) as DiscordGuild[];

  const managedGuilds = guilds
    .filter((guild) => {
      const permissions = BigInt(guild.permissions);
      const hasAdministrator = (permissions & ADMINISTRATOR_PERMISSION) !== ZERO_BIGINT;
      const hasManageGuild = (permissions & MANAGE_GUILD_PERMISSION) !== ZERO_BIGINT;
      return hasAdministrator || hasManageGuild;
    })
    .map((guild) => ({
      id: guild.id,
      name: guild.name,
      owner: guild.owner,
      iconUrl: guild.icon
        ? `https://cdn.discordapp.com/icons/${guild.id}/${guild.icon}.webp?size=256`
        : null
    }));

  return NextResponse.json({ guilds: managedGuilds });
}
