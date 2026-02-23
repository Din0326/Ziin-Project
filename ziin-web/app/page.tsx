"use client";

import * as React from "react";
import Image from "next/image";
import { IconMoon, IconSun } from "@tabler/icons-react";
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

export default function Page() {
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
          { key: "messageDeleteBulk", label: "大量刪除訊息" },
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
    } catch {
      toast.error("儲存失敗，請檢查網路後再試");
    } finally {
      setIsSavingLogSettings(false);
    }
  };

  const handleLoginClick = () => {
    void signIn("discord", { callbackUrl: "/" });
  };

  const handleLogoutClick = () => {
    void signOut({ callbackUrl: "/" });
  };

  const isAuthenticated = status === "authenticated";
  const showServerPicker = status === "authenticated" && !selectedServerId;
  const [theme, setTheme] = React.useState<"light" | "dark">("light");

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
        return;
      }

      const result = (await response.json()) as {
        settings: {
          prefix?: unknown;
          timezone?: unknown;
          language?: unknown;
        } | null;
      };
      const data = result.settings;
      if (!data) {
        setPrefixInput("");
        setSelectedTimezone(undefined);
        setTimezoneQuery("");
        setSelectedLanguage(undefined);
        return;
      }

      setPrefixInput(typeof data.prefix === "string" ? data.prefix : "");

      if (typeof data.timezone === "string") {
        const matchedTimezone = timezoneOptions.find((timezone) => {
          if (timezone.value === data.timezone || timezone.label === data.timezone) {
            return true;
          }
          return false;
        });
        setSelectedTimezone(matchedTimezone?.value);
        setTimezoneQuery(matchedTimezone?.label ?? data.timezone);
      } else {
        setSelectedTimezone(undefined);
        setTimezoneQuery("");
      }

      if (typeof data.language === "string") {
        if (data.language === "zh-TW") {
          setSelectedLanguage("zh-TW");
        } else if (data.language === "en") {
          setSelectedLanguage("English");
        } else if (data.language === "繁體中文") {
          setSelectedLanguage("zh-TW");
        } else {
          setSelectedLanguage(data.language);
        }
      } else {
        setSelectedLanguage(undefined);
      }
    };

    void loadServerSettings();

    return () => {
      active = false;
    };
  }, [selectedServerId, timezoneOptions]);

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
    };

    void loadLogSettings();

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
        onNavMainClick={setActiveNavMain}
        onSwitchServer={() => setSelectedServerId(undefined)}
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
                            onClick={() => {
                              setSelectedServerId(server.id);
                              setActiveNavMain("伺服器設定");
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
                    <h2 className="text-5xl font-semibold tracking-tight">伺服器設定</h2>
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
                    <h2 className="text-5xl font-semibold tracking-tight">Log 系統</h2>
                    <div className="bg-border h-px w-full" />
                    <div className="grid grid-cols-1 gap-4 pt-4 xl:grid-cols-2">
                      {logSections.map((section) => (
                        <div key={section.title} className="rounded-xl border bg-card/40 p-4">
                          <h3 className="text-base font-semibold">{section.title}</h3>
                          <div className="mt-3 space-y-2">
                            {section.items.map((item) => (
                              <div
                                key={item.key}
                                className="flex items-center justify-between rounded-md border bg-background/40 px-3 py-2">
                                <span className="text-sm">{item.label}</span>
                                <Button
                                  type="button"
                                  size="sm"
                                  variant={logSettings[item.key] ? "default" : "outline"}
                                  className="min-w-16"
                                  onClick={() => toggleLogSetting(item.key)}>
                                  {logSettings[item.key] ? "開啟" : "關閉"}
                                </Button>
                              </div>
                            ))}
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
              </div>
            </div>
          </div>
        </div>
      </SidebarInset>

    </SidebarProvider>
  );
}
