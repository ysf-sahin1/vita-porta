export type FormattedSignal = { label: string; display: string };

export function formatSignal(key: string, value: unknown): FormattedSignal | null {
  if (typeof value === "boolean") {
    return formatBool(key, value);
  }
  if (typeof value === "string") {
    return formatString(key, value);
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return formatNumber(key, value);
  }
  return null;
}

function formatBool(key: string, v: boolean): FormattedSignal | null {
  const yesNo = v ? "Var" : "Yok";
  switch (key) {
    case "pallor":
      return { label: "Solgunluk", display: yesNo };
    case "sway":
    case "sway_detected":
      return { label: "Sallantı", display: yesNo };
    case "fever_flag":
      return { label: "Ateş Şüphesi", display: yesNo };
    case "hypothermia_flag":
      return { label: "Hipotermi", display: yesNo };
    default:
      return null;
  }
}

function formatString(key: string, v: string): FormattedSignal | null {
  switch (key) {
    case "posture":
      return { label: "Duruş", display: v === "dik" ? "Dik" : v === "eğik" ? "Eğik" : cap(v) };
    case "skin_tone":
      return {
        label: "Cilt Tonu",
        display:
          v === "solgun"
            ? "Solgun"
            : v === "belirsiz"
              ? "Belirsiz"
              : v === "normal"
                ? "Normal"
                : cap(v),
      };
    case "symmetry_status":
      return { label: "Simetri", display: v === "anormal" ? "Anormal" : "Normal" };
    case "breathing_pattern":
    case "pattern":
      return {
        label: "Solunum",
        display:
          v === "hızlı"
            ? "Hızlı"
            : v === "yavaş"
              ? "Yavaş"
              : v === "düzensiz"
                ? "Düzensiz"
                : v === "normal"
                  ? "Normal"
                  : v === "apne_riski"
                    ? "Apne Riski"
                    : cap(v),
      };
    case "severity":
      return {
        label: "Şiddet",
        display:
          v === "high"
            ? "Yüksek"
            : v === "mild"
              ? "Hafif"
              : v === "none"
                ? "Yok"
                : v === "moderate"
                  ? "Orta"
                  : cap(v),
      };
    case "sensor_type":
      return {
        label: "Sensör",
        display: v === "rgb_proxy" ? "RGB Proxy" : v === "thermal" ? "Termal" : cap(v),
      };
    default:
      return null;
  }
}

function formatNumber(key: string, v: number): FormattedSignal | null {
  switch (key) {
    case "avg_visibility":
      return { label: "Görünürlük", display: pct(v) };
    case "symmetry":
      return { label: "Simetri Skoru", display: pct(v) };
    case "hsv_v":
      return { label: "Parlaklık", display: v.toFixed(2) };
    case "color_variance":
      return { label: "Renk Varyansı", display: v.toFixed(1) };
    case "mean_saturation":
      return { label: "Doygunluk", display: v.toFixed(1) };
    case "face_detected_ratio":
      return { label: "Yüz Tespiti", display: pct(v) };
    case "rate_bpm":
    case "breaths_per_minute":
      return { label: "Solunum Hızı", display: `${Math.round(v)}/dk` };
    case "regularity":
      return { label: "Düzenlilik", display: pct(v) };
    case "movement_intensity":
      return { label: "Hareket Yoğunluğu", display: v.toFixed(1) };
    case "temp_estimate_c":
      return { label: "Sıcaklık", display: `${v.toFixed(1)}°C` };
    case "warmth_score":
      return { label: "Sıcaklık Skoru", display: pct(v) };
    default:
      return null;
  }
}

function pct(v: number): string {
  return `%${Math.round(v * 100)}`;
}

function cap(s: string): string {
  return s.length === 0 ? s : s.charAt(0).toLocaleUpperCase("tr-TR") + s.slice(1);
}
