"use client";

import * as React from "react";
import Image from "next/image";
import {
  IconBrandTwitch,
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
  const [isSavingPrefix, setIsSavingPrefix] = React.useState(false);
  const [isSavingTimezone, setIsSavingTimezone] = React.useState(false);
  const [isSavingLanguage, setIsSavingLanguage] = React.useState(false);
  const [logSettings, setLogSettings] = React.useState<Record<string, boolean>>(DEFAULT_LOG_SETTINGS);
  const [isSavingLogSettings, setIsSavingLogSettings] = React.useState(false);
  const [serverChannels, setServerChannels] = React.useState<Array<{ id: string; name: string }>>([]);
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
  const [isSavingLogChannels, setIsSavingLogChannels] = React.useState(false);
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
  const [youtubeNotificationChannel, setYouTubeNotificationChannel] = React.useState("");
  const [youtubeNotificationText, setYouTubeNotificationText] = React.useState(DEFAULT_YOUTUBE_NOTIFICATION_TEXT);
  const [youtubeSubscriptions, setYouTubeSubscriptions] = React.useState<YouTubeSubscription[]>([]);
  const [newYouTubeChannelInput, setNewYouTubeChannelInput] = React.useState("");
  const [isResolvingYouTubeChannel, setIsResolvingYouTubeChannel] = React.useState(false);
  const [isSavingYouTubeSettings, setIsSavingYouTubeSettings] = React.useState(false);
  const [savedTwitchSettings, setSavedTwitchSettings] = React.useState<TwitchSettingsSnapshot>({
    channel: "",
    text: DEFAULT_TWITCH_NOTIFICATION_TEXT,
    streamers: []
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
    if (!selectedServerId) {
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

  const handleSaveLogSettings = async () => {
    if (!selectedServerId) {
      return;
    }

    setIsSavingLogSettings(true);
    try {
      const response = await fetch(`/api/log-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ settings: logSettings })
      });
      if (!response.ok) {
        let errorMessage = "儲存失敗，請稍後再試";
        try {
          const errorData = (await response.json()) as { error?: unknown; message?: unknown };
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
      toast.success("Log 設定儲存成功");
      setSavedLogSettings(logSettings);
    } catch {
      toast.error("儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingLogSettings(false);
    }
  };

  const handleSaveLogChannels = async () => {
    if (!selectedServerId) {
      return;
    }

    setIsSavingLogChannels(true);
    try {
      const response = await fetch(`/api/server-settings/${selectedServerId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          guildLogId: logChannelTargets.guildLogId || null,
          memberLogId: logChannelTargets.memberLogId || null,
          messageLogId: logChannelTargets.messageLogId || null,
          voiceLogId: logChannelTargets.voiceLogId || null
        })
      });

      if (!response.ok) {
        let errorMessage = "儲存失敗，請稍後再試";
        try {
          const errorData = (await response.json()) as { error?: unknown; message?: unknown };
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

      toast.success("Log 頻道儲存成功");
      setSavedLogChannelTargets(logChannelTargets);
    } catch {
      toast.error("儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingLogChannels(false);
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

  const handleSaveTwitchSettings = async () => {
    if (!selectedServerId) {
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
    void signIn("discord", { callbackUrl: "/" });
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
  const isYouTubeDirty = React.useMemo(() => {
    const currentIds = youtubeSubscriptions.map((item) => item.id).sort();
    return (
      youtubeNotificationChannel !== savedYouTubeSettings.channel ||
      youtubeNotificationText !== savedYouTubeSettings.text ||
      JSON.stringify(currentIds) !== JSON.stringify(savedYouTubeSettings.subscriptionIds)
    );
  }, [savedYouTubeSettings, youtubeNotificationChannel, youtubeNotificationText, youtubeSubscriptions]);

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
    if (activeNavMain === "YouTube") {
      return isYouTubeDirty;
    }
    return false;
  }, [activeNavMain, isLogChannelsDirty, isLogSettingsDirty, isServerSettingsDirty, isTwitchDirty, isYouTubeDirty]);

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
      setShowBotInviteModal(false);
      setBotInviteUrl("");
      setBotInviteServerName("");
      setLogChannelTargets({
        memberLogId: "",
        guildLogId: "",
        messageLogId: "",
        voiceLogId: ""
      });
      setTwitchNotificationChannel("");
      setTwitchNotificationText(DEFAULT_TWITCH_NOTIFICATION_TEXT);
      setTwitchStreamers([]);
      setNewTwitchStreamer("");
      setYouTubeNotificationChannel("");
      setYouTubeNotificationText(DEFAULT_YOUTUBE_NOTIFICATION_TEXT);
      setYouTubeSubscriptions([]);
      setNewYouTubeChannelInput("");
      return;
    }

    let active = true;

    const loadServerSettings = async () => {
      const response = await fetch(`/api/server-settings/${selectedServerId}`, {
        method: "GET"
      });
      if (!active || !response.ok) {
        setPrefixInput("");
        setSelectedTimezone(undefined);
        setTimezoneQuery("");
        setSelectedLanguage(undefined);
        setLogChannelTargets({
          memberLogId: "",
          guildLogId: "",
          messageLogId: "",
          voiceLogId: ""
        });
        return;
      }

      const result = (await response.json()) as {
        settings: {
          prefix?: unknown;
          timezone?: unknown;
          language?: unknown;
          guildLogId?: unknown;
          memberLogId?: unknown;
          messageLogId?: unknown;
          voiceLogId?: unknown;
        } | null;
      };
      const data = result.settings;
      if (!data) {
        setPrefixInput("");
        setSelectedTimezone(undefined);
        setTimezoneQuery("");
        setSelectedLanguage(undefined);
        setLogChannelTargets({
          memberLogId: "",
          guildLogId: "",
          messageLogId: "",
          voiceLogId: ""
        });
        return;
      }

      setPrefixInput(typeof data.prefix === "string" ? data.prefix : "");
      let normalizedTimezoneValue: string | undefined;

      if (typeof data.timezone === "string") {
        const timezoneIdFromValue =
          data.timezone
            .split(/\s+/)
            .find((part) => part.includes("/") && part.length > 3) ?? null;
        const matchedTimezone = timezoneOptions.find((timezone) => {
          if (timezone.value === data.timezone || timezone.label === data.timezone) {
            return true;
          }
          if (timezoneIdFromValue && timezone.value === timezoneIdFromValue) {
            return true;
          }
          return false;
        });
        normalizedTimezoneValue = matchedTimezone?.value;
        setSelectedTimezone(matchedTimezone?.value);
        setTimezoneQuery(matchedTimezone?.label ?? data.timezone);
      } else {
        setSelectedTimezone(undefined);
        setTimezoneQuery("");
      }

      let normalizedLanguage: string | undefined;
      if (typeof data.language === "string") {
        if (data.language === "zh-TW") {
          normalizedLanguage = "zh-TW";
        } else if (data.language === "en") {
          normalizedLanguage = "English";
        } else if (data.language === "繁體中文") {
          normalizedLanguage = "zh-TW";
        } else {
          normalizedLanguage = data.language;
        }
        setSelectedLanguage(normalizedLanguage);
      } else {
        setSelectedLanguage(undefined);
      }

      setLogChannelTargets({
        guildLogId: typeof data.guildLogId === "string" ? data.guildLogId : "",
        memberLogId: typeof data.memberLogId === "string" ? data.memberLogId : "",
        messageLogId: typeof data.messageLogId === "string" ? data.messageLogId : "",
        voiceLogId: typeof data.voiceLogId === "string" ? data.voiceLogId : ""
      });
      setSavedServerSettings({
        prefix: typeof data.prefix === "string" ? data.prefix : "",
        timezone: normalizedTimezoneValue,
        language: normalizedLanguage
      });
      setSavedLogChannelTargets({
        guildLogId: typeof data.guildLogId === "string" ? data.guildLogId : "",
        memberLogId: typeof data.memberLogId === "string" ? data.memberLogId : "",
        messageLogId: typeof data.messageLogId === "string" ? data.messageLogId : "",
        voiceLogId: typeof data.voiceLogId === "string" ? data.voiceLogId : ""
      });
    };

    void loadServerSettings();

    return () => {
      active = false;
    };
  }, [selectedServerId, timezoneOptions]);

  React.useEffect(() => {
    if (!selectedServerId) {
      setServerChannels([]);
      return;
    }

    let active = true;

    const loadChannels = async () => {
      const response = await fetch(`/api/discord/guild-channels/${selectedServerId}`, {
        method: "GET"
      });

      if (!active || !response.ok) {
        setServerChannels([]);
        return;
      }

      const result = (await response.json()) as {
        channels?: Array<{ id: string; name: string }> | null;
      };

      setServerChannels(Array.isArray(result.channels) ? result.channels : []);
    };

    void loadChannels();

    return () => {
      active = false;
    };
  }, [selectedServerId]);

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
    if (!selectedServerId) {
      setLogSettings(DEFAULT_LOG_SETTINGS);
      return;
    }

    let active = true;

    const loadLogSettings = async () => {
      const response = await fetch(`/api/log-settings/${selectedServerId}`, {
        method: "GET"
      });
      if (!active || !response.ok) {
        setLogSettings(DEFAULT_LOG_SETTINGS);
        return;
      }

      const result = (await response.json()) as { settings?: Record<string, unknown> | null };
      const data = result.settings;
      if (!data) {
        setLogSettings(DEFAULT_LOG_SETTINGS);
        return;
      }

      const nextSettings: Record<string, boolean> = { ...DEFAULT_LOG_SETTINGS };
      for (const key of Object.keys(DEFAULT_LOG_SETTINGS)) {
        if (typeof data[key] === "boolean") {
          nextSettings[key] = data[key] as boolean;
        }
      }
      setLogSettings(nextSettings);
      setSavedLogSettings(nextSettings);
    };

    void loadLogSettings();

    return () => {
      active = false;
    };
  }, [selectedServerId]);

  React.useEffect(() => {
    if (!selectedServerId) {
      setTwitchNotificationChannel("");
      setTwitchNotificationText(DEFAULT_TWITCH_NOTIFICATION_TEXT);
      setTwitchStreamers([]);
      return;
    }

    let active = true;

    const loadTwitchSettings = async () => {
      const response = await fetch(`/api/twitch-settings/${selectedServerId}`, { method: "GET" });
      if (!active || !response.ok) {
        return;
      }

      const result = (await response.json()) as {
        settings?: {
          twitchNotificationChannel?: unknown;
          twitchNotificationText?: unknown;
          allStreamers?: unknown;
        } | null;
      };
      const data = result.settings;
      if (!data) {
        return;
      }

      setTwitchNotificationChannel(typeof data.twitchNotificationChannel === "string" ? data.twitchNotificationChannel : "");
      setTwitchNotificationText(
        typeof data.twitchNotificationText === "string"
          ? data.twitchNotificationText
          : DEFAULT_TWITCH_NOTIFICATION_TEXT
      );
      setTwitchStreamers(
        Array.isArray(data.allStreamers) ? data.allStreamers.filter((item): item is string => typeof item === "string") : []
      );
      setSavedTwitchSettings({
        channel: typeof data.twitchNotificationChannel === "string" ? data.twitchNotificationChannel : "",
        text:
          typeof data.twitchNotificationText === "string"
            ? data.twitchNotificationText
            : DEFAULT_TWITCH_NOTIFICATION_TEXT,
        streamers: Array.isArray(data.allStreamers)
          ? data.allStreamers.filter((item): item is string => typeof item === "string")
          : []
      });
    };

    void loadTwitchSettings();

    return () => {
      active = false;
    };
  }, [selectedServerId]);

  React.useEffect(() => {
    if (!selectedServerId) {
      setYouTubeNotificationChannel("");
      setYouTubeNotificationText(DEFAULT_YOUTUBE_NOTIFICATION_TEXT);
      setYouTubeSubscriptions([]);
      return;
    }

    let active = true;

    const loadYouTubeSettings = async () => {
      const response = await fetch(`/api/youtube-settings/${selectedServerId}`, { method: "GET" });
      if (!active || !response.ok) {
        return;
      }

      const result = (await response.json()) as {
        settings?: {
          youtubeNotificationChannel?: unknown;
          youtubeNotificationText?: unknown;
          youtubers?: unknown;
        } | null;
      };
      const data = result.settings;
      if (!data) {
        return;
      }

      setYouTubeNotificationChannel(typeof data.youtubeNotificationChannel === "string" ? data.youtubeNotificationChannel : "");
      setYouTubeNotificationText(
        typeof data.youtubeNotificationText === "string"
          ? data.youtubeNotificationText
          : DEFAULT_YOUTUBE_NOTIFICATION_TEXT
      );
      setYouTubeSubscriptions(
        Array.isArray(data.youtubers)
          ? data.youtubers
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
          : []
      );
      setSavedYouTubeSettings({
        channel: typeof data.youtubeNotificationChannel === "string" ? data.youtubeNotificationChannel : "",
        text:
          typeof data.youtubeNotificationText === "string"
            ? data.youtubeNotificationText
            : DEFAULT_YOUTUBE_NOTIFICATION_TEXT,
        subscriptionIds: Array.isArray(data.youtubers)
          ? data.youtubers
              .filter((item): item is Record<string, unknown> => typeof item === "object" && item !== null)
              .map((item) => (typeof item.id === "string" ? item.id : ""))
              .filter((id) => id.length > 0)
              .sort()
          : []
      });
    };

    void loadYouTubeSettings();

    return () => {
      active = false;
    };
  }, [selectedServerId]);

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
                          <Button className="!h-12 px-5" onClick={handleSavePrefix} disabled={isSavingPrefix}>
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
                            <Select
                              value={logChannelTargets[target.key] || "__none__"}
                              onValueChange={(value) =>
                                setLogChannelTargets((current) => ({
                                  ...current,
                                  [target.key]: value === "__none__" ? "" : value
                                }))
                              }>
                              <SelectTrigger className="!h-11 !w-full rounded-lg bg-background/40 text-sm">
                                <SelectValue placeholder="請選擇頻道" />
                              </SelectTrigger>
                              <SelectContent position="popper" side="bottom" align="start" sideOffset={6}>
                                <SelectItem value="__none__">不使用</SelectItem>
                                {serverChannels.map((channel) => (
                                  <SelectItem key={channel.id} value={channel.id}>
                                    #{channel.name}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 flex justify-end">
                        <Button className="px-6" onClick={handleSaveLogChannels} disabled={isSavingLogChannels}>
                          {isSavingLogChannels ? "儲存中..." : "儲存頻道設定"}
                        </Button>
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
                      <Button className="px-6" onClick={handleSaveLogSettings} disabled={isSavingLogSettings}>
                        {isSavingLogSettings ? "儲存中..." : "儲存所有設定"}
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
                          <Select
                            value={twitchNotificationChannel || "__none__"}
                            onValueChange={(value) =>
                              setTwitchNotificationChannel(value === "__none__" ? "" : value)
                            }>
                            <SelectTrigger className="!h-11 !w-full rounded-lg bg-background/40 text-sm">
                              <SelectValue placeholder="請選擇頻道" />
                            </SelectTrigger>
                            <SelectContent position="popper" side="bottom" align="start" sideOffset={6}>
                              <SelectItem value="__none__">不使用</SelectItem>
                              {serverChannels.map((channel) => (
                                <SelectItem key={channel.id} value={channel.id}>
                                  #{channel.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知訊息模板</p>
                          <Input
                            className="!h-11 rounded-lg bg-background/40 text-sm"
                            value={twitchNotificationText}
                            onChange={(event) => setTwitchNotificationText(event.target.value)}
                            placeholder="例如：**{streamer}** is live now!! **{url}**"
                          />
                          <p className="text-muted-foreground text-xs">
                            {"{streamer}"} 會自動替換實況主名稱，{"{url}"} 會自動替換實況連結。
                          </p>
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
                      <Button className="px-6" onClick={handleSaveTwitchSettings} disabled={isSavingTwitchSettings}>
                        {isSavingTwitchSettings ? "儲存中..." : "儲存 Twitch 設定"}
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
                          <Select
                            value={youtubeNotificationChannel || "__none__"}
                            onValueChange={(value) =>
                              setYouTubeNotificationChannel(value === "__none__" ? "" : value)
                            }>
                            <SelectTrigger className="!h-11 !w-full rounded-lg bg-background/40 text-sm">
                              <SelectValue placeholder="請選擇頻道" />
                            </SelectTrigger>
                            <SelectContent position="popper" side="bottom" align="start" sideOffset={6}>
                              <SelectItem value="__none__">不使用</SelectItem>
                              {serverChannels.map((channel) => (
                                <SelectItem key={channel.id} value={channel.id}>
                                  #{channel.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="space-y-2">
                          <p className="text-muted-foreground text-sm">通知訊息模板</p>
                          <Input
                            className="!h-11 rounded-lg bg-background/40 text-sm"
                            value={youtubeNotificationText}
                            onChange={(event) => setYouTubeNotificationText(event.target.value)}
                            placeholder="例如：**{ytber}** upload a video!! **{url}**"
                          />
                          <p className="text-muted-foreground text-xs">
                            {"{ytber}"} 會自動替換 YouTuber 名稱，{"{url}"} 會自動替換影片連結。
                          </p>
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
                      <Button className="px-6" onClick={handleSaveYouTubeSettings} disabled={isSavingYouTubeSettings}>
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
                <a href={botInviteUrl}>
                  <Button className="h-12 px-8 text-base" disabled={!botInviteUrl}>
                    邀請機器人
                  </Button>
                </a>
              </div>
            </div>
          </div>
        )}
      </SidebarInset>

    </SidebarProvider>
  );
}
