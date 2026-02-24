"use client";

import * as React from "react";
import Image from "next/image";
import {
  IconBrandTwitch,
  IconBrandX,
  IconBrandYoutube,
  IconFileAnalytics,
  IconSettings
} from "@tabler/icons-react";

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem
} from "@/components/ui/sidebar";
import { NavMain } from "./nav-main";
import { NavUser } from "./nav-user";

const data = {
  user: {
    name: "shadcn",
    email: "m@example.com",
    avatar: "/avatars/shadcn.jpg"
  },
  navMain: [
    {
      title: "伺服器設定",
      url: "#",
      icon: IconSettings
    },
    {
      title: "Log 系統",
      url: "#",
      icon: IconFileAnalytics
    }
  ],
  navNotifications: [
    {
      title: "Twitch",
      url: "#",
      icon: IconBrandTwitch
    },
    {
      title: "YouTube",
      url: "#",
      icon: IconBrandYoutube
    },
    {
      title: "Twitter",
      url: "#",
      icon: IconBrandX
    }
  ],
};

export function AppSidebar({
  activeNavMainTitle,
  isAuthenticated = false,
  onLogin,
  onNavMainClick,
  onLogout,
  onSwitchServer,
  currentServerName,
  user,
  ...props
}: React.ComponentProps<typeof Sidebar> & {
  activeNavMainTitle?: string;
  isAuthenticated?: boolean;
  onLogin?: () => void;
  onNavMainClick?: (title: string) => void;
  onLogout?: () => void;
  onSwitchServer?: () => void;
  currentServerName?: string;
  user?: {
    name: string;
    email: string;
    avatar: string;
  };
}) {
  return (
    <Sidebar collapsible="none" className="h-svh border-r" {...props}>
      <SidebarHeader className="border-b">
        <SidebarMenu>
          <SidebarMenuItem>
            <div className="flex items-center gap-3 p-1.5">
              <Image src="/logo.png" alt="Ziin Bot" width={38} height={38} className="rounded-sm" />
              <span className="text-xl font-semibold">Ziin Bot</span>
            </div>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain
          items={data.navMain}
          notificationItems={data.navNotifications}
          activeTitle={activeNavMainTitle}
          onItemClick={onNavMainClick}
          onSwitchServer={onSwitchServer}
          currentServerName={currentServerName}
        />
      </SidebarContent>
      <SidebarFooter>
        <NavUser
          user={user ?? data.user}
          isAuthenticated={isAuthenticated}
          onLogin={onLogin}
          onLogout={onLogout}
        />
      </SidebarFooter>
    </Sidebar>
  );
}
