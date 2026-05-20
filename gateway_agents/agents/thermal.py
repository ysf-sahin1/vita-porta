"""Termal ajan — ESP32-CAM AMG8833 (öncelik) veya RGB proxy (fallback).

Politika (tek kaynak): firmware kendi içinde "MEDIUM veya HIGH güvende olduğum
son ölçüm" değerini ``last_confirmed`` bloğunda tutuyor. Anlık frame'in
güveni düşse bile son emin değer korunuyor. Gateway buna ``/thermal``
endpoint'inden ulaşır ve **DAİMA last_confirmed.skin_temp** yollar:

- ``last_confirmed.set == True``  → o değeri yolla (age bilgisi ile birlikte)
- ``last_confirmed.set == False`` → henüz hiç emin ölçüm yok, boş gözlem
- AMG hazır değil / ESP düştü   → RGB proxy fallback (eski davranış)

Böylece anlık vs son-emin arasında flip-flop olmaz; LLM hep "kameranın
gerçekten emin olduğu son sayı"yı görür. Yeni HIGH ölçüm geldiğinde
firmware last_confirmed'i otomatik günceller, gateway de o yeni değeri yollar.

Firmware sözleşmesi (Aşama 11 sonrası): firmware veriyi **etiketlemez**, sadece
ham sayı yollar. Klinik karar (ateş/hipotermi) supervisor LLM'in işi; bu ajan
sadece sayısal sinyali ve ham bayrakları (>37.5 / <35.5) iletir.

Çıktı sinyalleri:
    temp_estimate_c   float  — vücut sıcaklığı (°C, en son emin ölçüm)
    temp_ambient_c    float  — anlık ortam sıcaklığı (°C, AMG'den; proxy modda 0)
    distance_cm       float  — alın-sensör mesafesi (cm)
    quality_score     0..1   — AMG kalite skoru (son emin ölçüm anındaki)
    measurement_age_s float  — son emin ölçümden bu yana geçen saniye
    fever_flag        bool   — > 37.5 °C (ham eşik, klinik karar değil)
    hypothermia_flag  bool   — < 35.5 °C (ham eşik)
    warmth_score      0..1   — proxy normalize indeks (AMG modunda 0.5)
    sensor_type       str    — "amg8833" | "rgb_proxy"
    data_source       str    — "last_confirmed" | "waiting" | "rgb_fallback"
    confidence_level  str    — "yuksek" | "orta" (AMG) / "rgb"
"""

from __future__ import annotations

import logging

import httpx
import numpy as np

from gateway_agents.agents.base import Agent, AnalysisWindow
from orchestration.schemas import AgentObservation

logger = logging.getLogger(__name__)

try:
    import cv2

    _CV_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    _CV_AVAILABLE = False

try:
    import mediapipe as mp

    _MP_AVAILABLE = True
except ImportError:
    mp = None  # type: ignore[assignment]
    _MP_AVAILABLE = False

# Sağlıklı ten referans noktaları (LAB, 0-255 ölçeği) — RGB proxy fallback için
_LAB_A_NEUTRAL = 138.0
_LAB_B_NEUTRAL = 122.0
_A_RANGE = 25.0
_B_RANGE = 18.0

# Ham eşikler — supervisor'a sinyal vermek için, klinik karar değil
_FEVER_THRESHOLD = 37.5
_HYPOTHERMIA_THRESHOLD = 35.5
_BASE_TEMP = 36.5  # proxy kalibrasyonu

# ESP /thermal HTTP timeout — donanım yavaş yanıt verebilir, ama pencereyi tıkamasın
_ESP_TIMEOUT_S = 1.5
_ESP_PORT = 80

# AMG confidence → AgentObservation.confidence haritası
# Firmware'in evaluateConfidence() çıktısı (1=LOW, 2=MEDIUM, 3=HIGH) doğrudan
# güven seviyesi taşır — sayısal değere çevirip supervisor'a veriyoruz.
_AMG_CONFIDENCE_MAP = {3: 0.95, 2: 0.80, 1: 0.55, 0: 0.0}


class ThermalAgent(Agent):
    """ESP32-CAM AMG8833 (öncelik) veya RGB proxy (fallback) termal ajanı."""

    name = "thermal"

    def __init__(self, esp_host: str | None = None) -> None:
        if not _CV_AVAILABLE:
            raise RuntimeError("opencv-python yüklü değil.")
        self._esp_host = esp_host.strip() if esp_host else None
        self._http: httpx.Client | None = None
        if self._esp_host:
            self._http = httpx.Client(timeout=_ESP_TIMEOUT_S)
            logger.info("ThermalAgent: AMG8833 modunda — ESP=%s", self._esp_host)
        else:
            logger.info("ThermalAgent: RGB proxy modunda (ESP host verilmedi)")

        self._face = None
        if _MP_AVAILABLE:
            self._face = mp.solutions.face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            )

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        # 1. ESP /thermal yolu (varsa)
        if self._esp_host is not None:
            esp_obs = self._read_esp()
            if esp_obs is not None:
                return esp_obs
            logger.debug("ESP /thermal okunamadı, RGB proxy fallback'e geçiliyor.")

        # 2. RGB proxy fallback
        return self._analyze_rgb_proxy(window)

    # ------------------------------------------------------------- ESP yolu

    def _read_esp(self) -> AgentObservation | None:
        """ESP /thermal'dan son emin ölçümü oku. Hata → None (proxy'ye düş)."""

        assert self._http is not None
        url = f"http://{self._esp_host}:{_ESP_PORT}/thermal"
        try:
            resp = self._http.get(url)
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("ESP /thermal hatası (%s): %s", url, exc)
            return None

        # AMG hazır değilse → boş gözlem
        if not data.get("ok", False):
            return AgentObservation(
                agent="thermal",
                confidence=0.0,
                summary_tr="AMG8833 sensörü bağlı değil veya başlatılamadı.",
                signals=_empty_amg_signals(),
            )

        ambient = float(data.get("ambient", 0.0))
        last_confirmed = data.get("last_confirmed") or {}

        # Tek kaynak: last_confirmed. Hiç emin ölçüm yoksa "bekliyor".
        if not last_confirmed.get("set"):
            gate_reason = ((data.get("gate") or {}).get("reason")) or "veri yok"
            return AgentObservation(
                agent="thermal",
                confidence=0.0,
                summary_tr=f"Termal: henüz emin alın ölçümü yok ({gate_reason}).",
                signals={
                    **_empty_amg_signals(),
                    "temp_ambient_c": round(ambient, 1),
                    "data_source": "waiting",
                },
            )

        temp_c = round(float(last_confirmed.get("skin_temp", 0.0)), 1)
        distance_cm = round(float(last_confirmed.get("distance_cm", 0.0)), 1)
        quality = round(float(last_confirmed.get("quality", 0.0)), 3)
        age_ms = int(last_confirmed.get("age_ms", 0))
        age_s = round(age_ms / 1000.0, 1)
        lc_conf = int(last_confirmed.get("conf", 2))

        # Confidence: firmware'in son emin ölçümün güveni + yaşa göre stale cezası.
        # last_confirmed sadece MEDIUM/HIGH'ta yazıldığı için lc_conf ≥ 2 garantili.
        base_conf = _AMG_CONFIDENCE_MAP.get(lc_conf, 0.80)
        if age_ms > 30_000:
            confidence = round(max(0.30, base_conf * 0.70), 3)
            conf_label = f"son emin (eski, {age_s}s önce)"
        elif age_ms > 5_000:
            confidence = round(base_conf * 0.90, 3)
            conf_label = f"son emin ({age_s}s önce)"
        else:
            confidence = base_conf
            conf_label = "yuksek" if lc_conf == 3 else "orta"

        fever = temp_c > _FEVER_THRESHOLD
        hypothermia = temp_c < _HYPOTHERMIA_THRESHOLD
        summary_tr = _build_amg_summary(temp_c, ambient, distance_cm, age_s)

        return AgentObservation(
            agent="thermal",
            confidence=confidence,
            summary_tr=summary_tr,
            signals={
                "temp_estimate_c": temp_c,
                "temp_ambient_c": round(ambient, 1),
                "distance_cm": distance_cm,
                "quality_score": quality,
                "measurement_age_s": age_s,
                "fever_flag": fever,
                "hypothermia_flag": hypothermia,
                "warmth_score": 0.5,  # AMG modunda anlamsız, proxy ile şema uyumu
                "sensor_type": "amg8833",
                "data_source": "last_confirmed",
                "confidence_level": conf_label,
            },
        )

    # --------------------------------------------------------- RGB fallback

    def _analyze_rgb_proxy(self, window: AnalysisWindow) -> AgentObservation:
        if not window.frames:
            return _insufficient("Görüntü alınamadı.")

        a_vals: list[float] = []
        b_vals: list[float] = []
        face_hits = 0

        for frame in window.frames:
            roi, has_face = self._extract_face_roi(frame)
            if has_face:
                face_hits += 1
            if roi is None or roi.size == 0:
                continue
            lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
            a_vals.append(float(np.mean(lab[:, :, 1])))
            b_vals.append(float(np.mean(lab[:, :, 2])))

        if not a_vals:
            return _insufficient("Yüz ROI çıkarılamadı.")

        a_mean = float(np.mean(a_vals))
        b_mean = float(np.mean(b_vals))

        a_delta = (a_mean - _LAB_A_NEUTRAL) / _A_RANGE
        b_delta = (b_mean - _LAB_B_NEUTRAL) / _B_RANGE
        warmth = float(np.clip(0.6 * a_delta + 0.4 * b_delta, -1.0, 1.0))

        temp_c = round(_BASE_TEMP + 2.5 * warmth, 1)
        fever = temp_c > _FEVER_THRESHOLD
        hypothermia = temp_c < _HYPOTHERMIA_THRESHOLD
        warmth_score = round(float(np.clip(0.5 + warmth * 0.5, 0.0, 1.0)), 3)

        face_ratio = face_hits / len(window.frames)
        confidence = float(min(0.60, 0.25 + 0.55 * face_ratio))

        summary_tr = _build_proxy_summary(temp_c, fever, hypothermia, face_ratio > 0)

        return AgentObservation(
            agent="thermal",
            confidence=confidence,
            summary_tr=summary_tr,
            signals={
                "temp_estimate_c": temp_c,
                "temp_ambient_c": 0.0,
                "distance_cm": 0.0,
                "quality_score": 0.0,
                "measurement_age_s": 0.0,
                "fever_flag": fever,
                "hypothermia_flag": hypothermia,
                "warmth_score": warmth_score,
                "sensor_type": "rgb_proxy",
                "data_source": "rgb_fallback",
                "confidence_level": "rgb",
            },
        )

    def _extract_face_roi(self, frame: np.ndarray) -> tuple[np.ndarray | None, bool]:
        h, w = frame.shape[:2]
        if self._face is not None:
            rgb = frame[:, :, ::-1]
            result = self._face.process(rgb)
            if result.detections:
                box = result.detections[0].location_data.relative_bounding_box
                x = max(0, int(box.xmin * w))
                y = max(0, int(box.ymin * h))
                bw = max(1, int(box.width * w))
                bh = max(1, int(box.height * h))
                return frame[y : y + bh, x : x + bw], True
        # Fallback: yüz bölgesi olası orta-üst dikdörtgen
        cy0 = int(h * 0.10)
        cy1 = int(h * 0.55)
        cx0 = int(w * 0.30)
        cx1 = int(w * 0.70)
        return frame[cy0:cy1, cx0:cx1], False

    def close(self) -> None:
        if self._face is not None:
            self._face.close()
        if self._http is not None:
            self._http.close()
            self._http = None


# ------------------------------------------------------------------ helpers


def _build_amg_summary(
    temp_c: float, ambient: float, distance_cm: float, age_s: float
) -> str:
    if temp_c > _FEVER_THRESHOLD:
        descriptor = "ateş aralığı"
    elif temp_c < _HYPOTHERMIA_THRESHOLD:
        descriptor = "düşük sıcaklık"
    else:
        descriptor = "normal aralık"
    dist_note = f", {distance_cm:.0f} cm" if distance_cm > 0 else ""
    amb_note = f", ortam {ambient:.1f}°C" if ambient > 1.0 else ""
    age_note = f" ({age_s:.1f}s önce ölçüldü)" if age_s >= 1.0 else ""
    return f"Termal: {descriptor} — {temp_c:.1f}°C{dist_note}{amb_note}{age_note}. [AMG8833]"


def _empty_amg_signals() -> dict[str, float | str | bool]:
    """AMG yoluna özgü boş signal şeması — schema tutarlılığı için."""
    return {
        "temp_estimate_c": 0.0,
        "temp_ambient_c": 0.0,
        "distance_cm": 0.0,
        "quality_score": 0.0,
        "measurement_age_s": 0.0,
        "fever_flag": False,
        "hypothermia_flag": False,
        "warmth_score": 0.5,
        "sensor_type": "amg8833",
        "data_source": "sensor_offline",
        "confidence_level": "yok",
    }


def _build_proxy_summary(
    temp_c: float, fever: bool, hypothermia: bool, face_seen: bool
) -> str:
    sensor_note = "" if face_seen else " (yüz tespit edilemedi, ROI fallback)"
    if fever:
        return f"Termal: ateş şüphesi — tahmini {temp_c}°C{sensor_note}. [RGB proxy]"
    if hypothermia:
        return f"Termal: düşük sıcaklık — tahmini {temp_c}°C{sensor_note}. [RGB proxy]"
    return f"Termal: normal aralık — tahmini {temp_c}°C{sensor_note}. [RGB proxy]"


def _insufficient(reason: str) -> AgentObservation:
    return AgentObservation(
        agent="thermal",
        confidence=0.0,
        summary_tr=f"Termal veri yetersiz: {reason}",
        signals={
            "temp_estimate_c": 0.0,
            "temp_ambient_c": 0.0,
            "distance_cm": 0.0,
            "quality_score": 0.0,
            "measurement_age_s": 0.0,
            "fever_flag": False,
            "hypothermia_flag": False,
            "warmth_score": 0.5,
            "sensor_type": "rgb_proxy",
            "data_source": "rgb_fallback",
            "confidence_level": "rgb",
        },
    )
