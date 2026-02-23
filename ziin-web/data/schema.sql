PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS guild_settings (
  server_id TEXT PRIMARY KEY,
  prefix TEXT,
  language TEXT,
  timezone TEXT,
  guild_log_id TEXT,
  member_log_id TEXT,
  message_log_id TEXT,
  voice_log_id TEXT,
  setting_msg_id TEXT,
  setting_user_id TEXT,
  use_msg_id TEXT,
  use_user_id TEXT,
  ignore_channels_json TEXT DEFAULT '[]',
  updated_at INTEGER
);

CREATE TABLE IF NOT EXISTS log_settings (
  server_id TEXT NOT NULL,
  field_name TEXT NOT NULL,
  enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
  updated_at INTEGER,
  PRIMARY KEY (server_id, field_name)
);

CREATE TABLE IF NOT EXISTS user_guild_stats (
  user_id TEXT NOT NULL,
  server_id TEXT NOT NULL,
  total_msg INTEGER NOT NULL DEFAULT 0,
  voice_total_seconds INTEGER NOT NULL DEFAULT 0,
  stream_total_seconds INTEGER NOT NULL DEFAULT 0,
  last_voice_join_at INTEGER,
  updated_at INTEGER,
  PRIMARY KEY (user_id, server_id)
);

CREATE TABLE IF NOT EXISTS user_voice_channel_stats (
  user_id TEXT NOT NULL,
  server_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  voice_seconds INTEGER NOT NULL DEFAULT 0,
  last_join_at INTEGER,
  updated_at INTEGER,
  PRIMARY KEY (user_id, server_id, channel_id)
);

CREATE INDEX IF NOT EXISTS idx_log_settings_server_id ON log_settings(server_id);
CREATE INDEX IF NOT EXISTS idx_user_guild_stats_server_id ON user_guild_stats(server_id);
CREATE INDEX IF NOT EXISTS idx_user_voice_channel_stats_server_id ON user_voice_channel_stats(server_id);
