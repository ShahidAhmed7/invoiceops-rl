"""Load tasks from the ``tasks/`` directory."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from invoiceops.tasks.model import PrivateTask, PublicTask, TaskBundle

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TASK_ROOT = Path(os.environ.get("INVOICEOPS_TASK_ROOT", REPO_ROOT / "tasks"))


def _task_dir(task_id: str, root: Path) -> Path:
    matches = sorted(root.glob(f"*/{task_id}"))
    if len(matches) != 1:
        raise KeyError(f"task {task_id} not found under {root}")
    return matches[0]


def load_public(task_id: str, root: Path = DEFAULT_TASK_ROOT) -> PublicTask:
    path = _task_dir(task_id, root) / "public.json"
    return PublicTask.model_validate_json(path.read_text())


def load_private(task_id: str, root: Path = DEFAULT_TASK_ROOT) -> PrivateTask:
    path = _task_dir(task_id, root) / "private.json"
    return PrivateTask.model_validate_json(path.read_text())


def load_bundle(task_id: str, root: Path = DEFAULT_TASK_ROOT) -> TaskBundle:
    return TaskBundle(public=load_public(task_id, root), private=load_private(task_id, root))


@lru_cache(maxsize=8)
def manifest(root: Path = DEFAULT_TASK_ROOT) -> tuple[dict[str, str], ...]:
    return tuple(json.loads((root / "manifest.json").read_text()))


def task_ids(split: str | None = None, root: Path = DEFAULT_TASK_ROOT) -> list[str]:
    return [row["task_id"] for row in manifest(root) if split is None or row["split"] == split]
