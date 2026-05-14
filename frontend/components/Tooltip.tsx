"use client";

import { cn } from "@/lib/cn";
import { Info } from "lucide-react";
import { type ReactNode } from "react";

export interface TooltipProps {
  content: ReactNode;
  children?: ReactNode;
  align?: "left" | "center" | "right";
  className?: string;
}

export function Tooltip({ content, children, align = "center", className }: TooltipProps) {
  const alignCls =
    align === "left"
      ? "left-0"
      : align === "right"
        ? "right-0"
        : "left-1/2 -translate-x-1/2";
  return (
    <span className={cn("group relative inline-flex items-center align-middle", className)}>
      {children ?? <Info className="w-3.5 h-3.5 text-slate-400 cursor-help" strokeWidth={2.2} />}
      <span
        role="tooltip"
        className={cn(
          "pointer-events-none absolute bottom-full mb-2 z-20 w-64 max-w-[80vw]",
          "rounded-xl bg-slate-900/95 text-white text-xs leading-relaxed px-3 py-2 shadow-glassLg",
          "opacity-0 translate-y-1 transition-all duration-150",
          "group-hover:opacity-100 group-hover:translate-y-0",
          "group-focus-within:opacity-100 group-focus-within:translate-y-0",
          alignCls,
        )}
      >
        {content}
      </span>
    </span>
  );
}
