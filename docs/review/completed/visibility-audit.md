# Visibility Audit — Manual Assessment

Reviewer: Shahid Ahmed (independent solver) · Date: 2026-10-23
CLI artifact: `runs/review-support/invoiceops-visibility-T-8F0E1E.txt`
Supplemented by interactive session `manual-vis-01` (task T-D30567, F02
multi-revision PO world) plus earlier adversarial sessions.

## What the agent can see (verified through `invoiceops play`)

| Surface | Verified | Notes |
|---|---|---|
| Prompt | yes | Company, business date, queued invoice id, vendor, total. No family/split/expected-outcome hints. |
| `list_queue` | yes | Queue rows only: invoice id, vendor, total, case status/version. |
| `get_invoice` | yes | Full invoice + `ap_case` for queued invoices. |
| `get_purchase_order` | yes — **supplemented** | Default returns latest revision (rev 2) plus the full revisions list; `revision` arg returns each revision's lines/price. Verified on PO-5674 (rev1 price 4,480 vs rev2 4,853). |
| `get_receipts` | yes — **supplemented** | Returns full receipt records **with line quantities** (the CLI audit only printed summaries without `lines`; live output shows `lines:[{po_line_no, quantity}]`). |
| `get_history` | yes — **supplemented** | Vendor invoices (with quantities billed + payment_status: paid/unpaid/in_your_queue), payments, and credit notes — including `applied_to`/status fields needed for F05/F11 decisions. |
| `search_records` | yes | Restricted to the 7 public collections (`invoices`, `purchase_orders`, `receipts`, `vendors`, `documents`, `credit_notes`, `payments`). No path to `events`, `faults`, `roles`, or work tables. |
| `get_document` / `get_vendor` | yes | Policy bodies and vendor master records (verified flag, remit, tax id, contact email). |
| `check_inbox` | yes | Releases reply/approval events. Verified: receiving reply posts GRN-176 content to the agent after a clarification. |

## Private-data checks

- **Family / split / expected outcome / checks**: not present in any tool output reviewed; they live only in `private.json`/verifier.
- **World events and faults**: exist in the world record but are reachable only through their intended surface (inbox messages, tool errors). `manual-vis-01` found no tool that enumerates them; `search_records` rejects non-public collections.
- **Roles/approver limits**: role names surface through the `create_clarification` validation error (intended — the agent must know valid recipients); approver limits are in the written policy. No private data.
- **Private-field footer in the CLI audit** ("Private fields that must not appear above"): reviewer-generated comparison output, NOT agent-visible — confirmed it is appended by the audit harness, not returned by any tool.
- **state hashes in the log**: internal; not returned to the agent in tool results.

## Permissions / write surface

- Agent can only mutate: case disposition (own queue), clarifications, approval requests, payment proposals (propose/withdraw), submission.
- No tool can edit invoices, POs, receipts, vendors, payments, or credit notes (source tables are read-only; verified in `episode.py` — every source read goes through `source_rows`/`source_get`; writes go to work tables only).
- `_require_queued` blocks actions on invoices outside the agent's queue (verified via error `not_found` on wrong invoice id; and `unrelated_cases_untouched` verifier check protects cross-case state).

## Gaps / caveats found

1. **Clarification reply events are recipient-triggered, not content-triggered** — a vacuous message releases the scripted reply (manual-adv-05). Documented as finding B2 in `attack-log.md`; this is a world-simulation fidelity gap, not a leakage problem.
2. **Credit note `applied_to` is visible** — intended: the F05 trap is discoverable rather than hidden. Not a leak.
3. No instances of family label, split, task revision, private expectation, or sibling-split content observed in any agent-facing surface.

## Decision

Agent-visible surface contains all facts needed to solve every reviewed task
honestly, and no private/hidden data leaks through tools, prompts, schemas, or
post-clarification observations. Visibility: **clean**. (B2 remains a grading
defect, not a visibility defect.)
