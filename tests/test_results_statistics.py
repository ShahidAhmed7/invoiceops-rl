from __future__ import annotations

import itertools
import json
from pathlib import Path

import pytest
from scripts.analyze_results import exact_mcnemar, exact_signflip


def test_weighted_paired_test_matches_full_enumeration_with_ties() -> None:
    differences = [3, 2, 2, 1, 1, 1, -1, -1]
    observed = abs(sum(differences))
    extremes = sum(
        abs(sum(s * d for s, d in zip(signs, differences, strict=True))) >= observed
        for signs in itertools.product((-1, 1), repeat=len(differences))
    )
    result = exact_signflip(differences)
    assert result["two_sided_p"] == extremes / 256 == 0.140625
    assert exact_signflip([*differences, 0, 0]) == result
    assert exact_signflip([0, 0])["two_sided_p"] == 1


def test_exact_binary_pairs_use_only_discordant_tasks() -> None:
    assert exact_mcnemar(5, 1)["two_sided_p"] == 0.21875
    assert exact_mcnemar(8, 0)["two_sided_p"] == 2 / 256
    assert exact_mcnemar(0, 0)["two_sided_p"] == 1
    with pytest.raises(ValueError, match="nonnegative"):
        exact_mcnemar(-1, 0)


def test_published_counts_are_backed_by_complete_paired_observations() -> None:
    evidence = json.loads(Path("reports/statistics/paired_observations.json").read_text())
    rows = evidence["observations"]
    assert len(rows) == len({r["task_id"] for r in rows}) == 24
    assert len({r["company_id"] for r in rows}) == 4
    assert all(len(r[key]) == 4 for r in rows for key in ("baseline", "trained"))
    assert sum(sum(r["baseline"]) for r in rows) == 76
    assert sum(sum(r["trained"]) for r in rows) == 84
    assert len(evidence["source_episode_sha256"]) == 192


def test_bfcl_composite_is_labelled_as_subset_and_keeps_negative_result() -> None:
    analysis = json.loads(Path("reports/statistics/analysis.json").read_text())
    bfcl = analysis["bfcl"]
    micro = bfcl["executed_case_micro"]
    assert len(bfcl["categories"]) == 8
    assert sum(r["cases"] for r in bfcl["categories"]) == micro["cases"] == 2751
    assert micro["trained_correct"] - micro["baseline_correct"] == -3
    assert micro["delta"] < 0 and micro["official_bfcl_overall"] is False
