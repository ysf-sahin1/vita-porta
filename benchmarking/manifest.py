"""Load custom expert-labelled bundle or video benchmark manifests."""

from __future__ import annotations

from pathlib import Path

from benchmarking.models import BenchmarkDataset


def load_manifest(path: Path | str) -> BenchmarkDataset:
    manifest_path = Path(path).resolve()
    dataset = BenchmarkDataset.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    for case in dataset.cases:
        if case.video_path:
            video_path = Path(case.video_path)
            if not video_path.is_absolute():
                case.video_path = str((manifest_path.parent / video_path).resolve())
    return dataset
