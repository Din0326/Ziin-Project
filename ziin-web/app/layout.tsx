import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthSessionProvider } from "@/components/auth-session-provider";
import { Toaster } from "sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Ziin - Discord Logging System",
  description:
    "Ziin 是專為 Discord 打造的日誌系統，集中管理伺服器事件紀錄，包含成員、訊息、語音與頻道變更追蹤，並整合 Twitch、YouTube、X(Twitter) 社群通知。",
  icons: {
    icon: "/logo.png",
    shortcut: "/logo.png",
    apple: "/logo.png"
  }
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning
        className={`${geistSans.variable} ${geistMono.variable} font-mono antialiased`}
      >
        <AuthSessionProvider>{children}</AuthSessionProvider>
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
