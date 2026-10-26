"""Modal-side glue for durable rollout logging.

Attaches a :class:`RolloutRecorder` to the safety-wrapped trainer, wraps the
colocated vLLM ``llm.generate`` call so every raw backend call is captured with
finish reasons and sampled logprobs, freezes the dataset bundles, snapshots the
training code into the manifest, and commits the runs volume after every shard.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import logging
import time
from pathlib import Path
from typing import Any

from invoiceops.adapters.rollout_log import RolloutRecorder

log = logging.getLogger(__name__)

_STACK_PACKAGES = ("trl", "transformers", "torch", "vllm", "peft", "accelerate", "datasets")


def stack_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in _STACK_PACKAGES:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def code_snapshot(*roots: Path) -> dict[str, str]:
    """sha256 of every file under the given roots, keyed by posix relpath."""
    out: dict[str, str] = {}
    for root in roots:
        root = Path(root)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                out[str(path.relative_to(root.parent))] = hashlib.sha256(
                    path.read_bytes()
                ).hexdigest()
    return out


def sampling_dict(params: Any) -> dict[str, Any]:
    """Whitelist the vLLM SamplingParams fields that affect generation."""
    if params is None:
        return {}
    keys = (
        "n",
        "temperature",
        "top_p",
        "top_k",
        "min_p",
        "max_tokens",
        "repetition_penalty",
        "seed",
        "logprobs",
        "stop_token_ids",
        "structured_outputs",
    )
    out: dict[str, Any] = {}
    for key in keys:
        try:
            value = getattr(params, key, None)
        except Exception:
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            out[key] = value
        elif isinstance(value, (list, tuple)):
            out[key] = list(value)
        else:
            out[key] = str(value)
    return out


def _sampled_logprobs(output: Any) -> list[float | None] | None:
    """Per-token logprob of the actually sampled token (what TRL keeps)."""
    if getattr(output, "logprobs", None) is None:
        return None
    result: list[float | None] = []
    for token_id, position in zip(output.token_ids, output.logprobs, strict=True):
        entry = position.get(token_id) if isinstance(position, dict) else None
        result.append(entry.logprob if entry is not None else None)
    return result


def call_record(
    vllm_prompts: Any, sampling_params: Any, outputs: Any, seconds: float
) -> dict[str, Any]:
    """One raw ``llm.generate`` call: exact inputs, outputs, finish reasons, timing."""
    inputs = []
    for prompt in vllm_prompts:
        ids = prompt.get("prompt_token_ids") if isinstance(prompt, dict) else None
        if ids is None:
            ids = getattr(prompt, "prompt_token_ids", [])
        inputs.append([int(t) for t in ids])
    out_list = []
    for request_output in outputs:
        completions = []
        for output in request_output.outputs:
            completions.append(
                {
                    "token_ids": [int(t) for t in output.token_ids],
                    "finish_reason": getattr(output, "finish_reason", None),
                    "stop_reason": (
                        str(output.stop_reason)
                        if getattr(output, "stop_reason", None) is not None
                        else None
                    ),
                    "cumulative_logprob": getattr(output, "cumulative_logprob", None),
                    "sampled_logprobs": _sampled_logprobs(output),
                }
            )
        out_list.append(completions)
    return {
        "kind": "vllm_generate",
        "ts": time.time(),
        "seconds": round(seconds, 4),
        "n_inputs": len(inputs),
        "sampling": sampling_dict(sampling_params),
        "inputs": inputs,
        "outputs": out_list,
    }


def wrap_vllm_generate(trainer: Any, recorder: RolloutRecorder) -> bool:
    """Wrap the colocated ``llm.generate``; returns False if there is nothing to wrap."""
    generation = getattr(trainer, "vllm_generation", None)
    llm = getattr(generation, "llm", None)
    if llm is None:
        return False
    original = llm.generate
    if getattr(original, "_invoiceops_logged", False):
        return True

    def logged_generate(prompts: Any, *args: Any, **kwargs: Any) -> Any:
        started = time.monotonic()
        outputs = original(prompts, *args, **kwargs)
        seconds = time.monotonic() - started
        try:
            params = kwargs.get("sampling_params")
            if params is None and len(args) >= 1:
                params = args[0]
            recorder.model_call(call_record(prompts, params, outputs, seconds))
        except Exception:
            log.exception("trajectory recorder failed on a model call")
        return outputs

    logged_generate._invoiceops_logged = True  # type: ignore[attr-defined]
    try:
        llm.generate = logged_generate
    except (AttributeError, TypeError) as exc:
        raise RuntimeError(
            "cannot wrap llm.generate for trajectory logging; refusing to train unlogged"
        ) from exc
    return True


def attach_file_logger(run_dir: Path) -> logging.FileHandler:
    handler = logging.FileHandler(run_dir / "logs" / "train.log")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logging.getLogger().addHandler(handler)
    return handler


def attach_rollout_logging(
    trainer: Any,
    run_dir: Path,
    meta: dict[str, Any],
    *,
    commit: Any = None,
    resume: bool = False,
) -> RolloutRecorder:
    """Install the recorder on the trainer + environment and wrap vLLM."""
    from invoiceops.adapters import trl_env

    recorder = RolloutRecorder(run_dir, meta, commit=commit, resume=resume)
    trainer._trajectory_recorder = recorder
    trl_env.set_rollout_recorder(recorder)
    if not wrap_vllm_generate(trainer, recorder):
        raise RuntimeError(
            "trainer.vllm_generation.llm is missing; this run requires colocated vLLM "
            "for trajectory logging (use_vllm=True, vllm_mode='colocate')"
        )
    handler = attach_file_logger(run_dir)
    recorder._file_handler = handler
    log.info("trajectory recorder attached: run_dir=%s", run_dir)
    return recorder
