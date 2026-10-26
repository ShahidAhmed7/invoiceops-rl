"""Validate checkpoint candidates and development results before final evaluation."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any


def checkpoint_candidates(root: Path, max_candidates: int) -> list[Path]:
    """Prefer final/recent adapters, evaluating identical saved weights only once."""
    if max_candidates < 1:
        raise ValueError("max_candidates must be positive")
    checkpoints = sorted(
        (root / "checkpoints").glob("checkpoint-*"),
        key=lambda p: int(p.name.split("-")[1]),
        reverse=True,
    )
    candidates, seen = [], set()
    for path in [root / "final_adapter", *checkpoints]:
        weights = sorted(path.glob("adapter_model*.safetensors")) or sorted(
            path.glob("adapter_model*.bin")
        )
        if not weights:
            raise FileNotFoundError(f"no adapter weights in {path}")
        digest = hashlib.sha256()
        for file in [path / "adapter_config.json", *weights]:
            digest.update(file.name.encode())
            with file.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        signature = digest.digest()
        if signature not in seen:
            candidates.append(path)
            seen.add(signature)
        if len(candidates) == max_candidates:
            break
    return candidates


def selection_score(summary: dict[str, Any]) -> float:
    """Never select a checkpoint using an incomplete or unscorable development run."""
    expected = summary["tasks"] * summary["attempts_per_task"]
    score = summary["task_mean_success"]
    if (
        not expected
        or summary["scored_attempts"] != expected
        or summary["unscorable_attempts"]
        or summary.get("missing_attempts", 0)
        or score is None
        or not math.isfinite(score)
        or not 0 <= score <= 1
    ):
        raise ValueError("checkpoint selection requires a complete, fully scored dev run")
    return float(score)
