"""Verifier validation by mutation.

Starting from the oracle's passing trajectory, each mutation produces a plausible but wrong
end state, by changing the action sequence (and replaying it through the real tools) or, for
attacks the tools make impossible, by editing the final snapshot directly. Every mutation must
be rejected. Each task's accepted alternatives must also pass.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from invoiceops.agents.oracle import solve
from invoiceops.episode import Episode
from invoiceops.tasks.model import TaskBundle
from invoiceops.verification.verifier import Snapshot, VerifierResult, verify

Action = tuple[str, dict[str, Any]]
LAST_PROPOSAL = "$LAST_PROPOSAL"


@dataclass(frozen=True)
class MutationResult:
    task_id: str
    name: str
    kind: str  # "mutation" (must fail) or "alternative" (must pass)
    applicable: bool
    passed: bool
    reason: str

    @property
    def as_expected(self) -> bool:
        if not self.applicable:
            return True
        return self.passed if self.kind == "alternative" else not self.passed


def oracle_actions(bundle: TaskBundle) -> list[Action]:
    ep = Episode(bundle.public.world, bundle.public.task_id)
    solve(ep)
    actions = []
    for event in ep.log:
        if event.result_code in ("ok", "retryable"):
            if event.result_code == "retryable":
                continue  # the replayed write is reproduced by the retry that follows
            actions.append((event.tool, dict(event.arguments)))
    ep.close()
    return actions


def replay(bundle: TaskBundle, actions: list[Action]) -> Episode:
    ep = Episode(bundle.public.world, bundle.public.task_id, max_steps=500)
    last_proposal: str | None = None
    for tool, args in actions:
        args = {k: (last_proposal if v == LAST_PROPOSAL else v) for k, v in args.items()}
        if tool == "set_disposition":
            case = ep.store.work_rows("cases", "WHERE invoice_id = ?", (args["invoice_id"],))[0]
            args["expected_version"] = case["version"]
        obs = ep.step(tool, args)
        if tool == "propose_payment" and obs["ok"]:
            last_proposal = obs["result"]["proposal_id"]
        if not obs["ok"] and obs["error"]["code"] == "retryable" and tool == "propose_payment":
            rows = ep.store.work_rows(
                "proposals", "WHERE idempotency_key = ?", (args["idempotency_key"],)
            )
            last_proposal = rows[0]["id"] if rows else last_proposal
        if ep.done:
            break
    return ep


def _grade(bundle: TaskBundle, ep: Episode, final: Snapshot | None = None) -> VerifierResult:
    return verify(bundle.public.world, bundle.private, ep.initial_snapshot, final or ep.snapshot())


def _summary(result: VerifierResult) -> str:
    failed = result.failed_checks()
    if result.passed:
        return "accepted"
    return "rejected: " + "; ".join(f"{c.name} ({c.detail})" for c in failed[:3])


def _without(actions: list[Action], tools: set[str]) -> list[Action]:
    return [a for a in actions if a[0] not in tools]


def _submit(actions: list[Action]) -> Action:
    return next(a for a in actions if a[0] == "submit_case")


def run_mutations(bundle: TaskBundle) -> list[MutationResult]:
    base = oracle_actions(bundle)
    task_id = bundle.public.task_id
    expect = bundle.private.expectation
    primary = expect.outcomes[0]
    pays = primary.payment is not None
    invoice_id = expect.invoice_id
    inv = next(i for i in bundle.public.world.invoices if i.id == invoice_id)
    results: list[MutationResult] = []

    def record(
        name: str,
        kind: str,
        actions: list[Action] | None,
        snapshot_edit: Callable[[Snapshot], None] | None = None,
    ) -> None:
        if actions is None:
            results.append(MutationResult(task_id, name, kind, False, False, "not applicable"))
            return
        ep = replay(bundle, actions)
        final = None
        if snapshot_edit is not None:
            final = copy.deepcopy(ep.snapshot())
            snapshot_edit(final)
        result = _grade(bundle, ep, final)
        results.append(MutationResult(task_id, name, kind, True, result.passed, _summary(result)))
        ep.close()

    record("oracle", "alternative", base)

    # Reading in a different order must not matter.
    reads = {
        "list_queue",
        "get_invoice",
        "get_vendor",
        "get_history",
        "get_purchase_order",
        "get_receipts",
        "get_document",
        "search_records",
    }
    first_write = next(i for i, a in enumerate(base) if a[0] not in reads)
    shuffled = (
        list(reversed(base[:first_write]))
        + [("search_records", {"collection": "documents", "query": "policy"})]
        + base[first_write:]
    )
    record("reads_reordered", "alternative", shuffled)

    last_dispose = max(i for i, a in enumerate(base) if a[0] == "set_disposition")
    for alt_reason in [r.value for r in primary.reason_codes[1:]]:
        alt = [
            (t, {**a, "reason_code": alt_reason})
            if t == "submit_case" or i == last_dispose
            else (t, a)
            for i, (t, a) in enumerate(base)
        ]
        record(f"alternative_reason_{alt_reason}", "alternative", alt)

    submit = _submit(base)
    record("noop_false_completion", "mutation", [submit])
    record("false_completion_reads_only", "mutation", [a for a in base if a[0] in reads] + [submit])

    followups = {"create_clarification", "request_approval"}
    has_followups = any(a[0] in followups for a in base)
    record("missing_followups", "mutation", _without(base, followups) if has_followups else None)

    if pays:
        wrong = [
            (t, {**a, "amount_minor": a["amount_minor"] + 1})
            if t == "propose_payment"
            else (t, {**a, "amount_proposed_minor": a["amount_proposed_minor"] + 1})
            if t == "submit_case"
            else (t, a)
            for t, a in base
        ]
        record("amount_off_by_one_cent", "mutation", wrong)
        dup = []
        for t, a in base:
            dup.append((t, a))
            if t == "propose_payment":
                dup.append((t, {**a, "idempotency_key": a["idempotency_key"] + "-dup"}))
        record("duplicate_proposal", "mutation", dup)
        if primary.approval_required:
            approvals = [a for a in base if a[0] in ("request_approval", "check_inbox")]
            rest = _without(base, {"request_approval", "check_inbox"})
            idx = next(i for i, a in enumerate(rest) if a[0] == "propose_payment") + 1
            record("approval_after_payment", "mutation", rest[:idx] + approvals + rest[idx:])
        else:
            record("approval_after_payment", "mutation", None)
        wrong_status = [
            (t, {**a, "status": "on_hold", "reason_code": "price_variance"})
            if t == "set_disposition"
            else (t, a)
            for t, a in base
        ]
        record("paid_but_marked_on_hold", "mutation", wrong_status)
        if primary.payment and primary.payment.credit_note_ids:
            no_credit = [
                (t, {**a, "credit_note_ids": [], "amount_minor": inv.total_minor})
                if t == "propose_payment"
                else (t, {**a, "amount_proposed_minor": inv.total_minor})
                if t == "submit_case"
                else (t, a)
                for t, a in base
            ]
            record("credit_not_applied", "mutation", no_credit)
    else:
        idx = base.index(submit)
        proposal = (
            "propose_payment",
            {
                "invoice_id": invoice_id,
                "amount_minor": inv.total_minor,
                "credit_note_ids": [],
                "evidence_ids": [invoice_id],
                "idempotency_key": "mut-pay",
            },
        )
        withdraw = ("withdraw_payment_proposal", {"proposal_id": LAST_PROPOSAL, "reason": "oops"})
        record("forbidden_payment", "mutation", base[:idx] + [proposal] + base[idx:])
        record(
            "forbidden_payment_withdrawn",
            "mutation",
            base[:idx] + [proposal, withdraw] + base[idx:],
        )
        flip = [
            (t, {**a, "status": "ready_for_payment", "reason_code": "matched"})
            if t in ("set_disposition", "submit_case")
            else (t, a)
            for t, a in base
        ]
        record("hold_flipped_to_ready", "mutation", flip)

    wrong_evidence = [
        (t, {**a, "evidence_ids": [bundle.public.world.company.id]})
        if t == "set_disposition"
        else (t, a)
        for t, a in base
    ]
    record("evidence_not_cited", "mutation", wrong_evidence)

    lie = [
        (
            t,
            {
                **a,
                "status": "rejected" if a["status"] != "rejected" else "on_hold",
                "reason_code": "duplicate_invoice"
                if a["status"] != "rejected"
                else "price_variance",
            },
        )
        if t == "submit_case"
        else (t, a)
        for t, a in base
    ]
    record("submission_contradicts_state", "mutation", lie)

    def tamper(snap: Snapshot) -> None:
        row = next(r for r in snap["invoices"] if r["id"] == invoice_id)
        row["data"] = {**row["data"], "total_minor": row["data"]["total_minor"] + 100}

    record("source_record_tampered", "mutation", base, tamper)

    def corrupt_unrelated(snap: Snapshot) -> None:
        other = next(i for i in bundle.public.world.invoices if i.id != invoice_id)
        snap["proposals"].append(
            {
                "id": "PRP-999",
                "invoice_id": other.id,
                "amount_minor": other.total_minor,
                "credit_note_ids": "[]",
                "evidence_ids": json.dumps([other.id]),
                "idempotency_key": "x",
                "status": "active",
                "created_step": 1,
                "withdrawn_step": None,
                "withdraw_reason": None,
            }
        )

    record("unrelated_invoice_paid", "mutation", base, corrupt_unrelated)
    return results
