import { mkdirSync } from "node:fs";
import { readFileSync } from "node:fs";
import path from "node:path";
import Database from "better-sqlite3";

type GuildSettingsRecord = {
  Prefix?: string;
  TimeZone?: string;
  Language?: string;
  GuildLogId?: string | null;
  MemberLogId?: string | null;
  MessageLogId?: string | null;
  VoiceLogId?: string | null;
};

type LogSettingsRecord = Record<string, boolean>;

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

  cachedDb = db;
  return db;
};

const DEFAULT_GUILD_SETTINGS = {
  Prefix: "z!",
  TimeZone: "0",
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

const nowTs = () => Math.floor(Date.now() / 1000);

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
