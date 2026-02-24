-- Use DELETE mode for compatibility on Docker bind mounts (Windows host).
PRAGMA journal_mode = DELETE;

-- One row per guild (server).
CREATE TABLE IF NOT EXISTS guild_settings (
  server_id TEXT PRIMARY KEY,
  name TEXT,
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

-- One row per log switch (messageDelete, guildUpdate...).
CREATE TABLE IF NOT EXISTS log_settings (
  server_id TEXT NOT NULL,
  field_name TEXT NOT NULL,
  enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
  updated_at INTEGER,
  PRIMARY KEY (server_id, field_name)
);

-- Per-user aggregate stats in a guild.
CREATE TABLE IF NOT EXISTS user_guild_stats (
  user_id TEXT NOT NULL,
  server_id TEXT NOT NULL,
  total_msg INTEGER NOT NULL DEFAULT 0,
  total_hours REAL NOT NULL DEFAULT 0,
  voice_total_seconds INTEGER NOT NULL DEFAULT 0,
  stream_total_seconds INTEGER NOT NULL DEFAULT 0,
  stream_total_time INTEGER NOT NULL DEFAULT 0,
  last_message TEXT,
  stream_start_time TEXT,
  stream_end_time TEXT,
  last_voice_join_at INTEGER,
  updated_at INTEGER,
  PRIMARY KEY (user_id, server_id)
);

-- Per-user per-voice-channel aggregate stats in a guild.
CREATE TABLE IF NOT EXISTS user_voice_channel_stats (
  user_id TEXT NOT NULL,
  server_id TEXT NOT NULL,
  channel_id TEXT NOT NULL,
  voice_seconds INTEGER NOT NULL DEFAULT 0,
  last_join_at INTEGER,
  join_time TEXT,
  leave_time TEXT,
  updated_at INTEGER,
  PRIMARY KEY (user_id, server_id, channel_id)
);

-- Per-guild Twitch notification state.
CREATE TABLE IF NOT EXISTS twitch_data (
  server_id TEXT PRIMARY KEY,
  twitch_notification_channel TEXT,
  all_streamers TEXT NOT NULL DEFAULT '[]',
  online_streamers TEXT NOT NULL DEFAULT '[]',
  offline_streamers TEXT NOT NULL DEFAULT '[]',
  twitch_notification_text TEXT NOT NULL DEFAULT '**{streamer}** is live now!!\n**{url}**',
  updated_at INTEGER
);

-- Per-guild YouTube notification state.
CREATE TABLE IF NOT EXISTS youtube_data (
  server_id TEXT PRIMARY KEY,
  youtube_notification_text TEXT NOT NULL DEFAULT '**{ytber}** upload a video!!\n**{url}**',
  youtube_notification_channel TEXT,
  updated_at INTEGER
);

-- Per-guild YouTube subscriptions (one row per youtuber).
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

CREATE INDEX IF NOT EXISTS idx_log_settings_server_id ON log_settings(server_id);
CREATE INDEX IF NOT EXISTS idx_user_guild_stats_server_id ON user_guild_stats(server_id);
CREATE INDEX IF NOT EXISTS idx_user_voice_channel_stats_server_id ON user_voice_channel_stats(server_id);
CREATE INDEX IF NOT EXISTS idx_twitch_data_server_id ON twitch_data(server_id);
CREATE INDEX IF NOT EXISTS idx_youtube_data_server_id ON youtube_data(server_id);
CREATE INDEX IF NOT EXISTS idx_youtube_subscriptions_server_id ON youtube_subscriptions(server_id);
