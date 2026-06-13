"use client";

import { cn } from "@/lib/cn";
import { Activity, CameraOff } from "lucide-react";

interface PirStatusBannerProps {
  pirMotion: boolean | null;
}

export function PirStatusBanner({ pirMotion }: PirStatusBannerProps) {
  if (pirMotion === true) {
    return (
      <div
        className={cn(
          "flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm",
          "bg-emerald-50/80 border-emerald-200/70 text-emerald-800",
        )}
      >
        <span className="relative flex h-2.5 w-2.5 shrink-0">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
          <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500" />
        </span>
        <Activity className="h-4 w-4 shrink-0 text-emerald-600" strokeWidth={2} />
        <span className="font-medium">PIR: Hareket algılandı — kamera aktif, analiz çalışıyor.</span>
      </div>
    );
  }

  if (pirMotion === false) {
    return (
      <div
        className={cn(
          "flex items-center gap-3 rounded-2xl border px-4 py-3 text-sm",
          "bg-amber-50/80 border-amber-200/70 text-amber-800",
        )}
      >
        <CameraOff className="h-4 w-4 shrink-0 text-amber-500" strokeWidth={2} />
        <div>
          <span className="font-medium">PIR: Hareket algılanmıyor — kamera kapalı.</span>
          <span className="ml-2 text-amber-600/80">
            Kapı önüne yaklaşan biri olduğunda analiz otomatik başlayacak.
          </span>
        </div>
      </div>
    );
  }

  return null;
}
