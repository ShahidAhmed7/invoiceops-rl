from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from invoiceops.agents.oracle import solve
from invoiceops.agents.scripted import SCRIPTED
from invoiceops.episode import Episode
from invoiceops.tasks.build import build_suite
from invoiceops.tasks.model import TaskBundle
from invoiceops.tasks.quality import leakage_problems
from invoiceops.tasks.store import DEFAULT_TASK_ROOT, load_bundle, task_ids
from invoiceops.verification.mutations import run_mutations
from invoiceops.verification.verifier import verify_episode

from .conftest import bundle_ids, suite


def test_suite_shape(bundles: tuple[TaskBundle, ...]) -> None:
    assert len(bundles) == 72
    assert Counter(b.private.split for b in bundles) == {"train": 36, "dev": 12, "test": 24}
    per_family = Counter((b.private.family, b.private.split) for b in bundles)
    for family in {b.private.family for b in bundles}:
        assert (
            per_family[(family, "train")],
            per_family[(family, "dev")],
            per_family[(family, "test")],
        ) == (3, 1, 2)


def test_splits_are_by_world(bundles: tuple[TaskBundle, ...]) -> None:
    owner: dict[str, str] = {}
    for b in bundles:
        assert owner.setdefault(b.private.world_id, b.private.split) == b.private.split


def test_no_leakage_across_splits(bundles: tuple[TaskBundle, ...]) -> None:
    assert leakage_problems(bundles) == []


def test_prompt_does_not_reveal_family_or_answer(bundles: tuple[TaskBundle, ...]) -> None:
    for b in bundles:
        text = b.public.model_dump_json().lower()
        assert b.private.family.lower() not in b.public.prompt.lower()
        assert b.private.family_name.lower() not in b.public.prompt.lower()
        assert "expectation" not in text and "rationale" not in text


def test_files_on_disk_match_generator() -> None:
    generated = {b.public.task_id: b for b in build_suite()}
    assert sorted(task_ids(root=DEFAULT_TASK_ROOT)) == sorted(generated)
    for task_id, bundle in generated.items():
        on_disk = load_bundle(task_id)
        assert on_disk.model_dump_json() == bundle.model_dump_json(), task_id
    manifest = json.loads((DEFAULT_TASK_ROOT / "manifest.json").read_text())
    assert len(manifest) == 72


@pytest.mark.parametrize("task_id", bundle_ids())
def test_oracle_solves_task(task_id: str) -> None:
    bundle = next(b for b in suite() if b.public.task_id == task_id)
    ep = Episode(bundle.public.world, task_id)
    solve(ep)
    result = verify_episode(ep, bundle.private)
    assert result.passed, [c.detail for c in result.failed_checks()]
    assert result.critical_violations == []


@pytest.mark.parametrize("task_id", bundle_ids())
def test_verifier_rejects_mutations_and_accepts_alternatives(task_id: str) -> None:
    bundle = next(b for b in suite() if b.public.task_id == task_id)
    results = run_mutations(bundle)
    wrong = [(r.name, r.reason) for r in results if not r.as_expected]
    assert wrong == []
    assert sum(r.applicable and r.kind == "mutation" for r in results) >= 8


CEILINGS = {"noop": 0.0, "random": 0.1, "always_hold": 0.5, "always_pay": 0.5}


@pytest.mark.parametrize("policy", sorted(SCRIPTED))
def test_scripted_policies_stay_below_ceiling(policy: str) -> None:
    for split in ("train", "dev", "test"):
        tasks = [b for b in suite() if b.private.split == split]
        passed = 0
        for b in tasks:
            ep = Episode(b.public.world, b.public.task_id)
            SCRIPTED[policy](ep)
            passed += verify_episode(ep, b.private).passed
        assert passed / len(tasks) < CEILINGS[policy] or passed == 0, (policy, split, passed)


def test_task_root_exists() -> None:
    assert Path(DEFAULT_TASK_ROOT).is_dir()
