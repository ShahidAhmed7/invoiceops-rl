from __future__ import annotations

import copy
import json
from collections import Counter
from typing import Any

from modal_app.grpo_safety import trainer_with_rollout_safety
from modal_app.train_grpo import DEFAULTS, build_rows, merge

from invoiceops.adapters.trl_env import InvoiceOpsToolEnv, bundle_for_row
from invoiceops.agents.oracle import solve
from invoiceops.tasks.build import generated_training_variants
from invoiceops.tasks.store import task_ids

from .conftest import by_family


def test_training_curriculum_is_balanced_valid_and_reconstructible() -> None:
    rows = build_rows(merge(DEFAULTS, {"generated_variants": 144}))
    bundles = [bundle_for_row(row) for row in rows]
    assert len(rows) == len({b.public.task_id for b in bundles}) == 180
    assert Counter(b.private.variant for b in bundles) == {0: 60, 1: 60, 2: 60}
    assert set(Counter(b.private.family for b in bundles).values()) == {15}
    assert set(Counter(b.private.world_id for b in bundles).values()) == {30}
    heldout = set(task_ids("dev") + task_ids("test"))
    env = InvoiceOpsToolEnv()
    try:
        for row, bundle in zip(rows, bundles, strict=True):
            assert bundle.private.split == "train"
            assert bundle.public.task_id not in heldout
            assert row["prompt"][-1]["content"] == bundle.public.prompt
            assert row["task_id"] == bundle.public.task_id
            env.reset(**row)
            assert env._episode is not None
            solve(env._episode)
            assert env.get_reward() == 1.0, row["task_id"]
    finally:
        if env._episode is not None:
            env._episode.close()


def test_generated_full_cycle_covers_every_company_family_variant() -> None:
    bundles = list(generated_training_variants(216))
    triples = Counter((b.private.world_id, b.private.family, b.private.variant) for b in bundles)
    assert len(triples) == 216
    assert set(triples.values()) == {1}
    # start is a reproducible slice, including at a sweep boundary.
    tail = list(generated_training_variants(4, start=70))
    assert [b.model_dump() for b in tail] == [b.model_dump() for b in bundles[70:74]]


class StubGRPOTrainer:
    """TRL boundary double: parsed results enter before reward and loss-mask construction."""

    def __init__(self, environments: list[InvoiceOpsToolEnv], result: tuple[Any, ...]) -> None:
        self.environments = environments
        self.result = result
        self.mask_truncated_completions = True
        self.metrics: dict[str, float] = {}

    def _generate(self, prompts: list[Any]) -> tuple[Any, ...]:
        return self.result

    def _log_metric(self, name: str, value: float) -> None:
        self.metrics[name] = value


def _environment() -> InvoiceOpsToolEnv:
    env = InvoiceOpsToolEnv()
    env.reset(task_id=by_family("F01", 0).public.task_id)
    return env


def _result(messages: list[list[dict[str, Any]]]) -> tuple[Any, ...]:
    # EOS sentinel 999 deliberately survives the cutoff: this is the upstream mask's blind spot.
    return (
        [[1, 2] for _ in messages],
        [[100, 101, 999] for _ in messages],
        [[1, 0, 1] for _ in messages],
        messages,
        [[-0.1, 0.0, -0.2] for _ in messages],
        {},
        None,
        [[] for _ in messages],
    )


PENDING = {"role": "assistant", "tool_calls": [{"function": {"name": "get_invoice"}}]}


def test_unfinished_eos_tool_call_excluded_from_reward_and_loss() -> None:
    env = _environment()
    trainer_class = trainer_with_rollout_safety(StubGRPOTrainer)
    result = _result([[copy.deepcopy(PENDING)]])
    before = copy.deepcopy(result)
    trainer = trainer_class([env], result)
    try:
        assert env.get_reward() == 0.0
        actual = trainer._generate([])
        assert actual[2] == [[0, 0, 0]]
        assert env.get_reward() is None  # TRL omits it from the group baseline too.
        assert trainer.metrics["rollouts/tool_cutoff_ratio"] == 1.0
        for index in (0, 1, 3, 4):
            assert actual[index] == before[index]  # no fabricated token, message, or logprob
        env.reset(task_id=by_family("F01", 0).public.task_id)
        assert env.get_reward() == 0.0  # pooled environments don't retain the cutoff flag
    finally:
        assert env._episode is not None
        env._episode.close()


def test_terminal_success_and_natural_failure_keep_their_learning_signal() -> None:
    success, failure = _environment(), _environment()
    assert success._episode is not None
    solve(success._episode)
    # A response too large to retain after submit_case leaves a tool call at the end,
    # but the underlying environment has already reached a legitimate terminal state.
    result = _result([[copy.deepcopy(PENDING)], [{"role": "assistant", "content": "done"}]])
    trainer = trainer_with_rollout_safety(StubGRPOTrainer)([success, failure], result)
    try:
        assert trainer._generate([]) == result
        assert result[2] == [[1, 0, 1], [1, 0, 1]]
        assert (success.get_reward(), failure.get_reward()) == (1.0, 0.0)
        assert trainer.metrics["rollouts/tool_cutoff_ratio"] == 0.0
    finally:
        success._episode.close()
        assert failure._episode is not None
        failure._episode.close()


def test_masking_can_be_explicitly_disabled() -> None:
    env = _environment()
    result = _result([[copy.deepcopy(PENDING)]])
    trainer = trainer_with_rollout_safety(StubGRPOTrainer)([env], result)
    trainer.mask_truncated_completions = False
    try:
        trainer._generate([])
        assert result[2] == [[1, 0, 1]]
        assert env.get_reward() == 0.0
    finally:
        assert env._episode is not None
        env._episode.close()


def test_generated_row_specs_use_the_actual_variant() -> None:
    rows = build_rows(merge(DEFAULTS, {"generated_variants": 144}))[36:]
    assert Counter(json.loads(row["generated"])["variant"] for row in rows) == {
        0: 48,
        1: 48,
        2: 48,
    }
