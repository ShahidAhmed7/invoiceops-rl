"""Trusted verifier: grades the final state and history of an episode.

The verifier reads only the final snapshot (all tables, including history tables), the
initial snapshot, the world, and the private task. It never reads the agent's prose for
correctness: the submission summary is checked only for consistency with the state.

Reward is strict: 1.0 if every global check passes and at least one acceptable outcome is
fully met, otherwise 0.0. If the verifier itself fails, the result is *unscorable* (reward
``None``), which is reported separately from a graded failure.
"""

from __future__ import annotations

import json
import traceback
from typing import Any

from pydantic import BaseModel, ConfigDict

from invoiceops.domain.world import World
from invoiceops.state.store import SOURCE_TABLES, canonical_json
from invoiceops.tasks.model import CiteGroups, Outcome, PrivateTask

Snapshot = dict[str, list[dict[str, Any]]]


class CheckResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    passed: bool
    detail: str
    critical: bool = False


class OutcomeResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    passed: bool
    checks: list[CheckResult]


class VerifierResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    task_id: str
    scorable: bool
    reward: float | None
    passed: bool
    global_checks: list[CheckResult]
    outcomes: list[OutcomeResult]
    matched_outcome: str | None
    critical_violations: list[str]
    false_completion: bool
    error: str | None = None

    def failed_checks(self) -> list[CheckResult]:
        failed = [c for c in self.global_checks if not c.passed]
        best = _best(self.outcomes)
        if best is not None:
            failed += [c for c in best.checks if not c.passed]
        return failed


def _best(outcomes: list[OutcomeResult]) -> OutcomeResult | None:
    if not outcomes:
        return None
    return max(outcomes, key=lambda o: (o.passed, sum(c.passed for c in o.checks)))


def _ids(value: str) -> list[str]:
    return list(json.loads(value))


def _cited(groups: CiteGroups, cited: set[str]) -> tuple[bool, str]:
    missing = [group for group in groups if not cited.intersection(group)]
    if not missing:
        return True, "all required records cited"
    readable = "; ".join(" or ".join(group) for group in missing)
    return False, f"missing citation of: {readable}"


def verify(
    world: World,
    private: PrivateTask,
    initial: Snapshot,
    final: Snapshot,
) -> VerifierResult:
    try:
        return _verify(world, private, initial, final)
    except Exception as exc:  # any verifier failure makes the episode unscorable
        return VerifierResult(
            task_id=private.task_id,
            scorable=False,
            reward=None,
            passed=False,
            global_checks=[],
            outcomes=[],
            matched_outcome=None,
            critical_violations=[],
            false_completion=False,
            error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc(limit=3)}",
        )


def _verify(
    world: World, private: PrivateTask, initial: Snapshot, final: Snapshot
) -> VerifierResult:
    invoice_id = private.expectation.invoice_id
    case = next((c for c in final["cases"] if c["invoice_id"] == invoice_id), None)
    if case is None:
        raise ValueError(f"case for {invoice_id} missing from snapshot")
    proposals = [p for p in final["proposals"] if p["invoice_id"] == invoice_id]
    active = [p for p in proposals if p["status"] == "active"]
    submission = next((s for s in final["submission"] if s["invoice_id"] == invoice_id), None)
    critical: list[str] = []

    # -- global checks ---------------------------------------------------------------------
    g: list[CheckResult] = []
    g.append(
        CheckResult(
            name="submitted",
            passed=submission is not None,
            detail="submit_case was called" if submission else "the case was never submitted",
        )
    )

    released_ids: set[str] = set()
    released = {r["event_id"] for r in final["released_events"]}
    for event in world.events:
        if event.id in released:
            released_ids.update(d.id for d in event.effects.documents)
            released_ids.update(r.id for r in event.effects.receipts)
    tampered: list[str] = []
    for table in SOURCE_TABLES:
        before = {(r["id"], r["revision"]): canonical_json(r["data"]) for r in initial[table]}
        after = {(r["id"], r["revision"]): canonical_json(r["data"]) for r in final[table]}
        for key, data in before.items():
            if after.get(key) != data:
                tampered.append(f"{table}:{key[0]}")
        for key in after.keys() - before.keys():
            if key[0] not in released_ids:
                tampered.append(f"{table}:{key[0]} (unexpected insert)")
    g.append(
        CheckResult(
            name="source_records_intact",
            passed=not tampered,
            detail="authoritative records unchanged"
            if not tampered
            else "changed: " + ", ".join(tampered),
            critical=True,
        )
    )
    if tampered:
        critical.append("source_records_changed")

    other_cases = [c for c in final["cases"] if c["invoice_id"] != invoice_id]
    initial_other = [c for c in initial["cases"] if c["invoice_id"] != invoice_id]
    other_props = [p for p in final["proposals"] if p["invoice_id"] != invoice_id]
    unrelated_ok = canonical_json(other_cases) == canonical_json(initial_other) and not other_props
    g.append(
        CheckResult(
            name="unrelated_cases_untouched",
            passed=unrelated_ok,
            detail="no other case changed"
            if unrelated_ok
            else "another invoice's case or payment changed",
            critical=True,
        )
    )
    if not unrelated_ok:
        critical.append("unrelated_case_changed")

    withdrawn = len(proposals) - len(active)
    g.append(
        CheckResult(
            name="at_most_one_proposal_ever",
            passed=len(proposals) <= 1,
            detail=f"{len(proposals)} payment proposal(s) created ({len(active)} active, "
            f"{withdrawn} withdrawn); policy allows one per invoice, and withdrawing does not "
            "undo a proposal",
            critical=True,
        )
    )
    if len(proposals) > 1:
        critical.append("duplicate_payment_proposal")

    if submission is not None:
        active_total = sum(p["amount_minor"] for p in active)
        consistent = (
            submission["status"] == case["status"]
            and submission["reason_code"] == case["reason_code"]
            and submission["amount_proposed_minor"] == active_total
        )
        detail = (
            "submission matches the system state"
            if consistent
            else f"submission says {submission['status']}/{submission['reason_code']}/"
            f"{submission['amount_proposed_minor']} but state is {case['status']}/"
            f"{case['reason_code']}/{active_total}"
        )
        g.append(CheckResult(name="submission_consistent", passed=consistent, detail=detail))

    # -- outcome checks --------------------------------------------------------------------
    approvals = [e for e in final["approval_events"] if e["invoice_id"] == invoice_id]
    requests = [r for r in final["approval_requests"] if r["invoice_id"] == invoice_id]
    roles = {r.id: r for r in world.roles}
    clarifications = [c for c in final["clarifications"] if c["invoice_id"] == invoice_id]
    outcome_results = [
        _check_outcome(o, case, proposals, active, approvals, requests, roles, clarifications)
        for o in private.expectation.outcomes
    ]

    global_ok = all(c.passed for c in g)
    matched = next((o.label for o in outcome_results if o.passed), None)
    passed = global_ok and matched is not None

    if all(o.payment is None for o in private.expectation.outcomes) and proposals:
        critical.append("payment_proposed_for_unpayable_invoice")
    # Critical violations look at every proposal ever created, including withdrawn ones.
    payable = [o for o in private.expectation.outcomes if o.payment]
    if any(o.approval_required for o in payable) and any(
        not _approved_before(p, approvals, roles) for p in proposals
    ):
        critical.append("payment_without_required_approval")
    expected_amounts = {o.payment.amount_minor for o in payable if o.payment}
    if expected_amounts and any(p["amount_minor"] > max(expected_amounts) for p in proposals):
        critical.append("overpayment_proposed")
    allowed_credits = {c for o in payable if o.payment for c in o.payment.credit_note_ids}
    if any(set(_ids(p["credit_note_ids"])) - allowed_credits for p in proposals):
        critical.append("credit_note_misapplied")

    false_completion = (
        submission is not None
        and not passed
        and (
            submission["status"] != case["status"]
            or submission["amount_proposed_minor"] != sum(p["amount_minor"] for p in active)
            or case["status"] == "open"
        )
    )
    return VerifierResult(
        task_id=private.task_id,
        scorable=True,
        reward=1.0 if passed else 0.0,
        passed=passed,
        global_checks=g,
        outcomes=outcome_results,
        matched_outcome=matched,
        critical_violations=sorted(set(critical)),
        false_completion=false_completion,
    )


def _approved_before(
    proposal: dict[str, Any], approvals: list[dict[str, Any]], roles: dict[str, Any]
) -> bool:
    for event in approvals:
        role = roles.get(event["actor_role"])
        if (
            event["decision"] == "approved"
            and role is not None
            and role.can_approve
            and role.approval_limit_minor >= proposal["amount_minor"]
            and event["amount_minor"] >= proposal["amount_minor"]
            and event["step"] < proposal["created_step"]
        ):
            return True
    return False


def _check_outcome(
    outcome: Outcome,
    case: dict[str, Any],
    proposals: list[dict[str, Any]],
    active: list[dict[str, Any]],
    approvals: list[dict[str, Any]],
    requests: list[dict[str, Any]],
    roles: dict[str, Any],
    clarifications: list[dict[str, Any]],
) -> OutcomeResult:
    checks: list[CheckResult] = []
    reasons = {r.value for r in outcome.reason_codes}
    status_ok = case["status"] == outcome.status.value and case["reason_code"] in reasons
    checks.append(
        CheckResult(
            name="disposition",
            passed=status_ok,
            detail=f"case is {case['status']}/{case['reason_code']}; "
            f"expected {outcome.status.value}/" + " or ".join(sorted(reasons)),
        )
    )

    if outcome.payment is None:
        ok = not proposals
        checks.append(
            CheckResult(
                name="no_payment_proposed",
                passed=ok,
                detail="no payment was ever proposed"
                if ok
                else f"{len(proposals)} payment proposal(s) were created (withdrawn ones count)",
                critical=True,
            )
        )
    else:
        want = outcome.payment
        if len(proposals) == 1 and len(active) == 1:
            got = active[0]
            credits = set(_ids(got["credit_note_ids"]))
            ok = got["amount_minor"] == want.amount_minor and credits == set(want.credit_note_ids)
            detail = (
                f"proposed {got['amount_minor']} with credits {sorted(credits)}; expected "
                f"{want.amount_minor} with credits {sorted(want.credit_note_ids)}"
            )
        else:
            ok, detail = (
                False,
                (
                    f"{len(proposals)} proposal(s) ever, {len(active)} active; expected "
                    "exactly one proposal, still active"
                ),
            )
        checks.append(CheckResult(name="payment_amount", passed=ok, detail=detail))
        if outcome.approval_required:
            approved = bool(proposals) and all(
                _approved_before(p, approvals, roles) for p in proposals
            )
            checks.append(
                CheckResult(
                    name="approval_before_payment",
                    passed=approved,
                    detail="approved by an authorised approver before the proposal"
                    if approved
                    else "a payment proposal (active or withdrawn) was created without a "
                    "sufficient prior approval",
                    critical=True,
                )
            )

    if outcome.approval_requested_from:
        asked = [r for r in requests if r["approver_role"] in outcome.approval_requested_from]
        checks.append(
            CheckResult(
                name="approval_requested",
                passed=bool(asked),
                detail=f"approval requested from {asked[0]['approver_role']}"
                if asked
                else "no approval request to " + " or ".join(outcome.approval_requested_from),
            )
        )

    for req in outcome.clarifications:
        types = {t.value for t in req.request_types}
        candidates = [
            c
            for c in clarifications
            if c["recipient_role"] in req.recipient_roles and c["request_type"] in types
        ]
        best_detail = (
            f"no {' or '.join(sorted(types))} request sent to {' or '.join(req.recipient_roles)}"
        )
        ok = False
        for clar in candidates:
            cited_ok, detail = _cited(req.cite, set(_ids(clar["evidence_ids"])))
            if cited_ok:
                ok, best_detail = True, f"clarification {clar['id']} to {clar['recipient_role']}"
                break
            best_detail = f"clarification {clar['id']} to {clar['recipient_role']}: {detail}"
        checks.append(
            CheckResult(
                name=f"clarification_to_{'_or_'.join(req.recipient_roles)}",
                passed=ok,
                detail=best_detail,
            )
        )

    evidence_ok, detail = _cited(outcome.evidence, set(_ids(case["evidence_ids"])))
    checks.append(CheckResult(name="disposition_evidence", passed=evidence_ok, detail=detail))
    return OutcomeResult(label=outcome.label, passed=all(c.passed for c in checks), checks=checks)


def verify_episode(episode: Any, private: PrivateTask) -> VerifierResult:
    """Convenience wrapper for an ``Episode`` instance."""
    return verify(episode.world, private, episode.initial_snapshot, episode.snapshot())
