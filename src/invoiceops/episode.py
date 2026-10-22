"""Episode lifecycle: one agent working one task from reset to submission.

Every agent (model, human, or script) acts only through ``Episode.step(tool, arguments)``.
Each call is validated, applied in a transaction, logged with the state hash before and after,
and answered with a JSON-serialisable observation:

    {"ok": true, "result": ...}
    {"ok": false, "error": {"code": "...", "message": "..."}}

Error codes: unknown_tool, invalid_arguments, not_found, forbidden, stale_version,
retryable, step_limit_reached, episode_finished.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from invoiceops.domain.records import ALLOWED_REASONS, CaseStatus, ReasonCode
from invoiceops.domain.world import AGENT_ROLE_ID, World
from invoiceops.state.store import Store, canonical_json
from invoiceops.tools import spec

PAGE_SIZE = 10
DEFAULT_MAX_STEPS = 50


class ToolError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ActionEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    step: int
    tool: str
    arguments: dict[str, Any]
    result_code: str
    observation: dict[str, Any]
    state_before: str
    state_after: str


class Episode:
    def __init__(
        self,
        world: World,
        task_id: str = "",
        max_steps: int = DEFAULT_MAX_STEPS,
        episode_id: str | None = None,
    ) -> None:
        self.world = world
        self.task_id = task_id
        self.max_steps = max_steps
        self.episode_id = episode_id or uuid.uuid4().hex
        self.store = Store()
        self.store.load_world(world)
        self.step_count = 0
        self.done = False
        self.end_reason: str | None = None
        self.log: list[ActionEvent] = []
        self._inbox_seen = 0
        self._propose_calls = 0
        self._id_counter = 0
        self._roles = {r.id: r for r in world.roles}
        with self.store.transaction() as conn:
            for invoice_id in world.queue:
                conn.execute(
                    "INSERT INTO cases VALUES (?, ?, NULL, '[]', '', 1, 0)",
                    (invoice_id, CaseStatus.OPEN.value),
                )
        self.initial_snapshot = self.store.snapshot()

    # -- public API --------------------------------------------------------------------------

    def step(self, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = dict(arguments or {})
        before = self.store.state_hash()
        observation: dict[str, Any]
        if self.done:
            observation = _error("episode_finished", f"The episode has ended ({self.end_reason}).")
            self._record(tool, arguments, observation, before, before)
            return observation
        self.step_count += 1
        try:
            tool_spec = spec.TOOLS_BY_NAME.get(tool)
            if tool_spec is None:
                raise ToolError("unknown_tool", f"No tool named {tool!r}.")
            try:
                args = tool_spec.args.model_validate(arguments)
            except ValidationError as exc:
                raise ToolError("invalid_arguments", _validation_message(exc)) from exc
            handler = getattr(self, f"_tool_{tool}")
            result = handler(args)
            observation = {"ok": True, "result": result}
        except ToolError as exc:
            observation = _error(exc.code, exc.message)
        if not self.done and self.step_count >= self.max_steps:
            self.done = True
            self.end_reason = "step_limit_reached"
            observation["notice"] = "Step limit reached; the episode has ended."
        after = self.store.state_hash()
        self._record(tool, arguments, observation, before, after)
        return observation

    def snapshot(self) -> dict[str, list[dict[str, Any]]]:
        return self.store.snapshot()

    def close(self) -> None:
        self.store.close()

    # -- helpers -----------------------------------------------------------------------------

    def _record(
        self,
        tool: str,
        arguments: dict[str, Any],
        observation: dict[str, Any],
        before: str,
        after: str,
    ) -> None:
        code = "ok" if observation.get("ok") else str(observation["error"]["code"])
        self.log.append(
            ActionEvent(
                step=self.step_count,
                tool=tool,
                arguments=json.loads(canonical_json(arguments)) if _jsonable(arguments) else {},
                result_code=code,
                observation=observation,
                state_before=before,
                state_after=after,
            )
        )

    def _new_id(self, prefix: str) -> str:
        self._id_counter += 1
        return f"{prefix}-{self._id_counter:03d}"

    def _require_queued(self, invoice_id: str) -> dict[str, Any]:
        rows = self.store.work_rows("cases", "WHERE invoice_id = ?", (invoice_id,))
        if rows:
            return rows[0]
        if self.store.source_get("invoices", invoice_id) is not None:
            raise ToolError("forbidden", f"Invoice {invoice_id} is not in your queue.")
        raise ToolError("not_found", f"No invoice {invoice_id}.")

    def _require_records(self, ids: list[str]) -> list[str]:
        missing = [i for i in ids if not self.store.record_exists(i)]
        if missing:
            raise ToolError("not_found", "Unknown record ids: " + ", ".join(missing))
        return list(dict.fromkeys(ids))

    def _require_role(self, role_id: str) -> None:
        if role_id not in self._roles or role_id == AGENT_ROLE_ID:
            names = ", ".join(r for r in self._roles if r != AGENT_ROLE_ID)
            raise ToolError("invalid_arguments", f"Unknown role {role_id!r}. Roles: {names}.")

    def _idempotent(self, table: str, key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Return the existing row for ``key`` if it matches ``payload``; raise if it conflicts."""
        rows = self.store.work_rows(table, "WHERE idempotency_key = ?", (key,))
        if not rows:
            return None
        row = rows[0]
        for field, value in payload.items():
            stored = row[field]
            if isinstance(value, list):
                stored = json.loads(stored)
            if stored != value:
                raise ToolError(
                    "invalid_arguments",
                    f"Idempotency key {key!r} was already used with different arguments.",
                )
        return row

    # -- read tools --------------------------------------------------------------------------

    def _tool_list_queue(self, args: spec.NoArgs) -> list[dict[str, Any]]:
        out = []
        for case in self.store.work_rows("cases"):
            inv = self.store.source_get("invoices", case["invoice_id"])
            assert inv is not None
            vendor = self.store.source_get("vendors", inv["vendor_id"])
            out.append(
                {
                    "invoice_id": inv["id"],
                    "vendor_id": inv["vendor_id"],
                    "vendor_name": vendor["legal_name"] if vendor else None,
                    "total_minor": inv["total_minor"],
                    "received_on": inv["received_on"],
                    "case_status": case["status"],
                    "case_version": case["version"],
                }
            )
        return out

    def _tool_search_records(self, args: spec.SearchArgs) -> dict[str, Any]:
        rows = self.store.source_rows(args.collection)
        if args.collection == "purchase_orders":
            latest: dict[str, dict[str, Any]] = {}
            for row in rows:
                latest[row["id"]] = row
            rows = list(latest.values())
        summaries = [_summary(args.collection, row) for row in rows]
        needle = args.query.strip().lower()
        if needle:
            summaries = [s for s in summaries if needle in canonical_json(s).lower()]
        summaries.sort(key=lambda s: str(s["id"]))
        try:
            start = int(args.cursor) if args.cursor else 0
        except ValueError as exc:
            raise ToolError("invalid_arguments", "cursor must come from next_cursor") from exc
        page = summaries[start : start + PAGE_SIZE]
        nxt = start + PAGE_SIZE
        return {
            "collection": args.collection,
            "total": len(summaries),
            "results": page,
            "next_cursor": str(nxt) if nxt < len(summaries) else None,
        }

    def _tool_get_invoice(self, args: spec.InvoiceIdArgs) -> dict[str, Any]:
        inv = self.store.source_get("invoices", args.invoice_id)
        if inv is None:
            raise ToolError("not_found", f"No invoice {args.invoice_id}.")
        rows = self.store.work_rows("cases", "WHERE invoice_id = ?", (args.invoice_id,))
        if rows:
            case = rows[0]
            inv["ap_case"] = {
                "status": case["status"],
                "reason_code": case["reason_code"],
                "version": case["version"],
                "evidence_ids": json.loads(case["evidence_ids"]),
            }
        return inv

    def _tool_get_purchase_order(self, args: spec.PurchaseOrderArgs) -> dict[str, Any]:
        revisions = self.store.source_revisions("purchase_orders", args.po_id)
        if not revisions:
            raise ToolError("not_found", f"No purchase order {args.po_id}.")
        if args.revision is None:
            chosen = revisions[-1]
        else:
            matches = [r for r in revisions if r["revision"] == args.revision]
            if not matches:
                raise ToolError("not_found", f"{args.po_id} has no revision {args.revision}.")
            chosen = matches[0]
        result = dict(chosen)
        result["revisions"] = [
            {"revision": r["revision"], "approved_on": r["approved_on"]} for r in revisions
        ]
        return result

    def _tool_get_receipts(self, args: spec.PoIdArgs) -> dict[str, Any]:
        if not self.store.source_revisions("purchase_orders", args.po_id):
            raise ToolError("not_found", f"No purchase order {args.po_id}.")
        receipts = [r for r in self.store.source_rows("receipts") if r["po_id"] == args.po_id]
        return {"po_id": args.po_id, "receipts": receipts}

    def _tool_get_vendor(self, args: spec.VendorIdArgs) -> dict[str, Any]:
        vendor = self.store.source_get("vendors", args.vendor_id)
        if vendor is None:
            raise ToolError("not_found", f"No supplier {args.vendor_id}.")
        return vendor

    def _tool_get_document(self, args: spec.DocumentIdArgs) -> dict[str, Any]:
        doc = self.store.source_get("documents", args.document_id)
        if doc is None:
            raise ToolError("not_found", f"No document {args.document_id}.")
        return doc

    def _tool_get_history(self, args: spec.HistoryArgs) -> dict[str, Any]:
        if self.store.source_get("vendors", args.vendor_id) is None:
            raise ToolError("not_found", f"No supplier {args.vendor_id}.")
        payments = [
            p for p in self.store.source_rows("payments") if p["vendor_id"] == args.vendor_id
        ]
        paid = {p["invoice_id"]: p for p in payments}
        queued = {c["invoice_id"] for c in self.store.work_rows("cases")}
        invoices = []
        for inv in self.store.source_rows("invoices"):
            if inv["vendor_id"] != args.vendor_id:
                continue
            if args.po_id and inv["po_id"] != args.po_id:
                continue
            if inv["id"] in paid:
                status = paid[inv["id"]]["status"]
            elif inv["id"] in queued:
                status = "in_your_queue"
            else:
                status = "unpaid"
            invoices.append(
                {
                    "invoice_id": inv["id"],
                    "vendor_invoice_number": inv["vendor_invoice_number"],
                    "po_id": inv["po_id"],
                    "invoice_date": inv["invoice_date"],
                    "total_minor": inv["total_minor"],
                    "lines": [
                        {"po_line_no": ln["po_line_no"], "quantity": ln["quantity"]}
                        for ln in inv["lines"]
                    ],
                    "payment_status": status,
                }
            )
        invoice_ids = {i["invoice_id"] for i in invoices}
        if args.po_id:
            payments = [p for p in payments if p["invoice_id"] in invoice_ids]
        credits = [
            c
            for c in self.store.source_rows("credit_notes")
            if c["vendor_id"] == args.vendor_id
            and (not args.po_id or c["invoice_id"] in invoice_ids)
        ]
        return {"invoices": invoices, "payments": payments, "credit_notes": credits}

    # -- write tools -------------------------------------------------------------------------

    def _tool_set_disposition(self, args: spec.DispositionArgs) -> dict[str, Any]:
        case = self._require_queued(args.invoice_id)
        status = CaseStatus(args.status)
        reason = ReasonCode(args.reason_code)
        if reason not in ALLOWED_REASONS[status]:
            allowed = ", ".join(sorted(r.value for r in ALLOWED_REASONS[status]))
            raise ToolError(
                "invalid_arguments",
                f"Reason {reason.value} is not allowed for {status.value}: {allowed}.",
            )
        evidence = self._require_records(args.evidence_ids)
        if args.expected_version != case["version"]:
            raise ToolError(
                "stale_version",
                f"Case version is {case['version']}, not {args.expected_version}. "
                "Re-read the case and retry.",
            )
        version = case["version"] + 1
        with self.store.transaction() as conn:
            conn.execute(
                "UPDATE cases SET status=?, reason_code=?, evidence_ids=?, note=?, version=?, "
                "updated_step=? WHERE invoice_id=?",
                (
                    status.value,
                    reason.value,
                    json.dumps(evidence),
                    args.note,
                    version,
                    self.step_count,
                    args.invoice_id,
                ),
            )
            conn.execute(
                "INSERT INTO case_history (invoice_id, status, reason_code, evidence_ids, note, "
                "version, step) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    args.invoice_id,
                    status.value,
                    reason.value,
                    json.dumps(evidence),
                    args.note,
                    version,
                    self.step_count,
                ),
            )
        return {
            "invoice_id": args.invoice_id,
            "status": status.value,
            "reason_code": reason.value,
            "version": version,
        }

    def _tool_create_clarification(self, args: spec.ClarificationArgs) -> dict[str, Any]:
        self._require_queued(args.invoice_id)
        self._require_role(args.recipient_role)
        evidence = self._require_records(args.evidence_ids)
        payload = {
            "invoice_id": args.invoice_id,
            "recipient_role": args.recipient_role,
            "question": args.question,
            "evidence_ids": evidence,
        }
        existing = self._idempotent("clarifications", args.idempotency_key, payload)
        if existing:
            return {"clarification_id": existing["id"], "replayed": True}
        clar_id = self._new_id("CLR")
        with self.store.transaction() as conn:
            conn.execute(
                "INSERT INTO clarifications VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    clar_id,
                    args.invoice_id,
                    args.recipient_role,
                    args.question,
                    json.dumps(evidence),
                    args.idempotency_key,
                    self.step_count,
                ),
            )
        return {"clarification_id": clar_id, "replayed": False}

    def _tool_request_approval(self, args: spec.ApprovalArgs) -> dict[str, Any]:
        self._require_queued(args.invoice_id)
        self._require_role(args.approver_role)
        if not self._roles[args.approver_role].can_approve:
            raise ToolError(
                "invalid_arguments", f"Role {args.approver_role} cannot approve payments."
            )
        evidence = self._require_records(args.evidence_ids)
        payload = {
            "invoice_id": args.invoice_id,
            "approver_role": args.approver_role,
            "amount_minor": args.amount_minor,
            "evidence_ids": evidence,
        }
        existing = self._idempotent("approval_requests", args.idempotency_key, payload)
        if existing:
            return {"approval_request_id": existing["id"], "replayed": True}
        req_id = self._new_id("APR")
        with self.store.transaction() as conn:
            conn.execute(
                "INSERT INTO approval_requests VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')",
                (
                    req_id,
                    args.invoice_id,
                    args.approver_role,
                    args.amount_minor,
                    json.dumps(evidence),
                    args.idempotency_key,
                    self.step_count,
                ),
            )
        return {
            "approval_request_id": req_id,
            "replayed": False,
            "note": "The decision will arrive through check_inbox.",
        }

    def _tool_check_inbox(self, args: spec.NoArgs) -> dict[str, Any]:
        from invoiceops.events import release_due_events

        with self.store.transaction() as conn:
            release_due_events(self.store, conn, self.world, self.step_count, self._new_id)
        messages = self.store.work_rows("inbox", "WHERE seq > ?", (self._inbox_seen,))
        if messages:
            self._inbox_seen = messages[-1]["seq"]
        return {
            "messages": [
                {
                    "from_role": m["from_role"],
                    "kind": m["kind"],
                    "message": m["message"],
                    "record_ids": json.loads(m["record_ids"]),
                }
                for m in messages
            ]
        }

    def _tool_propose_payment(self, args: spec.ProposePaymentArgs) -> dict[str, Any]:
        self._require_queued(args.invoice_id)
        inv = self.store.source_get("invoices", args.invoice_id)
        assert inv is not None
        credits = self._require_records(args.credit_note_ids)
        for credit_id in credits:
            credit = self.store.source_get("credit_notes", credit_id)
            if credit is None:
                raise ToolError("invalid_arguments", f"{credit_id} is not a credit note.")
            if credit["vendor_id"] != inv["vendor_id"]:
                raise ToolError(
                    "invalid_arguments", f"Credit note {credit_id} belongs to another supplier."
                )
        evidence = self._require_records(args.evidence_ids)
        payload = {
            "invoice_id": args.invoice_id,
            "amount_minor": args.amount_minor,
            "credit_note_ids": credits,
            "evidence_ids": evidence,
        }
        existing = self._idempotent("proposals", args.idempotency_key, payload)
        if existing:
            return {"proposal_id": existing["id"], "status": existing["status"], "replayed": True}
        self._propose_calls += 1
        prop_id = self._new_id("PRP")
        with self.store.transaction() as conn:
            conn.execute(
                "INSERT INTO proposals VALUES (?, ?, ?, ?, ?, ?, 'active', ?, NULL, NULL)",
                (
                    prop_id,
                    args.invoice_id,
                    args.amount_minor,
                    json.dumps(credits),
                    json.dumps(evidence),
                    args.idempotency_key,
                    self.step_count,
                ),
            )
        for fault in self.world.faults:
            if fault.tool == "propose_payment" and fault.on_call == self._propose_calls:
                raise ToolError(
                    "retryable",
                    "Timed out waiting for the payment service. The request may or may not have "
                    "been recorded. Retry with the same idempotency key.",
                )
        return {"proposal_id": prop_id, "status": "active", "replayed": False}

    def _tool_withdraw_payment_proposal(self, args: spec.WithdrawArgs) -> dict[str, Any]:
        rows = self.store.work_rows("proposals", "WHERE id = ?", (args.proposal_id,))
        if not rows:
            raise ToolError("not_found", f"No payment proposal {args.proposal_id}.")
        if rows[0]["status"] != "active":
            raise ToolError("invalid_arguments", f"Proposal {args.proposal_id} is not active.")
        with self.store.transaction() as conn:
            conn.execute(
                "UPDATE proposals SET status='withdrawn', withdrawn_step=?, withdraw_reason=? "
                "WHERE id=?",
                (self.step_count, args.reason, args.proposal_id),
            )
        return {"proposal_id": args.proposal_id, "status": "withdrawn"}

    def _tool_submit_case(self, args: spec.SubmitArgs) -> dict[str, Any]:
        self._require_queued(args.invoice_id)
        evidence = self._require_records(args.evidence_ids)
        with self.store.transaction() as conn:
            conn.execute(
                "INSERT INTO submission VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    args.invoice_id,
                    args.status,
                    args.reason_code,
                    args.amount_proposed_minor,
                    json.dumps(evidence),
                    args.summary,
                    self.step_count,
                ),
            )
        self.done = True
        self.end_reason = "submitted"
        return {"submitted": True, "note": "The episode has ended."}


def _error(code: str, message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}}


def _validation_message(exc: ValidationError) -> str:
    parts = []
    for err in exc.errors()[:5]:
        loc = ".".join(str(p) for p in err["loc"]) or "arguments"
        parts.append(f"{loc}: {err['msg']}")
    return "; ".join(parts)


def _jsonable(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True


def _summary(collection: str, row: dict[str, Any]) -> dict[str, Any]:
    if collection == "invoices":
        return {
            "id": row["id"],
            "vendor_id": row["vendor_id"],
            "vendor_invoice_number": row["vendor_invoice_number"],
            "po_id": row["po_id"],
            "invoice_date": row["invoice_date"],
            "total_minor": row["total_minor"],
        }
    if collection == "purchase_orders":
        return {
            "id": row["id"],
            "revision": row["revision"],
            "vendor_id": row["vendor_id"],
            "department": row["department"],
            "approved_on": row["approved_on"],
        }
    if collection == "receipts":
        return {"id": row["id"], "po_id": row["po_id"], "received_on": row["received_on"]}
    if collection == "vendors":
        return {"id": row["id"], "legal_name": row["legal_name"], "verified": row["verified"]}
    if collection == "documents":
        return {
            "id": row["id"],
            "kind": row["kind"],
            "title": row["title"],
            "received_on": row["received_on"],
        }
    if collection == "credit_notes":
        return {
            "id": row["id"],
            "vendor_id": row["vendor_id"],
            "invoice_id": row["invoice_id"],
            "amount_minor": row["amount_minor"],
            "status": row["status"],
        }
    return {
        "id": row["id"],
        "invoice_id": row["invoice_id"],
        "vendor_id": row["vendor_id"],
        "amount_minor": row["amount_minor"],
        "status": row["status"],
        "paid_on": row["paid_on"],
    }
