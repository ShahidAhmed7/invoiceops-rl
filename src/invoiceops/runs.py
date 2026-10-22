"""Saved episodes: one JSON file per attempt, grouped in run directories."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from invoiceops.episode import ActionEvent, Episode
from invoiceops.verification.verifier import VerifierResult

RUNS_ROOT = Path("runs")


class EpisodeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    task_id: str
    attempt: int
    agent: str
    created_at: str
    end_reason: str | None
    steps: int
    log: list[ActionEvent]
    final_snapshot: dict[str, list[dict[str, Any]]]
    verifier: VerifierResult | None = None
    infrastructure_error: str | None = None
    messages: list[dict[str, Any]] = Field(default_factory=list)
    usage: dict[str, Any] = Field(default_factory=dict)
    seconds: float = 0.0


def now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_episode(
    episode: Episode,
    run_id: str,
    agent: str,
    attempt: int = 0,
    verifier: VerifierResult | None = None,
    infrastructure_error: str | None = None,
    messages: list[dict[str, Any]] | None = None,
    usage: dict[str, Any] | None = None,
    seconds: float = 0.0,
) -> EpisodeRecord:
    return EpisodeRecord(
        run_id=run_id,
        task_id=episode.task_id,
        attempt=attempt,
        agent=agent,
        created_at=now_iso(),
        end_reason=episode.end_reason,
        steps=episode.step_count,
        log=episode.log,
        final_snapshot=episode.snapshot(),
        verifier=verifier,
        infrastructure_error=infrastructure_error,
        messages=messages or [],
        usage=usage or {},
        seconds=seconds,
    )


def episode_path(run_dir: Path, task_id: str, attempt: int) -> Path:
    return run_dir / "episodes" / f"{task_id}__{attempt}.json"


def save_episode(run_dir: Path, record: EpisodeRecord) -> Path:
    path = episode_path(run_dir, record.task_id, record.attempt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=1))
    return path


def load_episodes(run_dir: Path) -> list[EpisodeRecord]:
    files = sorted((run_dir / "episodes").glob("*.json"))
    return [EpisodeRecord.model_validate_json(f.read_text()) for f in files]


def find_run(run_id: str, root: Path = RUNS_ROOT) -> Path:
    for candidate in (Path(run_id), root / run_id):
        if (candidate / "episodes").is_dir():
            return candidate
    raise FileNotFoundError(f"run {run_id} not found under {root}")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
