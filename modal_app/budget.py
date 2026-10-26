"""Budget guard and spend ledger for Modal jobs. Pure Python; no Modal import needed.

Rules (BUILD_PLAN.md section 4.4):
* Rates must be confirmed from the Modal dashboard before any launch.
* Jobs that use InvoiceOps tasks need the signed pre-GPU review.
* A job's worst case (timeout x rate) must fit in the money left after setting aside the caps
  of every job that has not run yet, so no job can eat another job's budget.
* An optional ``spend_limit_usd`` caps total spend so far: the owner raises it when they
  release more credit. A job is refused if spend so far plus its worst case would exceed it.
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
class Allocation:
    """A separately released dollar pool bound to one Modal account profile.

    Ledger entries carry ``allocation``; entries without it belong to the default pool
    governed by ``total_usd``/``spend_limit_usd``. An allocation's limit governs its
    member jobs regardless of the default pool's released credit.
    """

    name: str
    limit_usd: float
    account_profile: str
    jobs: tuple[str, ...]


@dataclass(frozen=True)
class Budget:
    total_usd: float
    rates_confirmed: bool
    rates: dict[str, float]
    jobs: dict[str, Job]
    spend_limit_usd: float | None = None
    allocations: dict[str, Allocation] | None = None

    def rate(self, job: Job) -> float:
        return self.rates[job.gpu]

    def worst_case(self, job: Job) -> float:
        return round(self.rate(job) * job.timeout_min / 60, 4)

    def allocation_for(self, job_name: str) -> Allocation | None:
        for alloc in (self.allocations or {}).values():
            if job_name in alloc.jobs:
                return alloc
        return None


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
    allocations = {
        name: Allocation(
            name=name,
            limit_usd=float(spec["limit_usd"]),
            account_profile=str(spec["account_profile"]),
            jobs=tuple(spec["jobs"]),
        )
        for name, spec in (data.get("allocations") or {}).items()
    }
    for alloc in allocations.values():
        missing = [j for j in alloc.jobs if j not in jobs]
        if missing:
            raise BudgetError(f"allocation {alloc.name} names unknown jobs: {missing}")
    budget = Budget(
        total_usd=float(data["total_usd"]),
        rates_confirmed=bool(data["rates_confirmed"]),
        rates={k: float(v) for k, v in data["rates_usd_per_hour"].items()},
        jobs=jobs,
        spend_limit_usd=(
            None if data.get("spend_limit_usd") is None else float(data["spend_limit_usd"])
        ),
        allocations=allocations,
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
    account_profile: str = "default",
) -> dict[str, float]:
    """Raise ``BudgetError`` if the job may not start; otherwise return the money figures.

    Jobs named in an ``allocations`` entry are charged to that allocation: their ledger
    lines carry the allocation name and only same-allocation entries count toward spent,
    done and reserved. All other jobs use the default pool exactly as before, except that
    allocation jobs no longer reserve their caps from the default pool.
    """
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

    alloc = budget.allocation_for(job_name)
    if alloc is not None:
        return _check_allocated(budget, job, alloc, ledger, rerun, account_profile)

    alloc_jobs = {j for a in (budget.allocations or {}).values() for j in a.jobs}
    unscoped = [e for e in ledger if not e.get("allocation")]
    done = {e["job"] for e in unscoped if e.get("status") == "succeeded"}
    if job_name in done and not rerun:
        raise BudgetError(f"{job_name} already succeeded; pass --rerun to spend on it again")
    spent = sum(float(e.get("cost_usd", 0.0)) for e in unscoped)
    reserved = sum(
        j.cap_usd
        for name, j in budget.jobs.items()
        if name not in done and name != job_name and name not in alloc_jobs
    )
    available = budget.total_usd - spent - reserved
    worst = budget.worst_case(job)
    limit = budget.spend_limit_usd
    if limit is not None and spent + worst > limit + 1e-9:
        raise BudgetError(
            f"{job_name} could cost up to ${worst:.2f}, but only ${max(limit - spent, 0):.2f} "
            f"of the released ${limit:.2f} is left (spent ${spent:.2f}); the owner raises "
            "spend_limit_usd in budget.yaml to release more"
        )
    if worst > available + 1e-9:
        raise BudgetError(
            f"{job_name} could cost up to ${worst:.2f} "
            f"(timeout {job.timeout_min} min on {job.gpu}) "
            f"but only ${available:.2f} is free after reserving other jobs' caps "
            f"(spent ${spent:.2f}, reserved ${reserved:.2f})"
        )
    return {"spent": spent, "reserved": reserved, "available": available, "worst_case": worst}


def _check_allocated(
    budget: Budget,
    job: Job,
    alloc: Allocation,
    ledger: list[dict[str, Any]],
    rerun: bool,
    account_profile: str,
) -> dict[str, float]:
    """Admission check for a job paid from a dedicated ``allocations`` entry."""
    if account_profile != alloc.account_profile:
        raise BudgetError(
            f"{job.name} is paid from the '{alloc.name}' allocation, which is bound to Modal "
            f"profile {alloc.account_profile!r} (resolved profile: {account_profile!r}); run "
            "with the right --env-file / MODAL_PROFILE so the charge lands on that account"
        )
    scoped = [e for e in ledger if e.get("allocation") == alloc.name]
    done = {e["job"] for e in scoped if e.get("status") == "succeeded"}
    if job.name in done and not rerun:
        raise BudgetError(
            f"{job.name} already succeeded under allocation '{alloc.name}'; "
            "pass --rerun to spend on it again"
        )
    spent = sum(float(e.get("cost_usd", 0.0)) for e in scoped)
    # Reserve the other unfinished member jobs' worst cases inside the allocation so a
    # smoke cannot eat the main run's money.
    reserved = sum(
        budget.worst_case(budget.jobs[name])
        for name in alloc.jobs
        if name != job.name and name not in done
    )
    worst = budget.worst_case(job)
    remaining = alloc.limit_usd - spent - reserved
    if worst > remaining + 1e-9:
        raise BudgetError(
            f"{job.name} could cost up to ${worst:.2f} (timeout {job.timeout_min} min on "
            f"{job.gpu}) but allocation '{alloc.name}' has only ${max(remaining, 0):.2f} left "
            f"of its ${alloc.limit_usd:.2f} (spent ${spent:.2f}, reserved ${reserved:.2f} "
            "for the remaining member jobs)"
        )
    return {
        "spent": spent,
        "reserved": reserved,
        "available": remaining,
        "worst_case": worst,
        "allocation_limit": alloc.limit_usd,
    }
