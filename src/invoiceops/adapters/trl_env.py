"""Adapter for TRL's ``GRPOTrainer(environment_factory=...)`` (verified against TRL 1.16.0).

TRL creates one instance per rollout, calls ``reset(**dataset_row)`` before generation,
exposes every public method as a tool, and calls ``get_reward()`` once the rollout ends.
The dataset row carries a ``task_id`` (a task on disk) or a ``generated`` spec for a
procedurally generated training instance; the agent never chooses its task.

This module imports nothing from TRL, so it can be tested without the training stack.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from invoiceops.adapters.tool_methods import ToolMethods
from invoiceops.episode import Episode
from invoiceops.tasks.build import build_task
from invoiceops.tasks.model import TaskBundle
from invoiceops.tasks.store import load_bundle
from invoiceops.verification.verifier import verify_episode
from invoiceops.worlds.companies import COMPANIES_BY_ID

log = logging.getLogger(__name__)


def bundle_for_row(row: dict[str, Any]) -> TaskBundle:
    """Resolve a dataset row to a task. Rows are created by the trusted training script."""
    if row.get("generated"):
        spec = (
            json.loads(row["generated"]) if isinstance(row["generated"], str) else row["generated"]
        )
        return build_task(
            COMPANIES_BY_ID[spec["world_id"]], spec["family"], spec["variant"], salt=spec["salt"]
        )
    return load_bundle(str(row["task_id"]))


class InvoiceOpsToolEnv(ToolMethods):
    def __init__(self) -> None:
        self._episode: Episode | None = None
        self._bundle: TaskBundle | None = None

    def reset(self, **row: Any) -> str | None:
        """Start a fresh episode for the task named in the dataset row."""
        if self._episode is not None:
            self._episode.close()
        self._bundle = bundle_for_row(row)
        self._episode = Episode(
            self._bundle.public.world,
            self._bundle.public.task_id,
            max_steps=self._bundle.public.max_steps,
        )
        return None  # the task prompt is already in the dataset's "prompt" column

    def get_reward(self) -> float | None:
        """Strict 0/1 reward from the trusted verifier; ``None`` if the episode is unscorable."""
        if self._episode is None or self._bundle is None:
            return None
        result = verify_episode(self._episode, self._bundle.private)
        if not result.scorable:
            log.error("unscorable episode %s: %s", self._bundle.public.task_id, result.error)
            return None
        return result.reward

    def _dispatch(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self._episode is None:
            return {"ok": False, "error": {"code": "episode_finished", "message": "No episode."}}
        return self._episode.step(tool, arguments)
