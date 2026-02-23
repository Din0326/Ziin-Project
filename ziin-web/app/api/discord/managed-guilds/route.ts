import { NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";

export async function GET() {
  const session = await getServerSession(authOptions);
  const accessToken = session?.accessToken;

  if (!accessToken) {
    return NextResponse.json({ message: "Unauthorized" }, { status: 401 });
  }

  const result = await fetchDiscordGuilds(accessToken);
  if (!result.ok) {
    return NextResponse.json({ message: "Failed to fetch guilds" }, { status: result.status });
  }

  const managedGuilds = result.guilds
    .filter((guild) => {
      return hasManagePermission(guild.permissions);
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
