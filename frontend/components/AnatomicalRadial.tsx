"use client";

import { cn } from "@/lib/cn";
import type { AgentObservation, TriageCategory } from "@/lib/types";
import { AgentCard, type Agent } from "./AgentPanel";

// Anatomik radyal yerleşim (3 ajan):
//   ┌──────────────────────────────┐
//   │ [Expression]   [Thermal]     │
//   │           \   /              │
//   │            🧍                │
//   │           /                  │
//   │       [Gait]                 │
//   └──────────────────────────────┘
//
// Container sabit aspect (5/3) — SVG viewBox koordinatları yüzde olarak
// tasarlandı, kart pozisyonları aynı koordinat sisteminde. Silüet kategoriye
// göre soft pulse atar, bağlantı çizgileri dashed flow ile sürekli canlı.

const SILHOUETTE_COLOR: Record<TriageCategory, { stroke: string; pulse: string }> = {
  red: { stroke: "#dc2626", pulse: "rgba(220, 38, 38, 0.35)" },
  yellow: { stroke: "#eab308", pulse: "rgba(234, 179, 8, 0.30)" },
  green: { stroke: "#16a34a", pulse: "rgba(22, 163, 74, 0.30)" },
  insufficient: { stroke: "#64748b", pulse: "rgba(100, 116, 139, 0.20)" },
};

// Bağlantı çizgileri için ajan kart kenarından silüet anatomik bölgesine
// koordinat çiftleri (viewBox: 0 0 100 60). Her ajan vücudun gözlemlediği
// bölgeye işaret eder.
const CONNECTIONS: Record<
  Agent,
  { from: [number, number]; to: [number, number]; color: string }
> = {
  expression: { from: [28, 14], to: [47, 8], color: "#a78bfa" },   // kafa sol
  thermal:    { from: [72, 14], to: [53, 8], color: "#fb923c" },   // alın
  gait:       { from: [50, 56], to: [50, 50], color: "#818cf8" },  // bacaklar
};

// Ajan kartlarının container içindeki yüzdelik konumu (left/top, width).
const CARD_POSITIONS: Record<Agent, { left: string; top: string }> = {
  expression: { left: "0%",  top: "3%"  },
  thermal:    { left: "72%", top: "3%"  },
  gait:       { left: "36%", top: "82%" },
};

const CARD_WIDTH = "28%";

export interface AnatomicalRadialProps {
  observations: Partial<Record<Agent, AgentObservation>>;
  category: TriageCategory | null;
}

export function AnatomicalRadial({ observations, category }: AnatomicalRadialProps) {
  const cat = category ?? "insufficient";
  const colors = SILHOUETTE_COLOR[cat];

  return (
    <div className="relative w-full aspect-[5/3] max-w-[1200px] mx-auto">
      {/* Dekoratif arka plan — yumuşak halka */}
      <div
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[36%] aspect-square rounded-full"
        style={{
          background: `radial-gradient(circle, ${colors.pulse} 0%, rgba(255,255,255,0) 70%)`,
        }}
        aria-hidden
      />

      {/* SVG: bağlantı çizgileri + silüet */}
      <svg
        viewBox="0 0 100 60"
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0 w-full h-full pointer-events-none"
        aria-hidden
      >
        {/* Bağlantı çizgileri — sadece gözlem varsa görünür */}
        {(Object.keys(CONNECTIONS) as Agent[]).map((agent) => {
          const conn = CONNECTIONS[agent];
          const hasObs = !!observations[agent];
          return (
            <line
              key={agent}
              x1={conn.from[0]}
              y1={conn.from[1]}
              x2={conn.to[0]}
              y2={conn.to[1]}
              stroke={conn.color}
              strokeWidth={0.25}
              strokeDasharray="0.6 0.8"
              strokeLinecap="round"
              className={hasObs ? "animate-lineFlow" : "opacity-25"}
              style={{ opacity: hasObs ? 0.7 : 0.18 }}
            />
          );
        })}

        {/* Silüet — büyük çöp adam, kategori rengi, soft pulse */}
        <SilhouetteVector observations={observations} stroke={colors.stroke} />
      </svg>

      {/* Ajan kartları — absolute positioned */}
      {(Object.keys(CARD_POSITIONS) as Agent[]).map((agent) => (
        <div
          key={agent}
          className="absolute"
          style={{
            left: CARD_POSITIONS[agent].left,
            top: CARD_POSITIONS[agent].top,
            width: CARD_WIDTH,
          }}
        >
          <AgentCard agent={agent} obs={observations[agent]} />
        </div>
      ))}
    </div>
  );
}

// ============================================================ silüet vektör

function SilhouetteVector({
  observations,
  stroke,
}: {
  observations: Partial<Record<Agent, AgentObservation>>;
  stroke: string;
}) {
  // Yürüyüş ajanı sallantı/asimetri sinyaliyle pozu değiştir
  const gait = observations.gait;
  const swaying = !!(gait?.signals?.sway_detected || gait?.signals?.sway);
  const asymmetric = String(gait?.signals?.symmetry_status ?? "") === "anormal";

  // viewBox 100x60; silüet ortada cx=50
  // Kafa cy=8, omuz cy=18, göğüs cy=26, bel cy=36, ayak cy=52
  const cx = 50;
  const shoulderL = asymmetric ? 17 : 18;
  const shoulderR = asymmetric ? 19 : 18;

  return (
    <g
      className={cn(
        "transition-transform duration-500",
        swaying && "origin-bottom animate-silhouetteSway",
      )}
      style={{ transformOrigin: `${cx}% 90%` }}
    >
      {/* Pulse halkası — kategori rengi */}
      <circle
        cx={cx}
        cy={30}
        r={18}
        fill="none"
        stroke={stroke}
        strokeWidth={0.15}
        strokeOpacity={0.25}
        className="animate-silhouettePulse"
        style={{ transformOrigin: `${cx}px 30px` }}
      />

      {/* Baş */}
      <circle cx={cx} cy={8} r={3.2} fill="none" stroke={stroke} strokeWidth={0.6} />
      {/* Boyun */}
      <line x1={cx} y1={11.2} x2={cx} y2={14} stroke={stroke} strokeWidth={0.6} strokeLinecap="round" />
      {/* Omuz hattı */}
      <line
        x1={cx - 5}
        y1={shoulderL}
        x2={cx + 5}
        y2={shoulderR}
        stroke={stroke}
        strokeWidth={0.6}
        strokeLinecap="round"
      />
      {/* Gövde */}
      <line
        x1={cx}
        y1={14}
        x2={cx}
        y2={36}
        stroke={stroke}
        strokeWidth={0.7}
        strokeLinecap="round"
      />
      {/* Kollar */}
      <line
        x1={cx - 5}
        y1={shoulderL}
        x2={cx - 8}
        y2={28}
        stroke={stroke}
        strokeWidth={0.55}
        strokeLinecap="round"
      />
      <line
        x1={cx + 5}
        y1={shoulderR}
        x2={cx + 8}
        y2={28}
        stroke={stroke}
        strokeWidth={0.55}
        strokeLinecap="round"
      />
      {/* Bacaklar */}
      <line
        x1={cx}
        y1={36}
        x2={cx - 4}
        y2={52}
        stroke={stroke}
        strokeWidth={0.7}
        strokeLinecap="round"
      />
      <line
        x1={cx}
        y1={36}
        x2={cx + 4}
        y2={52}
        stroke={stroke}
        strokeWidth={0.7}
        strokeLinecap="round"
      />
    </g>
  );
}
