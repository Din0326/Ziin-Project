"use client";

import * as React from "react";
import Image from "next/image";
import {
  IconBrandTwitch,
  IconBrandX,
  IconBrandYoutube,
  IconFileAnalytics,
  IconMoon,
  IconSettings,
  IconSun,
  IconX
} from "@tabler/icons-react";
import { signIn, signOut, useSession } from "next-auth/react";
import { AppSidebar } from "@/components/app-sidebar";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { toast } from "sonner";

const DEFAULT_LOG_SETTINGS: Record<string, boolean> = {
  memberAdd: false,
  memberKick: false,
  memberNickUpdate: true,
  memberRemove: false,
  memberUnban: false,
  memberUpdate: true,
  roleCreate: false,
  roleDelete: false,
  roleUpdate: false,
  channelCreate: false,
  channelDelete: false,
  guildUpdate: false,
  messageDelete: true,
  messageDeleteBulk: false,
  messageUpdate: true,
  voiceChannelJoin: false,
  voiceChannelLeave: false,
  voiceChannelSwitch: false,
  voiceStateUpdate: false
};
const UNAVAILABLE_LOG_SETTING_KEYS = new Set(["messageDeleteBulk"]);
const DEFAULT_TWITCH_NOTIFICATION_TEXT = "**{streamer}** is live now!!\n**{url}**";
const DEFAULT_YOUTUBE_NOTIFICATION_TEXT = "**{ytber}** upload a video!!\n**{url}**";
const DEFAULT_TWITTER_NOTIFICATION_TEXT = "**{xuser}** posted a new tweet!\n**{url}**";

const escapeHtml = (value: string) =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");

const renderPreviewMarkdown = (value: string) => {
  const lines = value.split("\n").map((line) => {
    let html = escapeHtml(line);
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*([^*]+)\*/g, "<em>$1</em>");
    html = html.replace(/~~([^~]+)~~/g, "<del>$1</del>");
    html = html.replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noreferrer noopener">$1</a>'
    );
    return html;
  });
  return lines.join("<br />");
};

type YouTubeSubscription = {
  id: string;
  name: string;
  videoId: string;
  streamId: string;
  shortId: string;
  videoHistory: string[];
  streamHistory: string[];
  shortHistory: string[];
};

type ServerSettingsSnapshot = {
  prefix: string;
  timezone?: string;
  language?: string;
};

type TwitchSettingsSnapshot = {
  channel: string;
  text: string;
  streamers: string[];
};

type YouTubeSettingsSnapshot = {
  channel: string;
  text: string;
  subscriptionIds: string[];
};

type TwitterSubscription = {
  id: string;
  name: string;
  tweetId: string;
  tweetHistory: string[];
};

type TwitterSettingsSnapshot = {
  channel: string;
  text: string;
  accountIds: string[];
};

type BootstrapPayload = {
  bootstrap?: {
    serverSettings?: {
      prefix?: unknown;
      timezone?: unknown;
      language?: unknown;
      guildLogId?: unknown;
      memberLogId?: unknown;
      messageLogId?: unknown;
      voiceLogId?: unknown;
    } | null;
    logSettings?: Record<string, unknown> | null;
    twitchSettings?: {
      twitchNotificationChannel?: unknown;
      twitchNotificationText?: unknown;
      allStreamers?: unknown;
    } | null;
    twitterSettings?: {
      twitterNotificationChannel?: unknown;
      twitterNotificationText?: unknown;
      xusers?: unknown;
    } | null;
    youtubeSettings?: {
      youtubeNotificationChannel?: unknown;
      youtubeNotificationText?: unknown;
      youtubers?: unknown;
    } | null;
    channels?: Array<{ id: string; name: string }> | null;
    roles?: Array<{ id: string; name: string; managed?: boolean }> | null;
  } | null;
};

export default function Page() {
  const LOG_CHANNEL_TARGETS = [
    { key: "memberLogId", label: "成員事件頻道" },
    { key: "guildLogId", label: "伺服器事件頻道" },
    { key: "messageLogId", label: "訊息事件頻道" },
    { key: "voiceLogId", label: "語音事件頻道" }
  ] as const;

  const [activeNavMain, setActiveNavMain] = React.useState("伺服器設定");
  const [managedServers, setManagedServers] = React.useState<
    { id: string; name: string; owner: boolean; iconUrl: string | null }[]
  >([]);
  const [selectedServerId, setSelectedServerId] = React.useState<string | undefined>(undefined);
  const [prefixInput, setPrefixInput] = React.useState("");
  const [selectedTimezone, setSelectedTimezone] = React.useState<string | undefined>(undefined);
  const [selectedLanguage, setSelectedLanguage] = React.useState<string | undefined>(undefined);
  const [timezoneQuery, setTimezoneQuery] = React.useState("");
  const [showTimezoneSuggestions, setShowTimezoneSuggestions] = React.useState(false);
  const [channelQueries, setChannelQueries] = React.useState<Record<string, string>>({});
  const [showChannelSuggestions, setShowChannelSuggestions] = React.useState<Record<string, boolean>>({});
  const [isSavingPrefix, setIsSavingPrefix] = React.useState(false);
  const [isSavingTimezone, setIsSavingTimezone] = React.useState(false);
  const [isSavingLanguage, setIsSavingLanguage] = React.useState(false);
  const [logSettings, setLogSettings] = React.useState<Record<string, boolean>>(DEFAULT_LOG_SETTINGS);
  const [isSavingLogConfig, setIsSavingLogConfig] = React.useState(false);
  const [serverChannels, setServerChannels] = React.useState<Array<{ id: string; name: string }>>([]);
  const [serverRoles, setServerRoles] = React.useState<Array<{ id: string; name: string; managed: boolean }>>([]);
  const [logChannelTargets, setLogChannelTargets] = React.useState<{
    memberLogId: string;
    guildLogId: string;
    messageLogId: string;
    voiceLogId: string;
  }>({
    memberLogId: "",
    guildLogId: "",
    messageLogId: "",
    voiceLogId: ""
  });
  const [savedServerSettings, setSavedServerSettings] = React.useState<ServerSettingsSnapshot>({
    prefix: "",
    timezone: undefined,
    language: undefined
  });
  const [savedLogSettings, setSavedLogSettings] = React.useState<Record<string, boolean>>(DEFAULT_LOG_SETTINGS);
  const [savedLogChannelTargets, setSavedLogChannelTargets] = React.useState<{
    memberLogId: string;
    guildLogId: string;
    messageLogId: string;
    voiceLogId: string;
  }>({
    memberLogId: "",
    guildLogId: "",
    messageLogId: "",
    voiceLogId: ""
  });
  const [twitchNotificationChannel, setTwitchNotificationChannel] = React.useState("");
  const [twitchNotificationText, setTwitchNotificationText] = React.useState(DEFAULT_TWITCH_NOTIFICATION_TEXT);
  const [twitchStreamers, setTwitchStreamers] = React.useState<string[]>([]);
  const [newTwitchStreamer, setNewTwitchStreamer] = React.useState("");
  const [isSavingTwitchSettings, setIsSavingTwitchSettings] = React.useState(false);
  const [twitterNotificationChannel, setTwitterNotificationChannel] = React.useState("");
  const [twitterNotificationText, setTwitterNotificationText] = React.useState(DEFAULT_TWITTER_NOTIFICATION_TEXT);
  const [twitterAccounts, setTwitterAccounts] = React.useState<TwitterSubscription[]>([]);
  const [newTwitterAccount, setNewTwitterAccount] = React.useState("");
  const [isSavingTwitterSettings, setIsSavingTwitterSettings] = React.useState(false);
  const [youtubeNotificationChannel, setYouTubeNotificationChannel] = React.useState("");
  const [youtubeNotificationText, setYouTubeNotificationText] = React.useState(DEFAULT_YOUTUBE_NOTIFICATION_TEXT);
  const twitchTemplateRef = React.useRef<HTMLTextAreaElement | null>(null);
  const youtubeTemplateRef = React.useRef<HTMLTextAreaElement | null>(null);
  const [youtubeSubscriptions, setYouTubeSubscriptions] = React.useState<YouTubeSubscription[]>([]);
  const [newYouTubeChannelInput, setNewYouTubeChannelInput] = React.useState("");
  const [isResolvingYouTubeChannel, setIsResolvingYouTubeChannel] = React.useState(false);
  const [isSavingYouTubeSettings, setIsSavingYouTubeSettings] = React.useState(false);
  const [savedTwitchSettings, setSavedTwitchSettings] = React.useState<TwitchSettingsSnapshot>({
    channel: "",
    text: DEFAULT_TWITCH_NOTIFICATION_TEXT,
    streamers: []
  });
  const [savedTwitterSettings, setSavedTwitterSettings] = React.useState<TwitterSettingsSnapshot>({
    channel: "",
    text: DEFAULT_TWITTER_NOTIFICATION_TEXT,
    accountIds: []
  });
  const [savedYouTubeSettings, setSavedYouTubeSettings] = React.useState<YouTubeSettingsSnapshot>({
    channel: "",
    text: DEFAULT_YOUTUBE_NOTIFICATION_TEXT,
    subscriptionIds: []
  });
  const [isCheckingServerSelection, setIsCheckingServerSelection] = React.useState(false);
  const [showBotInviteModal, setShowBotInviteModal] = React.useState(false);
  const [botInviteUrl, setBotInviteUrl] = React.useState("");
  const [botInviteServerName, setBotInviteServerName] = React.useState("");
  const { data: session, status } = useSession();
  const currentServerName = managedServers.find((server) => server.id === selectedServerId)?.name;
  const timezoneOptions = React.useMemo(() => {
    const zones =
      typeof Intl.supportedValuesOf === "function"
        ? Intl.supportedValuesOf("timeZone")
        : ["UTC", "Asia/Taipei"];

    const formatOffset = (zone: string) => {
      const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: zone,
        timeZoneName: "shortOffset"
      }).formatToParts(new Date());
      const value = parts.find((part) => part.type === "timeZoneName")?.value ?? "GMT+0";
      return value.replace("GMT", "UTC");
    };

    return zones.map((zone) => ({
      value: zone,
      label: `${formatOffset(zone)} ${zone}`
    }));
  }, []);
  const languageOptions = React.useMemo(
    () => [
      { value: "zh-TW", label: "繁體中文" },
      { value: "English", label: "English" }
    ],
    []
  );
  const logSections = React.useMemo(
    () => [
      {
        title: "成員事件",
        items: [
          { key: "memberAdd", label: "成員加入" },
          { key: "memberKick", label: "成員踢出" },
          { key: "memberNickUpdate", label: "暱稱變更" },
          { key: "memberRemove", label: "成員離開" },
          { key: "memberUnban", label: "解除封鎖" },
          { key: "memberUpdate", label: "成員資訊更新" }
        ]
      },
      {
        title: "身分組與頻道",
        items: [
          { key: "roleCreate", label: "建立身分組" },
          { key: "roleDelete", label: "刪除身分組" },
          { key: "roleUpdate", label: "身分組更新" },
          { key: "channelCreate", label: "建立頻道" },
          { key: "channelDelete", label: "刪除頻道" },
          { key: "guildUpdate", label: "伺服器設定更新" }
        ]
      },
      {
        title: "訊息事件",
        items: [
          { key: "messageDelete", label: "刪除訊息" },
          { key: "messageDeleteBulk", label: "大量刪除訊息", unavailable: true },
          { key: "messageUpdate", label: "編輯訊息" }
        ]
      },
      {
        title: "語音事件",
        items: [
          { key: "voiceChannelJoin", label: "加入語音頻道" },
          { key: "voiceChannelLeave", label: "離開語音頻道" },
          { key: "voiceChannelSwitch", label: "切換語音頻道" },
          { key: "voiceStateUpdate", label: "語音狀態更新" }
        ]
      }
    ],
    []
  );
  const filteredTimezoneOptions = React.useMemo(() => {
    const keyword = timezoneQuery.trim().toLowerCase();
    if (!keyword) {
      return timezoneOptions;
    }
    return timezoneOptions.filter(
      (timezone) =>
        timezone.label.toLowerCase().includes(keyword) || timezone.value.toLowerCase().includes(keyword)
    );
  }, [timezoneOptions, timezoneQuery]);
  const isTimezoneSelectionValid = React.useMemo(() => {
    const query = timezoneQuery.trim();
    return timezoneOptions.some(
      (timezone) => timezone.value === selectedTimezone && timezone.label === query
    );
  }, [selectedTimezone, timezoneOptions, timezoneQuery]);

  const selectTimezone = (timezone: { value: string; label: string }) => {
    setSelectedTimezone(timezone.value);
    setTimezoneQuery(timezone.label);
    setShowTimezoneSuggestions(false);
  };

  const getChannelLabel = React.useCallback(
    (channelId?: string) => {
      if (!channelId) {
        return "";
      }
      const channel = serverChannels.find((item) => item.id === channelId);
      return channel ? `#${channel.name}` : "";
    },
    [serverChannels]
  );

  const getChannelInputValue = React.useCallback(
    (pickerKey: string, selectedChannelId?: string) => {
      const query = channelQueries[pickerKey];
      if (typeof query === "string") {
        return query;
      }
      return getChannelLabel(selectedChannelId);
    },
    [channelQueries, getChannelLabel]
  );

  const getFilteredChannels = React.useCallback(
    (pickerKey: string) => {
      const keyword = (channelQueries[pickerKey] ?? "").trim().toLowerCase();
      if (!keyword) {
        return serverChannels;
      }
      return serverChannels.filter(
        (channel) => channel.name.toLowerCase().includes(keyword) || channel.id.includes(keyword)
      );
    },
    [channelQueries, serverChannels]
  );

  const selectChannel = React.useCallback(
    (
      pickerKey: string,
      channel: { id: string; name: string } | null,
      onSelect: (channelId: string) => void
    ) => {
      onSelect(channel ? channel.id : "");
      setChannelQueries((current) => ({
        ...current,
        [pickerKey]: channel ? `#${channel.name}` : ""
      }));
      setShowChannelSuggestions((current) => ({ ...current, [pickerKey]: false }));
    },
    []
  );
  const insertRoleMention = React.useCallback((value: string, setText: React.Dispatch<React.SetStateAction<string>>) => {
    if (!value) {
      return;
    }
    const mention = `<@&${value}>`;
    setText((current) => `${current}${current ? " " : ""}${mention}`);
  }, []);
  const resizeTemplateTextarea = React.useCallback((target: HTMLTextAreaElement) => {
    target.style.height = "auto";
    target.style.height = `${target.scrollHeight}px`;
  }, []);
  const autoResizeTemplateInput = React.useCallback((event: React.FormEvent<HTMLTextAreaElement>) => {
    const target = event.currentTarget;
    resizeTemplateTextarea(target);
  }, [resizeTemplateTextarea]);

  React.useEffect(() => {
    if (twitchTemplateRef.current) {
      resizeTemplateTextarea(twitchTemplateRef.current);
    }
    if (youtubeTemplateRef.current) {
      resizeTemplateTextarea(youtubeTemplateRef.current);
    }
  }, []);
  React.useEffect(() => {
    if (twitchTemplateRef.current) {
      resizeTemplateTextarea(twitchTemplateRef.current);
    }
  }, [resizeTemplateTextarea, twitchNotificationText]);
  React.useEffect(() => {
    if (youtubeTemplateRef.current) {
      resizeTemplateTextarea(youtubeTemplateRef.current);
    }
  }, [resizeTemplateTextarea, youtubeNotificationText]);
  const isChannelPickerValid = React.useCallback(
    (pickerKey: string, selectedChannelId?: string) => {
      const hasQuery = Object.prototype.hasOwnProperty.call(channelQueries, pickerKey);
      if (!hasQuery) {
        return true;
      }

      const query = (channelQueries[pickerKey] ?? "").trim();
      if (!query) {
        return !selectedChannelId;
      }

      return query === getChannelLabel(selectedChannelId);
    },
    [channelQueries, getChannelLabel]
  );

  const toggleLogSetting = (key: string) => {
    if (UNAVAILABLE_LOG_SETTING_KEYS.has(key)) {
      return;
    }

    setLogSettings((current) => ({
      ...current,
      [key]: !current[key]
    }));
  };

  const handleSavePrefix = async () => {
    if (!selectedServerId || !prefixInput.trim()) {
      return;
    }

    setIsSavingPrefix(true);
    try {
      const response = await fetch(`/api/server-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prefix: prefixInput.trim() })
      });
      if (!response.ok) {
        let errorMessage = "儲存失敗，請稍後再試";
        try {
          const errorData = (await response.json()) as { error?: unknown };
          if (typeof errorData.error === "string" && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          // ignore response parse errors
        }
        toast.error(errorMessage);
        return;
      }
      toast.success("前綴儲存成功");
      setSavedServerSettings((current) => ({ ...current, prefix: prefixInput.trim() }));
    } catch {
      toast.error("儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingPrefix(false);
    }
  };

  const handleSaveTimezone = async () => {
    if (!selectedServerId || !isTimezoneSelectionValid || !selectedTimezone) {
      return;
    }

    setIsSavingTimezone(true);
    try {
      const response = await fetch(`/api/server-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timezone: selectedTimezone })
      });
      if (!response.ok) {
        let errorMessage = "儲存失敗，請稍後再試";
        try {
          const errorData = (await response.json()) as { error?: unknown };
          if (typeof errorData.error === "string" && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          // ignore response parse errors
        }
        toast.error(errorMessage);
        return;
      }
      toast.success("時區儲存成功");
      setSavedServerSettings((current) => ({ ...current, timezone: selectedTimezone }));
    } catch {
      toast.error("儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingTimezone(false);
    }
  };

  const handleSaveLanguage = async () => {
    if (!selectedServerId || !selectedLanguage) {
      return;
    }

    setIsSavingLanguage(true);
    try {
      const response = await fetch(`/api/server-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ language: selectedLanguage })
      });
      if (!response.ok) {
        let errorMessage = "儲存失敗，請稍後再試";
        try {
          const errorData = (await response.json()) as { error?: unknown };
          if (typeof errorData.error === "string" && errorData.error) {
            errorMessage = errorData.error;
          }
        } catch {
          // ignore response parse errors
        }
        toast.error(errorMessage);
        return;
      }
      toast.success("語言儲存成功");
      setSavedServerSettings((current) => ({ ...current, language: selectedLanguage }));
    } catch {
      toast.error("儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingLanguage(false);
    }
  };

  const handleSaveLogConfig = async () => {
    if (!selectedServerId) {
      return;
    }
    if (!isLogChannelSelectionValid) {
      toast.error("請從清單選擇有效的頻道，或清空欄位");
      return;
    }

    setIsSavingLogConfig(true);
    try {
      const settingsResponse = await fetch(`/api/log-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ settings: logSettings })
      });
      if (!settingsResponse.ok) {
        let errorMessage = "儲存失敗，請稍後再試";
        try {
          const errorData = (await settingsResponse.json()) as { error?: unknown; message?: unknown };
          if (typeof errorData.error === "string" && errorData.error) {
            errorMessage = errorData.error;
          } else if (typeof errorData.message === "string" && errorData.message) {
            errorMessage = errorData.message;
          }
        } catch {
          // ignore response parse errors
        }
        toast.error(errorMessage);
        return;
      }

      const channelsResponse = await fetch(`/api/server-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          guildLogId: logChannelTargets.guildLogId || null,
          memberLogId: logChannelTargets.memberLogId || null,
          messageLogId: logChannelTargets.messageLogId || null,
          voiceLogId: logChannelTargets.voiceLogId || null
        })
      });

      if (!channelsResponse.ok) {
        let errorMessage = "儲存失敗，請稍後再試";
        try {
          const errorData = (await channelsResponse.json()) as { error?: unknown; message?: unknown };
          if (typeof errorData.error === "string" && errorData.error) {
            errorMessage = errorData.error;
          } else if (typeof errorData.message === "string" && errorData.message) {
            errorMessage = errorData.message;
          }
        } catch {
          // ignore response parse errors
        }
        toast.error(errorMessage);
        return;
      }

      setSavedLogSettings(logSettings);
      setSavedLogChannelTargets(logChannelTargets);
      toast.success("Log 設定儲存成功");
    } catch {
      toast.error("儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingLogConfig(false);
    }
  };

  const handleAddTwitchStreamer = () => {
    const value = newTwitchStreamer.trim().toLowerCase();
    if (!value) {
      return;
    }
    if (twitchStreamers.includes(value)) {
      toast.error("此 Twitch 使用者已在清單中");
      return;
    }
    setTwitchStreamers((current) => [...current, value]);
    setNewTwitchStreamer("");
  };

  const handleRemoveTwitchStreamer = (value: string) => {
    setTwitchStreamers((current) => current.filter((item) => item !== value));
  };

  const normalizeTwitterHandle = (value: string) => {
    const input = value.trim();
    if (!input) {
      return "";
    }
    const match = input.match(/(?:x\.com|twitter\.com)\/([A-Za-z0-9_]{1,15})/i);
    if (match?.[1]) {
      return match[1].toLowerCase();
    }
    return input.replace(/^@+/, "").toLowerCase();
  };

  const handleSaveTwitchSettings = async () => {
    if (!selectedServerId) {
      return;
    }
    if (!isTwitchChannelSelectionValid) {
      toast.error("請從清單選擇有效的通知頻道，或清空欄位");
      return;
    }

    setIsSavingTwitchSettings(true);
    try {
      const response = await fetch(`/api/twitch-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          twitchNotificationChannel: twitchNotificationChannel || null,
          twitchNotificationText,
          allStreamers: twitchStreamers
        })
      });

      if (!response.ok) {
        toast.error("Twitch 設定儲存失敗");
        return;
      }
      toast.success("Twitch 設定儲存成功");
      setSavedTwitchSettings({
        channel: twitchNotificationChannel,
        text: twitchNotificationText,
        streamers: [...twitchStreamers]
      });
    } catch {
      toast.error("Twitch 設定儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingTwitchSettings(false);
    }
  };

  const handleAddTwitterAccount = () => {
    const value = normalizeTwitterHandle(newTwitterAccount);
    if (!value) {
      return;
    }
    if (twitterAccounts.some((item) => item.id === value)) {
      toast.error("此 Twitter 帳號已在清單中");
      return;
    }
    setTwitterAccounts((current) => [
      ...current,
      {
        id: value,
        name: value,
        tweetId: "",
        tweetHistory: []
      }
    ]);
    setNewTwitterAccount("");
  };

  const handleRemoveTwitterAccount = (value: string) => {
    setTwitterAccounts((current) => current.filter((item) => item.id !== value));
  };

  const handleSaveTwitterSettings = async () => {
    if (!selectedServerId) {
      return;
    }
    if (!isTwitterChannelSelectionValid) {
      toast.error("請從清單選擇有效的通知頻道，或清空欄位");
      return;
    }

    setIsSavingTwitterSettings(true);
    try {
      const response = await fetch(`/api/twitter-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          twitterNotificationChannel: twitterNotificationChannel || null,
          twitterNotificationText,
          xusers: twitterAccounts.map((item) => ({
            ...item,
            name: resolvedProfileNames[`twitter:${item.id}`] ?? item.name
          }))
        })
      });

      if (!response.ok) {
        toast.error("Twitter 設定儲存失敗");
        return;
      }
      toast.success("Twitter 設定儲存成功");
      setSavedTwitterSettings({
        channel: twitterNotificationChannel,
        text: twitterNotificationText,
        accountIds: twitterAccounts.map((item) => item.id).sort()
      });
    } catch {
      toast.error("Twitter 設定儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingTwitterSettings(false);
    }
  };

  const handleAddYouTubeSubscription = async () => {
    const input = newYouTubeChannelInput.trim();
    if (!input) {
      return;
    }

    setIsResolvingYouTubeChannel(true);
    try {
      const response = await fetch("/api/youtube-resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input })
      });

      const result = (await response.json()) as {
        channelId?: unknown;
        channelName?: unknown;
        message?: unknown;
      };

      if (!response.ok || typeof result.channelId !== "string") {
        toast.error(typeof result.message === "string" ? result.message : "無法解析 YouTube 頻道網址");
        return;
      }

      const channelId = result.channelId;
      if (youtubeSubscriptions.some((item) => item.id === channelId)) {
        toast.error("此 YouTube 頻道已在清單中");
        return;
      }

      setYouTubeSubscriptions((current) => [
        ...current,
        {
          id: channelId,
          name: typeof result.channelName === "string" && result.channelName ? result.channelName : channelId,
          videoId: "",
          streamId: "",
          shortId: "",
          videoHistory: [],
          streamHistory: [],
          shortHistory: []
        }
      ]);
      setNewYouTubeChannelInput("");
    } catch {
      toast.error("無法解析 YouTube 頻道網址，請稍後再試");
    } finally {
      setIsResolvingYouTubeChannel(false);
    }
  };

  const handleRemoveYouTubeSubscription = (channelId: string) => {
    setYouTubeSubscriptions((current) => current.filter((item) => item.id !== channelId));
  };

  const handleSaveYouTubeSettings = async () => {
    if (!selectedServerId) {
      return;
    }
    if (!isYouTubeChannelSelectionValid) {
      toast.error("請從清單選擇有效的通知頻道，或清空欄位");
      return;
    }

    setIsSavingYouTubeSettings(true);
    try {
      const response = await fetch(`/api/youtube-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          youtubeNotificationChannel: youtubeNotificationChannel || null,
          youtubeNotificationText,
          youtubers: youtubeSubscriptions
        })
      });

      if (!response.ok) {
        toast.error("YouTube 設定儲存失敗");
        return;
      }
      toast.success("YouTube 設定儲存成功");
      setSavedYouTubeSettings({
        channel: youtubeNotificationChannel,
        text: youtubeNotificationText,
        subscriptionIds: youtubeSubscriptions.map((item) => item.id).sort()
      });
    } catch {
      toast.error("YouTube 設定儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingYouTubeSettings(false);
    }
  };

  const handleLoginClick = () => {
    void signIn("discord", { callbackUrl: "/dashboard" });
  };

  const handleLogoutClick = () => {
    void signOut({ callbackUrl: "/" });
  };

  const handleServerSelect = async (server: { id: string; name: string }) => {
    if (isCheckingServerSelection) {
      return;
    }

    setIsCheckingServerSelection(true);
    try {
      const response = await fetch(`/api/discord/bot-membership/${server.id}`, { method: "GET" });
      if (!response.ok) {
        toast.error("伺服器驗證失敗，請稍後再試");
        return;
      }

      const result = (await response.json()) as { inGuild?: unknown; inviteUrl?: unknown };
      if (result.inGuild === false) {
        setShowBotInviteModal(true);
        setBotInviteUrl(typeof result.inviteUrl === "string" ? result.inviteUrl : "");
        setBotInviteServerName(server.name);
        return;
      }

      setShowBotInviteModal(false);
      setSelectedServerId(server.id);
      setActiveNavMain("伺服器設定");
    } catch {
      toast.error("伺服器驗證失敗，請稍後再試");
    } finally {
      setIsCheckingServerSelection(false);
    }
  };

  const isAuthenticated = status === "authenticated";
  const showServerPicker = status === "authenticated" && !selectedServerId;
  const [theme, setTheme] = React.useState<"light" | "dark">("light");
  const [avatarFallbacks, setAvatarFallbacks] = React.useState<Record<string, boolean>>({});
  const [resolvedAvatars, setResolvedAvatars] = React.useState<Record<string, string>>({});
  const [resolvedProfileNames, setResolvedProfileNames] = React.useState<Record<string, string>>({});
  const [resolvedTwitterHandles, setResolvedTwitterHandles] = React.useState<Record<string, string>>({});
  const isServerSettingsDirty = React.useMemo(
    () =>
      prefixInput.trim() !== savedServerSettings.prefix ||
      selectedTimezone !== savedServerSettings.timezone ||
      selectedLanguage !== savedServerSettings.language,
    [prefixInput, savedServerSettings, selectedLanguage, selectedTimezone]
  );
  const isLogSettingsDirty = React.useMemo(
    () => JSON.stringify(logSettings) !== JSON.stringify(savedLogSettings),
    [logSettings, savedLogSettings]
  );
  const isLogChannelsDirty = React.useMemo(
    () => JSON.stringify(logChannelTargets) !== JSON.stringify(savedLogChannelTargets),
    [logChannelTargets, savedLogChannelTargets]
  );
  const isTwitchDirty = React.useMemo(
    () =>
      twitchNotificationChannel !== savedTwitchSettings.channel ||
      twitchNotificationText !== savedTwitchSettings.text ||
      JSON.stringify(twitchStreamers) !== JSON.stringify(savedTwitchSettings.streamers),
    [savedTwitchSettings, twitchNotificationChannel, twitchNotificationText, twitchStreamers]
  );
  const isTwitterDirty = React.useMemo(() => {
    const currentIds = twitterAccounts.map((item) => item.id).sort();
    return (
      twitterNotificationChannel !== savedTwitterSettings.channel ||
      twitterNotificationText !== savedTwitterSettings.text ||
      JSON.stringify(currentIds) !== JSON.stringify(savedTwitterSettings.accountIds)
    );
  }, [savedTwitterSettings, twitterAccounts, twitterNotificationChannel, twitterNotificationText]);
  const isYouTubeDirty = React.useMemo(() => {
    const currentIds = youtubeSubscriptions.map((item) => item.id).sort();
    return (
      youtubeNotificationChannel !== savedYouTubeSettings.channel ||
      youtubeNotificationText !== savedYouTubeSettings.text ||
      JSON.stringify(currentIds) !== JSON.stringify(savedYouTubeSettings.subscriptionIds)
    );
  }, [savedYouTubeSettings, youtubeNotificationChannel, youtubeNotificationText, youtubeSubscriptions]);
  const isLogChannelSelectionValid = React.useMemo(
    () =>
      isChannelPickerValid("log:memberLogId", logChannelTargets.memberLogId) &&
      isChannelPickerValid("log:guildLogId", logChannelTargets.guildLogId) &&
      isChannelPickerValid("log:messageLogId", logChannelTargets.messageLogId) &&
      isChannelPickerValid("log:voiceLogId", logChannelTargets.voiceLogId),
    [
      isChannelPickerValid,
      logChannelTargets.memberLogId,
      logChannelTargets.guildLogId,
      logChannelTargets.messageLogId,
      logChannelTargets.voiceLogId
    ]
  );
  const isTwitchChannelSelectionValid = React.useMemo(
    () => isChannelPickerValid("twitch:notification", twitchNotificationChannel),
    [isChannelPickerValid, twitchNotificationChannel]
  );
  const isYouTubeChannelSelectionValid = React.useMemo(
    () => isChannelPickerValid("youtube:notification", youtubeNotificationChannel),
    [isChannelPickerValid, youtubeNotificationChannel]
  );
  const isTwitterChannelSelectionValid = React.useMemo(
    () => isChannelPickerValid("twitter:notification", twitterNotificationChannel),
    [isChannelPickerValid, twitterNotificationChannel]
  );
  const twitchTemplatePreview = React.useMemo(
    () =>
      twitchNotificationText
        .replaceAll("{streamer}", "Din4ni")
        .replaceAll("{url}", "https://twitch.tv/din4ni")
        .replaceAll("\\n", "\n"),
    [twitchNotificationText]
  );
  const youtubeTemplatePreview = React.useMemo(
    () =>
      youtubeNotificationText
        .replaceAll("{ytber}", "Din Channel")
        .replaceAll("{url}", "https://youtu.be/dQw4w9WgXcQ")
        .replaceAll("\\n", "\n"),
    [youtubeNotificationText]
  );
  const twitchTemplatePreviewHtml = React.useMemo(
    () => renderPreviewMarkdown(twitchTemplatePreview),
    [twitchTemplatePreview]
  );
  const youtubeTemplatePreviewHtml = React.useMemo(
    () => renderPreviewMarkdown(youtubeTemplatePreview),
    [youtubeTemplatePreview]
  );
  const twitterTemplatePreview = React.useMemo(
    () =>
      twitterNotificationText
        .replaceAll("{xuser}", "din4ni")
        .replaceAll("{url}", "https://x.com/din4ni/status/1234567890123456789")
        .replaceAll("\\n", "\n"),
    [twitterNotificationText]
  );
  const twitterTemplatePreviewHtml = React.useMemo(
    () => renderPreviewMarkdown(twitterTemplatePreview),
    [twitterTemplatePreview]
  );

  const hasUnsavedChangesOnCurrentPage = React.useMemo(() => {
    if (activeNavMain === "伺服器設定") {
      return isServerSettingsDirty;
    }
    if (activeNavMain === "Log 系統") {
      return isLogSettingsDirty || isLogChannelsDirty;
    }
    if (activeNavMain === "Twitch") {
      return isTwitchDirty;
    }
    if (activeNavMain === "Twitter") {
      return isTwitterDirty;
    }
    if (activeNavMain === "YouTube") {
      return isYouTubeDirty;
    }
    return false;
  }, [activeNavMain, isLogChannelsDirty, isLogSettingsDirty, isServerSettingsDirty, isTwitchDirty, isTwitterDirty, isYouTubeDirty]);

  const confirmLeaveIfUnsaved = React.useCallback(() => {
    if (!hasUnsavedChangesOnCurrentPage) {
      return true;
    }
    return window.confirm("已更改項目尚未儲存，確定要離開嗎？");
  }, [hasUnsavedChangesOnCurrentPage]);

  const discardUnsavedCurrentPage = React.useCallback(() => {
    if (activeNavMain === "伺服器設定") {
      setPrefixInput(savedServerSettings.prefix);
      setSelectedTimezone(savedServerSettings.timezone);
      if (savedServerSettings.timezone) {
        const matched = timezoneOptions.find((timezone) => timezone.value === savedServerSettings.timezone);
        setTimezoneQuery(matched?.label ?? savedServerSettings.timezone);
      } else {
        setTimezoneQuery("");
      }
      setSelectedLanguage(savedServerSettings.language);
      return;
    }

    if (activeNavMain === "Log 系統") {
      setLogSettings(savedLogSettings);
      setLogChannelTargets(savedLogChannelTargets);
      return;
    }

    if (activeNavMain === "Twitch") {
      setTwitchNotificationChannel(savedTwitchSettings.channel);
      setTwitchNotificationText(savedTwitchSettings.text);
      setTwitchStreamers(savedTwitchSettings.streamers);
      setNewTwitchStreamer("");
      return;
    }

    if (activeNavMain === "Twitter") {
      setTwitterNotificationChannel(savedTwitterSettings.channel);
      setTwitterNotificationText(savedTwitterSettings.text);
      setTwitterAccounts((current) => {
        const byId = new Map(current.map((item) => [item.id, item]));
        return savedTwitterSettings.accountIds.map((id) => {
          const existing = byId.get(id);
          if (existing) {
            return existing;
          }
          return {
            id,
            name: id,
            tweetId: "",
            tweetHistory: []
          };
        });
      });
      setNewTwitterAccount("");
      return;
    }

    if (activeNavMain === "YouTube") {
      setYouTubeNotificationChannel(savedYouTubeSettings.channel);
      setYouTubeNotificationText(savedYouTubeSettings.text);
      setYouTubeSubscriptions((current) => {
        const byId = new Map(current.map((item) => [item.id, item]));
        return savedYouTubeSettings.subscriptionIds.map((id) => {
          const existing = byId.get(id);
          if (existing) {
            return existing;
          }
          return {
            id,
            name: id,
            videoId: "",
            streamId: "",
            shortId: "",
            videoHistory: [],
            streamHistory: [],
            shortHistory: []
          };
        });
      });
      setNewYouTubeChannelInput("");
    }
  }, [
    activeNavMain,
    savedLogChannelTargets,
    savedLogSettings,
    savedServerSettings,
    savedTwitchSettings,
    savedTwitterSettings,
    savedYouTubeSettings,
    timezoneOptions
  ]);

  const handleNavMainChange = React.useCallback(
    (nextTitle: string) => {
      if (nextTitle === activeNavMain) {
        return;
      }
      if (!confirmLeaveIfUnsaved()) {
        return;
      }
      if (hasUnsavedChangesOnCurrentPage) {
        discardUnsavedCurrentPage();
      }
      setActiveNavMain(nextTitle);
    },
    [activeNavMain, confirmLeaveIfUnsaved, discardUnsavedCurrentPage, hasUnsavedChangesOnCurrentPage]
  );

  const handleSwitchServer = React.useCallback(() => {
    if (!confirmLeaveIfUnsaved()) {
      return;
    }
    if (hasUnsavedChangesOnCurrentPage) {
      discardUnsavedCurrentPage();
    }
    setSelectedServerId(undefined);
  }, [confirmLeaveIfUnsaved, discardUnsavedCurrentPage, hasUnsavedChangesOnCurrentPage]);

  React.useEffect(() => {
    if (!isAuthenticated || showServerPicker) {
      document.title = "Dashboard - Ziin";
      return;
    }

    document.title = `${activeNavMain} - ${currentServerName ?? "Ziin"}`;
  }, [activeNavMain, currentServerName, isAuthenticated, showServerPicker]);

  React.useEffect(() => {
    const savedTheme = window.localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const nextTheme =
      savedTheme === "dark" || savedTheme === "light"
        ? savedTheme
        : prefersDark
          ? "dark"
          : "light";

    document.documentElement.classList.toggle("dark", nextTheme === "dark");
    setTheme(nextTheme);
  }, []);

  const toggleTheme = () => {
    const nextTheme = theme === "dark" ? "light" : "dark";
    document.documentElement.classList.toggle("dark", nextTheme === "dark");
    window.localStorage.setItem("theme", nextTheme);
    setTheme(nextTheme);
  };

  React.useEffect(() => {
    if (status !== "authenticated") {
      setManagedServers([]);
      setSelectedServerId(undefined);
      return;
    }

    const abortController = new AbortController();

    const loadManagedServers = async () => {
      try {
        const response = await fetch("/api/discord/managed-guilds", {
          method: "GET",
          signal: abortController.signal
        });

        if (!response.ok) {
          setManagedServers([]);
          setSelectedServerId(undefined);
          return;
        }

        const result = (await response.json()) as {
          guilds: { id: string; name: string; owner: boolean; iconUrl: string | null }[];
        };
        setManagedServers(result.guilds);
        setSelectedServerId((current) =>
          current && result.guilds.some((guild) => guild.id === current) ? current : undefined
        );
      } catch (error) {
        // Ignore expected cancellation during unmount/re-render.
        if (abortController.signal.aborted) {
          return;
        }
        if (error instanceof Error && error.name === "AbortError") {
          return;
        }
        throw error;
      }
    };

    void loadManagedServers();

    return () => {
      abortController.abort();
    };
  }, [status]);

  React.useEffect(() => {
    if (!selectedServerId) {
      setPrefixInput("");
      setSelectedTimezone(undefined);
      setTimezoneQuery("");
      setSelectedLanguage(undefined);
      setSavedServerSettings({
        prefix: "",
        timezone: undefined,
        language: undefined
      });
      setShowBotInviteModal(false);
      setBotInviteUrl("");
      setBotInviteServerName("");
      setChannelQueries({});
      setShowChannelSuggestions({});
      setServerChannels([]);
      setServerRoles([]);
      setLogSettings(DEFAULT_LOG_SETTINGS);
      setLogChannelTargets({
        memberLogId: "",
        guildLogId: "",
        messageLogId: "",
        voiceLogId: ""
      });
      setSavedLogSettings(DEFAULT_LOG_SETTINGS);
      setSavedLogChannelTargets({
        memberLogId: "",
        guildLogId: "",
        messageLogId: "",
        voiceLogId: ""
      });
      setTwitchNotificationChannel("");
      setTwitchNotificationText(DEFAULT_TWITCH_NOTIFICATION_TEXT);
      setTwitchStreamers([]);
      setSavedTwitchSettings({
        channel: "",
        text: DEFAULT_TWITCH_NOTIFICATION_TEXT,
        streamers: []
      });
      setNewTwitchStreamer("");
      setTwitterNotificationChannel("");
      setTwitterNotificationText(DEFAULT_TWITTER_NOTIFICATION_TEXT);
      setTwitterAccounts([]);
      setSavedTwitterSettings({
        channel: "",
        text: DEFAULT_TWITTER_NOTIFICATION_TEXT,
        accountIds: []
      });
      setNewTwitterAccount("");
      setYouTubeNotificationChannel("");
      setYouTubeNotificationText(DEFAULT_YOUTUBE_NOTIFICATION_TEXT);
      setYouTubeSubscriptions([]);
      setSavedYouTubeSettings({
        channel: "",
        text: DEFAULT_YOUTUBE_NOTIFICATION_TEXT,
        subscriptionIds: []
      });
      setNewYouTubeChannelInput("");
      return;
    }

    let active = true;

    const loadBootstrap = async () => {
      const response = await fetch(`/api/server-settings/${selectedServerId}/bootstrap`, {
        method: "GET"
      });
      if (!active || !response.ok) {
        setServerChannels([]);
        setServerRoles([]);
        return;
      }

      const result = (await response.json()) as BootstrapPayload;
      const bootstrap = result.bootstrap;
      if (!bootstrap) {
        setServerChannels([]);
        setServerRoles([]);
        return;
      }

      const serverData = bootstrap.serverSettings;
      const logData = bootstrap.logSettings;
      const twitchData = bootstrap.twitchSettings;
      const twitterData = bootstrap.twitterSettings;
      const youtubeData = bootstrap.youtubeSettings;

      const prefix = typeof serverData?.prefix === "string" ? serverData.prefix : "";
      let normalizedTimezoneValue: string | undefined;
      if (typeof serverData?.timezone === "string") {
        const timezoneIdFromValue =
          serverData.timezone
            .split(/\s+/)
            .find((part) => part.includes("/") && part.length > 3) ?? null;
        const matchedTimezone = timezoneOptions.find((timezone) => {
          if (timezone.value === serverData.timezone || timezone.label === serverData.timezone) {
            return true;
          }
          if (timezoneIdFromValue && timezone.value === timezoneIdFromValue) {
            return true;
          }
          return false;
        });
        normalizedTimezoneValue = matchedTimezone?.value;
        setSelectedTimezone(matchedTimezone?.value);
        setTimezoneQuery(matchedTimezone?.label ?? serverData.timezone);
      } else {
        setSelectedTimezone(undefined);
        setTimezoneQuery("");
      }

      let normalizedLanguage: string | undefined;
      if (typeof serverData?.language === "string") {
        if (serverData.language === "zh-TW") {
          normalizedLanguage = "zh-TW";
        } else if (serverData.language === "en") {
          normalizedLanguage = "English";
        } else if (serverData.language === "繁體中文") {
          normalizedLanguage = "zh-TW";
        } else {
          normalizedLanguage = serverData.language;
        }
      }

      const nextLogChannels = {
        guildLogId: typeof serverData?.guildLogId === "string" ? serverData.guildLogId : "",
        memberLogId: typeof serverData?.memberLogId === "string" ? serverData.memberLogId : "",
        messageLogId: typeof serverData?.messageLogId === "string" ? serverData.messageLogId : "",
        voiceLogId: typeof serverData?.voiceLogId === "string" ? serverData.voiceLogId : ""
      };

      const nextLogSettings: Record<string, boolean> = { ...DEFAULT_LOG_SETTINGS };
      if (logData) {
        for (const key of Object.keys(DEFAULT_LOG_SETTINGS)) {
          if (typeof logData[key] === "boolean") {
            nextLogSettings[key] = logData[key] as boolean;
          }
        }
      }

      const nextTwitchChannel =
        typeof twitchData?.twitchNotificationChannel === "string" ? twitchData.twitchNotificationChannel : "";
      const nextTwitchText =
        typeof twitchData?.twitchNotificationText === "string"
          ? twitchData.twitchNotificationText
          : DEFAULT_TWITCH_NOTIFICATION_TEXT;
      const nextTwitchStreamers = Array.isArray(twitchData?.allStreamers)
        ? twitchData.allStreamers.filter((item): item is string => typeof item === "string")
        : [];

      const nextYouTubeChannel =
        typeof youtubeData?.youtubeNotificationChannel === "string" ? youtubeData.youtubeNotificationChannel : "";
      const nextYouTubeText =
        typeof youtubeData?.youtubeNotificationText === "string"
          ? youtubeData.youtubeNotificationText
          : DEFAULT_YOUTUBE_NOTIFICATION_TEXT;
      const nextYouTubeSubs = Array.isArray(youtubeData?.youtubers)
        ? youtubeData.youtubers
            .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
            .map((item) => ({
              id: typeof item.id === "string" ? item.id : "",
              name: typeof item.name === "string" ? item.name : typeof item.id === "string" ? item.id : "",
              videoId: typeof item.videoId === "string" ? item.videoId : "",
              streamId: typeof item.streamId === "string" ? item.streamId : "",
              shortId: typeof item.shortId === "string" ? item.shortId : "",
              videoHistory: Array.isArray(item.videoHistory)
                ? item.videoHistory.filter((value): value is string => typeof value === "string")
                : [],
              streamHistory: Array.isArray(item.streamHistory)
                ? item.streamHistory.filter((value): value is string => typeof value === "string")
                : [],
              shortHistory: Array.isArray(item.shortHistory)
                ? item.shortHistory.filter((value): value is string => typeof value === "string")
                : []
            }))
            .filter((item) => item.id)
        : [];

      const nextTwitterChannel =
        typeof twitterData?.twitterNotificationChannel === "string" ? twitterData.twitterNotificationChannel : "";
      const nextTwitterText =
        typeof twitterData?.twitterNotificationText === "string"
          ? twitterData.twitterNotificationText
          : DEFAULT_TWITTER_NOTIFICATION_TEXT;
      const nextTwitterAccounts = Array.isArray(twitterData?.xusers)
        ? twitterData.xusers
            .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
            .map((item) => ({
              id:
                typeof item.id === "string"
                  ? item.id.trim().toLowerCase().replace(/^@+/, "")
                  : "",
              name: typeof item.name === "string" ? item.name : typeof item.id === "string" ? item.id : "",
              tweetId: typeof item.tweetId === "string" ? item.tweetId : "",
              tweetHistory: Array.isArray(item.tweetHistory)
                ? item.tweetHistory.filter((value): value is string => typeof value === "string")
                : []
            }))
            .filter((item) => item.id)
        : [];

      const nextChannels = Array.isArray(bootstrap.channels)
        ? bootstrap.channels
            .filter((channel): channel is { id: string; name: string } => {
              return typeof channel.id === "string" && typeof channel.name === "string";
            })
        : [];
      const nextRoles = Array.isArray(bootstrap.roles)
        ? bootstrap.roles
            .filter((role): role is { id: string; name: string; managed: boolean } => {
              return (
                typeof role.id === "string" &&
                typeof role.name === "string" &&
                typeof role.managed === "boolean"
              );
            })
        : [];

      setPrefixInput(prefix);
      setSelectedLanguage(normalizedLanguage);
      setSavedServerSettings({
        prefix,
        timezone: normalizedTimezoneValue,
        language: normalizedLanguage
      });
      setLogChannelTargets(nextLogChannels);
      setSavedLogChannelTargets(nextLogChannels);
      setLogSettings(nextLogSettings);
      setSavedLogSettings(nextLogSettings);
      setTwitchNotificationChannel(nextTwitchChannel);
      setTwitchNotificationText(nextTwitchText);
      setTwitchStreamers(nextTwitchStreamers);
      setSavedTwitchSettings({
        channel: nextTwitchChannel,
        text: nextTwitchText,
        streamers: [...nextTwitchStreamers]
      });
      setYouTubeNotificationChannel(nextYouTubeChannel);
      setYouTubeNotificationText(nextYouTubeText);
      setYouTubeSubscriptions(nextYouTubeSubs);
      setTwitterNotificationChannel(nextTwitterChannel);
      setTwitterNotificationText(nextTwitterText);
      setTwitterAccounts(nextTwitterAccounts);
      setSavedYouTubeSettings({
        channel: nextYouTubeChannel,
        text: nextYouTubeText,
        subscriptionIds: nextYouTubeSubs.map((item) => item.id).sort()
      });
      setSavedTwitterSettings({
        channel: nextTwitterChannel,
        text: nextTwitterText,
        accountIds: nextTwitterAccounts.map((item) => item.id).sort()
      });
      setServerChannels(nextChannels);
      setServerRoles(nextRoles);
    };

    void loadBootstrap();

    return () => {
      active = false;
    };
  }, [selectedServerId, timezoneOptions]);

  React.useEffect(() => {
    const resolveAvatar = async (platform: "twitch" | "youtube", id: string) => {
      const key = `${platform}:${id}`;
      if (resolvedAvatars[key] || avatarFallbacks[key]) {
        return;
      }
      try {
        const response = await fetch(
          `/api/profile-avatar?platform=${encodeURIComponent(platform)}&id=${encodeURIComponent(id)}`,
          { method: "GET" }
        );
        if (!response.ok) {
          setAvatarFallbacks((current) => ({ ...current, [key]: true }));
          return;
        }
        const result = (await response.json()) as { avatarUrl?: unknown; profileName?: unknown };
        if (typeof result.avatarUrl !== "string" || !result.avatarUrl) {
          setAvatarFallbacks((current) => ({ ...current, [key]: true }));
          return;
        }
        const avatarUrl = result.avatarUrl;
        setResolvedAvatars((current) => ({ ...current, [key]: avatarUrl }));
        if (typeof result.profileName === "string" && result.profileName.trim()) {
          const profileName = result.profileName.trim();
          setResolvedProfileNames((current) => ({ ...current, [key]: profileName }));
        }
        if (platform === "youtube" && typeof result.profileName === "string" && result.profileName.trim()) {
          const profileName = result.profileName.trim();
          setYouTubeSubscriptions((current) =>
            current.map((item) => {
              if (item.id !== id) {
                return item;
              }
              if (item.name && item.name !== item.id) {
                return item;
              }
              return { ...item, name: profileName };
            })
          );
        }
      } catch {
        setAvatarFallbacks((current) => ({ ...current, [key]: true }));
      }
    };

    twitchStreamers.forEach((streamer) => {
      void resolveAvatar("twitch", streamer);
    });
    youtubeSubscriptions.forEach((subscription) => {
      void resolveAvatar("youtube", subscription.id);
    });
  }, [avatarFallbacks, resolvedAvatars, twitchStreamers, youtubeSubscriptions]);

  React.useEffect(() => {
    const resolveTwitterProfile = async (id: string) => {
      const key = `twitter:${id}`;
      if (resolvedProfileNames[key] && resolvedTwitterHandles[key]) {
        return;
      }
      try {
        const response = await fetch(`/api/twitter-profile?handle=${encodeURIComponent(id)}`, { method: "GET" });
        if (!response.ok) {
          return;
        }
        const result = (await response.json()) as { profileName?: unknown; handle?: unknown };
        const profileName = typeof result.profileName === "string" ? result.profileName.trim() : "";
        if (profileName) {
          setResolvedProfileNames((current) => ({ ...current, [key]: profileName }));
          setTwitterAccounts((current) =>
            current.map((item) => (item.id === id && item.name !== profileName ? { ...item, name: profileName } : item))
          );
        }
        const twitterHandle = typeof result.handle === "string" ? result.handle.trim() : "";
        if (twitterHandle) {
          setResolvedTwitterHandles((current) => ({ ...current, [key]: twitterHandle }));
        }
      } catch {
        // no-op: keep fallback display
      }
    };

    twitterAccounts.forEach((account) => {
      void resolveTwitterProfile(account.id);
    });
  }, [resolvedProfileNames, resolvedTwitterHandles, twitterAccounts]);

  return (
    <SidebarProvider
      className="h-svh overflow-hidden"
      style={
        {
          "--sidebar-width": "calc(var(--spacing) * 80)",
          "--header-height": "calc(var(--spacing) * 16 + 2px)"
        } as React.CSSProperties
      }>
      <AppSidebar
        variant="sidebar"
        activeNavMainTitle={isAuthenticated && !showServerPicker ? activeNavMain : undefined}
        isAuthenticated={isAuthenticated}
        onLogin={handleLoginClick}
        onNavMainClick={handleNavMainChange}
        onSwitchServer={handleSwitchServer}
        onLogout={handleLogoutClick}
        currentServerName={currentServerName}
        user={{
          name: session?.user?.name ?? "Guest",
          email: session?.user?.email ?? "",
          avatar: session?.user?.image ?? ""
        }}
      />
      <SidebarInset className="h-svh overflow-hidden">
        <SiteHeader>
          <Button
            className="h-9 px-3 leading-none"
            onClick={isAuthenticated ? handleLogoutClick : handleLoginClick}
            disabled={status === "loading"}>
            {status === "loading" ? "載入中..." : isAuthenticated ? "登出" : "登入"}
          </Button>
          <Button
            type="button"
            variant="outline"
            className="h-9 w-9 p-0 leading-none"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? "切換為淺色模式" : "切換為深色模式"}>
            {theme === "dark" ? <IconSun className="size-4" /> : <IconMoon className="size-4" />}
          </Button>
        </SiteHeader>
        <div className="no-scrollbar flex flex-1 flex-col overflow-y-auto">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-1 flex-col py-4 md:py-6">
              <div className="flex-1 px-4 lg:px-6">
                {!isAuthenticated && (
                  <div className="flex min-h-[70vh] flex-col items-center justify-center gap-6 text-center">
                    <Image
                      src="/logo.png"
                      alt="Ziin Bot Logo"
                      width={220}
                      height={220}
                      className="h-40 w-40 md:h-56 md:w-56"
                      priority
                    />
                    <h1 className="text-4xl font-semibold tracking-tight md:text-6xl">Ziin Bot</h1>
                  </div>
                )}
                {showServerPicker && (
                  <div className="space-y-6">
                    <h2 className="text-4xl font-semibold tracking-tight">選擇伺服器</h2>
                    <div className="pr-1">
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
                        {managedServers.map((server) => (
                          <button
                            key={server.id}
                            type="button"
                            className="group relative h-40 overflow-hidden rounded-2xl border text-left transition hover:scale-[1.01] hover:border-primary/60"
                            disabled={isCheckingServerSelection}
                            onClick={() => {
                              void handleServerSelect(server);
                            }}>
                            <div
                              className="absolute inset-0 bg-slate-900"
                              style={
                                server.iconUrl
                                  ? {
                                      backgroundImage: `url(${server.iconUrl})`,
                                      backgroundSize: "cover",
                                      backgroundPosition: "center"
                                    }
                                  : undefined
                              }
                            />
                            {!server.iconUrl && (
                              <div
                                className="absolute inset-0"
                                style={{
                                  background:
                                    "linear-gradient(120deg, rgba(51,65,85,0.95) 0%, rgba(15,23,42,0.95) 45%, rgba(30,41,59,0.95) 100%)"
                                }}
                              />
                            )}
                            <div className="absolute inset-0 bg-black/55" />
                            <div className="relative flex h-full flex-col justify-between p-4 text-white">
                              {server.iconUrl ? (
                                <Image
                                  src={server.iconUrl}
                                  alt={server.name}
                                  width={40}
                                  height={40}
                                  className="h-10 w-10 rounded-md border border-white/35 object-cover"
                                />
                              ) : (
                                <div className="flex h-10 w-10 items-center justify-center rounded-md border border-white/35 bg-white/20 text-sm font-semibold">
                                  {server.name.slice(0, 1)}
                                </div>
                              )}
                              <div>
                                <p className="truncate text-2xl font-semibold">{server.name}</p>
                                <div className="mt-1">
                                  <p className="text-sm text-white/80">
                                    {server.owner ? "伺服器擁有者" : "伺服器管理員"}
                                  </p>
                                </div>
                              </div>
                            </div>
                          </button>
                        ))}
                        {managedServers.length === 0 && (
                          <div className="rounded-2xl border bg-card px-5 py-8 text-muted-foreground md:col-span-2 xl:col-span-3 2xl:col-span-4">
                            尚未找到可管理的伺服器
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {isAuthenticated && !showServerPicker && activeNavMain === "伺服器設定" && (
                  <div className="mx-auto mt-8 w-full max-w-[66.666%] space-y-5">
                    <h2 className="flex items-center gap-3 text-5xl font-semibold tracking-tight">
                      <IconSettings className="size-11" />
                      <span>伺服器設定</span>
                    </h2>
                    <div className="bg-border h-px w-full" />
                    <div className="grid grid-cols-2 gap-6 pt-4">
                      <div className="space-y-3">
                        <p className="text-muted-foreground text-sm font-medium tracking-wide uppercase">
                          伺服器自訂前綴
                        </p>
                        <div className="flex w-full max-w-[32rem] items-center gap-3">
                          <Input
                            className="!h-12 flex-1 rounded-lg bg-background/40 text-base"
                            placeholder="請輸入前綴，例如 !"
                            value={prefixInput}
                            onChange={(event) => setPrefixInput(event.target.value)}
                          />
                          <Button
                            className="!h-12 px-5"
                            onClick={handleSavePrefix}
                            disabled={isSavingPrefix || !prefixInput.trim()}>
                            {isSavingPrefix ? "儲存中..." : "確認"}
                          </Button>
                        </div>
                      </div>
                      <div />
                      <div className="space-y-3">
                        <p className="text-muted-foreground text-sm font-medium tracking-wide uppercase">
                          伺服器時區
                        </p>
                        <div className="flex w-full max-w-[32rem] items-center gap-3">
                          <div className="relative flex-1">
                            <Input
                              className="!h-12 w-full rounded-lg bg-background/40 text-base"
                              value={timezoneQuery}
                              placeholder="請輸入或搜尋時區，例如 UTC+8 Taipei"
                              onFocus={() => setShowTimezoneSuggestions(true)}
                              onBlur={() => {
                                window.setTimeout(() => setShowTimezoneSuggestions(false), 120);
                              }}
                              onChange={(event) => {
                                setTimezoneQuery(event.target.value);
                                setShowTimezoneSuggestions(true);
                              }}
                            />
                            {showTimezoneSuggestions && (
                              <div className="bg-popover no-scrollbar absolute z-40 mt-1 max-h-64 w-full overflow-y-auto rounded-md border shadow-md">
                                {filteredTimezoneOptions.length === 0 && (
                                  <div className="text-muted-foreground px-3 py-2 text-sm">找不到符合的時區</div>
                                )}
                                {filteredTimezoneOptions.map((timezone) => (
                                  <button
                                    key={timezone.value}
                                    type="button"
                                    className="hover:bg-accent block w-full px-3 py-2 text-left text-sm"
                                    onMouseDown={(event) => {
                                      event.preventDefault();
                                      selectTimezone(timezone);
                                    }}>
                                    {timezone.label}
                                  </button>
                                ))}
                              </div>
                            )}
                          </div>
                          <Button
                            className="!h-12 px-5"
                            disabled={!isTimezoneSelectionValid || isSavingTimezone}
                            onClick={handleSaveTimezone}>
                            {isSavingTimezone ? "儲存中..." : "確認"}
                          </Button>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <p className="text-muted-foreground text-sm font-medium tracking-wide uppercase">
                          伺服器語言
                        </p>
                        <div className="flex w-full max-w-[32rem] items-center gap-3">
                          <div className="flex-1">
                            <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                              <SelectTrigger className="!h-12 !w-full rounded-lg bg-background/40 text-base">
                                <SelectValue placeholder="請選擇語言" />
                              </SelectTrigger>
                              <SelectContent position="popper" side="bottom" align="start" sideOffset={6}>
                                {languageOptions.map((language) => (
                                  <SelectItem key={language.value} value={language.value}>
                                    {language.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <Button
                            className="!h-12 px-5"
                            disabled={!selectedLanguage || isSavingLanguage}
                            onClick={handleSaveLanguage}>
                            {isSavingLanguage ? "儲存中..." : "確認"}
                          </Button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {isAuthenticated && !showServerPicker && activeNavMain === "Log 系統" && (
                  <div className="mx-auto mt-8 w-full max-w-[66.666%] space-y-5">
                    <h2 className="flex items-center gap-3 text-5xl font-semibold tracking-tight">
                      <IconFileAnalytics className="size-11" />
                      <span>Log 系統</span>
                    </h2>
                    <div className="bg-border h-px w-full" />
                    <div className="rounded-xl border bg-card/40 p-4">
                      <h3 className="text-base font-semibold">事件通知頻道</h3>
                      <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                        {LOG_CHANNEL_TARGETS.map((target) => (
                          <div key={target.key} className="space-y-2">
                            <p className="text-muted-foreground text-sm">{target.label}</p>
                            <div className="relative">
                              <Input
                                className="!h-11 w-full rounded-lg bg-background/40 text-sm"
                                value={getChannelInputValue(`log:${target.key}`, logChannelTargets[target.key])}
                                placeholder="輸入頻道名稱篩選"
                                onFocus={() =>
                                  setShowChannelSuggestions((current) => ({
                                    ...current,
                                    [`log:${target.key}`]: true
                                  }))
                                }
                                onBlur={() => {
                                  window.setTimeout(
                                    () =>
                                      setShowChannelSuggestions((current) => ({
                                        ...current,
                                        [`log:${target.key}`]: false
                                      })),
                                    120
                                  );
                                }}
                                onChange={(event) => {
                                  const value = event.target.value;
                                  setChannelQueries((current) => ({
                                    ...current,
                                    [`log:${target.key}`]: value
                                  }));
                                  setLogChannelTargets((current) => ({
                                    ...current,
                                    [target.key]: ""
                                  }));
                                  setShowChannelSuggestions((current) => ({
                                    ...current,
                                    [`log:${target.key}`]: true
                                  }));
                                }}
                              />
                              {showChannelSuggestions[`log:${target.key}`] && (
                                <div className="bg-popover no-scrollbar absolute z-40 mt-1 max-h-64 w-full overflow-y-auto rounded-md border shadow-md">
                                  {getFilteredChannels(`log:${target.key}`).map((channel) => (
                                    <button
                                      key={channel.id}
                                      type="button"
                                      className="hover:bg-accent block w-full px-3 py-2 text-left text-sm"
                                      onMouseDown={(event) => {
                                        event.preventDefault();
                                        selectChannel(`log:${target.key}`, channel, (channelId) =>
                                          setLogChannelTargets((current) => ({
                                            ...current,
                                            [target.key]: channelId
                                          }))
                                        );
                                      }}>
                                      #{channel.name}
                                    </button>
                                  ))}
                                  {getFilteredChannels(`log:${target.key}`).length === 0 && (
                                    <div className="text-muted-foreground px-3 py-2 text-sm">找不到符合的頻道</div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="grid grid-cols-1 gap-4 pt-4 xl:grid-cols-2">
                      {logSections.map((section) => (
                        <div key={section.title} className="rounded-xl border bg-card/40 p-4">
                          <h3 className="text-base font-semibold">{section.title}</h3>
                          <div className="mt-3 space-y-2">
                            {section.items.map((item) => {
                              const isUnavailable = item.unavailable === true;

                              return (
                                <div
                                  key={item.key}
                                  className={`flex items-center justify-between rounded-md border px-3 py-2 ${
                                    isUnavailable
                                      ? "border-dashed border-muted-foreground/40 bg-muted/40"
                                      : "bg-background/40"
                                  }`}>
                                  <span className="text-sm">
                                    {item.label}
                                    {isUnavailable && (
                                      <span className="text-muted-foreground ml-2 text-xs">暫不開放</span>
                                    )}
                                  </span>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant={
                                      isUnavailable ? "secondary" : logSettings[item.key] ? "default" : "outline"
                                    }
                                    className="min-w-16"
                                    disabled={isUnavailable}
                                    onClick={() => toggleLogSetting(item.key)}>
                                    {isUnavailable ? "暫不開放" : logSettings[item.key] ? "開啟" : "關閉"}
                                  </Button>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      ))}
                    </div>
                    <div className="flex justify-end pt-2">
                      <Button
                        className="px-6"
                        onClick={handleSaveLogConfig}
                        disabled={isSavingLogConfig || !isLogChannelSelectionValid}>
                        {isSavingLogConfig ? "儲存中..." : "儲存 Log 設定"}
                      </Button>
                    </div>
                  </div>
                )}
                {isAuthenticated && !showServerPicker && activeNavMain === "Twitch" && (
                  <div className="mx-auto mt-8 w-full max-w-[66.666%] space-y-5">
                    <h2 className="flex items-center gap-3 text-5xl font-semibold tracking-tight">
                      <IconBrandTwitch className="size-11" />
                      <span>Twitch</span>
                    </h2>
                    <div className="bg-border h-px w-full" />
                    <div className="rounded-xl border bg-card/40 p-4">
                      <h3 className="text-base font-semibold">通知設定</h3>
                      <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知頻道</p>
                          <div className="relative">
                            <Input
                              className="!h-11 w-full rounded-lg bg-background/40 text-sm"
                              value={getChannelInputValue("twitch:notification", twitchNotificationChannel)}
                              placeholder="輸入頻道名稱篩選"
                              onFocus={() =>
                                setShowChannelSuggestions((current) => ({
                                  ...current,
                                  "twitch:notification": true
                                }))
                              }
                              onBlur={() => {
                                window.setTimeout(
                                  () =>
                                    setShowChannelSuggestions((current) => ({
                                      ...current,
                                      "twitch:notification": false
                                    })),
                                  120
                                );
                              }}
                              onChange={(event) => {
                                const value = event.target.value;
                                setChannelQueries((current) => ({
                                  ...current,
                                  "twitch:notification": value
                                }));
                                setTwitchNotificationChannel("");
                                setShowChannelSuggestions((current) => ({
                                  ...current,
                                  "twitch:notification": true
                                }));
                              }}
                            />
                            {showChannelSuggestions["twitch:notification"] && (
                              <div className="bg-popover no-scrollbar absolute z-40 mt-1 max-h-64 w-full overflow-y-auto rounded-md border shadow-md">
                                {getFilteredChannels("twitch:notification").map((channel) => (
                                  <button
                                    key={channel.id}
                                    type="button"
                                    className="hover:bg-accent block w-full px-3 py-2 text-left text-sm"
                                    onMouseDown={(event) => {
                                      event.preventDefault();
                                      selectChannel("twitch:notification", channel, setTwitchNotificationChannel);
                                    }}>
                                    #{channel.name}
                                  </button>
                                ))}
                                {getFilteredChannels("twitch:notification").length === 0 && (
                                  <div className="text-muted-foreground px-3 py-2 text-sm">找不到符合的頻道</div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知訊息模板</p>
                          <textarea
                            ref={twitchTemplateRef}
                            className="focus-visible:border-ring focus-visible:ring-ring/50 min-h-11 w-full resize-none overflow-hidden rounded-lg border bg-background/40 px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px]"
                            value={twitchNotificationText}
                            onChange={(event) => setTwitchNotificationText(event.target.value)}
                            onInput={autoResizeTemplateInput}
                            placeholder="例如：**{streamer}** is live now!! **{url}**"
                            rows={2}
                          />
                          <p className="text-muted-foreground text-xs">
                            {"{streamer}"} 會自動替換實況主名稱，{"{url}"} 會自動替換實況連結。
                          </p>
                          <Select onValueChange={(value) => insertRoleMention(value, setTwitchNotificationText)}>
                            <SelectTrigger className="!h-10 !w-full rounded-lg bg-background/40 text-sm">
                              <SelectValue placeholder="插入身分組提及（@Role）" />
                            </SelectTrigger>
                            <SelectContent position="popper" side="bottom" align="start" sideOffset={6}>
                              {serverRoles.map((role) => (
                                <SelectItem key={role.id} value={role.id}>
                                  @{role.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <div className="rounded-lg border bg-background/30 p-3">
                            <p className="text-muted-foreground text-xs">Discord 預覽</p>
                            <div className="mt-2 rounded-md border bg-card/60 p-3">
                              <div
                                className="break-all text-sm [&_a]:underline [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5"
                                dangerouslySetInnerHTML={{ __html: twitchTemplatePreviewHtml }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="rounded-xl border bg-card/40 p-4">
                      <h3 className="text-base font-semibold">追蹤名單</h3>
                      <div className="mt-3 flex gap-2">
                        <Input
                          className="!h-11 rounded-lg bg-background/40 text-sm"
                          value={newTwitchStreamer}
                          onChange={(event) => setNewTwitchStreamer(event.target.value)}
                          placeholder="輸入 Twitch 帳號，例如 din4ni"
                        />
                        <Button className="px-5" onClick={handleAddTwitchStreamer}>
                          新增
                        </Button>
                      </div>
                      <div className="mt-4 space-y-2">
                        {twitchStreamers.length === 0 && (
                          <p className="text-muted-foreground text-sm">尚未加入任何 Twitch 帳號</p>
                        )}
                        {twitchStreamers.map((streamer) => (
                          <div key={streamer} className="flex items-center justify-between rounded-md border px-3 py-2">
                            <div className="flex items-center gap-2">
                              {avatarFallbacks[`twitch:${streamer}`] ? (
                                <div className="bg-muted text-muted-foreground flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold">
                                  {streamer.slice(0, 1).toUpperCase()}
                                </div>
                              ) : !resolvedAvatars[`twitch:${streamer}`] ? (
                                <div className="bg-muted/60 h-8 w-8 rounded-full border" />
                              ) : (
                                <img
                                  src={resolvedAvatars[`twitch:${streamer}`]}
                                  alt={`${streamer} avatar`}
                                  className="h-8 w-8 rounded-full border object-cover"
                                  referrerPolicy="no-referrer"
                                  onError={() =>
                                    setAvatarFallbacks((current) => ({ ...current, [`twitch:${streamer}`]: true }))
                                  }
                                />
                              )}
                              <span className="text-sm">
                                {resolvedProfileNames[`twitch:${streamer}`] &&
                                resolvedProfileNames[`twitch:${streamer}`].toLowerCase() !== streamer.toLowerCase()
                                  ? `${resolvedProfileNames[`twitch:${streamer}`]} (${streamer})`
                                  : streamer}
                              </span>
                            </div>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              onClick={() => handleRemoveTwitchStreamer(streamer)}>
                              移除
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="flex justify-end pt-2">
                      <Button
                        className="px-6"
                        onClick={handleSaveTwitchSettings}
                        disabled={isSavingTwitchSettings || !isTwitchChannelSelectionValid}>
                        {isSavingTwitchSettings ? "儲存中..." : "儲存 Twitch 設定"}
                      </Button>
                    </div>
                  </div>
                )}
                {isAuthenticated && !showServerPicker && activeNavMain === "Twitter" && (
                  <div className="mx-auto mt-8 w-full max-w-[66.666%] space-y-5">
                    <h2 className="flex items-center gap-3 text-5xl font-semibold tracking-tight">
                      <IconBrandX className="size-11" />
                      <span>Twitter</span>
                    </h2>
                    <div className="bg-border h-px w-full" />
                    <div className="rounded-xl border bg-card/40 p-4">
                      <h3 className="text-base font-semibold">通知設定</h3>
                      <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知頻道</p>
                          <div className="relative">
                            <Input
                              className="!h-11 w-full rounded-lg bg-background/40 text-sm"
                              value={getChannelInputValue("twitter:notification", twitterNotificationChannel)}
                              placeholder="輸入頻道名稱篩選"
                              onFocus={() =>
                                setShowChannelSuggestions((current) => ({
                                  ...current,
                                  "twitter:notification": true
                                }))
                              }
                              onBlur={() => {
                                window.setTimeout(
                                  () =>
                                    setShowChannelSuggestions((current) => ({
                                      ...current,
                                      "twitter:notification": false
                                    })),
                                  120
                                );
                              }}
                              onChange={(event) => {
                                const value = event.target.value;
                                setChannelQueries((current) => ({
                                  ...current,
                                  "twitter:notification": value
                                }));
                                setTwitterNotificationChannel("");
                                setShowChannelSuggestions((current) => ({
                                  ...current,
                                  "twitter:notification": true
                                }));
                              }}
                            />
                            {showChannelSuggestions["twitter:notification"] && (
                              <div className="bg-popover no-scrollbar absolute z-40 mt-1 max-h-64 w-full overflow-y-auto rounded-md border shadow-md">
                                {getFilteredChannels("twitter:notification").map((channel) => (
                                  <button
                                    key={channel.id}
                                    type="button"
                                    className="hover:bg-accent block w-full px-3 py-2 text-left text-sm"
                                    onMouseDown={(event) => {
                                      event.preventDefault();
                                      selectChannel("twitter:notification", channel, setTwitterNotificationChannel);
                                    }}>
                                    #{channel.name}
                                  </button>
                                ))}
                                {getFilteredChannels("twitter:notification").length === 0 && (
                                  <div className="text-muted-foreground px-3 py-2 text-sm">找不到符合的頻道</div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知訊息模板</p>
                          <textarea
                            className="focus-visible:border-ring focus-visible:ring-ring/50 min-h-11 w-full resize-none overflow-hidden rounded-lg border bg-background/40 px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px]"
                            value={twitterNotificationText}
                            onChange={(event) => setTwitterNotificationText(event.target.value)}
                            placeholder="例如：**{xuser}** posted a new tweet! **{url}**"
                            rows={2}
                          />
                          <p className="text-muted-foreground text-xs">
                            {"{xuser}"} 會自動替換帳號名稱，{"{url}"} 會自動替換貼文連結。
                          </p>
                          <Select onValueChange={(value) => insertRoleMention(value, setTwitterNotificationText)}>
                            <SelectTrigger className="!h-10 !w-full rounded-lg bg-background/40 text-sm">
                              <SelectValue placeholder="插入身分組提及（@Role）" />
                            </SelectTrigger>
                            <SelectContent position="popper" side="bottom" align="start" sideOffset={6}>
                              {serverRoles.map((role) => (
                                <SelectItem key={role.id} value={role.id}>
                                  @{role.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <div className="rounded-lg border bg-background/30 p-3">
                            <p className="text-muted-foreground text-xs">Discord 預覽</p>
                            <div className="mt-2 rounded-md border bg-card/60 p-3">
                              <div
                                className="break-all text-sm [&_a]:underline [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5"
                                dangerouslySetInnerHTML={{ __html: twitterTemplatePreviewHtml }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="rounded-xl border bg-card/40 p-4">
                      <h3 className="text-base font-semibold">追蹤帳號</h3>
                      <div className="mt-3 flex gap-2">
                        <Input
                          className="!h-11 rounded-lg bg-background/40 text-sm"
                          value={newTwitterAccount}
                          onChange={(event) => setNewTwitterAccount(event.target.value)}
                          placeholder="輸入 @handle 或 https://x.com/handle"
                        />
                        <Button className="px-5" onClick={handleAddTwitterAccount}>
                          新增
                        </Button>
                      </div>
                      <div className="mt-4 space-y-2">
                        {twitterAccounts.length === 0 && (
                          <p className="text-muted-foreground text-sm">尚未加入任何 Twitter 帳號</p>
                        )}
                        {twitterAccounts.map((account) => (
                          <div key={account.id} className="flex items-center justify-between rounded-md border px-3 py-2">
                            <div className="flex items-center gap-2">
                              <div className="bg-muted text-muted-foreground flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold">
                                {(resolvedTwitterHandles[`twitter:${account.id}`] || account.id)
                                  .slice(0, 1)
                                  .toUpperCase()}
                              </div>
                              <div>
                                <p className="text-sm font-semibold">
                                  {resolvedProfileNames[`twitter:${account.id}`] || account.name || account.id}
                                </p>
                                <p className="text-muted-foreground text-xs">
                                  @{resolvedTwitterHandles[`twitter:${account.id}`] || account.id}
                                </p>
                              </div>
                            </div>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              onClick={() => handleRemoveTwitterAccount(account.id)}>
                              移除
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="flex justify-end pt-2">
                      <Button
                        className="px-6"
                        onClick={handleSaveTwitterSettings}
                        disabled={isSavingTwitterSettings || !isTwitterChannelSelectionValid}>
                        {isSavingTwitterSettings ? "儲存中..." : "儲存 Twitter 設定"}
                      </Button>
                    </div>
                  </div>
                )}
                {isAuthenticated && !showServerPicker && activeNavMain === "YouTube" && (
                  <div className="mx-auto mt-8 w-full max-w-[66.666%] space-y-5">
                    <h2 className="flex items-center gap-3 text-5xl font-semibold tracking-tight">
                      <IconBrandYoutube className="size-11" />
                      <span>YouTube</span>
                    </h2>
                    <div className="bg-border h-px w-full" />
                    <div className="rounded-xl border bg-card/40 p-4">
                      <h3 className="text-base font-semibold">通知設定</h3>
                      <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知頻道</p>
                          <div className="relative">
                            <Input
                              className="!h-11 w-full rounded-lg bg-background/40 text-sm"
                              value={getChannelInputValue("youtube:notification", youtubeNotificationChannel)}
                              placeholder="輸入頻道名稱篩選"
                              onFocus={() =>
                                setShowChannelSuggestions((current) => ({
                                  ...current,
                                  "youtube:notification": true
                                }))
                              }
                              onBlur={() => {
                                window.setTimeout(
                                  () =>
                                    setShowChannelSuggestions((current) => ({
                                      ...current,
                                      "youtube:notification": false
                                    })),
                                  120
                                );
                              }}
                              onChange={(event) => {
                                const value = event.target.value;
                                setChannelQueries((current) => ({
                                  ...current,
                                  "youtube:notification": value
                                }));
                                setYouTubeNotificationChannel("");
                                setShowChannelSuggestions((current) => ({
                                  ...current,
                                  "youtube:notification": true
                                }));
                              }}
                            />
                            {showChannelSuggestions["youtube:notification"] && (
                              <div className="bg-popover no-scrollbar absolute z-40 mt-1 max-h-64 w-full overflow-y-auto rounded-md border shadow-md">
                                {getFilteredChannels("youtube:notification").map((channel) => (
                                  <button
                                    key={channel.id}
                                    type="button"
                                    className="hover:bg-accent block w-full px-3 py-2 text-left text-sm"
                                    onMouseDown={(event) => {
                                      event.preventDefault();
                                      selectChannel("youtube:notification", channel, setYouTubeNotificationChannel);
                                    }}>
                                    #{channel.name}
                                  </button>
                                ))}
                                {getFilteredChannels("youtube:notification").length === 0 && (
                                  <div className="text-muted-foreground px-3 py-2 text-sm">找不到符合的頻道</div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知訊息模板</p>
                          <textarea
                            ref={youtubeTemplateRef}
                            className="focus-visible:border-ring focus-visible:ring-ring/50 min-h-11 w-full resize-none overflow-hidden rounded-lg border bg-background/40 px-3 py-2 text-sm shadow-xs transition-[color,box-shadow] outline-none focus-visible:ring-[3px]"
                            value={youtubeNotificationText}
                            onChange={(event) => setYouTubeNotificationText(event.target.value)}
                            onInput={autoResizeTemplateInput}
                            placeholder="例如：**{ytber}** upload a video!! **{url}**"
                            rows={2}
                          />
                          <p className="text-muted-foreground text-xs">
                            {"{ytber}"} 會自動替換 YouTuber 名稱，{"{url}"} 會自動替換影片連結。
                          </p>
                          <Select onValueChange={(value) => insertRoleMention(value, setYouTubeNotificationText)}>
                            <SelectTrigger className="!h-10 !w-full rounded-lg bg-background/40 text-sm">
                              <SelectValue placeholder="插入身分組提及（@Role）" />
                            </SelectTrigger>
                            <SelectContent position="popper" side="bottom" align="start" sideOffset={6}>
                              {serverRoles.map((role) => (
                                <SelectItem key={role.id} value={role.id}>
                                  @{role.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <div className="rounded-lg border bg-background/30 p-3">
                            <p className="text-muted-foreground text-xs">Discord 預覽</p>
                            <div className="mt-2 rounded-md border bg-card/60 p-3">
                              <div
                                className="break-all text-sm [&_a]:underline [&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5"
                                dangerouslySetInnerHTML={{ __html: youtubeTemplatePreviewHtml }}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    <div className="rounded-xl border bg-card/40 p-4">
                      <h3 className="text-base font-semibold">追蹤頻道</h3>
                      <div className="mt-3 flex gap-2">
                        <Input
                          className="!h-11 rounded-lg bg-background/40 text-sm"
                          value={newYouTubeChannelInput}
                          onChange={(event) => setNewYouTubeChannelInput(event.target.value)}
                          placeholder="貼上 YouTube 頻道網址（例如 https://youtube.com/@name）"
                        />
                        <Button
                          className="px-5"
                          onClick={() => void handleAddYouTubeSubscription()}
                          disabled={isResolvingYouTubeChannel}>
                          {isResolvingYouTubeChannel ? "解析中..." : "新增"}
                        </Button>
                      </div>
                      <div className="mt-4 space-y-2">
                        {youtubeSubscriptions.length === 0 && (
                          <p className="text-muted-foreground text-sm">尚未加入任何 YouTube 頻道</p>
                        )}
                        {youtubeSubscriptions.map((subscription) => (
                          <div key={subscription.id} className="flex items-center justify-between rounded-md border px-3 py-2">
                            <div className="flex items-center gap-2">
                              {avatarFallbacks[`youtube:${subscription.id}`] ? (
                                <div className="bg-muted text-muted-foreground flex h-8 w-8 items-center justify-center rounded-full text-xs font-semibold">
                                  {(subscription.name || subscription.id).slice(0, 1).toUpperCase()}
                                </div>
                              ) : !resolvedAvatars[`youtube:${subscription.id}`] ? (
                                <div className="bg-muted/60 h-8 w-8 rounded-full border" />
                              ) : (
                                <img
                                  src={resolvedAvatars[`youtube:${subscription.id}`]}
                                  alt={`${subscription.name || subscription.id} avatar`}
                                  className="h-8 w-8 rounded-full border object-cover"
                                  referrerPolicy="no-referrer"
                                  onError={() =>
                                    setAvatarFallbacks((current) => ({
                                      ...current,
                                      [`youtube:${subscription.id}`]: true
                                    }))
                                  }
                                />
                              )}
                              <div>
                              <p className="text-sm font-semibold">{subscription.name || subscription.id}</p>
                              <p className="text-muted-foreground text-xs">{subscription.id}</p>
                              </div>
                            </div>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              onClick={() => handleRemoveYouTubeSubscription(subscription.id)}>
                              移除
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="flex justify-end pt-2">
                      <Button
                        className="px-6"
                        onClick={handleSaveYouTubeSettings}
                        disabled={isSavingYouTubeSettings || !isYouTubeChannelSelectionValid}>
                        {isSavingYouTubeSettings ? "儲存中..." : "儲存 YouTube 設定"}
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        {showBotInviteModal && (
          <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4">
            <div className="relative w-full max-w-xl rounded-2xl border bg-card px-8 py-9 shadow-2xl">
              <button
                type="button"
                aria-label="關閉提示"
                className="text-muted-foreground hover:text-foreground absolute top-4 right-4 rounded-md p-1"
                onClick={() => setShowBotInviteModal(false)}>
                <IconX className="size-5" />
              </button>
              <h3 className="text-center text-2xl font-semibold">機器人尚未加入伺服器</h3>
              <p className="text-muted-foreground mt-4 text-center text-base leading-relaxed">
                Ziin 尚未加入 {botInviteServerName} ，請先邀請機器人再進行設定。
              </p>
              <div className="mt-7 flex items-center justify-center gap-3">
                <Button
                  className="h-12 px-8 text-base"
                  disabled={!botInviteUrl}
                  onClick={() => {
                    if (!botInviteUrl) {
                      return;
                    }
                    const width = 560;
                    const height = 760;
                    const left = Math.max(0, Math.floor(window.screenX + (window.outerWidth - width) / 2));
                    const top = Math.max(0, Math.floor(window.screenY + (window.outerHeight - height) / 2));
                    const popup = window.open(
                      botInviteUrl,
                      "ziinBotInvite",
                      [
                        "popup=yes",
                        `width=${width}`,
                        `height=${height}`,
                        `left=${left}`,
                        `top=${top}`,
                        "menubar=no",
                        "toolbar=no",
                        "location=yes",
                        "status=no",
                        "scrollbars=yes",
                        "resizable=yes",
                        "noopener",
                        "noreferrer"
                      ].join(",")
                    );
                    if (!popup) {
                      window.open(botInviteUrl, "_blank", "noopener,noreferrer");
                    }
                  }}>
                  邀請機器人
                </Button>
              </div>
            </div>
          </div>
        )}
      </SidebarInset>

    </SidebarProvider>
  );
}
