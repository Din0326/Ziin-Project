"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { signOut, useSession } from "next-auth/react";

export default function HomePage() {
  const { data: session, status } = useSession();
  const isAuthenticated = status === "authenticated";
  const [menuOpen, setMenuOpen] = React.useState(false);
  const authTabRef = React.useRef<Window | null>(null);
  const authFlowRef = React.useRef(false);
  const router = useRouter();

  React.useEffect(() => {
    const isAuthTab = window.name === "ziin-auth-tab";
    if (isAuthTab && window.opener && !window.opener.closed) {
      window.location.replace("/auth/popup-close");
      return;
    }

    const params = new URLSearchParams(window.location.search);
    const error = params.get("error");
    const callbackUrl = params.get("callbackUrl") ?? "";
    const isPopupFlow = callbackUrl.includes("/auth/popup-close");
    if (!error || !isPopupFlow) {
      return;
    }
    window.location.replace("/auth/popup-close");
  }, [router]);

  const syncSessionAfterAuth = React.useCallback(async () => {
    try {
      const resp = await fetch("/api/auth/session", { method: "GET", cache: "no-store" });
      if (resp.ok) {
        const sessionData = (await resp.json()) as { user?: unknown } | null;
        if (sessionData?.user) {
          authFlowRef.current = false;
          router.push("/dashboard");
          return;
        }
      }
    } catch {
      // ignore transient session fetch errors
    }
    authFlowRef.current = false;
    router.refresh();
  }, [router]);

  React.useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.origin !== window.location.origin) {
        return;
      }
      if (!event.data || event.data.type !== "ziin-auth-finished") {
        return;
      }
      void syncSessionAfterAuth();
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [syncSessionAfterAuth]);

  React.useEffect(() => {
    const timer = window.setInterval(() => {
      if (!authFlowRef.current) {
        return;
      }
      const tab = authTabRef.current;
      if (!tab) {
        return;
      }
      if (!tab.closed) {
        return;
      }
      authTabRef.current = null;
      void syncSessionAfterAuth();
    }, 350);

    return () => window.clearInterval(timer);
  }, [syncSessionAfterAuth]);
  const openNewTab = React.useCallback((url: string) => {
    const tab = window.open(url, "ziin-auth-tab");
    if (!tab) {
      window.alert("瀏覽器阻擋了新分頁，請允許彈出視窗後再試一次。");
      return;
    }
    tab.focus();
  }, []);

  const handleLoginClick = React.useCallback(async () => {
    const authTab = window.open("about:blank", "ziin-auth-tab");
    if (!authTab) {
      window.alert("瀏覽器阻擋了新分頁，請允許彈出視窗後再試一次。");
      return;
    }
    authTab.name = "ziin-auth-tab";
    authTabRef.current = authTab;
    authFlowRef.current = true;

    try {
      const csrfResp = await fetch("/api/auth/csrf", { method: "GET", cache: "no-store" });
      if (!csrfResp.ok) {
        authTab.close();
        authFlowRef.current = false;
        return;
      }
      const csrfData = (await csrfResp.json()) as { csrfToken?: string };
      const csrfToken = typeof csrfData.csrfToken === "string" ? csrfData.csrfToken : "";
      if (!csrfToken) {
        authTab.close();
        authFlowRef.current = false;
        return;
      }

      const body = new URLSearchParams({
        csrfToken,
        callbackUrl: "/auth/popup-close",
        json: "true"
      });
      const signinResp = await fetch("/api/auth/signin/discord", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded"
        },
        body
      });
      if (!signinResp.ok) {
        authTab.close();
        authFlowRef.current = false;
        return;
      }
      const signinData = (await signinResp.json()) as { url?: string };
      if (!signinData.url) {
        authTab.close();
        authFlowRef.current = false;
        return;
      }
      authTab.location.href = signinData.url;
      authTab.focus();
    } catch {
      authTab.close();
      authFlowRef.current = false;
    }
  }, []);

  const handleInviteClick = React.useCallback(() => {
    openNewTab("/api/discord/bot-invite");
  }, [openNewTab]);

  const handleDashboardClick = React.useCallback(async () => {
    if (isAuthenticated) {
      router.push("/dashboard");
      return;
    }
    await handleLoginClick();
  }, [handleLoginClick, isAuthenticated, router]);

  return (
    <main className="relative min-h-screen overflow-hidden bg-[#171a2b] text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_0%_20%,rgba(136,118,255,0.18),transparent_38%),radial-gradient(circle_at_100%_-10%,rgba(81,102,255,0.12),transparent_35%),linear-gradient(90deg,rgba(99,102,241,0.08),transparent_42%)]" />

      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-6">
        <Link href="/" className="flex items-center gap-3">
          <Image src="/logo.png" alt="Ziin Bot" width={40} height={40} className="rounded-md" priority />
          <span className="text-2xl font-semibold tracking-tight">Ziin Bot</span>
        </Link>

        <nav className="hidden items-center gap-8 text-sm font-semibold text-slate-300 md:flex">
          <a href="#features" className="transition hover:text-white">Log Features</a>
          <a href="#scenes" className="transition hover:text-white">Use Cases</a>
          <a href="#social" className="text-amber-300 transition hover:text-amber-200">Social Alerts</a>
        </nav>

        <div className="relative flex items-center gap-2">
          {isAuthenticated ? (
            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                className="h-11 w-11 overflow-hidden rounded-full border border-white/20 bg-white/10 transition hover:bg-white/20"
                aria-label="Open account menu"
              >
                {session?.user?.image ? (
                  <img
                    src={session.user.image}
                    alt={session.user.name ?? "Discord avatar"}
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span className="text-sm font-semibold">U</span>
                )}
              </button>
              {menuOpen && (
                <div className="absolute right-0 z-20 mt-2 w-44 rounded-lg border border-white/15 bg-[#1f2336] p-1 shadow-xl">
                  <Link
                    href="/dashboard"
                    onClick={() => setMenuOpen(false)}
                    className="block rounded-md px-3 py-2 text-sm font-semibold text-slate-100 transition hover:bg-white/10"
                  >
                    Dashboard
                  </Link>
                  <button
                    type="button"
                    onClick={() => void signOut({ callbackUrl: "/" })}
                    className="block w-full rounded-md px-3 py-2 text-left text-sm font-semibold text-red-300 transition hover:bg-red-500/10 hover:text-red-200"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              type="button"
              onClick={() => void handleLoginClick()}
              className="rounded-full border border-white/20 bg-white/10 px-4 py-2 text-sm font-semibold transition hover:bg-white/20"
            >
              Login
            </button>
          )}
        </div>
      </header>

      <section className="relative z-10 mx-auto flex min-h-[78vh] w-full max-w-3xl flex-col items-center justify-center px-6 text-center">
        <span className="mb-6 rounded-full border border-indigo-400/40 bg-indigo-500/10 px-5 py-2 text-sm font-semibold text-indigo-200">
          Core: Discord Log System
        </span>

        <h1 className="text-5xl font-semibold leading-tight tracking-tight md:text-7xl">
          Build A Professional
          <br />
          Server Log Center
        </h1>

        <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300 md:text-xl">
          Ziin focuses on detailed, channel-based event logs: member actions, message edits/deletes,
          role updates, voice activity, plus Twitch / YouTube / X notifications in one dashboard.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <button
            type="button"
            onClick={handleInviteClick}
            className="rounded-xl bg-indigo-400 px-8 py-3 text-base font-semibold text-slate-950 transition hover:bg-indigo-300"
          >
            Add Ziin To Discord
          </button>
          <button
            type="button"
            onClick={() => void handleDashboardClick()}
            className="rounded-xl border border-white/20 bg-white/5 px-8 py-3 text-base font-semibold transition hover:bg-white/10"
          >
            Dashboard
          </button>
        </div>
      </section>

      <footer className="relative z-10 border-t border-white/10 bg-black/25">
        <div className="mx-auto grid w-full max-w-7xl gap-10 px-6 py-10 md:grid-cols-4">
          <div>
            <div className="flex items-center gap-3">
              <Image src="/logo.png" alt="Ziin Bot" width={28} height={28} className="rounded-md" />
              <span className="text-lg font-semibold">Ziin Bot</span>
            </div>
            <p className="mt-3 text-sm text-slate-400">Ziin © 2025-2026</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-200">連接</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-400">
              <li>
                <Link href="/dashboard" className="transition hover:text-white">控制面板</Link>
              </li>
              <li>
                <a href="/api/discord/bot-invite" className="transition hover:text-white">邀請機器人</a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-200">其他</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-400">
              <li>
                <a href="https://discord.gg/EtQX9RB9Xr" target="_blank" rel="noreferrer" className="transition hover:text-white">
                  Discord
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-slate-200">規則</h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-400">
              <li>
                <Link href="/privacy" className="transition hover:text-white">隱私權聲明</Link>
              </li>
              <li>
                <Link href="/terms" className="transition hover:text-white">使用條款</Link>
              </li>
            </ul>
          </div>
        </div>
      </footer>
    </main>
  );
}
