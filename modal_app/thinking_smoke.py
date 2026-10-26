"""Dev-only inference smoke for Thinking-2507, including reasoning and latency diagnostics."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from invoiceops.agents.openai_runner import ModelConfig, chat
from invoiceops.evaluation.run import evaluate
from invoiceops.runs import load_episodes
from invoiceops.tasks.store import task_ids
from invoiceops.tools.spec import openai_tools
from modal_app import settings, vllm_server


def distribution(values: list[float]) -> dict[str, float | int | None]:
    ordered = sorted(values)
    return {
        "count": len(values),
        "total": sum(values),
        "mean": sum(values) / len(values) if values else None,
        "p50": ordered[math.ceil(0.50 * len(values)) - 1] if values else None,
        "p95": ordered[math.ceil(0.95 * len(values)) - 1] if values else None,
        "max": max(values) if values else None,
    }


def roundtrip(cfg: ModelConfig) -> dict[str, Any]:
    tools = [t for t in openai_tools() if t["function"]["name"] in ("get_invoice", "get_receipts")]
    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": "Read invoice INV-1 and the receipts for PO PO-7. Use both tools.",
        }
    ]
    parsed: list[dict[str, Any]] = []
    reasoning_tokens = completion_tokens = 0
    started = time.monotonic()
    finish_reasons = []
    for _ in range(3):
        reply = chat(cfg, messages, tools)
        choice = reply["choices"][0]
        message = choice["message"]
        finish_reasons.append(choice.get("finish_reason"))
        completion_tokens += int((reply.get("usage") or {}).get("completion_tokens", 0))
        thought = message.get("reasoning") or message.get("reasoning_content") or ""
        if thought and cfg.reasoning_token_counter is not None:
            reasoning_tokens += cfg.reasoning_token_counter(thought)
        calls = message.get("tool_calls") or []
        messages.append(
            {"role": "assistant", "content": message.get("content") or "", "tool_calls": calls}
        )
        for call in calls:
            function = call["function"]
            arguments = json.loads(function["arguments"])
            parsed.append({"name": function["name"], "arguments": arguments})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": json.dumps(
                        {"ok": True, "result": {"invoice_id": "INV-1", "po_id": "PO-7"}}
                    ),
                }
            )
        if {p["name"] for p in parsed} == {"get_invoice", "get_receipts"}:
            break
    correct = any(
        p == {"name": "get_invoice", "arguments": {"invoice_id": "INV-1"}} for p in parsed
    ) and any(p == {"name": "get_receipts", "arguments": {"po_id": "PO-7"}} for p in parsed)
    return {
        "ok": correct and "length" not in finish_reasons,
        "tool_calls": parsed,
        "reasoning_tokens": reasoning_tokens,
        "completion_tokens": completion_tokens,
        "finish_reasons": finish_reasons,
        "seconds": time.monotonic() - started,
    }


def run_smoke(run_dir: Path) -> dict[str, Any]:
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer

    model = settings.THINKING_MODEL
    revision = settings.REVISIONS[model]
    tokenizer = Tokenizer.from_file(hf_hub_download(model, "tokenizer.json", revision=revision))
    cfg = ModelConfig(
        base_url="http://127.0.0.1:8001/v1",
        model="agent",
        temperature=0.6,
        top_p=0.95,
        max_tokens=32768,
        context_tokens=131072,
        extra_body={"top_k": 20},
        reasoning_token_counter=lambda text: len(tokenizer.encode(text).ids),
    )
    started = time.monotonic()
    proc = vllm_server.start(
        model, 8001, "agent", 0.85, revision=revision, extra=("--reasoning-parser", "qwen3")
    )
    startup_seconds = time.monotonic() - started
    try:
        tool_check = roundtrip(cfg)
        summary = evaluate(
            "model",
            task_ids("dev"),
            run_dir,
            attempts=1,
            model=cfg,
            prompt_version=settings.AGENT_PROMPT,
            concurrency=4,
            extra_config={
                "model_id": model,
                "revision": revision,
                "splits": ["dev"],
                "context_tokens": cfg.context_tokens,
                "top_k": 20,
                "reasoning_parser": "qwen3",
                "thinking_token_budget": None,
            },
        )
        records = load_episodes(run_dir)
        turns = [turn for record in records for turn in record.usage.get("turns", [])]
        counts = [
            turn["reasoning_tokens"] for turn in turns if turn["reasoning_tokens"] is not None
        ]
        result = {
            "model": model,
            "revision": revision,
            "prompt": settings.AGENT_PROMPT,
            "max_tokens_per_turn": cfg.max_tokens,
            "context_tokens": cfg.context_tokens,
            "temperature": cfg.temperature,
            "top_p": cfg.top_p,
            "top_k": 20,
            "concurrency": 4,
            "roundtrip": tool_check,
            "dev": summary,
            "startup_seconds": startup_seconds,
            "total_seconds": time.monotonic() - started,
            "reasoning_token_count_method": "Pinned tokenizer applied to parsed reasoning text",
            "reasoning_tokens_per_turn": distribution(counts),
            "turns_with_unknown_reasoning_token_count": len(turns) - len(counts),
            "completion_tokens_per_turn": distribution([t["completion_tokens"] for t in turns]),
            "seconds_per_turn": distribution([t["seconds"] for t in turns]),
            "seconds_per_episode": distribution([r.seconds for r in records]),
            "episodes": [
                {
                    "task_id": r.task_id,
                    "passed": r.verifier.passed if r.verifier else None,
                    "error": r.infrastructure_error,
                    "seconds": r.seconds,
                    "completion_tokens": r.usage.get("completion_tokens"),
                    "reasoning_tokens": r.usage.get("reasoning_tokens"),
                    "truncated_turns": r.usage.get("truncated_turns"),
                    "failed_checks": [c.name for c in r.verifier.failed_checks()]
                    if r.verifier
                    else [],
                    "turns": r.usage.get("turns", []),
                }
                for r in records
            ],
        }
        result["pipeline_ok"] = (
            tool_check["ok"]
            and summary["scored_attempts"] == 12
            and summary["unscorable_attempts"] == 0
            and summary["tokens"]["truncated_turns"] == 0
            and summary["tokens"]["context_limit_stops"] == 0
            and sum(counts) > 0
        )
        return result
    finally:
        vllm_server.stop(proc)
