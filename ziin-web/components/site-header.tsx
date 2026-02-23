"use client";

import * as React from "react";

export function SiteHeader({ children }: { children?: React.ReactNode }) {
  return (
    <header className="bg-background/90 sticky top-0 z-10 flex h-(--header-height) shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-(--header-height)">
      <div className="flex w-full items-center justify-end gap-2 px-4 lg:px-6">{children}</div>
    </header>
  );
}
