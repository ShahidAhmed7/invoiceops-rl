"""OpenEnv adapter (verified against ``openenv==0.10.0``; install with ``invoiceops[openenv]``).

The environment is an ``MCPEnvironment``: agents discover tools with ``ListToolsAction`` and
call them with ``CallToolAction``. Persistent episodes use OpenEnv's WebSocket session
endpoint (``/ws``); the plain HTTP ``/reset`` and ``/step`` endpoints create a fresh
environment per request.

``reset`` takes ``task_id`` from the trusted controller. Rewards are attached to the terminal
observation only when private task specs are mounted (``INVOICEOPS_PRIVATE_ROOT``); in the
agent-facing container they are not, and grading happens in the separate verifier container
from the episode export written to ``INVOICEOPS_EXPORT_DIR``.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from openenv.core.env_server.mcp_environment import MCPEnvironment
from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field

from invoiceops.adapters.tool_methods import TOOL_METHOD_NAMES, ToolMethods
from invoiceops.episode import Episode
from invoiceops.tasks.model import PublicTask
from invoiceops.tasks.store import DEFAULT_TASK_ROOT, load_private, load_public


class InvoiceOpsState(State):
    task_id: str | None = Field(default=None, description="Task being worked")


class InvoiceOpsResetObservation(Observation):
    task_id: str = Field(description="Task id")
    prompt: str = Field(description="Instructions for the agent")


class _Tools(ToolMethods):
    def __init__(self, env: InvoiceOpsEnvironment) -> None:
        self._env = env

    def _dispatch(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        episode = self._env.episode
        if episode is None:
            return {
                "ok": False,
                "error": {"code": "episode_finished", "message": "Call reset first."},
            }
        return episode.step(tool, arguments)


class InvoiceOpsEnvironment(MCPEnvironment):
    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self) -> None:
        mcp = FastMCP("invoiceops")
        self._tools = _Tools(self)
        for name in TOOL_METHOD_NAMES:
            mcp.tool(getattr(self._tools, name))
        super().__init__(mcp)
        self.episode: Episode | None = None
        self._public: PublicTask | None = None
        self._state = InvoiceOpsState(episode_id=None, step_count=0)
        self._task_root = Path(os.environ.get("INVOICEOPS_TASK_ROOT", DEFAULT_TASK_ROOT))
        private = os.environ.get("INVOICEOPS_PRIVATE_ROOT")
        self._private_root = Path(private) if private else None
        export = os.environ.get("INVOICEOPS_EXPORT_DIR")
        self._export_dir = Path(export) if export else None
        self._finalised = False

    def reset(
        self,
        seed: int | None = None,
        episode_id: str | None = None,
        task_id: str | None = None,
        **kwargs: Any,
    ) -> InvoiceOpsResetObservation:
        if not task_id:
            raise ValueError("reset requires task_id (chosen by the controller)")
        if self.episode is not None:
            self.episode.close()
        self._public = load_public(task_id, self._task_root)
        self.episode = Episode(
            self._public.world, task_id, max_steps=self._public.max_steps, episode_id=episode_id
        )
        self._finalised = False
        self._state = InvoiceOpsState(
            episode_id=self.episode.episode_id, step_count=0, task_id=task_id
        )
        return InvoiceOpsResetObservation(task_id=task_id, prompt=self._public.prompt, done=False)

    def step(self, action: Action, timeout_s: float | None = None, **kwargs: Any) -> Observation:
        return self._finish(super().step(action, timeout_s=timeout_s, **kwargs))

    async def step_async(
        self, action: Action, timeout_s: float | None = None, **kwargs: Any
    ) -> Observation:
        return self._finish(await super().step_async(action, timeout_s=timeout_s, **kwargs))

    def _step_impl(
        self, action: Action, timeout_s: float | None = None, **kwargs: Any
    ) -> Observation:
        return Observation(done=False, metadata={"error": "Use ListToolsAction or CallToolAction."})

    def _finish(self, observation: Observation) -> Observation:
        episode = self.episode
        if episode is None:
            return observation
        self._state = InvoiceOpsState(
            episode_id=episode.episode_id, step_count=episode.step_count, task_id=episode.task_id
        )
        if not episode.done:
            return observation
        observation.done = True
        if self._finalised:
            return observation
        self._finalised = True
        if self._export_dir is not None:
            self._export_dir.mkdir(parents=True, exist_ok=True)
            export = {
                "task_id": episode.task_id,
                "episode_id": episode.episode_id,
                "end_reason": episode.end_reason,
                "log": [e.model_dump() for e in episode.log],
                "final_snapshot": episode.snapshot(),
            }
            path = self._export_dir / f"{episode.episode_id}.json"
            path.write_text(json.dumps(export))
        if self._private_root is not None:
            private = load_private(episode.task_id, self._private_root)
            # Imported here: the agent-facing image ships without the verifier package.
            from invoiceops.verification.verifier import verify_episode

            result = verify_episode(episode, private)
            observation.reward = result.reward
            observation.metadata = {**observation.metadata, "verifier": result.model_dump()}
        return observation

    @property
    def state(self) -> InvoiceOpsState:
        return self._state

    def close(self) -> None:
        if self.episode is not None:
            self.episode.close()
            self.episode = None
        super().close()
