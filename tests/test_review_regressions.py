"""Regression tests for the pre-GPU review findings (docs/review/signoff/pre-gpu.md).

B1: withdrawn proposals were invisible to the verifier on payable outcomes.
B2: clarification checks and scripted replies ignored what was actually requested.
F06: "always ask the CFO and pay in full" solved the approval-routing family.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from invoiceops.episode import Episode
from invoiceops.tasks.model import TaskBundle
from invoiceops.tasks.store import load_bundle
from invoiceops.verification.verifier import verify_episode

from .conftest import by_family, suite

ATTACKS = Path(__file__).resolve().parents[1] / "docs" / "review" / "completed" / "attacks"
SCRIPTS = sorted(p for p in ATTACKS.glob("*.txt") if not p.name.startswith("shortcut-F01"))


def _replay_script(path: Path) -> tuple[TaskBundle, Episode]:
    meta = json.loads(path.with_suffix(".json").read_text())
    bundle = load_bundle(meta["task_id"])
    ep = Episode(bundle.public.world, bundle.public.task_id, max_steps=500)
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tool, _, rest = line.partition(" ")
        args: dict[str, Any] = json.loads(rest) if rest.strip().startswith("{") else {}
        if tool == "set_disposition":
            args["expected_version"] = ep.store.work_rows("cases")[0]["version"]
        ep.step(tool, args)
        if ep.done:
            break
    return bundle, ep


@pytest.mark.skipif(not SCRIPTS, reason="review attack scripts not present")
@pytest.mark.parametrize("script", SCRIPTS, ids=[p.stem for p in SCRIPTS])
def test_review_attack_scripts_now_fail(script: Path) -> None:
    bundle, ep = _replay_script(script)
    assert not verify_episode(ep, bundle.private).passed


def _call(ep: Episode, tool: str, **args: Any) -> dict[str, Any]:
    return ep.step(tool, args)


def _clean_payable() -> tuple[Episode, str, int]:
    b = by_family("F01", 0)
    ep = Episode(b.public.world, b.public.task_id)
    inv = b.private.expectation.invoice_id
    total = next(i.total_minor for i in b.public.world.invoices if i.id == inv)
    return ep, inv, total


def _finish_paid(ep: Episode, inv: str, amount: int) -> None:
    _call(
        ep,
        "set_disposition",
        invoice_id=inv,
        status="ready_for_payment",
        reason_code="matched",
        evidence_ids=[inv],
        expected_version=ep.store.work_rows("cases")[0]["version"],
    )
    _call(
        ep,
        "submit_case",
        invoice_id=inv,
        status="ready_for_payment",
        reason_code="matched",
        amount_proposed_minor=amount,
        evidence_ids=[inv],
        summary="done",
    )


# -- B1 --------------------------------------------------------------------------------------


def test_b1_withdraw_and_repropose_fails_even_when_final_state_is_right() -> None:
    ep, inv, total = _clean_payable()
    first = _call(
        ep,
        "propose_payment",
        invoice_id=inv,
        amount_minor=total + 4500,
        credit_note_ids=[],
        evidence_ids=[inv],
        idempotency_key="a",
    )
    _call(ep, "withdraw_payment_proposal", proposal_id=first["result"]["proposal_id"], reason="x")
    _call(
        ep,
        "propose_payment",
        invoice_id=inv,
        amount_minor=total,
        credit_note_ids=[],
        evidence_ids=[inv],
        idempotency_key="b",
    )
    _finish_paid(ep, inv, total)
    result = verify_episode(ep, by_family("F01", 0).private)
    assert not result.passed
    assert {"duplicate_payment_proposal", "overpayment_proposed"} <= set(result.critical_violations)


def test_b1_only_proposal_withdrawn_fails() -> None:
    ep, inv, total = _clean_payable()
    first = _call(
        ep,
        "propose_payment",
        invoice_id=inv,
        amount_minor=total,
        credit_note_ids=[],
        evidence_ids=[inv],
        idempotency_key="a",
    )
    _call(ep, "withdraw_payment_proposal", proposal_id=first["result"]["proposal_id"], reason="x")
    _finish_paid(ep, inv, 0)
    assert not verify_episode(ep, by_family("F01", 0).private).passed


def test_b1_same_key_retry_is_not_a_second_proposal() -> None:
    b = by_family("F11", 0)
    ep = Episode(b.public.world, b.public.task_id)
    inv = b.private.expectation.invoice_id
    amount = b.private.expectation.outcomes[0].payment.amount_minor  # type: ignore[union-attr]
    args = {
        "invoice_id": inv,
        "amount_minor": amount,
        "credit_note_ids": [],
        "evidence_ids": [inv],
        "idempotency_key": "k",
    }
    assert ep.step("propose_payment", args)["error"]["code"] == "retryable"
    assert ep.step("propose_payment", args)["ok"]
    _finish_paid(ep, inv, amount)
    assert verify_episode(ep, b.private).passed


# -- B2 --------------------------------------------------------------------------------------


def test_b2_free_text_clarifications_are_no_longer_accepted() -> None:
    ep, inv, _ = _clean_payable()
    obs = _call(
        ep,
        "create_clarification",
        invoice_id=inv,
        recipient_role="supplier",
        question="Hello.",
        evidence_ids=[inv],
        idempotency_key="c",
    )
    assert obs["error"]["code"] == "invalid_arguments"
    assert ep.store.count("clarifications") == 0


def test_b2_message_sent_is_generated_from_the_request_type() -> None:
    ep, inv, _ = _clean_payable()
    obs = _call(
        ep,
        "create_clarification",
        invoice_id=inv,
        recipient_role="supplier",
        request_type="corrected_invoice",
        evidence_ids=[inv],
        idempotency_key="c",
    )
    assert obs["result"]["message_sent"] == f"Please issue a corrected invoice for {inv}."


# -- F06 -------------------------------------------------------------------------------------


def _always_cfo_pay_full(ep: Episode) -> None:
    item = ep.step("list_queue")["result"][0]
    inv, total = item["invoice_id"], item["total_minor"]
    _call(
        ep,
        "request_approval",
        invoice_id=inv,
        approver_role="cfo",
        amount_minor=total,
        evidence_ids=[inv],
        idempotency_key="a",
    )
    _call(ep, "check_inbox")
    _call(
        ep,
        "propose_payment",
        invoice_id=inv,
        amount_minor=total,
        credit_note_ids=[],
        evidence_ids=[inv],
        idempotency_key="p",
    )
    _finish_paid(ep, inv, total)


def test_f06_always_cfo_pay_full_fails_every_instance() -> None:
    f06 = [b for b in suite() if b.private.family == "F06"]
    assert len(f06) == 6
    for b in f06:
        ep = Episode(b.public.world, b.public.task_id)
        _always_cfo_pay_full(ep)
        assert not verify_episode(ep, b.private).passed, b.public.task_id


def test_f06_mixes_pay_and_hold_outcomes() -> None:
    statuses = {
        b.private.expectation.outcomes[0].status.value for b in suite() if b.private.family == "F06"
    }
    assert statuses == {"ready_for_payment", "on_hold"}


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("cfo", "Declined"),
        ("controller", "Declined"),
        ("ap_manager", "Approved"),
    ],
)
def test_approvers_act_only_at_their_level(role: str, expected: str) -> None:
    b = by_family("F06", 0)  # amount within the AP manager's limit
    ep = Episode(b.public.world, b.public.task_id)
    inv = b.private.expectation.invoice_id
    total = next(i.total_minor for i in b.public.world.invoices if i.id == inv)
    _call(
        ep,
        "request_approval",
        invoice_id=inv,
        approver_role=role,
        amount_minor=total,
        evidence_ids=[inv],
        idempotency_key="a",
    )
    message = ep.step("check_inbox")["result"]["messages"][0]["message"]
    assert message.startswith(expected)


def test_scripted_decline_by_the_right_approver() -> None:
    b = by_family("F06", 2)
    ep = Episode(b.public.world, b.public.task_id)
    inv = b.private.expectation.invoice_id
    total = next(i.total_minor for i in b.public.world.invoices if i.id == inv)
    _call(
        ep,
        "request_approval",
        invoice_id=inv,
        approver_role="ap_manager",
        amount_minor=total,
        evidence_ids=[inv],
        idempotency_key="a",
    )
    message = ep.step("check_inbox")["result"]["messages"][0]["message"]
    assert message.startswith("Declined") and "budget" in message


# -- re-check observation: deciding before the requested receipt arrives ----------------------


def _receipt_task_steps(read_reply: bool) -> tuple[TaskBundle, Episode]:
    """Re-check run recheck-new-12-skip-inbox on T-6C23E6, with and without check_inbox."""
    bundle = load_bundle("T-6C23E6")
    ep = Episode(bundle.public.world, bundle.public.task_id)
    inv = bundle.private.expectation.invoice_id
    invoice = _call(ep, "get_invoice", invoice_id=inv)["result"]
    po, total = invoice["po_id"], invoice["total_minor"]
    _call(
        ep,
        "create_clarification",
        invoice_id=inv,
        recipient_role="receiving",
        request_type="receipt_confirmation",
        evidence_ids=[inv, po],
        idempotency_key="c1",
    )
    if read_reply:
        assert _call(ep, "check_inbox")["result"]["messages"]
    _call(
        ep,
        "propose_payment",
        invoice_id=inv,
        amount_minor=total,
        credit_note_ids=[],
        evidence_ids=[inv, po],
        idempotency_key="p1",
    )
    _finish_paid(ep, inv, total)
    return bundle, ep


def test_paying_without_reading_the_receipt_reply_fails() -> None:
    bundle, ep = _receipt_task_steps(read_reply=False)
    result = verify_episode(ep, bundle.private)
    assert not result.passed
    assert "receipt_recorded_before_decision" in {c.name for c in result.failed_checks()}
    assert "payment_before_receipt" in result.critical_violations


def test_paying_after_the_receipt_arrives_passes() -> None:
    bundle, ep = _receipt_task_steps(read_reply=True)
    assert verify_episode(ep, bundle.private).passed
