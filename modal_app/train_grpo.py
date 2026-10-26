"""GRPO training with TRL's ``environment_factory`` (TRL 1.16.0) and LoRA.

The trainer owns the tool loop: for each rollout it creates an ``InvoiceOpsToolEnv``, calls
``reset(**row)``, executes the model's tool calls against the environment (tool results are
masked out of the loss), and calls ``get_reward()`` (the trusted verifier) when the rollout
ends. Training uses the train split and generated training variants only.
"""

from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "run_name": "grpo",
    "model": "Qwen/Qwen3-4B-Instruct-2507",
    "prompt_version": "v3d",
    "generated_variants": 144,
    "seed": 7,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.0,
    "grpo": {
        "learning_rate": 2e-5,
        "num_generations": 8,
        # 2 x 16 keeps 32 rollouts per step while each forward pass handles two sequences.
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 16,
        "max_steps": 150,
        # In TRL's tool loop the completion is every assistant turn plus every tool result. A full
        # oracle rollout is about 2.4k tokens and one that reads every record about 8.7k.
        # Owner requested more room for longer rollouts on 2026-10-26.
        "max_completion_length": 24576,
        # Match the test server's 131k context window, as requested by the owner.
        # The rollout completion budget above still bounds actual training sequence length.
        "vllm_max_model_length": 131072,
        # Token truncation is handled by TRL; our trainer wrapper also excludes unfinished
        # EOS-terminated tool calls at rollout limits from the loss and reward baseline.
        "mask_truncated_completions": True,
        "max_tool_calling_iterations": 30,
        "temperature": 1.0,
        "use_vllm": True,
        "vllm_mode": "colocate",
        "vllm_gpu_memory_utilization": 0.35,
        "bf16": True,
        # TRL loads a model given by name in float32 unless told otherwise.
        "model_init_kwargs": {"dtype": "bfloat16"},
        "gradient_checkpointing": True,
        "logging_steps": 1,
        "save_steps": 25,
        "save_total_limit": 8,
        "log_completions": True,
        "report_to": "none",
    },
    # ~124 s per optimizer step -> 150 steps ≈ 310 min; +startup/save headroom. The
    # Modal function hard-kills at 360 min; the wall clock stops cleanly before that.
    "wall_clock_limit_min": 345,
}


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in override.items():
        out[key] = (
            merge(out[key], value)
            if isinstance(value, dict) and isinstance(out.get(key), dict)
            else value
        )
    return out


def build_rows(config: dict[str, Any]) -> list[dict[str, Any]]:
    from invoiceops.agents.prompts import system_prompt
    from invoiceops.tasks.build import generated_training_variants
    from invoiceops.tasks.store import load_public, task_ids

    system = system_prompt(config["prompt_version"])
    rows: list[dict[str, Any]] = []
    for task_id in task_ids("train"):
        public = load_public(task_id)
        rows.append(
            {
                "prompt": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": public.prompt},
                ],
                "task_id": task_id,
                "generated": "",
                "row_index": len(rows),
            }
        )
    for n, bundle in enumerate(generated_training_variants(int(config["generated_variants"]))):
        if bundle.private.split != "train":
            raise RuntimeError("generated variants must come from training worlds")
        spec = {
            "world_id": bundle.private.world_id,
            "family": bundle.private.family,
            "variant": bundle.private.variant,
            "salt": f"gen{n}",
        }
        rows.append(
            {
                "prompt": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": bundle.public.prompt},
                ],
                "task_id": bundle.public.task_id,
                "generated": json.dumps(spec),
                "row_index": len(rows),
            }
        )
    return rows


def _prior_interrupted_run(out: Path, config_sha: str) -> tuple[Path, dict[str, Any]] | None:
    """Latest usable checkpoint if ``out`` holds a same-config interrupted run.

    A preempted Modal container restarts the function with the same input; when
    the prior attempt committed trajectory shards and a checkpoint, continuing
    in place preserves one logical run (each attempt is recorded in the
    manifest) instead of silently discarding it or mixing artifacts.
    """
    manifest_path = out / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text())
    except ValueError:
        return None
    if manifest.get("status") == "completed":
        return None
    prior_sha = (manifest.get("meta") or {}).get("config_sha256")
    if prior_sha is not None and prior_sha != config_sha:
        return None
    ckpts = []
    for ckpt in (out / "checkpoints").glob("checkpoint-*"):
        tail = ckpt.name.rsplit("-", 1)[-1]
        if (
            tail.isdigit()
            and (ckpt / "trainer_state.json").exists()
            and (ckpt / "optimizer.pt").exists()
            and (ckpt / "adapter_model.safetensors").exists()
        ):
            ckpts.append((int(tail), ckpt))
    if not ckpts:
        return None
    return max(ckpts)[1], manifest


def run_training(config: dict[str, Any], output_root: Path, commit: Any = None) -> dict[str, Any]:
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import TrainerCallback
    from trl import GRPOConfig, GRPOTrainer

    from invoiceops.adapters.rollout_log import sha256_bytes
    from invoiceops.adapters.trl_env import InvoiceOpsToolEnv, bundle_for_row
    from modal_app.grpo_safety import trainer_with_rollout_safety
    from modal_app.settings import REVISIONS
    from modal_app.trajectory_logging import (
        attach_rollout_logging,
        code_snapshot,
        stack_versions,
    )

    if commit is None:
        try:
            from modal_app.app import runs

            commit = runs.commit
        except Exception:  # pragma: no cover - only reachable off Modal
            commit = None

    config = merge(DEFAULTS, config)
    out = output_root / config["run_name"]
    # Train on the exact weights the evaluations name; TRL also loads the tokenizer at it.
    init = {
        "revision": REVISIONS.get(config["model"]),
        **config["grpo"].get("model_init_kwargs", {}),
    }
    config["grpo"] = {**config["grpo"], "model_init_kwargs": init}
    config_bytes = json.dumps(config, indent=2, sort_keys=True).encode()
    config_sha = sha256_bytes(config_bytes)

    resume_from: Path | None = None
    prior_started_epoch: float | None = None
    if out.exists():
        prior = _prior_interrupted_run(out, config_sha)
        if prior is None:
            # Refuse stale directories so retries cannot mix artifacts.
            raise FileExistsError(17, "File exists", str(out))
        resume_from, prior_manifest = prior
        prior_started = (prior_manifest.get("meta") or {}).get("started_epoch")
        if isinstance(prior_started, (int, float)):
            prior_started_epoch = float(prior_started)
    else:
        out.mkdir(parents=True)
        (out / "config.json").write_bytes(config_bytes)

    known = {f.name for f in dataclasses.fields(GRPOConfig)}
    unknown = sorted(set(config["grpo"]) - known)
    if unknown:  # fail before loading any weights
        raise ValueError(f"GRPOConfig in this TRL version has no fields: {unknown}")
    args = GRPOConfig(output_dir=str(out / "checkpoints"), seed=config["seed"], **config["grpo"])

    rows = build_rows(config)
    dataset = Dataset.from_list(rows).shuffle(seed=config["seed"])
    started = time.monotonic()
    if prior_started_epoch is not None:
        # The soft wall-clock covers the whole run across attempts.
        started -= max(0.0, time.time() - prior_started_epoch)
    limit_s = 60 * float(config["wall_clock_limit_min"])

    class WallClockStop(TrainerCallback):  # type: ignore[misc]
        def on_step_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> Any:
            if time.monotonic() - started > limit_s:
                control.should_training_stop = True
                control.should_save = True
            return control

    trainer_class = trainer_with_rollout_safety(GRPOTrainer)
    trainer = trainer_class(
        model=config["model"],
        args=args,
        train_dataset=dataset,
        environment_factory=InvoiceOpsToolEnv,
        peft_config=LoraConfig(
            r=config["lora_r"],
            lora_alpha=config["lora_alpha"],
            lora_dropout=config["lora_dropout"],
            target_modules="all-linear",
            task_type="CAUSAL_LM",
        ),
        callbacks=[WallClockStop()],
    )

    import invoiceops
    import modal_app as modal_app_pkg

    meta = {
        "run_name": config["run_name"],
        "model": config["model"],
        "revision": config["grpo"]["model_init_kwargs"].get("revision"),
        "prompt_version": config["prompt_version"],
        "seed": config["seed"],
        "generated_variants": config["generated_variants"],
        "rows": len(rows),
        "wall_clock_limit_min": config["wall_clock_limit_min"],
        "config_sha256": sha256_bytes(config_bytes),
        "stack": stack_versions(),
        "code": code_snapshot(
            Path(invoiceops.__file__).parent, Path(modal_app_pkg.__file__).parent
        ),
    }
    recorder = attach_rollout_logging(
        trainer, out, meta, commit=commit, resume=resume_from is not None
    )
    recorder.record_dataset(rows, bundle_for_row)

    if resume_from is not None:
        # HF resume reloads optimizer/scheduler/RNG/data position; load the LoRA
        # adapter explicitly so weights never depend on Trainer's peft handling.
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file

        set_peft_model_state_dict(
            trainer.model, load_file(str(resume_from / "adapter_model.safetensors"))
        )

    try:
        trainer.train(resume_from_checkpoint=str(resume_from) if resume_from is not None else None)
        final = out / "final_adapter"
        trainer.save_model(str(final))
        (out / "log_history.json").write_text(json.dumps(trainer.state.log_history, indent=1))
        status = (
            "completed"
            if trainer.state.global_step >= int(config["grpo"]["max_steps"])
            else "stopped_wallclock"
        )
        result = {
            "output": str(out),
            "steps": trainer.state.global_step,
            "run_name": config["run_name"],
            "checkpoints": sorted(p.name for p in (out / "checkpoints").glob("checkpoint-*")),
            "final_adapter_files": sorted(p.name for p in final.iterdir()),
            # Per-step log (reward, completion lengths, ...); the full file stays on the volume.
            "log_history": trainer.state.log_history[-10:],
            "rows": len(rows),
            "seconds": time.monotonic() - started,
            "status": status,
        }
    except BaseException as exc:
        recorder.close("failed", repr(exc))
        raise
    recorder.flush_step_logs(trainer.state.log_history)
    recorder.close(status)
    result["trajectory_manifest"] = str(out / "manifest.json")
    result["rollouts_logged"] = recorder.manifest["counters"]["rollouts"]
    from invoiceops.adapters.trl_env import set_rollout_recorder

    set_rollout_recorder(None)
    if commit is not None:
        commit()
    return result


def merge_adapter(base: str, revision: str | None, adapter: Path, target: Path) -> Path:
    """Merge LoRA weights so benchmarks can serve the trained model under the base name."""
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model = AutoModelForCausalLM.from_pretrained(
        base, revision=revision, torch_dtype=torch.bfloat16
    )
    merged = PeftModel.from_pretrained(model, str(adapter)).merge_and_unload()
    merged.save_pretrained(str(target))
    AutoTokenizer.from_pretrained(base, revision=revision).save_pretrained(str(target))
    return target
