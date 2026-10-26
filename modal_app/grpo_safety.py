"""Project-specific completion masking and trajectory capture for pinned TRL 1.16.

TRL can exit with an EOS-terminated assistant tool call whose response did not fit or whose
execution would exceed the iteration limit. EOS alone therefore does not prove the rollout
finished. Keep the generated token IDs intact, but remove unfinished rollouts from both the
loss mask and the reward-group baseline before TRL computes either of them.

The same wrapper feeds ``modal_app.trajectory_logging``'s recorder: every generation batch
is bracketed by begin/finish hooks and ``_generate`` snapshots the raw tool mask before
safety masking rewrites it, so shards preserve both views.
"""

from __future__ import annotations

import inspect
from typing import Any


def _tool_specs(trainer: Any) -> dict[str, Any]:
    """Serializable description of the tool surface rendered into each prompt."""
    specs: dict[str, Any] = {}
    for name, tools in getattr(trainer, "_env_tools", {}).items():
        entries = []
        for tool in tools:
            try:
                entries.append(
                    {
                        "name": getattr(tool, "__name__", str(tool)),
                        "signature": str(inspect.signature(tool)),
                        "doc": inspect.getdoc(tool),
                    }
                )
            except (TypeError, ValueError):
                entries.append({"name": getattr(tool, "__name__", str(tool))})
        specs[name] = entries
    return specs


def trainer_with_rollout_safety(base: type[Any]) -> type[Any]:
    """Extend GRPOTrainer without importing the GPU stack during local environment tests."""

    class InvoiceOpsGRPOTrainer(base):  # type: ignore[misc, valid-type]
        def _generate_and_score_completions(self, inputs: list[Any]) -> Any:
            recorder = getattr(self, "_trajectory_recorder", None)
            if recorder is None:
                return super()._generate_and_score_completions(inputs)
            recorder.begin_batch(
                global_step=self.state.global_step,
                micro_step=self._step,
                epoch=self.state.epoch,
                inputs=inputs,
                tool_specs=_tool_specs(self),
            )
            try:
                output = super()._generate_and_score_completions(inputs)
            except BaseException as exc:
                recorder.abort_batch(exc)
                raise
            advantages = output.get("advantages") if hasattr(output, "get") else None
            recorder.finish_batch(
                advantages=(advantages.tolist() if hasattr(advantages, "tolist") else advantages),
                environments=getattr(self, "environments", None),
                eos_token_ids=set(self.eos_token_ids) | {self._tokenizer.pad_token_id},
                num_generations=self.num_generations,
                global_step_after=self.state.global_step,
                log_history=list(self.state.log_history),
            )
            return output

        def _generate(self, prompts: list[Any]) -> Any:
            result = super()._generate(prompts)
            # Pinned TRL returns prompt IDs, completion IDs, tool masks, parsed messages,
            # logprobs, extra fields, images, and tool images. Metrics have been collected;
            # rewards, tensor masks and the DAPO token denominator are computed afterwards.
            (
                prompt_ids,
                completion_ids,
                tool_masks,
                completions,
                logprobs,
                _extra_fields,
                _images,
                _tool_images,
            ) = result
            mask_raw = [list(m) for m in tool_masks] if tool_masks is not None else None
            safety_masked: list[int] = []
            if self.mask_truncated_completions and tool_masks is not None:
                for idx, (environment, messages, mask) in enumerate(
                    zip(self.environments, completions, tool_masks, strict=True)
                ):
                    if (
                        messages
                        and messages[-1].get("tool_calls")
                        and environment._mark_rollout_truncated()
                    ):
                        mask[:] = [0] * len(mask)
                        safety_masked.append(idx)
                # This supplements TRL's EOS-only clipped_ratio without changing token
                # counts or manufacturing a replacement token/logprob to signal truncation.
                self._log_metric(
                    "rollouts/tool_cutoff_ratio", len(safety_masked) / len(completions)
                )
            recorder = getattr(self, "_trajectory_recorder", None)
            if recorder is not None:
                try:
                    decoded = self._tokenizer.batch_decode(
                        completion_ids, skip_special_tokens=False
                    )
                except Exception:
                    decoded = None
                recorder.capture_generation(
                    prompts=prompts,
                    prompt_ids=prompt_ids,
                    completion_ids=completion_ids,
                    tool_mask_raw=mask_raw,
                    tool_mask_final=(
                        [list(m) for m in tool_masks] if tool_masks is not None else None
                    ),
                    completions=completions,
                    logprobs=logprobs,
                    safety_masked=safety_masked,
                    decoded=decoded,
                )
            return result

    return InvoiceOpsGRPOTrainer
