"""Yüz ifadesi ajanı — MediaPipe Face Mesh ile ağrı / bilinç / asimetri tespiti.

468 landmark üzerinden geometrik kural-tabanlı analiz:
    - EAR (Eye Aspect Ratio) → göz açıklığı / bilinç hint'i
    - Kaş içe-çatma (PSPI'ın basitleştirilmiş hâli) → ağrı
    - Sol-sağ landmark çifti sapması → yüz simetrisi (FAST protokol girdisi)

Pre-trained Face Mesh modeli yeterli; özel ağrı sınıflandırıcı bağlanmadan
geometrik proxy modunda çalışır (confidence max 0.55). Gerçek pain estimator
modeli bağlandığında ``sensor_type="trained_model"`` olur, confidence 0.95'e
çıkar.

Çıktı sinyalleri:
    expression_state    str    — "ağrı" | "distres" | "sakin" | "belirsiz"
    pain_score          0..1   — basitleştirilmiş PSPI proxy
    eye_openness        0..1   — EAR normalize edilmiş
    face_asymmetry      0..1   — sol-sağ landmark sapması
    consciousness_hint  str    — "uyanık" | "yarı_uyanık" | "belirsiz"
    face_detected_ratio 0..1   — Face Mesh tespit oranı
    landmark_count      float  — ortalama landmark sayısı (mesh kalitesi)
    sensor_type         str    — "geometric_proxy" | "trained_model"
"""

from __future__ import annotations

import logging

import numpy as np

from gateway_agents.agents.base import Agent, AnalysisWindow
from orchestration.schemas import AgentObservation

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp

    _MP_AVAILABLE = True
except ImportError:
    mp = None  # type: ignore[assignment]
    _MP_AVAILABLE = False


# MediaPipe Face Mesh standart 468-landmark haritasındaki anahtar noktalar
_LEFT_EYE_TOP = 159
_LEFT_EYE_BOTTOM = 145
_LEFT_EYE_INNER = 133
_LEFT_EYE_OUTER = 33

_RIGHT_EYE_TOP = 386
_RIGHT_EYE_BOTTOM = 374
_RIGHT_EYE_INNER = 362
_RIGHT_EYE_OUTER = 263

_LEFT_BROW_INNER = 55
_RIGHT_BROW_INNER = 285

_NOSE_TIP = 1

# Simetri sapması için kullanılacak sol-sağ landmark çiftleri
_SYMMETRY_PAIRS: tuple[tuple[int, int], ...] = (
    (33, 263),   # göz dış köşesi
    (133, 362),  # göz iç köşesi
    (55, 285),   # kaş iç ucu
    (52, 282),   # kaş orta
    (61, 291),   # ağız köşesi
    (50, 280),   # yanak
)

# Eşikler — deneysel kalibrasyon (klinik değer değil, demo amaçlı).
_EAR_OPEN = 0.20
_EAR_HALF = 0.10
_PAIN_HIGH = 0.6
_PAIN_MID = 0.3


class ExpressionAgent(Agent):
    """MediaPipe Face Mesh tabanlı yüz ifadesi / ağrı / bilinç ajanı."""

    name = "expression"

    def __init__(self) -> None:
        if not _MP_AVAILABLE:
            raise RuntimeError("mediapipe yüklü değil. `pip install mediapipe` ile kur.")
        self._mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        if not window.frames:
            return _insufficient("Görüntü alınamadı.")

        ears: list[float] = []
        pains: list[float] = []
        asyms: list[float] = []
        landmark_counts: list[int] = []
        face_hits = 0

        for frame in window.frames:
            if frame is None or frame.ndim != 3:
                continue
            rgb = frame[:, :, ::-1]
            result = self._mesh.process(rgb)
            if not result.multi_face_landmarks:
                continue
            face_hits += 1
            lm = result.multi_face_landmarks[0].landmark
            landmark_counts.append(len(lm))
            ears.append(_eye_aspect_ratio(lm))
            pains.append(_pain_score(lm))
            asyms.append(_face_asymmetry(lm))

        total = len(window.frames)
        if not ears:
            return _insufficient("Yüz mesh tespit edilemedi.")

        ear_mean = float(np.mean(ears))
        pain_mean = float(np.mean(pains))
        asym_mean = float(np.mean(asyms))
        face_ratio = face_hits / max(1, total)
        landmark_avg = float(int(np.mean(landmark_counts))) if landmark_counts else 0.0

        eye_openness = round(float(np.clip(ear_mean / 0.35, 0.0, 1.0)), 3)
        pain_score = round(float(np.clip(pain_mean, 0.0, 1.0)), 3)
        face_asymmetry = round(float(np.clip(asym_mean, 0.0, 1.0)), 3)

        if ear_mean < _EAR_HALF:
            consciousness = "belirsiz"
        elif ear_mean < _EAR_OPEN:
            consciousness = "yarı_uyanık"
        else:
            consciousness = "uyanık"

        if pain_score >= _PAIN_HIGH:
            expression_state = "ağrı"
        elif pain_score >= _PAIN_MID:
            expression_state = "distres"
        elif face_ratio >= 0.5:
            expression_state = "sakin"
        else:
            expression_state = "belirsiz"

        # Geometrik proxy modu: güven üst sınırı 0.55; trained model
        # bağlandığında 0.95'e çıkar.
        confidence = float(min(0.55, 0.20 + 0.55 * face_ratio))

        return AgentObservation(
            agent="expression",
            confidence=confidence,
            summary_tr=_build_summary(expression_state, eye_openness, face_asymmetry),
            signals={
                "expression_state": expression_state,
                "pain_score": pain_score,
                "eye_openness": eye_openness,
                "face_asymmetry": face_asymmetry,
                "consciousness_hint": consciousness,
                "face_detected_ratio": round(face_ratio, 3),
                "landmark_count": landmark_avg,
                "sensor_type": "geometric_proxy",
            },
        )

    def close(self) -> None:
        try:
            self._mesh.close()
        except Exception:  # noqa: BLE001 — defensive shutdown
            logger.debug("Face mesh kapanışında hata yutuldu.", exc_info=True)


def _eye_aspect_ratio(lm) -> float:
    """Soldaki ve sağdaki EAR ortalaması; 0.25 civarı normal açık göz."""

    def _ear(top: int, bot: int, inner: int, outer: int) -> float:
        vertical = abs(lm[top].y - lm[bot].y)
        horizontal = abs(lm[inner].x - lm[outer].x)
        if horizontal < 1e-6:
            return 0.0
        return float(vertical / horizontal)

    left = _ear(_LEFT_EYE_TOP, _LEFT_EYE_BOTTOM, _LEFT_EYE_INNER, _LEFT_EYE_OUTER)
    right = _ear(_RIGHT_EYE_TOP, _RIGHT_EYE_BOTTOM, _RIGHT_EYE_INNER, _RIGHT_EYE_OUTER)
    return (left + right) / 2.0


def _pain_score(lm) -> float:
    """PSPI'ın basitleştirilmiş hâli: kaş içe-çatma + göz kısma kombinasyonu.

    Gerçek PSPI dört AU'nun toplamıdır (kaş düşürme, göz kısma, dudak
    kalkması, göz kapama). Burada eğitilmiş sınıflandırıcı yokken sadece
    geometrik olarak ölçülebilen iki bileşeni kullanıyoruz.
    """

    brow_distance = abs(lm[_LEFT_BROW_INNER].x - lm[_RIGHT_BROW_INNER].x)
    face_width = abs(lm[_LEFT_EYE_OUTER].x - lm[_RIGHT_EYE_OUTER].x)
    if face_width < 1e-6:
        return 0.0

    brow_ratio = brow_distance / face_width
    # Nötr yüzde brow_ratio ≈ 0.30-0.35; kaş çatıkken ≈ 0.20-0.25
    brow_furrow = float(np.clip((0.35 - brow_ratio) / 0.15, 0.0, 1.0))

    ear = _eye_aspect_ratio(lm)
    # Normal göz EAR ≈ 0.25-0.30; göz kısıkken ≈ 0.10-0.15
    eye_squint = float(np.clip((0.25 - ear) / 0.20, 0.0, 1.0))

    return 0.6 * brow_furrow + 0.4 * eye_squint


def _face_asymmetry(lm) -> float:
    """Sol-sağ landmark çiftlerinin yüz orta hattına göre sapması (0..1)."""

    nose_x = lm[_NOSE_TIP].x
    face_width = abs(lm[_LEFT_EYE_OUTER].x - lm[_RIGHT_EYE_OUTER].x)
    if face_width < 1e-6:
        return 0.0

    deltas: list[float] = []
    for left_idx, right_idx in _SYMMETRY_PAIRS:
        left = lm[left_idx]
        right = lm[right_idx]
        left_dx = abs(left.x - nose_x)
        right_dx = abs(right.x - nose_x)
        x_delta = abs(left_dx - right_dx) / face_width
        y_delta = abs(left.y - right.y) / face_width
        deltas.append(x_delta + y_delta)

    raw = float(np.mean(deltas)) if deltas else 0.0
    # 0.0-0.15 normal aralık; >0.30 belirgin asimetri (felç şüphesi)
    return float(np.clip(raw / 0.30, 0.0, 1.0))


def _build_summary(state: str, eye_openness: float, asymmetry: float) -> str:
    asym_note = ", yüz asimetrisi belirgin" if asymmetry >= 0.6 else ""
    if state == "ağrı":
        return (
            f"Yüz ifadesi: ağrı bulguları (göz %{int(eye_openness*100)} açık)"
            f"{asym_note}. [Geometrik proxy]"
        )
    if state == "distres":
        return f"Yüz ifadesi: distres / rahatsızlık belirtileri{asym_note}. [Geometrik proxy]"
    if state == "sakin":
        return f"Yüz ifadesi: sakin, ağrı sinyali yok{asym_note}. [Geometrik proxy]"
    return "Yüz ifadesi belirsiz — yeterli mimik sinyali yok. [Geometrik proxy]"


def _insufficient(reason: str) -> AgentObservation:
    return AgentObservation(
        agent="expression",
        confidence=0.0,
        summary_tr=f"Yüz ifadesi verisi yetersiz: {reason}",
        signals={
            "expression_state": "belirsiz",
            "pain_score": 0.0,
            "eye_openness": 0.0,
            "face_asymmetry": 0.0,
            "consciousness_hint": "belirsiz",
            "face_detected_ratio": 0.0,
            "landmark_count": 0.0,
            "sensor_type": "geometric_proxy",
        },
    )
