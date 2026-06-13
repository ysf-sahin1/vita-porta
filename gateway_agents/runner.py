"""Gateway orchestrator.

Reads frames from a ``FrameSource``, groups them into ``window_duration_s``
analysis windows, fans the three visual agents (gait, thermal, expression)
out across a thread pool, and POSTs the resulting :class:`AgentBundle`
to the backend's ``/api/triage/run`` endpoint.

CLI usage::

    python -m gateway_agents.runner                           # default: webcam index 0
    python -m gateway_agents.runner --video data/demo/red.mp4
    python -m gateway_agents.runner --webcam 0
    python -m gateway_agents.runner --mqtt
    python -m gateway_agents.runner --esp 192.168.4.1
    python -m gateway_agents.runner --esp 192.168.4.1 --pir-pin 17   # Raspberry Pi + PIR
    python -m gateway_agents.runner --webcam 0 --mock-pir             # PIR olmadan test
"""

from __future__ import annotations

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor
from types import TracebackType

import httpx

from gateway_agents.agents import (
    AnalysisWindow,
    ExpressionAgent,
    GaitAgent,
    ThermalAgent,
)
from gateway_agents.io import EspCamSource, FrameSource, VideoFileSource, WebcamSource
from gateway_agents.io.pir import PirProtocol, build_pir_trigger
from orchestration.schemas import AgentBundle, AgentObservation, bundle_completeness_issues

logger = logging.getLogger("vita_porta.runner")

_TRIAGE_ENDPOINT = "/api/triage/run"
# Soğuk başlangıçta supervisor pipeline'ı (ChromaDB embed + RAG + Anthropic +
# feedback retrieve) 10sn'yi aşabiliyor — özellikle ilk birkaç pencerede.
# Sıcak cache ile genelde 2-4sn. 30sn marj yeterli, donmaktan korur.
_HTTP_TIMEOUT_S = 30.0


_VERDICT_TIMEOUT_S = 1.5
_ESP_PORT = 80
_VALID_VERDICT_LEVELS = {"red", "yellow", "green", "insufficient"}


class Runner:
    """Pulls frames, runs three agents in parallel, posts the bundle to the backend.

    If ``esp_host`` is provided, the ThermalAgent reads live AMG8833 data from
    ``http://{esp_host}/thermal`` and the supervisor's verdict is pushed back
    to ``http://{esp_host}/verdict`` to drive the LED. With ``esp_host=None``
    the runner falls back to RGB proxy thermal and skips the verdict callback —
    keeping webcam-only / video / unit-test paths unchanged.
    """

    def __init__(
        self,
        source: FrameSource,
        backend_url: str = "http://127.0.0.1:8000",
        window_duration_s: float = 3.0,
        max_workers: int = 3,
        esp_host: str | None = None,
        pir: PirProtocol | None = None,
    ) -> None:
        self.source = source
        self.backend_url = backend_url.rstrip("/")
        self.window_duration_s = window_duration_s
        self.esp_host = esp_host.strip() if esp_host else None

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._http = httpx.Client(timeout=_HTTP_TIMEOUT_S)

        self._gait = GaitAgent()
        self._thermal = ThermalAgent(esp_host=self.esp_host)
        self._expression = ExpressionAgent()

        self._frame_iter = source.frames()
        self._closed = False
        self._pir = pir

    # ------------------------------------------------------------------ public

    def analyze_once(self) -> AgentBundle | None:
        """Collect and analyse one window without posting it to the backend.

        Benchmark and offline evaluation flows use this method so the exact
        gateway agents can be measured without polluting live triage history.
        """

        window = self._collect_window()
        if window is None:
            logger.info("Pencere oluşturulamadı; kaynak tükendi.")
            return None

        logger.info(
            "Pencere toplandı: %d frame @ %.2f fps (≈%.2fs)",
            len(window.frames),
            window.fps,
            window.duration_s,
        )

        bundle = self._analyze(window)
        self._log_bundle(bundle)
        return bundle

    def run_once(self) -> AgentBundle | None:
        """Collect one window, analyse it, POST the bundle, return it."""

        bundle = self.analyze_once()
        if bundle is None:
            return None
        self._post_bundle(bundle)
        return bundle

    def run_forever(self, pir: PirProtocol | None = None) -> None:
        """Loop ``run_once`` until the source is exhausted or Ctrl+C is hit.

        Args:
            pir: PIR tetikleyici. Verilirse her analiz penceresi öncesinde
                 hareket algılanana kadar bloke eder. None ise sürekli çalışır.
        """
        if pir is not None:
            logger.info("PIR modu aktif — hareket algılanmadan analiz başlamaz.")

        _last_pir_motion: bool | None = None

        try:
            while True:
                if pir is not None and not pir.motion_detected:
                    if _last_pir_motion is not False:
                        _last_pir_motion = False
                        self._report_pir_state(motion=False)
                    logger.info("PIR: hareket bekleniyor...")
                    pir.wait_for_motion()
                    logger.info("PIR: hareket algılandı, analiz başlıyor.")
                    _last_pir_motion = True
                    self._report_pir_state(motion=True)
                elif pir is not None and _last_pir_motion is None:
                    _last_pir_motion = True
                    self._report_pir_state(motion=True)

                bundle = self.run_once()
                if bundle is None:
                    logger.info("Kaynak tükendi; döngü sonlandırılıyor.")
                    return
        except KeyboardInterrupt:
            logger.info("Kullanıcı durdurdu (Ctrl+C).")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        self._executor.shutdown(wait=False)
        try:
            self._http.close()
        except Exception:  # noqa: BLE001 — defensive shutdown
            logger.debug("HTTP istemcisi kapatılırken hata yutuldu.", exc_info=True)

        for agent in (
            self._gait,
            self._thermal,
            self._expression,
        ):
            close_fn = getattr(agent, "close", None)
            if callable(close_fn):
                try:
                    close_fn()
                except Exception:  # noqa: BLE001
                    logger.debug("Ajan kapanışında hata yutuldu.", exc_info=True)

        try:
            self.source.close()
        except Exception:  # noqa: BLE001
            logger.debug("Kaynak kapanışında hata yutuldu.", exc_info=True)

        if self._pir is not None:
            try:
                self._pir.close()
            except Exception:  # noqa: BLE001
                logger.debug("PIR kapatılırken hata yutuldu.", exc_info=True)

    # ---------------------------------------------------------------- context

    def __enter__(self) -> Runner:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # --------------------------------------------------------------- internal

    def _collect_window(self) -> AnalysisWindow | None:
        fps = float(self.source.fps) if self.source.fps else 15.0
        target = max(1, int(self.window_duration_s * fps))
        frames: list = []
        for frame in self._frame_iter:
            frames.append(frame)
            if len(frames) >= target:
                break
        if not frames:
            return None
        return AnalysisWindow(frames=frames, fps=fps)

    def _analyze(self, window: AnalysisWindow) -> AgentBundle:
        gait_fut = self._executor.submit(self._gait.analyze, window)
        thermal_fut = self._executor.submit(self._thermal.analyze, window)
        expression_fut = self._executor.submit(self._expression.analyze, window)
        gait_obs = gait_fut.result()
        thermal_obs = thermal_fut.result()
        expression_obs = expression_fut.result()
        return _build_bundle(gait_obs, thermal_obs, expression_obs)

    def _is_bundle_meaningful(self, bundle: AgentBundle) -> bool:
        """3 ajanın da kendi eşiğinin üstünde olmasını şart koşar.

        Analiz politikası (kullanıcı kararı): postür + sıcaklık + yüz ifadesi
        BİR ARADA gelmezse triaj yapılmaz. Tek modaliteyle LLM çağırmak hem
        token israfı hem de garbage-in-garbage-out üretiyor. Eksik kalan
        ajanları debug log'a kaydederiz ki demo'da hangi sensörün düştüğü
        anında görülsün.
        """
        issues = bundle_completeness_issues(bundle)
        if issues:
            logger.debug(
                "Bundle eksik (%d/3 ajan eşik altında): %s",
                len(issues),
                ", ".join(f"{a}({r})" for a, r in issues),
            )
            return False
        return True

    def _post_bundle(self, bundle: AgentBundle) -> None:
        if not self._is_bundle_meaningful(bundle):
            return

        url = f"{self.backend_url}{_TRIAGE_ENDPOINT}"
        try:
            resp = self._http.post(url, json=bundle.model_dump(mode="json"))
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("Backend POST başarısız (%s): %s", url, exc)
            return

        try:
            payload = resp.json()
        except ValueError:
            logger.warning("Backend yanıtı JSON değil: %r", resp.text[:200])
            return

        category = payload.get("category")
        logger.info(
            "Karar: %s — %s (güven=%.2f)",
            category,
            payload.get("rationale_tr"),
            float(payload.get("confidence", 0.0) or 0.0),
        )

        # Karar zincirini kapat: supervisor verdict'ini ESP'ye ilet → LED yanar.
        # esp_host yoksa (webcam/video/test) atlanır.
        if self.esp_host and isinstance(category, str):
            self._push_verdict(category)

    def _report_pir_state(self, motion: bool) -> None:
        """PIR durumunu backend'e bildir — best-effort, hata yutulur."""
        url = f"{self.backend_url}/api/pir/report"
        try:
            self._http.post(url, json={"motion": motion}, timeout=2.0)
        except httpx.HTTPError as exc:
            logger.debug("PIR raporu gönderilemedi (%s): %s", url, exc)

    def _push_verdict(self, category: str) -> None:
        """ESP /verdict endpoint'ini çağır — best-effort, hata yutulur."""

        level = category.lower().strip()
        if level not in _VALID_VERDICT_LEVELS:
            logger.debug("Geçersiz verdict kategorisi atlandı: %r", category)
            return

        url = f"http://{self.esp_host}:{_ESP_PORT}/verdict"
        try:
            resp = self._http.get(
                url,
                params={"level": level, "src": "supervisor"},
                timeout=_VERDICT_TIMEOUT_S,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            logger.warning("ESP /verdict çağrısı başarısız (%s): %s", url, exc)
            return
        logger.info("ESP LED güncellendi: level=%s", level)

    def _log_bundle(self, bundle: AgentBundle) -> None:
        for obs in bundle.observations():
            logger.info(
                "Ajan=%s güven=%.2f özet=%s",
                obs.agent,
                obs.confidence,
                obs.summary_tr,
            )


def _build_bundle(
    gait: AgentObservation,
    thermal: AgentObservation,
    expression: AgentObservation,
) -> AgentBundle:
    return AgentBundle(
        gait=gait,
        thermal=thermal,
        expression=expression,
    )


# ============================================================== CLI plumbing


def _make_source(args: argparse.Namespace) -> FrameSource:
    if args.video is not None:
        return VideoFileSource(path=args.video, loop=args.loop)
    if args.mqtt:
        from gateway_agents.io.mqtt import MqttSource

        return MqttSource()
    if args.esp is not None:
        return EspCamSource(host=args.esp, fallback_webcam=True)
    return WebcamSource(device_index=args.webcam)


def _build_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gateway_agents.runner",
        description="Vita Porta gateway runner — frame yakalar, ajanları çalıştırır, "
        "backend'e gönderir.",
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument(
        "--video",
        type=str,
        default=None,
        help="Dosyadan oynatılacak video yolu (mp4 vs.).",
    )
    src.add_argument(
        "--webcam",
        type=int,
        nargs="?",
        const=0,
        default=None,
        help="Webcam aygıt indexi (varsayılan 0).",
    )
    src.add_argument(
        "--mqtt",
        action="store_true",
        help="Edge cihazından MQTT üzerinden frame al.",
    )
    src.add_argument(
        "--esp",
        type=str,
        default=None,
        metavar="IP",
        help="ESP32-CAM IP adresi (ör. 192.168.1.42). Stream: http://<IP>:81/stream",
    )
    parser.add_argument("--loop", action="store_true", help="Video sonsuz döngüde oynatılsın.")
    parser.add_argument("--backend", type=str, default="http://127.0.0.1:8000")
    parser.add_argument("--window", type=float, default=3.0, help="Pencere süresi (sn).")
    parser.add_argument("--log-level", default="INFO")
    # Raspberry Pi PIR sensörü
    pir_group = parser.add_mutually_exclusive_group()
    pir_group.add_argument(
        "--pir-pin",
        type=int,
        default=None,
        metavar="GPIO",
        help="Raspberry Pi PIR sensörünün GPIO pin numarası (BCM, ör. 17). "
             "PIR_PIN ortam değişkeniyle de ayarlanabilir.",
    )
    pir_group.add_argument(
        "--mock-pir",
        action="store_true",
        help="Gerçek GPIO olmadan PIR modunu simüle eder (geliştirme/test).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_argparser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    # Default to webcam 0 if no source was specified.
    if args.video is None and args.webcam is None and not args.mqtt and args.esp is None:
        args.webcam = 0

    source_label = (
        f"video={args.video}"
        if args.video is not None
        else ("mqtt" if args.mqtt else (f"esp={args.esp}" if args.esp else f"webcam={args.webcam}"))
    )
    logger.info(
        "Vita Porta runner başlatılıyor — kaynak: %s, hedef: %s",
        source_label,
        args.backend,
    )

    import os as _os

    pir: PirProtocol | None = None
    pir_pin = args.pir_pin or (_os.getenv("PIR_PIN") and int(_os.environ["PIR_PIN"]))
    if args.mock_pir:
        pir = build_pir_trigger(pin=0, mock_fallback=True)
    elif pir_pin:
        pir = build_pir_trigger(pin=int(pir_pin), mock_fallback=False)

    source = _make_source(args)
    with Runner(
        source=source,
        backend_url=args.backend,
        window_duration_s=args.window,
        esp_host=args.esp,
        pir=pir,
    ) as runner:
        runner.run_forever(pir=pir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
