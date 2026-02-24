import { NextRequest, NextResponse } from "next/server";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getLogSettings, getServerSettings, getTwitchSettings, getYouTubeSettings } from "@/lib/local-db";
import { getDiscordAccessToken } from "@/lib/server-auth";

type DiscordChannel = {
  id: string;
  name: string;
  type: number;
  parent_id: string | null;
  position: number;
};

type DiscordRole = {
  id: string;
  name: string;
  position: number;
  managed?: boolean;
};

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

const normalizeTimezoneLabel = (value: string): string | null => {
  const raw = value.trim();
  if (!raw) {
    return null;
  }

  const formatOffsetByZone = (zone: string): string => {
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: zone,
      timeZoneName: "shortOffset"
    }).formatToParts(new Date());
    const offset = parts.find((part) => part.type === "timeZoneName")?.value ?? "GMT+0";
    return offset.replace("GMT", "UTC");
  };

  if (/^-?\d+$/.test(raw)) {
    const hours = Number.parseInt(raw, 10);
    if (Number.isNaN(hours) || hours < -12 || hours > 14) {
      return null;
    }
    if (hours === 8) {
      return "UTC+8 Asia/Taipei";
    }
    return `UTC${hours >= 0 ? "+" : ""}${hours}`;
  }

  if (/^(UTC|GMT)\s*[+-]?\d{1,2}(?::\d{2})?(?:\s+\S+)?$/i.test(raw)) {
    return raw.replace(/^GMT/i, "UTC");
  }

  try {
    const offset = formatOffsetByZone(raw);
    return `${offset} ${raw}`;
  } catch {
    return null;
  }
};

const isLoggableTextChannel = (type: number) => type === 0 || type === 5;

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

  const [serverSettings, logSettings, twitchSettings, youtubeSettings, channelsResponse, rolesResponse] =
    await Promise.all([
      getServerSettings(serverId),
      getLogSettings(serverId),
      getTwitchSettings(serverId),
      getYouTubeSettings(serverId),
      fetch(`https://discord.com/api/v10/guilds/${serverId}/channels`, {
        headers: {
          Authorization: `Bot ${botToken}`
        },
        cache: "no-store"
      }),
      fetch(`https://discord.com/api/v10/guilds/${serverId}/roles`, {
        headers: {
          Authorization: `Bot ${botToken}`
        },
        cache: "no-store"
      })
    ]);

  if (!channelsResponse.ok) {
    return NextResponse.json({ message: "Failed to fetch channels" }, { status: channelsResponse.status });
  }
  if (!rolesResponse.ok) {
    return NextResponse.json({ message: "Failed to fetch roles" }, { status: rolesResponse.status });
  }

  const channels = ((await channelsResponse.json()) as DiscordChannel[])
    .filter((channel) => isLoggableTextChannel(channel.type))
    .sort((a, b) => a.position - b.position)
    .map((channel) => ({
      id: channel.id,
      name: channel.name
    }));

  const roles = ((await rolesResponse.json()) as DiscordRole[])
    .filter((role) => role.name !== "@everyone")
    .sort((a, b) => b.position - a.position)
    .map((role) => ({
      id: role.id,
      name: role.name,
      managed: role.managed === true
    }));

  const mappedLogSettings = Object.fromEntries(
    Object.entries(logFieldMap).map(([key, fieldName]) => [key, logSettings[fieldName] === true])
  );

  return NextResponse.json({
    bootstrap: {
      serverSettings: {
        prefix: serverSettings.Prefix ?? "",
        timezone: typeof serverSettings.TimeZone === "string" ? normalizeTimezoneLabel(serverSettings.TimeZone) : null,
        language: serverSettings.Language ?? null,
        guildLogId: serverSettings.GuildLogId ?? null,
        memberLogId: serverSettings.MemberLogId ?? null,
        messageLogId: serverSettings.MessageLogId ?? null,
        voiceLogId: serverSettings.VoiceLogId ?? null
      },
      logSettings: mappedLogSettings,
      twitchSettings: {
        twitchNotificationChannel: twitchSettings.TwitchNotificationChannel,
        twitchNotificationText: twitchSettings.TwitchNotificationText,
        allStreamers: twitchSettings.AllStreamers
      },
      youtubeSettings: {
        youtubeNotificationChannel: youtubeSettings.YouTubeNotificationChannel,
        youtubeNotificationText: youtubeSettings.YouTubeNotificationText,
        youtubers: youtubeSettings.YouTubers
      },
      channels,
      roles
    }
  });
}
