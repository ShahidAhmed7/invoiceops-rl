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
    "prompt_version": "v1",
    "generated_variants": 144,
    "seed": 7,
    "lora_r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.0,
    "grpo": {
        "learning_rate": 2e-5,
        "num_generations": 8,
        # 2 x 16 keeps 32 rollouts per step while each forward pass holds the logits of two
        # sequences of up to 20k tokens (about 12 GB in bf16), not eight.
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 16,
        "max_steps": 150,
        # In TRL's tool loop the completion is every assistant turn plus every tool result. A full
        # oracle rollout is about 2.4k tokens and one that reads every record about 8.7k.
        "max_completion_length": 16384,
        # The prompt (system prompt, tool schemas, task) is about 3.2k tokens.
        "vllm_max_model_length": 20480,
        # A rollout cut off by the budget is left out of the loss instead of being scored as a
        # failure the policy never saw the end of.
        "mask_truncated_completions": True,
        "max_tool_calling_iterations": 30,
        "temperature": 1.0,
        "use_vllm": True,
        "vllm_mode": "colocate",
        "vllm_gpu_memory_utilization": 0.35,
        "bf16": True,
        "gradient_checkpointing": True,
        "logging_steps": 1,
        "save_steps": 25,
        "save_total_limit": 8,
        "log_completions": True,
        "report_to": "none",
    },
    "wall_clock_limit_min": 225,
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


def build_rows(config: dict[str, Any]) -> list[dict[str, str | list[dict[str, str]]]]:
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
            }
        )
    return rows


def run_training(config: dict[str, Any], output_root: Path) -> dict[str, Any]:
    from datasets import Dataset
    from peft import LoraConfig
    from transformers import TrainerCallback
    from trl import GRPOConfig, GRPOTrainer

    from invoiceops.adapters.trl_env import InvoiceOpsToolEnv

    config = merge(DEFAULTS, config)
    out = output_root / config["run_name"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "config.json").write_text(json.dumps(config, indent=2, sort_keys=True))

    known = {f.name for f in dataclasses.fields(GRPOConfig)}
    unknown = sorted(set(config["grpo"]) - known)
    if unknown:  # fail before loading any weights
        raise ValueError(f"GRPOConfig in this TRL version has no fields: {unknown}")
    args = GRPOConfig(output_dir=str(out / "checkpoints"), seed=config["seed"], **config["grpo"])

    rows = build_rows(config)
    dataset = Dataset.from_list(rows).shuffle(seed=config["seed"])
    started = time.monotonic()
    limit_s = 60 * float(config["wall_clock_limit_min"])

    class WallClockStop(TrainerCallback):  # type: ignore[misc]
        def on_step_end(self, args: Any, state: Any, control: Any, **kwargs: Any) -> Any:
            if time.monotonic() - started > limit_s:
                control.should_training_stop = True
                control.should_save = True
            return control

    trainer = GRPOTrainer(
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
    trainer.train()
    final = out / "final_adapter"
    trainer.save_model(str(final))
    (out / "log_history.json").write_text(json.dumps(trainer.state.log_history, indent=1))
    return {
        "output": str(out),
        "steps": trainer.state.global_step,
        "rows": len(rows),
        "seconds": time.monotonic() - started,
    }


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
