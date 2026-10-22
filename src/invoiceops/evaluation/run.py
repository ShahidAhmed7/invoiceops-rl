"""Run agents on tasks, grade every attempt, and write a report."""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from invoiceops.agents.openai_runner import InfrastructureError, ModelConfig, run_episode
from invoiceops.agents.oracle import solve
from invoiceops.agents.prompts import system_prompt
from invoiceops.agents.scripted import SCRIPTED
from invoiceops.episode import Episode
from invoiceops.evaluation.metrics import summarise, to_markdown
from invoiceops.runs import EpisodeRecord, record_episode, save_episode, write_json
from invoiceops.tasks.model import PrivateTask
from invoiceops.tasks.store import DEFAULT_TASK_ROOT, load_bundle
from invoiceops.verification.verifier import verify_episode

LOCAL_AGENTS: dict[str, Callable[[Episode], None]] = {"oracle": solve, **SCRIPTED}


def run_attempt(
    task_id: str,
    attempt: int,
    agent: str,
    run_id: str,
    model: ModelConfig | None,
    prompt_version: str,
    task_root: Path,
) -> EpisodeRecord:
    bundle = load_bundle(task_id, task_root)
    episode = Episode(bundle.public.world, task_id, max_steps=bundle.public.max_steps)
    messages: list[dict[str, Any]] = []
    usage: dict[str, Any] = {}
    error: str | None = None
    start = time.monotonic()
    try:
        if agent == "model":
            assert model is not None
            messages, usage = run_episode(
                episode, bundle.public.prompt, system_prompt(prompt_version), model
            )
        else:
            LOCAL_AGENTS[agent](episode)
    except InfrastructureError as exc:
        error = str(exc)
    seconds = time.monotonic() - start
    verifier = None if error else verify_episode(episode, bundle.private)
    record = record_episode(
        episode, run_id, agent, attempt, verifier, error, messages, usage, seconds
    )
    episode.close()
    return record


def evaluate(
    agent: str,
    task_ids: list[str],
    run_dir: Path,
    attempts: int = 1,
    model: ModelConfig | None = None,
    prompt_version: str = "v1",
    concurrency: int = 1,
    task_root: Path = DEFAULT_TASK_ROOT,
    extra_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if agent not in LOCAL_AGENTS and agent != "model":
        raise ValueError(f"unknown agent {agent}")
    run_id = run_dir.name
    jobs = [(t, a) for t in task_ids for a in range(attempts)]

    def work(job: tuple[str, int]) -> EpisodeRecord:
        record = run_attempt(job[0], job[1], agent, run_id, model, prompt_version, task_root)
        save_episode(run_dir, record)
        return record

    with ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        records = list(pool.map(work, jobs))
    privates: dict[str, PrivateTask] = {t: load_bundle(t, task_root).private for t in task_ids}
    summary = summarise(records, privates)
    config: dict[str, Any] = {
        "agent": agent,
        "tasks": len(task_ids),
        "attempts": attempts,
        "prompt_version": prompt_version if agent == "model" else "n/a",
        **(extra_config or {}),
    }
    if model is not None:
        config.update(
            model=model.model,
            temperature=model.temperature,
            top_p=model.top_p,
            max_tool_calls=model.max_tool_calls,
            max_tokens=model.max_tokens,
        )
    write_json(run_dir / "config.json", config)
    write_json(run_dir / "summary.json", summary)
    (run_dir / "report.md").write_text(to_markdown(f"Evaluation: {agent}", config, summary))
    return summary
