from __future__ import annotations

from typing import Any

from invoiceops.agents.oracle import solve
from invoiceops.episode import Episode

from .conftest import by_family


def _ep(family: str = "F01", variant: int = 0, **kw: Any) -> tuple[Episode, str]:
    b = by_family(family, variant)
    return Episode(b.public.world, b.public.task_id, **kw), b.private.expectation.invoice_id


def code(obs: dict[str, Any]) -> str:
    return "ok" if obs["ok"] else str(obs["error"]["code"])


def test_unknown_tool_and_bad_arguments() -> None:
    ep, inv = _ep()
    assert code(ep.step("execute_sql", {"q": "drop"})) == "unknown_tool"
    assert code(ep.step("get_invoice", {})) == "invalid_arguments"
    assert code(ep.step("get_invoice", {"invoice_id": inv, "extra": 1})) == "invalid_arguments"
    assert code(ep.step("get_invoice", {"invoice_id": "INV-0"})) == "not_found"


def test_only_queued_invoices_can_be_changed() -> None:
    ep, inv = _ep()
    other = next(i.id for i in ep.world.invoices if i.id != inv)
    obs = ep.step(
        "set_disposition",
        {
            "invoice_id": other,
            "status": "on_hold",
            "reason_code": "price_variance",
            "evidence_ids": [other],
            "expected_version": 1,
        },
    )
    assert code(obs) == "forbidden"


def test_reason_must_fit_status_and_evidence_must_exist() -> None:
    ep, inv = _ep()
    base = {"invoice_id": inv, "expected_version": 1}
    bad_reason = {**base, "status": "on_hold", "reason_code": "matched", "evidence_ids": [inv]}
    assert code(ep.step("set_disposition", bad_reason)) == "invalid_arguments"
    missing = {
        **base,
        "status": "on_hold",
        "reason_code": "price_variance",
        "evidence_ids": ["X-1"],
    }
    assert code(ep.step("set_disposition", missing)) == "not_found"


def test_stale_version_leaves_state_unchanged() -> None:
    ep, inv = _ep()
    args = {
        "invoice_id": inv,
        "status": "on_hold",
        "reason_code": "price_variance",
        "evidence_ids": [inv],
        "expected_version": 1,
    }
    assert code(ep.step("set_disposition", args)) == "ok"
    before = ep.store.state_hash()
    assert code(ep.step("set_disposition", args)) == "stale_version"
    assert ep.store.state_hash() == before


def test_idempotency_replay_and_conflict() -> None:
    ep, inv = _ep()
    args = {
        "invoice_id": inv,
        "amount_minor": 100,
        "credit_note_ids": [],
        "evidence_ids": [inv],
        "idempotency_key": "k1",
    }
    first = ep.step("propose_payment", args)
    again = ep.step("propose_payment", args)
    assert (
        again["result"]["replayed"]
        and again["result"]["proposal_id"] == first["result"]["proposal_id"]
    )
    assert ep.store.count("proposals") == 1
    assert code(ep.step("propose_payment", {**args, "amount_minor": 101})) == "invalid_arguments"


def test_lost_response_fault_then_retry_creates_one_proposal() -> None:
    ep, inv = _ep("F11", 0)
    args = {
        "invoice_id": inv,
        "amount_minor": 100,
        "credit_note_ids": [],
        "evidence_ids": [inv],
        "idempotency_key": "k1",
    }
    assert code(ep.step("propose_payment", args)) == "retryable"
    assert ep.store.count("proposals") == 1  # the write happened
    assert code(ep.step("propose_payment", args)) == "ok"
    assert ep.store.count("proposals") == 1


def test_agent_cannot_approve_and_non_approvers_cannot_be_asked() -> None:
    ep, inv = _ep()
    args = {
        "invoice_id": inv,
        "approver_role": "procurement",
        "amount_minor": 100,
        "evidence_ids": [inv],
        "idempotency_key": "a1",
    }
    assert code(ep.step("request_approval", args)) == "invalid_arguments"
    assert (
        code(ep.step("request_approval", {**args, "approver_role": "ap_assistant"}))
        == "invalid_arguments"
    )
    assert ep.store.count("approval_events") == 0


def test_approval_decision_only_after_request_and_by_limit() -> None:
    ep, inv = _ep("F06", 1)  # amount above the AP manager's limit
    assert ep.step("check_inbox")["result"]["messages"] == []
    total = next(i.total_minor for i in ep.world.invoices if i.id == inv)
    req = {"invoice_id": inv, "amount_minor": total, "evidence_ids": [inv]}
    ep.step("request_approval", {**req, "approver_role": "ap_manager", "idempotency_key": "a"})
    msgs = ep.step("check_inbox")["result"]["messages"]
    assert msgs[0]["message"].startswith("Declined")
    ep.step("request_approval", {**req, "approver_role": "controller", "idempotency_key": "b"})
    msgs = ep.step("check_inbox")["result"]["messages"]
    assert msgs[0]["message"].startswith("Approved")
    assert ep.step("check_inbox")["result"]["messages"] == []
    assert ep.store.count("approval_events") == 2


def test_scripted_event_needs_its_trigger_and_fires_once() -> None:
    ep, inv = _ep("F08", 0)
    po = next(i.po_id for i in ep.world.invoices if i.id == inv)
    assert ep.step("check_inbox")["result"]["messages"] == []
    assert ep.step("get_receipts", {"po_id": po})["result"]["receipts"] == []
    ep.step(
        "create_clarification",
        {
            "invoice_id": inv,
            "recipient_role": "supplier",
            "question": "?",
            "evidence_ids": [inv],
            "idempotency_key": "c",
        },
    )
    assert ep.step("check_inbox")["result"]["messages"] == []  # wrong recipient
    ep.step(
        "create_clarification",
        {
            "invoice_id": inv,
            "recipient_role": "receiving",
            "question": "?",
            "evidence_ids": [inv],
            "idempotency_key": "d",
        },
    )
    assert len(ep.step("check_inbox")["result"]["messages"]) == 1
    assert ep.step("check_inbox")["result"]["messages"] == []
    assert len(ep.step("get_receipts", {"po_id": po})["result"]["receipts"]) == 1


def test_step_limit_and_finished_episode() -> None:
    ep, _ = _ep(max_steps=3)
    for _ in range(3):
        ep.step("list_queue")
    assert ep.done and ep.end_reason == "step_limit_reached"
    assert code(ep.step("list_queue")) == "episode_finished"


def test_search_pagination_is_deterministic() -> None:
    ep, _ = _ep()
    page1 = ep.step("search_records", {"collection": "invoices"})["result"]
    ids = [r["id"] for r in page1["results"]]
    assert ids == sorted(ids)
    if page1["next_cursor"]:
        page2 = ep.step(
            "search_records", {"collection": "invoices", "cursor": page1["next_cursor"]}
        )
        assert not set(ids) & {r["id"] for r in page2["result"]["results"]}


def test_action_log_replays_to_identical_state() -> None:
    b = by_family("F08", 1)
    ep = Episode(b.public.world, b.public.task_id)
    solve(ep)
    replayed = Episode(b.public.world, b.public.task_id)
    for event in ep.log:
        replayed.step(event.tool, event.arguments)
    assert [e.state_after for e in replayed.log] == [e.state_after for e in ep.log]
