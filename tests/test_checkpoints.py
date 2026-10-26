from __future__ import annotations

from pathlib import Path

import pytest
from modal_app.checkpoints import checkpoint_candidates, selection_score


def _adapter(root: Path, name: str, weights: bytes) -> Path:
    folder = root / name if name == "final_adapter" else root / "checkpoints" / name
    folder.mkdir(parents=True)
    (folder / "adapter_config.json").write_text('{"r": 16}')
    (folder / "adapter_model.safetensors").write_bytes(weights)
    return folder


def test_candidate_selection_deduplicates_final_and_fills_with_distinct_checkpoints(
    tmp_path: Path,
) -> None:
    final = _adapter(tmp_path, "final_adapter", b"step150")
    _adapter(tmp_path, "checkpoint-150", b"step150")
    previous = [
        _adapter(tmp_path, f"checkpoint-{step}", str(step).encode()) for step in (125, 100, 75)
    ]
    assert checkpoint_candidates(tmp_path, 4) == [final, *previous]
    assert checkpoint_candidates(tmp_path, 1) == [final]


def test_missing_adapter_fails_before_serving(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="no adapter weights"):
        checkpoint_candidates(tmp_path, 4)


def test_checkpoint_selection_requires_all_dev_attempts_scored() -> None:
    summary = {
        "tasks": 12,
        "attempts_per_task": 2,
        "scored_attempts": 24,
        "unscorable_attempts": 0,
        "task_mean_success": 0.0,
    }
    assert selection_score(summary) == 0.0  # a genuine all-fail run is still valid
    for update in (
        {"scored_attempts": 23},
        {"unscorable_attempts": 1},
        {"missing_attempts": 1},
        {"task_mean_success": None},
        {"task_mean_success": float("nan")},
    ):
        with pytest.raises(ValueError, match="fully scored"):
            selection_score({**summary, **update})
