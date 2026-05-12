"""Gateway orchestrator.

Reads frames from a ``FrameSource``, groups them into ``window_duration_s``
analysis windows, fans the three visual agents out across a thread pool, and
POSTs the resulting :class:`AgentBundle` to the backend's ``/api/triage/run``
endpoint.

CLI usage::

    python -m gateway_agents.runner                       # default: webcam index 0
    python -m gateway_agents.runner --video data/demo/red.mp4
    python -m gateway_agents.runner --webcam 0
    python -m gateway_agents.runner --mqtt
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
    GaitAgent,
    RespirationAgent,
    SkinAgent,
)
from gateway_agents.io import FrameSource, VideoFileSource, WebcamSource
from orchestration.schemas import AgentBundle, AgentObservation

logger = logging.getLogger("vita_porta.runner")

_TRIAGE_ENDPOINT = "/api/triage/run"
_HTTP_TIMEOUT_S = 10.0


class Runner:
    """Pulls frames, runs three agents in parallel, posts the bundle to the backend."""

    def __init__(
        self,
        source: FrameSource,
        backend_url: str = "http://127.0.0.1:8000",
        window_duration_s: float = 3.0,
        max_workers: int = 3,
    ) -> None:
        self.source = source
        self.backend_url = backend_url.rstrip("/")
        self.window_duration_s = window_duration_s

        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._http = httpx.Client(timeout=_HTTP_TIMEOUT_S)

        self._gait = GaitAgent()
        self._skin = SkinAgent()
        self._respiration = RespirationAgent()

        self._frame_iter = source.frames()
        self._closed = False

    # ------------------------------------------------------------------ public

    def run_once(self) -> AgentBundle | None:
        """Collect one window, analyse it, POST the bundle, return it."""

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
        self._post_bundle(bundle)
        return bundle

    def run_forever(self) -> None:
        """Loop ``run_once`` until the source is exhausted or Ctrl+C is hit."""

        try:
            while True:
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

        for agent in (self._gait, self._skin, self._respiration):
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

    # ---------------------------------------------------------------- context

    def __enter__(self) -> "Runner":
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
        skin_fut = self._executor.submit(self._skin.analyze, window)
        resp_fut = self._executor.submit(self._respiration.analyze, window)
        gait_obs = gait_fut.result()
        skin_obs = skin_fut.result()
        resp_obs = resp_fut.result()
        return _build_bundle(gait_obs, skin_obs, resp_obs)

    def _post_bundle(self, bundle: AgentBundle) -> None:
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

        logger.info(
            "Karar: %s — %s (güven=%.2f)",
            payload.get("category"),
            payload.get("rationale_tr"),
            float(payload.get("confidence", 0.0) or 0.0),
        )

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
    skin: AgentObservation,
    respiration: AgentObservation,
) -> AgentBundle:
    return AgentBundle(gait=gait, skin=skin, respiration=respiration)


# ============================================================== CLI plumbing


def _make_source(args: argparse.Namespace) -> FrameSource:
    if args.video is not None:
        return VideoFileSource(path=args.video, loop=args.loop)
    if args.mqtt:
        # Lazy import — paho-mqtt is optional at runtime.
        from gateway_agents.io.mqtt import MqttSource

        return MqttSource()
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
    parser.add_argument("--loop", action="store_true", help="Video sonsuz döngüde oynatılsın.")
    parser.add_argument("--backend", type=str, default="http://127.0.0.1:8000")
    parser.add_argument("--window", type=float, default=3.0, help="Pencere süresi (sn).")
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_argparser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    # Default to webcam 0 if nothing was specified.
    if args.video is None and args.webcam is None and not args.mqtt:
        args.webcam = 0

    source_label = (
        f"video={args.video}"
        if args.video is not None
        else ("mqtt" if args.mqtt else f"webcam={args.webcam}")
    )
    logger.info("Vita Porta runner başlatılıyor — kaynak: %s, hedef: %s", source_label, args.backend)

    source = _make_source(args)
    with Runner(
        source=source,
        backend_url=args.backend,
        window_duration_s=args.window,
    ) as runner:
        runner.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
