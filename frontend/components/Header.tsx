"use client";

import { ShieldCheck } from "lucide-react";

export function Header({ status }: { status: "connecting" | "live" | "offline" }) {
  const dot =
    status === "live" ? "bg-emerald-500" : status === "connecting" ? "bg-amber-400" : "bg-slate-400";
  const label =
    status === "live" ? "Canlı yayın" : status === "connecting" ? "Bağlanıyor…" : "Çevrimdışı";
  return (
    <header className="flex items-center justify-between border-b border-slate-200 pb-5">
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-slate-900 p-2.5 text-white">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <div className="text-xl font-bold text-slate-900">Vita Porta</div>
          <div className="text-xs text-slate-500 -mt-0.5">
            Hemşire triaj asistanı · Sistem öneridir, son karar hemşireye aittir
          </div>
        </div>
      </div>
      <div className="flex items-center gap-2 text-sm text-slate-600">
        <span className={`inline-block w-2 h-2 rounded-full ${dot}`} />
        {label}
      </div>
    </header>
  );
}
