"""Gateway orchestrator.

Bir frame kaynağından sürekli pencere alır, üç ajanı paralel çalıştırır, bir
AgentBundle üretip backend'in /api/triage/run endpoint'ine POST eder.

Kullanım:
    python -m gateway_agents.runner --source webcam
    python -m gateway_agents.runner --source video --path data/demo/red.mp4 --loop
    python -m gateway_agents.runner --source webcam --dry-run   # backend'e göndermez, stdout'a basar
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from concurrent.futures import ThreadPoolExecutor

import httpx

from gateway_agents.agents import (
    AnalysisWindow,
    GaitAgent,
    RespirationAgent,
    SkinAgent,
)
from gateway_agents.io import FrameSource, VideoFileSource, WebcamSource
from orchestration.schemas import AgentBundle, AgentObservation

logger = logging.getLogger("vita_porta.gateway")


class GatewayRunner:
    def __init__(
        self,
        source: FrameSource,
        backend_url: str = "http://127.0.0.1:8000",
        dry_run: bool = False,
    ) -> None:
        self.source = source
        self.backend_url = backend_url.rstrip("/")
        self.dry_run = dry_run
        self._executor = ThreadPoolExecutor(max_workers=3)
        # Ajanları lazily yarat — webcam yokken bile import edilebilsin diye burada
        self._gait = GaitAgent()
        self._skin = SkinAgent()
        self._respiration = RespirationAgent()

    async def run(self) -> None:
        async with httpx.AsyncClient(timeout=15.0) as client:
            for window in self.source.windows():
                bundle = await self._analyze_window(window)
                if self.dry_run:
                    logger.info(
                        "DRY-RUN bundle: gait=%s skin=%s resp=%s",
                        bundle.gait and bundle.gait.summary_tr,
                        bundle.skin and bundle.skin.summary_tr,
                        bundle.respiration and bundle.respiration.summary_tr,
                    )
                    continue
                try:
                    resp = await client.post(
                        f"{self.backend_url}/api/triage/run",
                        json=bundle.model_dump(mode="json"),
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                    logger.info(
                        "Karar: %s — %s",
                        payload.get("category"),
                        payload.get("rationale_tr"),
                    )
                except httpx.HTTPError as exc:
                    logger.warning("Backend POST başarısız: %s", exc)

    async def _analyze_window(self, window: AnalysisWindow) -> AgentBundle:
        loop = asyncio.get_running_loop()
        # 3 ajanı paralel çalıştır — CPU-bound olduğu için thread pool yeterli
        gait_fut = loop.run_in_executor(self._executor, self._gait.analyze, window)
        skin_fut = loop.run_in_executor(self._executor, self._skin.analyze, window)
        resp_fut = loop.run_in_executor(self._executor, self._respiration.analyze, window)
        gait_obs, skin_obs, resp_obs = await asyncio.gather(gait_fut, skin_fut, resp_fut)
        return _build_bundle(gait_obs, skin_obs, resp_obs)

    def close(self) -> None:
        self._executor.shutdown(wait=False)
        self.source.close()
        if hasattr(self._gait, "close"):
            self._gait.close()
        if hasattr(self._skin, "close"):
            self._skin.close()


def _build_bundle(
    gait: AgentObservation,
    skin: AgentObservation,
    respiration: AgentObservation,
) -> AgentBundle:
    return AgentBundle(gait=gait, skin=skin, respiration=respiration)


def _make_source(args: argparse.Namespace) -> FrameSource:
    if args.source == "webcam":
        return WebcamSource(
            camera_index=args.camera,
            window_seconds=args.window,
            target_fps=args.fps,
        )
    if args.source == "video":
        if not args.path:
            raise SystemExit("video kaynağı için --path zorunlu.")
        return VideoFileSource(path=args.path, window_seconds=args.window, loop=args.loop)
    raise SystemExit(f"Bilinmeyen kaynak: {args.source}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vita Porta gateway runner")
    parser.add_argument("--source", choices=["webcam", "video"], default="webcam")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--path", type=str, default=None)
    parser.add_argument("--loop", action="store_true", help="Video sonsuz döngü")
    parser.add_argument("--window", type=float, default=3.0, help="Pencere süresi (sn)")
    parser.add_argument("--fps", type=float, default=15.0)
    parser.add_argument("--backend", type=str, default="http://127.0.0.1:8000")
    parser.add_argument("--dry-run", action="store_true", help="Backend'e POST etme")
    parser.add_argument("--log-level", default="INFO")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )

    source = _make_source(args)
    runner = GatewayRunner(source=source, backend_url=args.backend, dry_run=args.dry_run)
    try:
        asyncio.run(runner.run())
    except KeyboardInterrupt:
        logger.info("Durduruldu (Ctrl+C).")
    finally:
        runner.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
