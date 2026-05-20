import type { AgentObservation } from "@/lib/types";

export type AgentReason = {
  text: string;
  severity: "info" | "warn" | "error";
};

const HIGH_CONF = 0.65;
const MID_CONF = 0.45;

export function inferAgentReason(obs: AgentObservation): AgentReason | null {
  const signals = obs.signals ?? {};
  const conf = obs.confidence;

  if (obs.agent === "gait") {
    const vis = numericOrNull(signals.avg_visibility);
    if (vis !== null && vis < 0.4) {
      return { text: "Vücut tam görünmüyor — kamera açısı veya mesafe uygun değil.", severity: "warn" };
    }
    if (conf < MID_CONF) {
      return { text: "Vücut landmark'ları yetersiz — yürüyüş analizi sınırlı.", severity: "warn" };
    }
    return null;
  }

  if (obs.agent === "thermal") {
    const sensor = String(signals.sensor_type ?? "");
    if (sensor === "rgb_proxy") {
      return {
        text: "RGB proxy modu — gerçek termal sensör yerine renk analizi kullanılıyor.",
        severity: "info",
      };
    }
    if (conf < MID_CONF) {
      return { text: "Yüz ROI bulunamadı — sıcaklık tahmini sınırlı.", severity: "warn" };
    }
    return null;
  }

  if (obs.agent === "expression") {
    const sensor = String(signals.sensor_type ?? "");
    const faceRatio = numericOrNull(signals.face_detected_ratio);
    if (sensor === "geometric_proxy") {
      return {
        text: "Geometrik proxy modu — eğitilmiş ağrı sınıflandırıcı yerine landmark geometrisi kullanılıyor.",
        severity: "info",
      };
    }
    if (faceRatio !== null && faceRatio < 0.3) {
      return { text: "Yüz mesh yakalanamadı — mimik analizi sınırlı.", severity: "warn" };
    }
    if (conf < MID_CONF) {
      return { text: "İfade sinyali zayıf — kameraya bakılması gerekiyor.", severity: "warn" };
    }
    return null;
  }

  return null;
}

export function confidenceTier(conf: number): "high" | "mid" | "low" {
  if (conf >= HIGH_CONF) return "high";
  if (conf >= MID_CONF) return "mid";
  return "low";
}

function numericOrNull(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  return null;
}
