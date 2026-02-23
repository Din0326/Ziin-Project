"use client";

import { type Icon } from "@tabler/icons-react";
import { Button } from "@/components/ui/button";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem
} from "@/components/ui/sidebar";

export function NavMain({
  items,
  activeTitle,
  onItemClick,
  onSwitchServer,
  currentServerName
}: {
  items: {
    title: string;
    url: string;
    icon?: Icon;
  }[];
  activeTitle?: string;
  onItemClick?: (title: string) => void;
  onSwitchServer?: () => void;
  currentServerName?: string;
}) {
  const displayServerName = currentServerName
    ? Array.from(currentServerName).length > 20
      ? `${Array.from(currentServerName).slice(0, 20).join("")}...`
      : currentServerName
    : "";

  return (
    <SidebarGroup>
      <SidebarGroupContent>
        <div className="mb-3 px-2">
          <Button
            type="button"
            variant="outline"
            className="!h-12 w-full justify-start px-3 text-base"
            onClick={onSwitchServer}>
            切換伺服器
          </Button>
          {currentServerName && (
            <p
              className="mt-4 truncate px-1 text-lg font-semibold text-muted-foreground"
              title={`目前：${currentServerName}`}>
              目前：{displayServerName}
            </p>
          )}
        </div>
        <SidebarGroupLabel>Home</SidebarGroupLabel>
        <SidebarMenu>
          {items.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton
                className="!h-12 gap-3"
                tooltip={item.title}
                isActive={item.title === activeTitle}
                onClick={() => onItemClick?.(item.title)}>
                {item.icon && <item.icon className="h-5 w-5" />}
                <span className="text-lg font-semibold tracking-wide">{item.title}</span>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
