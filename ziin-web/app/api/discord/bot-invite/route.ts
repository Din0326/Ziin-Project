import { NextResponse } from "next/server";

const buildInviteUrl = (clientId: string) => {
  const params = new URLSearchParams({
    client_id: clientId,
    permissions: "8",
    scope: "bot applications.commands"
  });
  return `https://discord.com/oauth2/authorize?${params.toString()}`;
};

export async function GET() {
  const clientId =
    process.env.DISCORD_BOT_ID ?? process.env.DISCORD_APPLICATION_ID ?? process.env.DISCORD_CLIENT_ID ?? "";

  if (!clientId) {
    return NextResponse.json({ message: "Bot client id missing" }, { status: 500 });
  }

  return NextResponse.redirect(buildInviteUrl(clientId));
}

