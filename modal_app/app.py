"""Modal functions for the GPU phases (BUILD_PLAN.md Phases 11A-14).

Never call these directly: launch them with ``python -m modal_app.launch <job>``, which checks
the budget, the review sign-off, and records the spend. Each function has no retries, one
container at most, and a hard timeout matching ``budget.yaml``.

Status: written against modal 1.6.2, vllm 0.31.0, trl 1.16.0, tau2-bench 318fa35, and
bfcl-eval 2026.3.23 from their installed source code, but not yet executed on Modal (no Modal
access existed while building). Phase 11A's smoke jobs are the first real execution.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import modal

from modal_app import settings

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
CUDA_BASE = "nvidia/cuda:12.8.1-devel-ubuntu22.04"

app = modal.App("invoiceops")
hf_cache = modal.Volume.from_name("invoiceops-hf-cache", create_if_missing=True)
runs = modal.Volume.from_name("invoiceops-runs", create_if_missing=True)
VOLUMES: dict[str | os.PathLike[str], modal.Volume] = {"/hf-cache": hf_cache, "/runs": runs}
ENV = {
    "HF_HOME": "/hf-cache",
    "INVOICEOPS_TASK_ROOT": "/root/tasks",
    "TOKENIZERS_PARALLELISM": "false",
}


def _with_sources(image: modal.Image) -> modal.Image:
    return (
        image.env(ENV)
        # The default ignore keeps only .py files, which would drop the system prompts (.md).
        .add_local_python_source("invoiceops", "modal_app", ignore=["**/__pycache__", "**/*.pyc"])
        .add_local_dir(REPO / "tasks", "/root/tasks")
    )


cpu_image = _with_sources(
    modal.Image.debian_slim(python_version="3.12").uv_pip_install(
        "huggingface_hub==1.33.0", "pydantic==2.14.1", "pyyaml", "tokenizers==0.23.3"
    )
)

serve_image = _with_sources(
    modal.Image.from_registry(CUDA_BASE, add_python="3.12")
    .entrypoint([])
    .apt_install("git")
    .uv_pip_install(requirements=[str(HERE / "requirements-serve.txt")])
    .run_commands(
        "pip install uv==0.11.32",
        "uv venv /opt/tau2 --python 3.12",
        f"uv pip install --python /opt/tau2/bin/python "
        f"'tau2 @ git+{settings.TAU2_REPO}@{settings.TAU2_COMMIT}'",
        "uv venv /opt/bfcl --python 3.12",
        # qwen_agent (imported by bfcl-eval) needs soundfile but does not declare it.
        f"uv pip install --python /opt/bfcl/bin/python bfcl-eval=={settings.BFCL_VERSION} "
        "soundfile==0.14.0",
    )
)

train_image = _with_sources(
    modal.Image.from_registry(CUDA_BASE, add_python="3.12")
    .entrypoint([])
    .apt_install("git")
    .uv_pip_install(requirements=[str(HERE / "requirements-train.txt")])
)


def _revision(model: str) -> str:
    revision = settings.REVISIONS.get(model)
    if not revision:
        raise RuntimeError(
            f"{model} has no pinned revision; run inspect_models and fill settings.REVISIONS"
        )
    return revision


def _save(path: str, data: Any) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, sort_keys=True))
    runs.commit()


# -- Phase 11A ---------------------------------------------------------------------------------


@app.function(image=cpu_image, volumes=VOLUMES, timeout=10 * 60, max_containers=1, retries=0)
def inspect_models() -> dict[str, Any]:
    """Record license, architecture, tool-calling template, and revision of each model."""
    from huggingface_hub import HfApi, hf_hub_download

    api = HfApi()
    report: dict[str, Any] = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    for model in settings.REVISIONS:
        entry: dict[str, Any] = {}
        try:
            info = api.model_info(model)
            entry["revision"] = info.sha
            card = info.card_data.to_dict() if info.card_data else {}
            entry["license"] = card.get("license")
            entry["pipeline_tag"] = info.pipeline_tag
            entry["gated"] = getattr(info, "gated", None)
            config = json.loads(
                Path(hf_hub_download(model, "config.json", revision=info.sha)).read_text()
            )
            entry["architectures"] = config.get("architectures")
            entry["model_type"] = config.get("model_type")
            entry["max_position_embeddings"] = config.get("max_position_embeddings")
            heads = config.get("num_key_value_heads")
            head_dim = config.get("head_dim") or (
                config["hidden_size"] // config["num_attention_heads"]
                if config.get("hidden_size") and config.get("num_attention_heads")
                else None
            )
            if heads and head_dim and config.get("num_hidden_layers"):
                # bf16 K and V for every layer
                entry["kv_cache_bytes_per_token"] = (
                    2 * 2 * config["num_hidden_layers"] * heads * head_dim
                )
            tok = json.loads(
                Path(hf_hub_download(model, "tokenizer_config.json", revision=info.sha)).read_text()
            )
            template = tok.get("chat_template") or ""
            if not template:
                try:
                    template = Path(
                        hf_hub_download(model, "chat_template.jinja", revision=info.sha)
                    ).read_text()
                except Exception:
                    template = ""
            entry["chat_template_mentions_tools"] = "tools" in template
            entry["exists"] = True
        except Exception as exc:
            entry = {"exists": False, "error": f"{type(exc).__name__}: {exc}"}
        report[model] = entry
    report["token_counts"] = _token_counts(settings.CANDIDATE_MODEL, report)
    _save("/runs/model_verification.json", report)
    return report


def _token_counts(model: str, report: dict[str, Any]) -> dict[str, Any]:
    """Exact token counts of the largest texts an episode carries, with the candidate tokenizer."""
    from huggingface_hub import hf_hub_download
    from tokenizers import Tokenizer

    from invoiceops.agents.oracle import solve
    from invoiceops.agents.prompts import system_prompt
    from invoiceops.episode import Episode
    from invoiceops.tasks.store import load_bundle, task_ids
    from invoiceops.tools.spec import openai_tools

    try:
        revision = (report.get(model) or {}).get("revision")
        tok = Tokenizer.from_file(hf_hub_download(model, "tokenizer.json", revision=revision))
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}

    def count(text: str) -> int:
        return len(tok.encode(text).ids)

    tools = "\n".join(json.dumps(t, ensure_ascii=False) for t in openai_tools())
    oracle_completion, longest_observation, longest_document = 0, 0, 0
    for split in ("train", "dev", "test"):
        for task_id in task_ids(split):
            bundle = load_bundle(task_id)
            ep = Episode(bundle.public.world, task_id, max_steps=10_000)
            solve(ep)
            texts = [json.dumps(e.observation, ensure_ascii=False) for e in ep.log]
            texts += [json.dumps(e.arguments, ensure_ascii=False) for e in ep.log]
            ep.close()
            reader = Episode(bundle.public.world, task_id, max_steps=10_000)
            for doc in bundle.public.world.documents:
                obs = reader.step("get_document", {"document_id": doc.id})
                longest_document = max(longest_document, count(json.dumps(obs, ensure_ascii=False)))
            reader.close()
            oracle_completion = max(oracle_completion, sum(count(t) for t in texts))
            longest_observation = max([longest_observation, *(count(t) for t in texts)])
    return {
        "model": model,
        "tool_schemas": count(tools),
        "system_v1": count(system_prompt("v1")),
        "system_v2": count(system_prompt("v2")),
        "oracle_completion_max": oracle_completion,
        "longest_oracle_observation": longest_observation,
        "longest_document_observation": longest_document,
        "max_model_len": settings.MAX_MODEL_LEN,
        "agent_max_tokens": settings.AGENT_MAX_TOKENS,
    }


def _two_tool_roundtrip(port: int, served: str) -> dict[str, Any]:
    import urllib.request

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_invoice",
                "description": "Read an invoice.",
                "parameters": {
                    "type": "object",
                    "properties": {"invoice_id": {"type": "string"}},
                    "required": ["invoice_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_receipts",
                "description": "Read receipts for a PO.",
                "parameters": {
                    "type": "object",
                    "properties": {"po_id": {"type": "string"}},
                    "required": ["po_id"],
                },
            },
        },
    ]
    body = {
        "model": served,
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": "Read invoice INV-1 and the receipts for PO PO-7. Use both tools.",
            }
        ],
    }
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        reply = json.loads(response.read())
    calls = reply["choices"][0]["message"].get("tool_calls") or []
    parsed = []
    for call in calls:
        parsed.append(
            {
                "name": call["function"]["name"],
                "arguments": json.loads(call["function"]["arguments"]),
            }
        )
    return {
        "tool_calls": parsed,
        "ok": {c["name"] for c in parsed} == {"get_invoice", "get_receipts"},
    }


def _bfcl(
    tag: str,
    served_base: str,
    port: int,
    categories: tuple[str, ...],
    handler: str,
    limit: int | None = None,
) -> dict[str, Any]:
    root = Path("/runs/bfcl") / tag
    root.mkdir(parents=True, exist_ok=True)
    env = {
        **os.environ,
        "LOCAL_SERVER_ENDPOINT": "127.0.0.1",
        "LOCAL_SERVER_PORT": str(port),
        "BFCL_PROJECT_ROOT": str(root),
    }
    category_flags = [flag for c in categories for flag in ("--test-category", c)]
    generate = [
        "/opt/bfcl/bin/bfcl",
        "generate",
        "--model",
        handler,
        *category_flags,
        "--skip-server-setup",
        "--backend",
        "vllm",
        "--num-threads",
        "16",
        "--temperature",
        "0.001",
    ]
    if limit:
        ids = {}
        data_dir = Path(
            subprocess.check_output(
                [
                    "/opt/bfcl/bin/python",
                    "-c",
                    "import bfcl_eval, pathlib; "
                    "print(pathlib.Path(bfcl_eval.__file__).parent / 'data')",
                ],
                text=True,
            ).strip()
        )
        for category in categories:
            lines = (data_dir / f"BFCL_v4_{category}.json").read_text().splitlines()[:limit]
            ids[category] = [json.loads(line)["id"] for line in lines]
        (root / "test_case_ids_to_generate.json").write_text(json.dumps(ids))
        generate.append("--run-ids")
    subprocess.run(generate, env=env, check=True, cwd=root)
    subprocess.run(
        ["/opt/bfcl/bin/bfcl", "evaluate", "--model", handler, *category_flags]
        + (["--partial-eval"] if limit else []),
        env=env,
        check=True,
        cwd=root,
    )
    scores = {str(p.relative_to(root)): p.read_text()[:20000] for p in root.rglob("*.csv")}
    runs.commit()
    return {"tag": tag, "served": served_base, "categories": categories, "score_files": scores}


def _smoke_serve(model: str, gpu_mem: float, bfcl_handler: str | None) -> dict[str, Any]:
    from modal_app import vllm_server

    revision = settings.REVISIONS.get(model)
    proc = vllm_server.start(model, 8001, model, gpu_mem, revision=revision)
    try:
        result: dict[str, Any] = {
            "model": model,
            "revision": revision,
            "roundtrip": _two_tool_roundtrip(8001, model),
        }
        if bfcl_handler:
            result["bfcl_smoke"] = _bfcl(
                f"smoke-{model.split('/')[-1]}",
                model,
                8001,
                ("simple_python", "multi_turn_base"),
                bfcl_handler,
                limit=5,
            )
    finally:
        vllm_server.stop(proc)
    _save(f"/runs/smoke/serve-{model.split('/')[-1]}.json", result)
    return result


@app.function(
    image=serve_image, gpu="L40S", volumes=VOLUMES, timeout=20 * 60, max_containers=1, retries=0
)
def smoke_serve_candidate(model: str = settings.CANDIDATE_MODEL) -> dict[str, Any]:
    return _smoke_serve(model, 0.85, f"{model}-FC" if model == settings.CANDIDATE_MODEL else None)


@app.function(
    image=serve_image, gpu="H100", volumes=VOLUMES, timeout=20 * 60, max_containers=1, retries=0
)
def smoke_serve_reference(model: str = settings.REFERENCE_FP8) -> dict[str, Any]:
    return _smoke_serve(model, 0.85, None)


def _tau2(
    tag: str, agent_model: str, agent_path: str | None, trials: int, num_tasks: int
) -> dict[str, Any]:
    from modal_app import vllm_server

    user_model = settings.REFERENCE_FP8
    agent_source = agent_path or agent_model
    same = agent_source == user_model
    user = vllm_server.start(
        user_model,
        8002,
        "user-sim",
        0.45 if not same else 0.85,
        revision=_revision(user_model),
        max_model_len=settings.MAX_MODEL_LEN if same else settings.USER_SIM_MAX_MODEL_LEN,
    )
    agent = None
    try:
        if not same:
            agent = vllm_server.start(
                agent_source,
                8001,
                "agent",
                0.40,
                revision=None if agent_path else _revision(agent_model),
            )
        out = Path("/runs/tau2") / tag
        cmd = [
            "/opt/tau2/bin/python",
            "/root/modal_app/tau2_driver.py",
            "--agent-model",
            "user-sim" if same else "agent",
            "--agent-port",
            "8002" if same else "8001",
            "--user-model",
            "user-sim",
            "--user-port",
            "8002",
            "--trials",
            str(trials),
            "--num-tasks",
            str(num_tasks),
            "--seed",
            str(settings.TAU2_SEED),
            "--agent-temperature",
            str(settings.AGENT_TEMPERATURE),
            "--agent-top-p",
            str(settings.AGENT_TOP_P),
            "--user-temperature",
            str(settings.USER_SIM_TEMPERATURE),
            "--out",
            str(out),
        ]
        start = time.monotonic()
        subprocess.run(cmd, check=True)
        summary = json.loads((out / "summary.json").read_text())
        summary["seconds"] = time.monotonic() - start
        summary["seconds_per_simulation"] = summary["seconds"] / max(1, summary["simulations"])
        summary["agent_source"] = agent_source
    finally:
        if agent is not None:
            vllm_server.stop(agent)
        vllm_server.stop(user)
    _save(f"/runs/tau2/{tag}/summary.json", summary)
    return summary


@app.function(
    image=serve_image, gpu="H100", volumes=VOLUMES, timeout=25 * 60, max_containers=1, retries=0
)
def smoke_tau2() -> dict[str, Any]:
    return _tau2("smoke", settings.CANDIDATE_MODEL, None, trials=1, num_tasks=2)


@app.function(
    image=serve_image, gpu="H100", volumes=VOLUMES, timeout=60 * 60, max_containers=1, retries=0
)
def tau2_eval(
    tag: str, agent_model: str, agent_path: str = "", trials: int = settings.TAU2_TRIALS
) -> dict[str, Any]:
    return _tau2(tag, agent_model, agent_path or None, trials=trials, num_tasks=0)


@app.function(
    image=serve_image, gpu="L40S", volumes=VOLUMES, timeout=35 * 60, max_containers=1, retries=0
)
def bfcl_eval(tag: str, model_path: str = "") -> dict[str, Any]:
    """BFCL on the candidate (or merged trained weights served under the candidate's name)."""
    from modal_app import vllm_server

    base = settings.CANDIDATE_MODEL
    source = model_path or base
    proc = vllm_server.start(
        source, 8001, base, 0.85, revision=None if model_path else _revision(base)
    )
    try:
        return _bfcl(tag, base, 8001, settings.BFCL_CATEGORIES, f"{base}-FC")
    finally:
        vllm_server.stop(proc)


# -- Phases 11B-14 (require the pre-GPU review sign-off) ----------------------------------------


def _invoiceops_eval(
    tag: str,
    model: str,
    model_path: str,
    splits: list[str],
    attempts: int,
    prompt: str,
    gpu_mem: float,
) -> dict[str, Any]:
    from invoiceops.agents.openai_runner import ModelConfig
    from invoiceops.evaluation.run import evaluate
    from invoiceops.tasks.store import task_ids
    from modal_app import vllm_server

    proc = vllm_server.start(
        model_path or model,
        8001,
        "agent",
        gpu_mem,
        revision=None if model_path else _revision(model),
    )
    try:
        cfg = ModelConfig(
            base_url="http://127.0.0.1:8001/v1",
            model="agent",
            temperature=settings.AGENT_TEMPERATURE,
            top_p=settings.AGENT_TOP_P,
            max_tokens=settings.AGENT_MAX_TOKENS,
            context_tokens=settings.MAX_MODEL_LEN,
        )
        tasks = [t for split in splits for t in task_ids(split)]
        summary = evaluate(
            "model",
            tasks,
            Path("/runs/invoiceops") / tag,
            attempts=attempts,
            model=cfg,
            prompt_version=prompt,
            concurrency=16,
            extra_config={
                "splits": splits,
                "model_id": model,
                "model_path": model_path,
                "revision": settings.REVISIONS.get(model),
            },
        )
    finally:
        vllm_server.stop(proc)
    runs.commit()
    return summary


@app.function(
    image=serve_image, gpu="L40S", volumes=VOLUMES, timeout=65 * 60, max_containers=1, retries=0
)
def invoiceops_eval_l40s(
    tag: str,
    model: str,
    model_path: str = "",
    splits: list[str] | None = None,
    attempts: int = 4,
    prompt: str = "v1",
) -> dict[str, Any]:
    return _invoiceops_eval(tag, model, model_path, splits or ["test"], attempts, prompt, 0.85)


@app.function(
    image=serve_image, gpu="H100", volumes=VOLUMES, timeout=50 * 60, max_containers=1, retries=0
)
def invoiceops_eval_h100(
    tag: str,
    model: str,
    model_path: str = "",
    splits: list[str] | None = None,
    attempts: int = 4,
    prompt: str = "v1",
) -> dict[str, Any]:
    return _invoiceops_eval(tag, model, model_path, splits or ["test"], attempts, prompt, 0.85)


@app.function(
    image=train_image, gpu="H100", volumes=VOLUMES, timeout=250 * 60, max_containers=1, retries=0
)
def train_grpo(config_json: str) -> dict[str, Any]:
    from modal_app.train_grpo import run_training

    config = json.loads(config_json)
    config.setdefault("revision", _revision(config["model"]))
    result = run_training(config, output_root=Path("/runs/train"))
    runs.commit()
    return result


@app.function(
    image=serve_image, gpu="L40S", volumes=VOLUMES, timeout=60 * 60, max_containers=1, retries=0
)
def select_checkpoint(run_name: str, attempts: int = 2, max_candidates: int = 4) -> dict[str, Any]:
    """Pick the training checkpoint with the best development-split success (dev only)."""
    from invoiceops.agents.openai_runner import ModelConfig
    from invoiceops.evaluation.run import evaluate
    from invoiceops.tasks.store import task_ids
    from modal_app import vllm_server

    root = Path("/runs/train") / run_name
    candidates = sorted(
        (root / "checkpoints").glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[1])
    )[-(max_candidates - 1) :]
    candidates.append(root / "final_adapter")
    base = settings.CANDIDATE_MODEL
    scores: dict[str, float | None] = {}
    for ckpt in candidates:
        proc = vllm_server.start(
            base, 8001, "agent", 0.85, revision=_revision(base), lora_path=str(ckpt)
        )
        try:
            cfg = ModelConfig(
                base_url="http://127.0.0.1:8001/v1",
                model="agent-lora",
                temperature=settings.AGENT_TEMPERATURE,
                top_p=settings.AGENT_TOP_P,
                max_tokens=settings.AGENT_MAX_TOKENS,
                context_tokens=settings.MAX_MODEL_LEN,
            )
            summary = evaluate(
                "model",
                task_ids("dev"),
                root / "selection" / ckpt.name,
                attempts=attempts,
                model=cfg,
                concurrency=16,
            )
            scores[ckpt.name] = summary["task_mean_success"]
        finally:
            vllm_server.stop(proc)
    best = max(scores, key=lambda name: (scores[name] or 0.0, name == "final_adapter"))
    result = {"run": run_name, "dev_scores": scores, "selected": best}
    _save(str(root / "selection.json"), result)
    return result


@app.function(
    image=train_image, gpu="L40S", volumes=VOLUMES, timeout=20 * 60, max_containers=1, retries=0
)
def merge_checkpoint(run_name: str, checkpoint: str) -> str:
    from modal_app.train_grpo import merge_adapter

    root = Path("/runs/train") / run_name
    source = (
        root / checkpoint if checkpoint == "final_adapter" else root / "checkpoints" / checkpoint
    )
    target = merge_adapter(
        settings.CANDIDATE_MODEL,
        _revision(settings.CANDIDATE_MODEL),
        source,
        root / "selected_merged",
    )
    runs.commit()
    return str(target)
