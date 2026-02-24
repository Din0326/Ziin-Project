import { mkdirSync } from "node:fs";
import { readFileSync } from "node:fs";
import path from "node:path";
import Database from "better-sqlite3";

type GuildSettingsRecord = {
  Prefix?: string;
  TimeZone?: string | null;
  Language?: string;
  GuildLogId?: string | null;
  MemberLogId?: string | null;
  MessageLogId?: string | null;
  VoiceLogId?: string | null;
};

type LogSettingsRecord = Record<string, boolean>;
type TwitchSettingsRecord = {
  TwitchNotificationChannel: string | null;
  TwitchNotificationText: string;
  AllStreamers: string[];
  OnlineStreamers: string[];
  OfflineStreamers: string[];
};

type YouTubeSubscriptionRecord = {
  id: string;
  name: string;
  videoId: string;
  streamId: string;
  shortId: string;
  videoHistory: string[];
  streamHistory: string[];
  shortHistory: string[];
};

type YouTubeSettingsRecord = {
  YouTubeNotificationChannel: string | null;
  YouTubeNotificationText: string;
  YouTubers: YouTubeSubscriptionRecord[];
};

type TwitterSubscriptionRecord = {
  id: string;
  name: string;
  tweetId: string;
  tweetHistory: string[];
};

type TwitterSettingsRecord = {
  TwitterNotificationChannel: string | null;
  TwitterNotificationText: string;
  XUsers: TwitterSubscriptionRecord[];
};

let cachedDb: Database.Database | null = null;

const getDbPath = () =>
  process.env.LOCAL_DB_PATH ? path.resolve(process.env.LOCAL_DB_PATH) : path.join(process.cwd(), "data", "local.db");

const getDb = () => {
  if (cachedDb) {
    return cachedDb;
  }

  const dbPath = getDbPath();
  mkdirSync(path.dirname(dbPath), { recursive: true });

  const db = new Database(dbPath);
  const schemaPath = path.join(process.cwd(), "data", "schema.sql");
  const schemaSql = readFileSync(schemaPath, "utf8");
  db.exec(schemaSql);
  ensureNotificationTables(db);

  cachedDb = db;
  return db;
};

const DEFAULT_GUILD_SETTINGS = {
  Prefix: "z!",
  TimeZone: null,
  Language: "English"
} as const;

const DEFAULT_LOG_SETTINGS: Array<{ fieldName: string; enabled: boolean }> = [
  { fieldName: "guildUpdate", enabled: false },
  { fieldName: "messageUpdate", enabled: true },
  { fieldName: "messageDelete", enabled: true },
  { fieldName: "RoleCreate", enabled: false },
  { fieldName: "RoleDelete", enabled: false },
  { fieldName: "RoleUpdate", enabled: false },
  { fieldName: "MemberUpdate", enabled: true },
  { fieldName: "MemberAdd", enabled: false },
  { fieldName: "MemberKick", enabled: false },
  { fieldName: "MemberUnban", enabled: false },
  { fieldName: "MemberRemove", enabled: false },
  { fieldName: "MemberNickUpdate", enabled: true },
  { fieldName: "channelCreate", enabled: false },
  { fieldName: "channelDelete", enabled: false },
  { fieldName: "channelUpdate", enabled: false },
  { fieldName: "voiceChannelJoin", enabled: false },
  { fieldName: "voiceChannelLeave", enabled: false },
  { fieldName: "voiceStateUpdate", enabled: false },
  { fieldName: "voiceChannelSwitch", enabled: false },
  { fieldName: "messageDeleteBulk", enabled: false }
];

const DEFAULT_TWITCH_NOTIFICATION_TEXT = "**{streamer}** is live now!!\n**{url}**";
const DEFAULT_YOUTUBE_NOTIFICATION_TEXT = "**{ytber}** upload a video!!\n**{url}**";
const DEFAULT_TWITTER_NOTIFICATION_TEXT = "**{xuser}** posted a new tweet!\n**{url}**";

const nowTs = () => Math.floor(Date.now() / 1000);

const parseJsonArray = (value: string | null | undefined): string[] => {
  if (!value) {
    return [];
  }
  try {
    const parsed = JSON.parse(value) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((item): item is string => typeof item === "string");
  } catch {
    return [];
  }
};

const normalizeStringList = (values: unknown): string[] => {
  if (!Array.isArray(values)) {
    return [];
  }
  const result: string[] = [];
  const seen = new Set<string>();
  for (const value of values) {
    if (typeof value !== "string") {
      continue;
    }
    const trimmed = value.trim();
    if (!trimmed || seen.has(trimmed)) {
      continue;
    }
    seen.add(trimmed);
    result.push(trimmed);
  }
  return result;
};

const normalizeChannelId = (value: unknown): string | null => {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(Math.trunc(value));
  }
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
};

const ensureNotificationTables = (db: Database.Database) => {
  db.exec(`
    CREATE TABLE IF NOT EXISTS twitch_data (
      server_id TEXT PRIMARY KEY,
      twitch_notification_channel TEXT,
      all_streamers TEXT NOT NULL DEFAULT '[]',
      online_streamers TEXT NOT NULL DEFAULT '[]',
      offline_streamers TEXT NOT NULL DEFAULT '[]',
      twitch_notification_text TEXT NOT NULL DEFAULT '**{streamer}** is live now!!\\n**{url}**',
      updated_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS youtube_data (
      server_id TEXT PRIMARY KEY,
      youtube_notification_text TEXT NOT NULL DEFAULT '**{ytber}** upload a video!!\\n**{url}**',
      youtube_notification_channel TEXT,
      updated_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS youtube_subscriptions (
      server_id TEXT NOT NULL,
      youtuber_id TEXT NOT NULL,
      channel_name TEXT,
      video_id TEXT,
      stream_id TEXT,
      short_id TEXT,
      video_history TEXT NOT NULL DEFAULT '[]',
      stream_history TEXT NOT NULL DEFAULT '[]',
      short_history TEXT NOT NULL DEFAULT '[]',
      updated_at INTEGER,
      PRIMARY KEY (server_id, youtuber_id)
    );

    CREATE TABLE IF NOT EXISTS twitter_data (
      server_id TEXT PRIMARY KEY,
      twitter_notification_text TEXT NOT NULL DEFAULT '**{xuser}** posted a new tweet!\\n**{url}**',
      twitter_notification_channel TEXT,
      updated_at INTEGER
    );

    CREATE TABLE IF NOT EXISTS twitter_subscriptions (
      server_id TEXT NOT NULL,
      account_id TEXT NOT NULL,
      display_name TEXT,
      tweet_id TEXT,
      tweet_history TEXT NOT NULL DEFAULT '[]',
      updated_at INTEGER,
      PRIMARY KEY (server_id, account_id)
    );

    CREATE INDEX IF NOT EXISTS idx_twitch_data_server_id ON twitch_data(server_id);
    CREATE INDEX IF NOT EXISTS idx_youtube_data_server_id ON youtube_data(server_id);
    CREATE INDEX IF NOT EXISTS idx_youtube_subscriptions_server_id ON youtube_subscriptions(server_id);
    CREATE INDEX IF NOT EXISTS idx_twitter_data_server_id ON twitter_data(server_id);
    CREATE INDEX IF NOT EXISTS idx_twitter_subscriptions_server_id ON twitter_subscriptions(server_id);
  `);

  const columns = db
    .prepare("PRAGMA table_info(youtube_subscriptions)")
    .all() as Array<{ name: string }>;
  const names = new Set(columns.map((column) => column.name));
  if (!names.has("video_history")) {
    db.exec("ALTER TABLE youtube_subscriptions ADD COLUMN video_history TEXT NOT NULL DEFAULT '[]'");
  }
  if (!names.has("stream_history")) {
    db.exec("ALTER TABLE youtube_subscriptions ADD COLUMN stream_history TEXT NOT NULL DEFAULT '[]'");
  }
  if (!names.has("short_history")) {
    db.exec("ALTER TABLE youtube_subscriptions ADD COLUMN short_history TEXT NOT NULL DEFAULT '[]'");
  }

  const twitterColumns = db
    .prepare("PRAGMA table_info(twitter_subscriptions)")
    .all() as Array<{ name: string }>;
  const twitterNames = new Set(twitterColumns.map((column) => column.name));
  if (!twitterNames.has("tweet_history")) {
    db.exec("ALTER TABLE twitter_subscriptions ADD COLUMN tweet_history TEXT NOT NULL DEFAULT '[]'");
  }
};

const ensureGuildSettingsDefaults = (db: Database.Database, serverId: string) => {
  const ts = nowTs();
  db.prepare(
    `
      INSERT INTO guild_settings (server_id, prefix, language, timezone, ignore_channels_json, updated_at)
      VALUES (?, ?, ?, ?, '[]', ?)
      ON CONFLICT(server_id) DO NOTHING
    `
  ).run(serverId, DEFAULT_GUILD_SETTINGS.Prefix, DEFAULT_GUILD_SETTINGS.Language, DEFAULT_GUILD_SETTINGS.TimeZone, ts);

  db.prepare(
    `
      UPDATE guild_settings
      SET
        prefix = COALESCE(prefix, ?),
        language = COALESCE(language, ?),
        timezone = COALESCE(timezone, ?),
        ignore_channels_json = COALESCE(ignore_channels_json, '[]'),
        updated_at = COALESCE(updated_at, ?)
      WHERE server_id = ?
    `
  ).run(
    DEFAULT_GUILD_SETTINGS.Prefix,
    DEFAULT_GUILD_SETTINGS.Language,
    DEFAULT_GUILD_SETTINGS.TimeZone,
    ts,
    serverId
  );
};

const ensureLogSettingsDefaults = (db: Database.Database, serverId: string) => {
  const ts = nowTs();
  const statement = db.prepare(
    `
      INSERT OR IGNORE INTO log_settings (server_id, field_name, enabled, updated_at)
      VALUES (?, ?, ?, ?)
    `
  );
  const transaction = db.transaction(() => {
    for (const item of DEFAULT_LOG_SETTINGS) {
      statement.run(serverId, item.fieldName, item.enabled ? 1 : 0, ts);
    }
  });
  transaction();
};

export const getServerSettings = async (serverId: string): Promise<GuildSettingsRecord> => {
  const db = getDb();
  ensureGuildSettingsDefaults(db, serverId);
  const row = db
    .prepare(
      "SELECT prefix, timezone, language, guild_log_id, member_log_id, message_log_id, voice_log_id FROM guild_settings WHERE server_id = ?"
    )
    .get(serverId) as
    | {
        prefix: string | null;
        timezone: string | null;
        language: string | null;
        guild_log_id: string | null;
        member_log_id: string | null;
        message_log_id: string | null;
        voice_log_id: string | null;
      }
    | undefined;

  return {
    Prefix: row?.prefix ?? DEFAULT_GUILD_SETTINGS.Prefix,
    TimeZone: row?.timezone ?? DEFAULT_GUILD_SETTINGS.TimeZone,
    Language: row?.language ?? DEFAULT_GUILD_SETTINGS.Language,
    GuildLogId: row?.guild_log_id ?? null,
    MemberLogId: row?.member_log_id ?? null,
    MessageLogId: row?.message_log_id ?? null,
    VoiceLogId: row?.voice_log_id ?? null
  };
};

export const upsertServerSettings = async (serverId: string, partial: GuildSettingsRecord) => {
  const db = getDb();

  const updates: string[] = [];
  const values: unknown[] = [];

  if (partial.Prefix !== undefined) {
    updates.push("prefix = ?");
    values.push(partial.Prefix);
  }
  if (partial.TimeZone !== undefined) {
    updates.push("timezone = ?");
    values.push(partial.TimeZone);
  }
  if (partial.Language !== undefined) {
    updates.push("language = ?");
    values.push(partial.Language);
  }
  if (partial.GuildLogId !== undefined) {
    updates.push("guild_log_id = ?");
    values.push(partial.GuildLogId);
  }
  if (partial.MemberLogId !== undefined) {
    updates.push("member_log_id = ?");
    values.push(partial.MemberLogId);
  }
  if (partial.MessageLogId !== undefined) {
    updates.push("message_log_id = ?");
    values.push(partial.MessageLogId);
  }
  if (partial.VoiceLogId !== undefined) {
    updates.push("voice_log_id = ?");
    values.push(partial.VoiceLogId);
  }

  if (updates.length === 0) {
    return;
  }

  db.prepare(
    `
      INSERT INTO guild_settings (server_id)
      VALUES (?)
      ON CONFLICT(server_id) DO NOTHING
    `
  ).run(serverId);

  db.prepare(`UPDATE guild_settings SET ${updates.join(", ")} WHERE server_id = ?`).run(...values, serverId);
};

export const getLogSettings = async (serverId: string): Promise<LogSettingsRecord> => {
  const db = getDb();
  ensureLogSettingsDefaults(db, serverId);
  const rows = db
    .prepare("SELECT field_name, enabled FROM log_settings WHERE server_id = ?")
    .all(serverId) as Array<{ field_name: string; enabled: number }>;

  return Object.fromEntries(rows.map((row) => [row.field_name, row.enabled === 1]));
};

export const upsertLogSettings = async (serverId: string, partial: LogSettingsRecord) => {
  const db = getDb();
  const entries = Object.entries(partial);
  if (entries.length === 0) {
    return;
  }

  const statement = db.prepare(`
    INSERT INTO log_settings (server_id, field_name, enabled)
    VALUES (?, ?, ?)
    ON CONFLICT(server_id, field_name)
    DO UPDATE SET enabled = excluded.enabled
  `);

  const transaction = db.transaction((rows: Array<[string, boolean]>) => {
    for (const [fieldName, value] of rows) {
      statement.run(serverId, fieldName, value ? 1 : 0);
    }
  });

  transaction(entries);
};

const ensureTwitchSettingsDefaults = (db: Database.Database, serverId: string) => {
  const ts = nowTs();
  db.prepare(
    `
      INSERT INTO twitch_data (
        server_id,
        twitch_notification_channel,
        all_streamers,
        online_streamers,
        offline_streamers,
        twitch_notification_text,
        updated_at
      )
      VALUES (?, NULL, '[]', '[]', '[]', ?, ?)
      ON CONFLICT(server_id) DO NOTHING
    `
  ).run(serverId, DEFAULT_TWITCH_NOTIFICATION_TEXT, ts);
};

const ensureYouTubeSettingsDefaults = (db: Database.Database, serverId: string) => {
  const ts = nowTs();
  db.prepare(
    `
      INSERT INTO youtube_data (
        server_id,
        youtube_notification_text,
        youtube_notification_channel,
        updated_at
      )
      VALUES (?, ?, NULL, ?)
      ON CONFLICT(server_id) DO NOTHING
    `
  ).run(serverId, DEFAULT_YOUTUBE_NOTIFICATION_TEXT, ts);
};

const ensureTwitterSettingsDefaults = (db: Database.Database, serverId: string) => {
  const ts = nowTs();
  db.prepare(
    `
      INSERT INTO twitter_data (
        server_id,
        twitter_notification_text,
        twitter_notification_channel,
        updated_at
      )
      VALUES (?, ?, NULL, ?)
      ON CONFLICT(server_id) DO NOTHING
    `
  ).run(serverId, DEFAULT_TWITTER_NOTIFICATION_TEXT, ts);
};

const normalizeYouTubeSubscriptions = (values: unknown): YouTubeSubscriptionRecord[] => {
  if (!Array.isArray(values)) {
    return [];
  }

  const result: YouTubeSubscriptionRecord[] = [];
  const seen = new Set<string>();

  for (const value of values) {
    if (typeof value !== "object" || value === null) {
      continue;
    }
    const record = value as Record<string, unknown>;
    const id = typeof record.id === "string" ? record.id.trim() : "";
    if (!id || seen.has(id)) {
      continue;
    }
    seen.add(id);

    const name = typeof record.name === "string" && record.name.trim() ? record.name.trim() : id;
    const videoId = typeof record.videoId === "string" ? record.videoId.trim() : "";
    const streamId = typeof record.streamId === "string" ? record.streamId.trim() : "";
    const shortId = typeof record.shortId === "string" ? record.shortId.trim() : "";
    const videoHistory = normalizeStringList(record.videoHistory);
    const streamHistory = normalizeStringList(record.streamHistory);
    const shortHistory = normalizeStringList(record.shortHistory);

    if (videoId && !videoHistory.includes(videoId)) {
      videoHistory.push(videoId);
    }
    if (streamId && !streamHistory.includes(streamId)) {
      streamHistory.push(streamId);
    }
    if (shortId && !shortHistory.includes(shortId)) {
      shortHistory.push(shortId);
    }

    result.push({
      id,
      name,
      videoId,
      streamId,
      shortId,
      videoHistory,
      streamHistory,
      shortHistory
    });
  }

  return result;
};

export const getTwitchSettings = async (serverId: string): Promise<TwitchSettingsRecord> => {
  const db = getDb();
  ensureTwitchSettingsDefaults(db, serverId);

  const row = db
    .prepare(
      `
        SELECT
          twitch_notification_channel,
          twitch_notification_text,
          all_streamers,
          online_streamers,
          offline_streamers
        FROM twitch_data
        WHERE server_id = ?
      `
    )
    .get(serverId) as
    | {
        twitch_notification_channel: string | null;
        twitch_notification_text: string | null;
        all_streamers: string | null;
        online_streamers: string | null;
        offline_streamers: string | null;
      }
    | undefined;

  return {
    TwitchNotificationChannel: row?.twitch_notification_channel ?? null,
    TwitchNotificationText: row?.twitch_notification_text ?? DEFAULT_TWITCH_NOTIFICATION_TEXT,
    AllStreamers: parseJsonArray(row?.all_streamers),
    OnlineStreamers: parseJsonArray(row?.online_streamers),
    OfflineStreamers: parseJsonArray(row?.offline_streamers)
  };
};

export const upsertTwitchSettings = async (
  serverId: string,
  partial: Partial<TwitchSettingsRecord>
) => {
  const db = getDb();
  ensureTwitchSettingsDefaults(db, serverId);

  const updates: string[] = [];
  const values: unknown[] = [];

  if (partial.TwitchNotificationChannel !== undefined) {
    updates.push("twitch_notification_channel = ?");
    values.push(normalizeChannelId(partial.TwitchNotificationChannel));
  }
  if (partial.TwitchNotificationText !== undefined) {
    updates.push("twitch_notification_text = ?");
    values.push(partial.TwitchNotificationText.trim() || DEFAULT_TWITCH_NOTIFICATION_TEXT);
  }
  if (partial.AllStreamers !== undefined) {
    updates.push("all_streamers = ?");
    values.push(JSON.stringify(normalizeStringList(partial.AllStreamers)));
  }
  if (partial.OnlineStreamers !== undefined) {
    updates.push("online_streamers = ?");
    values.push(JSON.stringify(normalizeStringList(partial.OnlineStreamers)));
  }
  if (partial.OfflineStreamers !== undefined) {
    updates.push("offline_streamers = ?");
    values.push(JSON.stringify(normalizeStringList(partial.OfflineStreamers)));
  }

  if (updates.length === 0) {
    return;
  }

  updates.push("updated_at = ?");
  values.push(nowTs());
  db.prepare(`UPDATE twitch_data SET ${updates.join(", ")} WHERE server_id = ?`).run(...values, serverId);
};

export const getYouTubeSettings = async (serverId: string): Promise<YouTubeSettingsRecord> => {
  const db = getDb();
  ensureYouTubeSettingsDefaults(db, serverId);

  const row = db
    .prepare(
      `
        SELECT
          youtube_notification_text,
          youtube_notification_channel
        FROM youtube_data
        WHERE server_id = ?
      `
    )
    .get(serverId) as
    | {
        youtube_notification_text: string | null;
        youtube_notification_channel: string | null;
      }
    | undefined;

  const youtubers = db
    .prepare(
      `
        SELECT
          youtuber_id,
          channel_name,
          video_id,
          stream_id,
          short_id,
          video_history,
          stream_history,
          short_history
        FROM youtube_subscriptions
        WHERE server_id = ?
      `
    )
    .all(serverId) as Array<{
    youtuber_id: string;
    channel_name: string | null;
    video_id: string | null;
    stream_id: string | null;
    short_id: string | null;
    video_history: string | null;
    stream_history: string | null;
    short_history: string | null;
  }>;

  return {
    YouTubeNotificationChannel: row?.youtube_notification_channel ?? null,
    YouTubeNotificationText: row?.youtube_notification_text ?? DEFAULT_YOUTUBE_NOTIFICATION_TEXT,
    YouTubers: youtubers.map((item) => {
      const id = item.youtuber_id;
      const videoHistory = parseJsonArray(item.video_history);
      const streamHistory = parseJsonArray(item.stream_history);
      const shortHistory = parseJsonArray(item.short_history);
      const videoId = item.video_id ?? "";
      const streamId = item.stream_id ?? "";
      const shortId = item.short_id ?? "";
      if (videoId && !videoHistory.includes(videoId)) {
        videoHistory.push(videoId);
      }
      if (streamId && !streamHistory.includes(streamId)) {
        streamHistory.push(streamId);
      }
      if (shortId && !shortHistory.includes(shortId)) {
        shortHistory.push(shortId);
      }
      return {
        id,
        name: item.channel_name?.trim() || id,
        videoId,
        streamId,
        shortId,
        videoHistory,
        streamHistory,
        shortHistory
      };
    })
  };
};

export const upsertYouTubeSettings = async (
  serverId: string,
  partial: Partial<YouTubeSettingsRecord>
) => {
  const db = getDb();
  ensureYouTubeSettingsDefaults(db, serverId);
  const ts = nowTs();

  const updates: string[] = [];
  const values: unknown[] = [];

  if (partial.YouTubeNotificationText !== undefined) {
    updates.push("youtube_notification_text = ?");
    values.push(partial.YouTubeNotificationText.trim() || DEFAULT_YOUTUBE_NOTIFICATION_TEXT);
  }
  if (partial.YouTubeNotificationChannel !== undefined) {
    updates.push("youtube_notification_channel = ?");
    values.push(normalizeChannelId(partial.YouTubeNotificationChannel));
  }

  if (updates.length > 0) {
    updates.push("updated_at = ?");
    values.push(ts);
    db.prepare(`UPDATE youtube_data SET ${updates.join(", ")} WHERE server_id = ?`).run(...values, serverId);
  }

  if (partial.YouTubers !== undefined) {
    const normalized = normalizeYouTubeSubscriptions(partial.YouTubers);
    const insertStatement = db.prepare(
      `
        INSERT INTO youtube_subscriptions (
          server_id,
          youtuber_id,
          channel_name,
          video_id,
          stream_id,
          short_id,
          video_history,
          stream_history,
          short_history,
          updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `
    );

    const transaction = db.transaction(() => {
      db.prepare("DELETE FROM youtube_subscriptions WHERE server_id = ?").run(serverId);
      for (const item of normalized) {
        insertStatement.run(
          serverId,
          item.id,
          item.name,
          item.videoId,
          item.streamId,
          item.shortId,
          JSON.stringify(item.videoHistory),
          JSON.stringify(item.streamHistory),
          JSON.stringify(item.shortHistory),
          ts
        );
      }
    });
    transaction();
  }
};

const normalizeTwitterSubscriptions = (values: unknown): TwitterSubscriptionRecord[] => {
  if (!Array.isArray(values)) {
    return [];
  }

  const result: TwitterSubscriptionRecord[] = [];
  const seen = new Set<string>();

  for (const value of values) {
    if (typeof value !== "object" || value === null) {
      continue;
    }
    const record = value as Record<string, unknown>;
    const id = typeof record.id === "string" ? record.id.trim().toLowerCase().replace(/^@+/, "") : "";
    if (!id || seen.has(id)) {
      continue;
    }
    seen.add(id);

    const name = typeof record.name === "string" && record.name.trim() ? record.name.trim() : id;
    const tweetId = typeof record.tweetId === "string" ? record.tweetId.trim() : "";
    const tweetHistory = normalizeStringList(record.tweetHistory);
    if (tweetId && !tweetHistory.includes(tweetId)) {
      tweetHistory.push(tweetId);
    }
    result.push({ id, name, tweetId, tweetHistory });
  }

  return result;
};

export const getTwitterSettings = async (serverId: string): Promise<TwitterSettingsRecord> => {
  const db = getDb();
  ensureTwitterSettingsDefaults(db, serverId);

  const row = db
    .prepare(
      `
        SELECT
          twitter_notification_text,
          twitter_notification_channel
        FROM twitter_data
        WHERE server_id = ?
      `
    )
    .get(serverId) as
    | {
        twitter_notification_text: string | null;
        twitter_notification_channel: string | null;
      }
    | undefined;

  const xusers = db
    .prepare(
      `
        SELECT
          account_id,
          display_name,
          tweet_id,
          tweet_history
        FROM twitter_subscriptions
        WHERE server_id = ?
      `
    )
    .all(serverId) as Array<{
    account_id: string;
    display_name: string | null;
    tweet_id: string | null;
    tweet_history: string | null;
  }>;

  return {
    TwitterNotificationChannel: row?.twitter_notification_channel ?? null,
    TwitterNotificationText: row?.twitter_notification_text ?? DEFAULT_TWITTER_NOTIFICATION_TEXT,
    XUsers: xusers.map((item) => {
      const id = item.account_id.trim().toLowerCase().replace(/^@+/, "");
      const tweetHistory = parseJsonArray(item.tweet_history);
      const tweetId = item.tweet_id ?? "";
      if (tweetId && !tweetHistory.includes(tweetId)) {
        tweetHistory.push(tweetId);
      }
      return {
        id,
        name: item.display_name?.trim() || id,
        tweetId,
        tweetHistory
      };
    })
  };
};

export const upsertTwitterSettings = async (
  serverId: string,
  partial: Partial<TwitterSettingsRecord>
) => {
  const db = getDb();
  ensureTwitterSettingsDefaults(db, serverId);
  const ts = nowTs();

  const updates: string[] = [];
  const values: unknown[] = [];

  if (partial.TwitterNotificationText !== undefined) {
    updates.push("twitter_notification_text = ?");
    values.push(partial.TwitterNotificationText.trim() || DEFAULT_TWITTER_NOTIFICATION_TEXT);
  }
  if (partial.TwitterNotificationChannel !== undefined) {
    updates.push("twitter_notification_channel = ?");
    values.push(normalizeChannelId(partial.TwitterNotificationChannel));
  }

  if (updates.length > 0) {
    updates.push("updated_at = ?");
    values.push(ts);
    db.prepare(`UPDATE twitter_data SET ${updates.join(", ")} WHERE server_id = ?`).run(...values, serverId);
  }

  if (partial.XUsers !== undefined) {
    const normalized = normalizeTwitterSubscriptions(partial.XUsers);
    const insertStatement = db.prepare(
      `
        INSERT INTO twitter_subscriptions (
          server_id,
          account_id,
          display_name,
          tweet_id,
          tweet_history,
          updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
      `
    );

    const transaction = db.transaction(() => {
      db.prepare("DELETE FROM twitter_subscriptions WHERE server_id = ?").run(serverId);
      for (const item of normalized) {
        insertStatement.run(
          serverId,
          item.id,
          item.name,
          item.tweetId,
          JSON.stringify(item.tweetHistory),
          ts
        );
      }
    });
    transaction();
  }
};
