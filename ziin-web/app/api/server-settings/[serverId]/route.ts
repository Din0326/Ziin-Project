import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { fetchDiscordGuilds, hasManagePermission } from "@/lib/discord-guilds";
import { getServerSettings, upsertServerSettings } from "@/lib/local-db";

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
    const value = parts.find((part) => part.type === "timeZoneName")?.value ?? "GMT+0";
    return value.replace("GMT", "UTC");
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

  const data = await getServerSettings(serverId);
  if (!data) {
    return NextResponse.json({ settings: null });
  }

  return NextResponse.json({
    settings: {
      prefix: data.Prefix ?? "",
      timezone: typeof data.TimeZone === "string" ? normalizeTimezoneLabel(data.TimeZone) : null,
      language: data.Language ?? null,
      guildLogId: data.GuildLogId ?? null,
      memberLogId: data.MemberLogId ?? null,
      messageLogId: data.MessageLogId ?? null,
      voiceLogId: data.VoiceLogId ?? null
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
    guildLogId?: unknown;
    memberLogId?: unknown;
    messageLogId?: unknown;
    voiceLogId?: unknown;
  };

  const updateData: {
    Prefix?: string;
    TimeZone?: string;
    Language?: string;
    GuildLogId?: string | null;
    MemberLogId?: string | null;
    MessageLogId?: string | null;
    VoiceLogId?: string | null;
  } = {};

  if (typeof payload.prefix === "string") {
    updateData.Prefix = payload.prefix.trim().slice(0, 32);
  }
  if (typeof payload.timezone === "string") {
    const normalizedTimezone = normalizeTimezoneLabel(payload.timezone);
    if (!normalizedTimezone) {
      return NextResponse.json({ message: "Invalid timezone" }, { status: 400 });
    }
    updateData.TimeZone = normalizedTimezone;
  }
  if (typeof payload.language === "string") {
    updateData.Language = payload.language;
  }

  const normalizeChannelId = (value: unknown) => {
    if (value === null) {
      return null;
    }
    if (typeof value !== "string") {
      return undefined;
    }
    const trimmed = value.trim();
    if (!trimmed) {
      return null;
    }
    return /^\d+$/.test(trimmed) ? trimmed : undefined;
  };

  const guildLogId = normalizeChannelId(payload.guildLogId);
  const memberLogId = normalizeChannelId(payload.memberLogId);
  const messageLogId = normalizeChannelId(payload.messageLogId);
  const voiceLogId = normalizeChannelId(payload.voiceLogId);
  if (guildLogId !== undefined) {
    updateData.GuildLogId = guildLogId;
  }
  if (memberLogId !== undefined) {
    updateData.MemberLogId = memberLogId;
  }
  if (messageLogId !== undefined) {
    updateData.MessageLogId = messageLogId;
  }
  if (voiceLogId !== undefined) {
    updateData.VoiceLogId = voiceLogId;
  }

  if (Object.keys(updateData).length === 0) {
    return NextResponse.json({ message: "No valid fields to update" }, { status: 400 });
  }

  await upsertServerSettings(serverId, updateData);

  return NextResponse.json({ ok: true });
}
