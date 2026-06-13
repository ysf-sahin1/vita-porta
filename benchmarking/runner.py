"""CLI for repeatable Vita Porta benchmark runs.

Examples:
    python -m benchmarking.runner
    python -m benchmarking.runner --engine configured
    python -m benchmarking.runner --manifest benchmark_manifest.json
"""

from __future__ import annotations

import argparse
import asyncio
import json

from benchmarking.datasets import synthetic_baseline_dataset
from benchmarking.evaluator import build_benchmark_supervisor, evaluate_dataset
from benchmarking.manifest import load_manifest
from benchmarking.store import BenchmarkReportStore


async def _run(args: argparse.Namespace) -> int:
    dataset = load_manifest(args.manifest) if args.manifest else synthetic_baseline_dataset()
    supervisor = build_benchmark_supervisor(args.engine)
    report = await evaluate_dataset(dataset, supervisor, engine=args.engine)
    store = BenchmarkReportStore(args.out)
    store.save(report)

    print(json.dumps(report.metrics.model_dump(mode="json"), ensure_ascii=False, indent=2))
    print(f"\nRapor kaydedildi: {store.path}")
    if report.synthetic:
        print("Not: Bu sentetik baseline klinik performans kanıtı değildir.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Vita Porta etiketli benchmark çalıştırıcısı")
    parser.add_argument(
        "--manifest",
        type=str,
        default=None,
        help="Özel benchmark manifest JSON yolu",
    )
    parser.add_argument(
        "--engine",
        choices=("mock", "configured"),
        default="mock",
        help="Tekrarlanabilir mock veya .env ile yapılandırılmış LLM",
    )
    parser.add_argument("--out", type=str, default=".benchmark/latest.json", help="Rapor JSON yolu")
    return asyncio.run(_run(parser.parse_args(argv)))


if __name__ == "__main__":
    raise SystemExit(main())
