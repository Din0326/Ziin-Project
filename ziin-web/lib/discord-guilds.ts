type DiscordGuild = {
  id: string;
  name: string;
  icon: string | null;
  owner: boolean;
  permissions: string;
};

type CacheEntry = {
  expiresAt: number;
  guilds: DiscordGuild[];
};

const CACHE_TTL_MS = 15_000;
const guildCache = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<{ ok: true; guilds: DiscordGuild[] } | { ok: false; status: number }>>();

const ADMINISTRATOR_PERMISSION = BigInt(0x8);
const MANAGE_GUILD_PERMISSION = BigInt(0x20);
const ZERO_BIGINT = BigInt(0);

export const hasManagePermission = (permissions: string) => {
  const bits = BigInt(permissions);
  return (
    (bits & ADMINISTRATOR_PERMISSION) !== ZERO_BIGINT || (bits & MANAGE_GUILD_PERMISSION) !== ZERO_BIGINT
  );
};

export const fetchDiscordGuilds = async (
  accessToken: string
): Promise<{ ok: true; guilds: DiscordGuild[] } | { ok: false; status: number }> => {
  const now = Date.now();
  const cached = guildCache.get(accessToken);
  if (cached && cached.expiresAt > now) {
    return { ok: true, guilds: cached.guilds };
  }

  const pending = inflight.get(accessToken);
  if (pending) {
    return pending;
  }

  const request = (async () => {
    const response = await fetch("https://discord.com/api/users/@me/guilds", {
      headers: {
        Authorization: `Bearer ${accessToken}`
      },
      cache: "no-store"
    });

    if (!response.ok) {
      return { ok: false as const, status: response.status };
    }

    const guilds = (await response.json()) as DiscordGuild[];
    guildCache.set(accessToken, { guilds, expiresAt: Date.now() + CACHE_TTL_MS });
    return { ok: true as const, guilds };
  })();

  inflight.set(accessToken, request);
  try {
    return await request;
  } finally {
    inflight.delete(accessToken);
  }
};

