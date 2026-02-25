"use client";

import * as React from "react";

export default function PopupClosePage() {
  React.useEffect(() => {
    if (window.opener && !window.opener.closed) {
      try {
        window.opener.postMessage({ type: "ziin-auth-finished" }, window.location.origin);
        window.opener.focus();
      } catch {
        // ignore cross-window errors
      }
    }

    const timer = window.setInterval(() => {
      window.close();
    }, 120);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#171a2b] px-6 text-center text-slate-100">
      <p className="text-sm text-slate-300">Auth finished. This window will close automatically.</p>
    </main>
  );
}
