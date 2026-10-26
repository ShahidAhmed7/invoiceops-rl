"""Reproduce paired statistics from audited task counts; optionally refresh from local traces.

    uv run --frozen --group analysis python scripts/analyze_results.py
    uv run --frozen --group analysis python scripts/analyze_results.py --refresh-observations

The default works from a fresh checkout. Refreshing requires the gitignored raw InvoiceOps
episodes downloaded from Modal. No inference, training, GPU jobs or external APIs are used.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "statistics"
OBSERVATIONS = OUT / "paired_observations.json"
SEED = 0
SAMPLES = 100_000


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def exact_signflip(values: Sequence[int]) -> dict[str, Any]:
    """Exact two-sided paired sign-flip distribution, including ties at the observed statistic.

    Integer differences are counts of successes, with a common denominator within an
    analysis. Dynamic programming enumerates all sign assignments without Monte Carlo.
    Zero differences contribute no information and leave the probability unchanged.
    """
    distribution = Counter({0: 1})
    nonzero = [abs(x) for x in values if x]
    for value in nonzero:
        updated: Counter[int] = Counter()
        for score, count in distribution.items():
            updated[score + value] += count
            updated[score - value] += count
        distribution = updated
    observed = abs(sum(values))
    extreme = sum(n for score, n in distribution.items() if abs(score) >= observed)
    total = 2 ** len(nonzero)
    return {
        "two_sided_p": extreme / total,
        "nonzero_pairs": len(nonzero),
        "sign_assignments": total,
        "extreme_assignments": extreme,
    }


def exact_mcnemar(gained: int, lost: int) -> dict[str, Any]:
    """Exact two-sided conditional binomial test on discordant paired binary outcomes."""
    if min(gained, lost) < 0:
        raise ValueError("discordant counts must be nonnegative")
    n = gained + lost
    tail = sum(math.comb(n, i) for i in range(min(gained, lost) + 1))
    return {"gained": gained, "lost": lost, "two_sided_p": min(1.0, 2 * tail / 2**n)}


def paired_bootstrap(
    base: Sequence[float], trained: Sequence[float], *, samples: int = SAMPLES
) -> dict[str, Any]:
    """Resample paired clusters, preserving both models and all trials within a cluster."""
    import numpy as np

    if not base or len(base) != len(trained):
        raise ValueError("paired arrays must be nonempty with equal lengths")
    a, b = np.asarray(base), np.asarray(trained)
    indices = np.random.default_rng(SEED).integers(0, len(a), size=(samples, len(a)))
    ab, bb = a[indices].mean(axis=1), b[indices].mean(axis=1)

    def interval(x: Any) -> list[float]:
        return [float(v) for v in np.quantile(x, [0.025, 0.975], method="inverted_cdf")]

    return {
        "baseline": float(a.mean()),
        "trained": float(b.mean()),
        "delta": float((b - a).mean()),
        "baseline_ci95": interval(ab),
        "trained_ci95": interval(bb),
        "delta_ci95": interval(bb - ab),
        "clusters": len(a),
    }


def refresh_observations() -> None:
    from invoiceops.runs import load_episodes
    from invoiceops.tasks.store import load_bundle

    folders = [
        ROOT / "runs/modal" / name for name in ("test-untrained-current-v3d", "test-trained-v3d")
    ]
    configs = [read_json(p / "config.json") for p in folders]
    matched = [
        "prompt_version",
        "temperature",
        "top_p",
        "max_tool_calls",
        "max_tokens",
        "context_tokens",
        "max_nudges",
        "revision",
        "task_data_sha256",
        "evaluation_sources_sha256",
    ]
    if any(configs[0][key] != configs[1][key] for key in matched):
        raise ValueError("baseline and trained evaluation settings do not match")
    by_model = []
    source_hashes = {}
    for folder in folders:
        records = load_episodes(folder)
        if len(records) != 96 or any(not r.verifier or not r.verifier.scorable for r in records):
            raise ValueError("requires all 96 audited, scorable attempts")
        grouped: dict[str, list[Any]] = defaultdict(list)
        for record in records:
            grouped[record.task_id].append(record)
        by_model.append(grouped)
        for file in sorted((folder / "episodes").glob("*.json")):
            with file.open("rb") as handle:
                source_hashes[str(file.relative_to(ROOT))] = hashlib.file_digest(
                    handle, "sha256"
                ).hexdigest()
    if by_model[0].keys() != by_model[1].keys():
        raise ValueError("models must cover the same tasks")
    observations = []
    for task_id in sorted(by_model[0]):
        bundle = load_bundle(task_id)
        row = {
            "task_id": task_id,
            "family": bundle.private.family,
            "family_name": bundle.private.family_name,
            "company_id": bundle.public.world.company.id,
            "company_name": bundle.public.world.company.name,
        }
        attachments = {d.id for d in bundle.public.world.documents if d.kind == "attachment"}
        for label, grouped in zip(("baseline", "trained"), by_model, strict=True):
            records = sorted(grouped[task_id], key=lambda r: r.attempt)
            if [r.attempt for r in records] != list(range(4)):
                raise ValueError("missing or duplicate trial")
            row[label] = [int(r.verifier.passed) for r in records]
            row[f"{label}_attachment_exposures"] = sum(
                any(
                    e.tool == "get_document" and e.arguments.get("document_id") in attachments
                    for e in r.log
                )
                for r in records
            )
        observations.append(row)
    OUT.mkdir(parents=True, exist_ok=True)
    OBSERVATIONS.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source": "audited raw InvoiceOps episodes",
                "baseline_run": str(folders[0].relative_to(ROOT)),
                "trained_run": str(folders[1].relative_to(ROOT)),
                "matched_config_fields": matched,
                "task_data_sha256": configs[0]["task_data_sha256"],
                "evaluation_sources_sha256": configs[0]["evaluation_sources_sha256"],
                "selected_adapter": configs[1]["merge_provenance"],
                "observations": observations,
                "source_episode_sha256": source_hashes,
            },
            indent=2,
        )
        + "\n"
    )


def binary_transition(rows: Sequence[dict[str, Any]], mode: str) -> dict[str, Any]:
    predicate = all if mode == "all" else any
    a = [int(predicate(r["baseline"])) for r in rows]
    b = [int(predicate(r["trained"])) for r in rows]
    gained = sum(not x and y for x, y in zip(a, b, strict=True))
    lost = sum(x and not y for x, y in zip(a, b, strict=True))
    return {**paired_bootstrap(a, b), **exact_mcnemar(gained, lost)}


def analyze_invoiceops(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) != 24 or len({r["task_id"] for r in rows}) != 24:
        raise ValueError("requires 24 distinct paired tasks")
    if any(
        len(r[key]) != 4 or any(x not in (0, 1) for x in r[key])
        for r in rows
        for key in ("baseline", "trained")
    ):
        raise ValueError("requires four binary outcomes per model and task")
    a, b = ([sum(r[key]) / 4 for r in rows] for key in ("baseline", "trained"))
    differences = [sum(r["trained"]) - sum(r["baseline"]) for r in rows]
    primary = {
        **paired_bootstrap(a, b),
        **exact_signflip(differences),
        "baseline_passes": sum(sum(r["baseline"]) for r in rows),
        "trained_passes": sum(sum(r["trained"]) for r in rows),
    }
    primary["baseline_failures"] = 96 - primary["baseline_passes"]
    primary["trained_failures"] = 96 - primary["trained_passes"]
    primary["relative_failure_reduction"] = (
        primary["baseline_failures"] - primary["trained_failures"]
    ) / primary["baseline_failures"]
    groups = {}
    for field, name in (("company_id", "companies"), ("family", "families")):
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row[field]].append(row)
        table = []
        for key, group in sorted(grouped.items()):
            ac = sum(sum(r["baseline"]) for r in group)
            bc = sum(sum(r["trained"]) for r in group)
            n = len(group) * 4
            table.append(
                {
                    "id": key,
                    "name": group[0]["company_name" if name == "companies" else "family_name"],
                    "tasks": len(group),
                    "attempts": n,
                    "baseline_passes": ac,
                    "trained_passes": bc,
                    "baseline": ac / n,
                    "trained": bc / n,
                    "delta": (bc - ac) / n,
                }
            )
        groups[name] = table
    companies = groups["companies"]
    if {c["tasks"] for c in companies} != {6}:
        raise ValueError("company comparison assumes six tasks per test company")
    leave_one_out = {
        c["id"]: (sum(differences) - (c["trained_passes"] - c["baseline_passes"])) / 72
        for c in companies
    }
    f10 = [r for r in rows if r["family"] == "F10"]
    return {
        "primary": primary,
        "pass_all_four": binary_transition(rows, "all"),
        "pass_any_four": binary_transition(rows, "any"),
        **groups,
        "tasks_improved": sum(d > 0 for d in differences),
        "tasks_worsened": sum(d < 0 for d in differences),
        "tasks_unchanged": sum(d == 0 for d in differences),
        "company_signflip": exact_signflip(
            [c["trained_passes"] - c["baseline_passes"] for c in companies]
        ),
        "leave_one_company_out_delta": leave_one_out,
        "f10_attachment_exposures": {
            key: sum(r[f"{key}_attachment_exposures"] for r in f10)
            for key in ("baseline", "trained")
        },
    }


def analyze_tau2() -> dict[str, Any]:
    a, b = [read_json(ROOT / f"reports/modal/tau2_{tag}.json") for tag in ("before", "after")]
    if a["per_task_mean_reward"].keys() != b["per_task_mean_reward"].keys():
        raise ValueError("tau2 task IDs differ")
    keys = sorted(a["per_task_mean_reward"])
    av, bv = ([r["per_task_mean_reward"][t] for t in keys] for r in (a, b))
    differences = [round(4 * (y - x)) for x, y in zip(av, bv, strict=True)]
    aa, ba = ([int(x == 1) for x in values] for values in (av, bv))
    return {
        "mean_reward": {
            **paired_bootstrap(av, bv),
            **exact_signflip(differences),
            "baseline_passes": round(sum(av) * 4),
            "trained_passes": round(sum(bv) * 4),
        },
        "pass_all_four": {
            **paired_bootstrap(aa, ba),
            **exact_mcnemar(
                sum(not x and y for x, y in zip(aa, ba, strict=True)),
                sum(x and not y for x, y in zip(aa, ba, strict=True)),
            ),
        },
    }


def analyze_bfcl() -> dict[str, Any]:
    before = read_json(ROOT / "reports/modal/bfcl_before.json")
    audit = read_json(ROOT / "reports/modal/bfcl_selected_audit.json")
    columns = [
        ("simple_python", "data_non_live.csv", "Python Simple AST"),
        ("multiple", "data_non_live.csv", "Multiple AST"),
        ("parallel", "data_non_live.csv", "Parallel AST"),
        ("parallel_multiple", "data_non_live.csv", "Parallel Multiple AST"),
        ("irrelevance", "data_non_live.csv", "Irrelevance Detection"),
        ("live_simple", "data_live.csv", "Python Simple AST"),
        ("live_multiple", "data_live.csv", "Python Multiple AST"),
        ("multi_turn_base", "data_multi_turn.csv", "Base"),
    ]
    rows = []
    for category, file, key in columns:
        published = next(csv.DictReader(io.StringIO(before["score_files"]["score/" + file])))[key]
        score = audit["categories"][category]
        n = score["total_count"]
        ac, bc = round(float(published[:-1]) / 100 * n), score["correct_count"]
        if f"{ac / n:.2%}" != published:
            raise ValueError("rounded baseline score does not uniquely reconstruct count")
        rows.append(
            {
                "category": category,
                "cases": n,
                "baseline_correct": ac,
                "trained_correct": bc,
                "baseline": ac / n,
                "trained": bc / n,
                "delta": (bc - ac) / n,
            }
        )
    total = sum(r["cases"] for r in rows)
    ac, bc = (sum(r[key] for r in rows) for key in ("baseline_correct", "trained_correct"))
    return {
        "categories": rows,
        "executed_case_micro": {
            "cases": total,
            "baseline_correct": ac,
            "trained_correct": bc,
            "baseline": ac / total,
            "trained": bc / total,
            "delta": (bc - ac) / total,
            "official_bfcl_overall": False,
        },
        "paired_case_inference": "Unavailable: baseline per-case outcomes are not local.",
    }


def analyze_prompting() -> dict[str, Any]:
    initial = read_json(ROOT / "reports/modal/test_candidate.json")["v1"]
    selected = read_json(ROOT / "reports/modal/fresh_untrained_control.json")
    trained = read_json(ROOT / "reports/modal/select_and_test.json")["test"]
    stages = []
    for name, prompt, result, source in (
        ("Initial prompt", "v1", initial, "reports/modal/test_candidate.json#/v1"),
        ("Selected prompt", "v3d", selected, "reports/modal/fresh_untrained_control.json"),
        ("Selected prompt + RL", "v3d", trained, "reports/modal/select_and_test.json#/test"),
    ):
        stages.append(
            {
                "stage": name,
                "prompt": prompt,
                "success": result["task_mean_success"],
                "passes": round(result["task_mean_success"] * result["scored_attempts"]),
                "attempts": result["scored_attempts"],
                "source": source,
            }
        )
    experiments = []
    for prompt in ("v3a", "v3b", "v3c", "v3d", "v4"):
        result = read_json(ROOT / f"reports/modal/prompt_trial-{prompt}.json")
        train, dev = result["train"], result["dev"]
        experiments.append(
            {
                "prompt": prompt,
                "train": train["task_mean_success"],
                "dev": dev["task_mean_success"],
                "train_dev": (
                    train["task_mean_success"] * train["tasks"]
                    + dev["task_mean_success"] * dev["tasks"]
                )
                / (train["tasks"] + dev["tasks"]),
                "critical_violation_rate": (
                    train["attempts_with_critical_violation"]
                    + dev["attempts_with_critical_violation"]
                )
                / (train["scored_attempts"] + dev["scored_attempts"]),
            }
        )
    return {
        "stages": stages,
        "selection_experiments": experiments,
        "initial_to_selected_delta": selected["task_mean_success"] - initial["task_mean_success"],
        "selected_to_rl_delta": trained["task_mean_success"] - selected["task_mean_success"],
    }


def write_report(data: dict[str, Any]) -> None:
    domain, external = data["invoiceops"], data["tau2"]
    primary = domain["primary"]
    metrics = [
        ("InvoiceOps strict success", primary),
        ("InvoiceOps all four attempts", domain["pass_all_four"]),
        ("τ² mean reward", external["mean_reward"]),
        ("τ² all four trials", external["pass_all_four"]),
    ]
    rows = []
    for name, result in metrics:
        low, high = result["delta_ci95"]
        rows.append(
            f"| {name} | {100 * result['baseline']:.3f}% | {100 * result['trained']:.3f}% "
            f"| {100 * result['delta']:+.3f} | [{100 * low:+.3f}, {100 * high:+.3f}] "
            f"| {result['two_sided_p']:.6f} |"
        )
    company_rows = []
    for c in domain["companies"]:
        leave_out = domain["leave_one_company_out_delta"][c["id"]]
        company_rows.append(
            f"| {c['name']} | {c['baseline_passes']}/24 | {c['trained_passes']}/24 "
            f"| {100 * c['delta']:+.3f} | {100 * leave_out:+.3f} |"
        )
    family_rows = [
        f"| {r['id']} · {r['name']} | {100 * r['baseline']:.1f}% "
        f"| {100 * r['trained']:.1f}% | {100 * r['delta']:+.1f} |"
        for r in domain["families"]
    ]
    prompt_rows = [
        f"| {r['stage']} | {r['prompt']} | {r['passes']}/{r['attempts']} "
        f"| {100 * r['success']:.3f}% |"
        for r in data["prompting"]["stages"]
    ]
    micro = data["bfcl"]["executed_case_micro"]
    text = (
        """# Statistical analysis of the completed experiment

This analysis reports observed effects, uncertainty and sensitivity checks for the
dev-selected step-125 adapter. Every successful and unsuccessful attempt remains in the
data. Primary inference compares the selected-prompt untrained model with the trained
model using identical task data, prompt, decoding and evaluation-source fingerprints.

## Initial prompt, selected prompt, and RL

| Configuration | Prompt | Passes | Strict success |
|---|---|---:|---:|
"""
        + "\n".join(prompt_rows)
        + """

The initial-to-selected prompt comparison is +71.875 percentage points. The additional
matched RL comparison is +8.333 points. Prompt source texts and the complete sequence of
selection experiments are retained in `reports/prompt_trials.md`; the three stage counts
and their source files are recorded in `reports/statistics/analysis.json`.

## Effect sizes and paired inference

| Outcome | Untrained | Trained | Δ (pp) | 95% paired-task interval (pp) | Exact two-sided p |
|---|---:|---:|---:|---:|---:|
"""
        + "\n".join(rows)
        + """

These are exploratory, post hoc analyses of completed runs. The InvoiceOps primary
endpoint was strict verifier success; secondary p-values are unadjusted and not
confirmatory. No reported RL or external effect is statistically significant at 0.05.

### What the positive domain effect means

- Success: **76/96 → 84/96**, eight additional successful attempts, +8.333 percentage points.
- Failures: **20 → 12**, a **40% relative reduction in the observed failure count**.
  This is a descriptive relative effect, not a 40-point accuracy gain.
- Repeat reliability: **14/24 → 18/24** tasks pass every attempt. Five tasks gain that
  consistency and one loses it; exact McNemar p = 0.218750.
- At-least-one success: **23/24 → 23/24**, unchanged. Training improved repeat execution
  on the sampled tasks, not the count of tasks solved at least once.
- Six task-level success rates improve, sixteen stay equal and two worsen. Every outcome
  is included rather than reporting only the improved tasks.

## Resampling and test definitions

**Bootstrap.** For each endpoint, resample paired task indices with replacement, keeping
both models and all four attempts together. Compute each model mean and their difference
in every resample. Use 100,000 draws from NumPy `default_rng(0)` and the 2.5th/97.5th
empirical percentiles (`method='inverted_cdf'`). InvoiceOps uses 24 task clusters; tau2
uses 40. These higher-resample intervals are generated directly for the figures; older
run summaries retain their original smaller-bootstrap intervals and unchanged point estimates.

**Exact paired sign-flip test.** Let d_i be the trained minus untrained number of successes
on task i. Under the exchangeable/symmetric paired null, enumerate the distribution of
sum(s_i d_i), for independent signs s_i in {-1,+1}. The two-sided p-value includes all
assignments with absolute sum at least the observed absolute sum. Zero differences do
not add information. A dynamic program enumerates the exact distribution: the primary
effect has 8 nonzero pairs, 256 assignments, and 36 extreme assignments (p = 0.140625).
The tau2 mean has 18 nonzero pairs and 262,144 assignments (p = 0.766815).

**Reliability.** Convert each task to a binary indicator for all four attempts succeeding.
Use the exact conditional binomial/McNemar test on gained and lost indicators. We do not
pair individual stochastic attempt indices or treat repeated attempts as independent tasks.

Task-level inference assumes tasks are suitable exchangeable units. Because InvoiceOps
tasks share companies, the company sensitivity below is essential; 24 tasks are not 24
independent companies. Neither the bootstrap nor a small p-value would repair prior test
inspection or establish a randomized causal experiment.

## Company sensitivity

Each of the four test companies contributes six tasks and 24 attempts.

| Company | Untrained passes | Trained passes | Company Δ (pp) | Δ omitting company (pp) |
|---|---:|---:|---:|---:|
"""
        + "\n".join(company_rows)
        + """

Three company means improve and one is unchanged. All four leave-one-company-out effects
are positive, from +5.556 to +11.111 points. This shows that the observed gain is not
entirely dependent on one company. It does not supply four independent confirmations:
the company-level exact sign-flip test has only three nonzero company differences and
eight assignments, giving **p = 0.250**. Four companies are too few for a precise
population-level generalization claim. We do not promote a small-cluster percentile
interval into a significance claim.

## Family-level description

| Family | Untrained | Trained | Change (pp) |
|---|---:|---:|---:|
"""
        + "\n".join(family_rows)
        + """

Six families improve, five are unchanged and one declines. Each row has only two tasks
and eight attempts, so no family-level significance tests are reported. F10 attachments
were opened in **0/8 attempts under either model**. Its gain is scenario completion,
not demonstrated resistance to prompt injection.

## External results

The RL dataset contained InvoiceOps tasks only. Tau2 uses the same retail tasks, customer
model, seed, trial count and ENV-only grading before and after training. Its mean reward
rises by 1.875 points and all-four reliability by 2.500 points. The mean-reward interval
is -6.25 to +10.00 points and exact p is 0.766815: positive point estimates, not established
general transfer. The all-four outcome has three gained and two lost tasks (p = 1.0).

BFCL's eight executed categories contain **2,751 cases**. Summing correct cases gives
**2,214 → 2,211**, or **80.480% → 80.371%** (-0.109 points). This is a custom
executed-case micro-average, not BFCL's official Overall score. Its weights are the
numbers of cases in the executed categories; it is not a category-balanced average.
Baseline integer counts are uniquely reconstructed from published rounded category
accuracies at the known denominators, with round-trip checks in the analysis script.

Two BFCL categories improve, five decline and one is unchanged. All category effects
appear in the external figure and `reports/bfcl_selected.md`. Baseline per-case outcomes
are not available locally, so no paired case-level test or formal noninferiority claim is
made. “Largely retained” describes the observed scores, not a proven statistical margin.

## Behavior and cost checks

- False completions: **3 → 0**. Critical-violation attempts: **3 → 4**. The results do
  not establish a safety improvement; sparse events cannot support strong rate claims.
- Mean tool calls: **10.656 → 10.823**. Mean seconds per attempt: **24.06 → 27.90**.
  Completion tokens: **106,450 → 123,178**. No speed or token-efficiency improvement is claimed.
- No InvoiceOps infrastructure errors, missing attempts, context-limit stops or truncated
  turns. All 96 trained and 96 control traces replay exactly.
- Tau2 has all 160 rewarded trials, including one max-step trajectory retained as a zero.
  Its standard ENV-only grading is narrower than full conversational correctness.

## Reproduction and source integrity

```bash
uv run --frozen --group analysis python scripts/analyze_results.py
```

The included `reports/statistics/paired_observations.json` holds the 24 task IDs,
company/family labels, all four binary outcomes per model, source episode hashes, matching
task/evaluation fingerprints and selected adapter provenance. It was extracted from the
previously audited raw records, not reconstructed from the headline success rate. Tau2
uses its per-task means; BFCL uses its category CSVs and audited denominators.

To re-extract the compact observations from the full local trajectories:

```bash
uv run --frozen --group analysis python scripts/analyze_results.py --refresh-observations
```

The standard command works without raw trajectories or model APIs. JSON statistics and
all SVG/PNG figures are regenerated deterministically from the included data and locked
analysis dependencies. Figures retain zero reference lines and show uncertainty or all
evaluated categories where applicable. The complete evaluated model is checkpoint 125,
with the same adapter SHA-256 across InvoiceOps, BFCL and tau2.
"""
    )
    if micro["baseline_correct"] != 2214 or micro["trained_correct"] != 2211:
        raise ValueError("BFCL narrative counts differ from the source analysis")
    (ROOT / "reports/statistical_analysis.md").write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh-observations", action="store_true")
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()
    if args.refresh_observations:
        refresh_observations()
    if not OBSERVATIONS.exists():
        raise SystemExit("Missing paired observations; refresh requires the local raw episodes.")
    observations = read_json(OBSERVATIONS)
    analysis = {
        "method": {
            "bootstrap_samples": SAMPLES,
            "seed": SEED,
            "bootstrap_interval": "paired percentile, inverted empirical CDF, 95%",
            "primary_unit": "task; all four attempts retained together",
            "company_sensitivity": "exact sign-flip and leave-one-company-out; four companies",
            "tests": "two-sided exact; no one-sided or independence-of-attempts tests",
            "analysis_timing": "post hoc exploratory analysis of completed runs",
            "secondary_p_values": "unadjusted, not confirmatory",
        },
        "invoiceops": analyze_invoiceops(observations["observations"]),
        "tau2": analyze_tau2(),
        "bfcl": analyze_bfcl(),
        "prompting": analyze_prompting(),
    }
    baseline = read_json(ROOT / "reports/modal/fresh_untrained_control.json")
    trained = read_json(ROOT / "reports/modal/select_and_test.json")["test"]
    analysis["behavior"] = {
        k: {"baseline": baseline[k], "trained": trained[k]}
        for k in (
            "attempts_with_critical_violation",
            "false_completions",
            "mean_tool_calls",
            "mean_seconds",
            "tokens",
        )
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    write_report(analysis)
    if not args.no_figures:
        from plot_results import render_all

        render_all(analysis, ROOT / "assets/figures")
    print(
        json.dumps(
            {
                "invoiceops": analysis["invoiceops"]["primary"],
                "reliability": analysis["invoiceops"]["pass_all_four"],
                "company_sensitivity": analysis["invoiceops"]["company_signflip"],
                "tau2": analysis["tau2"]["mean_reward"],
                "bfcl_executed_cases": analysis["bfcl"]["executed_case_micro"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
