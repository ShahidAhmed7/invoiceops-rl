"""Tool-calling loop against any OpenAI-compatible chat-completions endpoint (e.g. vLLM).

Standard library only, so it runs anywhere. Model or transport failures are recorded as
infrastructure errors, which make the episode unscorable rather than a graded failure.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from invoiceops.episode import Episode
from invoiceops.tools.spec import openai_tools

NUDGE = "Continue using the tools. When the case is resolved, call submit_case."
# Conservative size estimate for messages the server has not tokenized yet. The densest tool
# observations (digit-heavy JSON) measure about 1.93 characters per token with the Qwen tokenizer.
CHARS_PER_TOKEN = 1.8
MESSAGE_OVERHEAD_TOKENS = 16
# A turn needs room to finish a tool call; with less context left the episode ends unsolved.
MIN_TURN_TOKENS = 1024


class InfrastructureError(RuntimeError):
    pass


@dataclass
class ModelConfig:
    base_url: str
    model: str
    api_key: str = "EMPTY"
    temperature: float = 0.7
    top_p: float = 0.8
    # Per-turn generation cap; each turn also stays within the remaining context.
    max_tokens: int = 16384
    # The server's context window (vLLM --max-model-len); ``None`` means no client-side limit.
    context_tokens: int | None = None
    timeout_s: float = 900.0
    max_tool_calls: int = 40
    max_nudges: int = 2
    http_retries: int = 2
    extra_body: dict[str, Any] = field(default_factory=dict)


def chat(
    cfg: ModelConfig,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]],
    max_tokens: int | None = None,
) -> dict[str, Any]:
    body = {
        "model": cfg.model,
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": cfg.temperature,
        "top_p": cfg.top_p,
        "max_tokens": max_tokens or cfg.max_tokens,
        **cfg.extra_body,
    }
    request = urllib.request.Request(
        cfg.base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {cfg.api_key}"},
        method="POST",
    )
    last: Exception | None = None
    for attempt in range(cfg.http_retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=cfg.timeout_s) as response:
                return dict(json.loads(response.read()))
        except urllib.error.HTTPError as exc:
            last = exc
            with exc:
                detail = exc.read().decode(errors="replace")[:500]
            if exc.code < 500:
                raise InfrastructureError(f"HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
        if attempt < cfg.http_retries:
            time.sleep(min(8.0, 2.0**attempt))
    raise InfrastructureError(f"model endpoint failed: {last}")


def run_episode(
    episode: Episode, prompt: str, system: str, cfg: ModelConfig
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Drive one episode with the model. Returns the transcript and token usage."""
    tools = openai_tools()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    usage: dict[str, Any] = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "requests": 0,
        "truncated_turns": 0,
        "max_context_tokens": 0,
    }
    tool_calls_made = 0
    nudges = 0
    # Tokens the server counted for the conversation so far, and how many messages that covers.
    counted_tokens = _estimate_tokens(messages, tools)
    counted_messages = 0
    while not episode.done and tool_calls_made < cfg.max_tool_calls:
        max_tokens = cfg.max_tokens
        if cfg.context_tokens is not None:
            used = counted_tokens + _estimate_tokens(messages[counted_messages:], [])
            max_tokens = min(max_tokens, cfg.context_tokens - used)
            if max_tokens < MIN_TURN_TOKENS:
                usage["stopped"] = "context_limit"
                break
        response = chat(cfg, messages, tools, max_tokens)
        usage["requests"] += 1
        reported = response.get("usage") or {}
        for key in ("prompt_tokens", "completion_tokens"):
            usage[key] += int(reported.get(key, 0))
        choice = (response.get("choices") or [{}])[0]
        if choice.get("finish_reason") == "length":
            usage["truncated_turns"] += 1
        message = choice.get("message") or {}
        calls = message.get("tool_calls") or []
        assistant: dict[str, Any] = {"role": "assistant", "content": message.get("content") or ""}
        if calls:
            assistant["tool_calls"] = calls
        messages.append(assistant)
        if reported.get("prompt_tokens"):
            counted_tokens = int(reported["prompt_tokens"]) + int(
                reported.get("completion_tokens", 0)
            )
            counted_messages = len(messages)
            usage["max_context_tokens"] = max(usage["max_context_tokens"], counted_tokens)
        if not calls:
            if nudges >= cfg.max_nudges:
                break
            nudges += 1
            messages.append({"role": "user", "content": NUDGE})
            continue
        for call in calls:
            tool_calls_made += 1
            function = call.get("function") or {}
            name = str(function.get("name", ""))
            raw = function.get("arguments") or "{}"
            try:
                arguments = json.loads(raw) if isinstance(raw, str) else dict(raw)
                if not isinstance(arguments, dict):
                    raise ValueError("arguments must be a JSON object")
                observation = episode.step(name, arguments)
            except (ValueError, json.JSONDecodeError) as exc:
                observation = {
                    "ok": False,
                    "error": {"code": "invalid_arguments", "message": f"Bad JSON arguments: {exc}"},
                }
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id", ""),
                    "content": json.dumps(observation, ensure_ascii=False),
                }
            )
            if episode.done:
                break
    return messages, usage


def _estimate_tokens(messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> int:
    """Upper estimate of the tokens these messages (and tool schemas) add to the prompt."""
    chars = sum(len(json.dumps(m, ensure_ascii=False)) for m in messages)
    chars += sum(len(json.dumps(t, ensure_ascii=False)) for t in tools)
    return int(chars / CHARS_PER_TOKEN) + MESSAGE_OVERHEAD_TOKENS * (len(messages) + 1)
