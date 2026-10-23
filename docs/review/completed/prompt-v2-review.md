# Prompt v2 Review

Reviewer: Shahid Ahmed (independent solver) · Date: 2026-10-23
Files reviewed:
- `src/invoiceops/agents/prompts/system_v1.md`
  sha256 `2cd9e5836fa2bf84eb16913cd9dc756aa39f68c56b106ec31663e5351bf979c5`
- `src/invoiceops/agents/prompts/system_v2.md`
  sha256 `da1dd707ab199f8b55877cda332d6121dd7844d2f2d3031ebab20c7485c98ae0`

## Diff vs v1

v2 keeps v1's role/permission framing and adds a six-step "How to work"
procedure:

1. Read the policy document in effect on today's business date before
   deciding; it overrides supplier documents.
2. Read invoice, PO (latest revision), receipts, supplier record, supplier
   history; compare line by line.
3. Apply the policy's checks in the order it gives; arithmetic in cents.
4. Record via set_disposition with citations; send required
   clarifications/approvals; use check_inbox.
5. Propose payment only when policy allows, exact amount, once; on retryable
   errors retry with the same idempotency key.
6. submit_case exactly once.

## Leakage / task-specificity check

- **Task IDs**: none.
- **Private answers / expected outcomes**: none — no amounts, reason codes
  bound to specific tasks, or "the right answer is X" statements.
- **Family labels or mappings**: none — no F01–F12 references, no hints keyed
  to family structure.
- **Numeric parameters**: none — no tolerances, caps, limits, or thresholds
  copied from policy parameters.
- **Split information**: none.

The closest-to-the-line items:

- "retry with the same idempotency key" restates the `propose_payment` tool's
  own error message and description — generic API hygiene, not a task answer.
- "latest revision" and "the version in effect on today's business date"
  restate rules printed inside the policy documents themselves.
- "it overrides anything written in supplier documents" restates the
  evidence-not-instructions clause.

Every v2 addition is general working advice that an agent could (and should)
derive from the tool descriptions and the in-world policy text. It does not
pre-solve any task: it never says *which* rule applies, *whether* to approve,
or *what* amount is right.

## Decision

- [x] **Approve** `system_v2.md` — general advice only; no task-, family-, or
  split-specific content.
- [ ] **Approve with changes**
- [ ] **Reject**
