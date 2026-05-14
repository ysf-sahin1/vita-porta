"use client";

import { cn } from "@/lib/cn";
import type { AgentObservation } from "@/lib/types";

type PostureState = "upright" | "swaying" | "asymmetric" | "leaning" | "unknown";

export function PostureSilhouette({ obs }: { obs: AgentObservation | undefined }) {
  const state = derivePosture(obs);
  const label = LABEL[state];
  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-xl border px-3 py-2",
        state === "unknown"
          ? "border-dashed border-slate-200 bg-slate-50/50"
          : "border-slate-200/70 bg-white/60",
      )}
      title={label}
    >
      <Figure state={state} />
      <div className="flex-1 min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-slate-500">Postür</div>
        <div className="text-xs font-medium text-slate-700 truncate">{label}</div>
      </div>
    </div>
  );
}

const LABEL: Record<PostureState, string> = {
  upright: "Dik ve simetrik",
  swaying: "Sallantılı",
  asymmetric: "Omuzlarda asimetri",
  leaning: "Öne eğik duruş",
  unknown: "Veri bekleniyor",
};

function derivePosture(obs: AgentObservation | undefined): PostureState {
  if (!obs || obs.confidence <= 0) return "unknown";
  const s = obs.signals ?? {};

  const swayLive = s.sway_detected === true;
  const swayDemo = s.sway === true;
  const sway = swayLive || swayDemo;

  const symStatus = String(s.symmetry_status ?? "");
  const symDemo = typeof s.symmetry === "number" ? (s.symmetry as number) : null;
  const asymmetric = symStatus === "anormal" || (symDemo !== null && symDemo < 0.5);

  const posture = String(s.posture ?? "");
  const leaning = posture === "eğik" && !asymmetric;

  if (sway) return "swaying";
  if (asymmetric) return "asymmetric";
  if (leaning) return "leaning";
  return "upright";
}

function Figure({ state }: { state: PostureState }) {
  const stroke = state === "unknown" ? "#cbd5e1" : "#475569";
  const dash = state === "unknown" ? "3 3" : undefined;
  const wobble = state === "swaying";

  // Asimetrik: sol omuz aşağı, sağ omuz yukarı
  const leftShoulderY = state === "asymmetric" ? 16 : 14;
  const rightShoulderY = state === "asymmetric" ? 12 : 14;

  // Öne eğik: gövde sağa doğru hafif eğim (kameraya göre öne)
  const bodyLean = state === "leaning" ? 3 : 0;

  return (
    <svg
      viewBox="0 0 32 44"
      className={cn("w-9 h-12 flex-shrink-0", wobble && "origin-bottom animate-[wobble_1.6s_ease-in-out_infinite]")}
      aria-hidden
    >
      <style>{`@keyframes wobble {
        0%, 100% { transform: rotate(-4deg); }
        50% { transform: rotate(4deg); }
      }`}</style>
      {/* Baş */}
      <circle cx={16} cy={6} r={4} fill="none" stroke={stroke} strokeWidth={1.6} strokeDasharray={dash} />
      {/* Gövde */}
      <line
        x1={16}
        y1={10}
        x2={16 + bodyLean}
        y2={28}
        stroke={stroke}
        strokeWidth={1.8}
        strokeDasharray={dash}
        strokeLinecap="round"
      />
      {/* Kollar — omuz noktaları asimetri için kaymış */}
      <line
        x1={9}
        y1={leftShoulderY + 4}
        x2={16}
        y2={leftShoulderY}
        stroke={stroke}
        strokeWidth={1.6}
        strokeDasharray={dash}
        strokeLinecap="round"
      />
      <line
        x1={23}
        y1={rightShoulderY + 4}
        x2={16}
        y2={rightShoulderY}
        stroke={stroke}
        strokeWidth={1.6}
        strokeDasharray={dash}
        strokeLinecap="round"
      />
      {/* Bacaklar */}
      <line
        x1={16 + bodyLean}
        y1={28}
        x2={11}
        y2={40}
        stroke={stroke}
        strokeWidth={1.8}
        strokeDasharray={dash}
        strokeLinecap="round"
      />
      <line
        x1={16 + bodyLean}
        y1={28}
        x2={21}
        y2={40}
        stroke={stroke}
        strokeWidth={1.8}
        strokeDasharray={dash}
        strokeLinecap="round"
      />
    </svg>
  );
}
