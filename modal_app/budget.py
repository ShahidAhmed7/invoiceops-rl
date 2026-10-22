"""Budget guard and spend ledger for Modal jobs. Pure Python; no Modal import needed.

Rules (BUILD_PLAN.md section 4.4):
* Rates must be confirmed from the Modal dashboard before any launch.
* Jobs that use InvoiceOps tasks need the signed pre-GPU review.
* A job's worst case (timeout x rate) must fit in the money left after setting aside the caps
  of every job that has not run yet, so no job can eat another job's budget.
* Every launch is appended to the ledger with its measured wall-clock cost.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "modal_app" / "budget.yaml"
LEDGER = ROOT / "reports" / "modal_ledger.jsonl"
SIGNOFF = ROOT / "docs" / "review" / "signoff" / "pre-gpu.md"


class BudgetError(RuntimeError):
    pass


@dataclass(frozen=True)
class Job:
    name: str
    phase: str
    gpu: str
    cap_usd: float
    timeout_min: int
    needs_signoff: bool


@dataclass(frozen=True)
class Budget:
    total_usd: float
    rates_confirmed: bool
    rates: dict[str, float]
    jobs: dict[str, Job]

    def rate(self, job: Job) -> float:
        return self.rates[job.gpu]

    def worst_case(self, job: Job) -> float:
        return round(self.rate(job) * job.timeout_min / 60, 4)


def load_budget(path: Path = CONFIG) -> Budget:
    data = yaml.safe_load(path.read_text())
    jobs = {
        name: Job(
            name=name,
            phase=str(spec["phase"]),
            gpu=spec["gpu"],
            cap_usd=float(spec["cap_usd"]),
            timeout_min=int(spec["timeout_min"]),
            needs_signoff=bool(spec["needs_signoff"]),
        )
        for name, spec in data["jobs"].items()
    }
    budget = Budget(
        total_usd=float(data["total_usd"]),
        rates_confirmed=bool(data["rates_confirmed"]),
        rates={k: float(v) for k, v in data["rates_usd_per_hour"].items()},
        jobs=jobs,
    )
    caps = sum(j.cap_usd for j in jobs.values())
    if caps > budget.total_usd + 1e-9:
        raise BudgetError(f"job caps ({caps:.2f}) exceed the total budget ({budget.total_usd:.2f})")
    return budget


def read_ledger(path: Path = LEDGER) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def append_ledger(entry: dict[str, Any], path: Path = LEDGER) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def signoff_approved(path: Path = SIGNOFF) -> bool:
    if not path.exists():
        return False
    return re.search(r"-\s*\[[xX]\]\s*Approved", path.read_text()) is not None


def check_launch(
    budget: Budget,
    job_name: str,
    ledger: list[dict[str, Any]],
    signed_off: bool,
    rerun: bool = False,
) -> dict[str, float]:
    """Raise ``BudgetError`` if the job may not start; otherwise return the money figures."""
    if job_name not in budget.jobs:
        raise BudgetError(f"unknown job {job_name}; known: {', '.join(budget.jobs)}")
    job = budget.jobs[job_name]
    if not budget.rates_confirmed:
        raise BudgetError(
            "set rates_usd_per_hour from your Modal dashboard and rates_confirmed: true"
        )
    if job.needs_signoff and not signed_off:
        signoff = SIGNOFF.relative_to(ROOT)
        raise BudgetError(f"{job_name} uses InvoiceOps tasks: commit an approved {signoff} first")
    done = {e["job"] for e in ledger if e.get("status") == "succeeded"}
    if job_name in done and not rerun:
        raise BudgetError(f"{job_name} already succeeded; pass --rerun to spend on it again")
    spent = sum(float(e.get("cost_usd", 0.0)) for e in ledger)
    reserved = sum(
        j.cap_usd for name, j in budget.jobs.items() if name not in done and name != job_name
    )
    available = budget.total_usd - spent - reserved
    worst = budget.worst_case(job)
    if worst > available + 1e-9:
        raise BudgetError(
            f"{job_name} could cost up to ${worst:.2f} "
            f"(timeout {job.timeout_min} min on {job.gpu}) "
            f"but only ${available:.2f} is free after reserving other jobs' caps "
            f"(spent ${spent:.2f}, reserved ${reserved:.2f})"
        )
    return {"spent": spent, "reserved": reserved, "available": available, "worst_case": worst}
