# R3 Task Family Review

- **Family ID and name:** F06 Approval routing (re-check after the fix)
- **Task IDs reviewed:** T-DC7A6B (dev, w08-hearthmoor v2), T-0A802E (test, w10-juniperfold v1), T-0A0D10 (test, w12-marrowind v0), T-8979C8 (train, w02-bramblewood v0), T-2D6100 (train, w04-quillfeather v1), T-8E32C6 (train, w06-tamsin v2)
- **Reviewer initials:** Shahid Ahmed
- **Role:** Independent solver
- **Date:** 2026-10-23
- **Commit re-checked:** `f1c8f365cc27c9d77bb2aa43b6dc89c2a16bfae1` (includes `75270f4`)

## Checklist

Answer Yes / No / Unsure. Explain every No or Unsure under Notes.

| # | Question | Answer |
|---|---|---|
| 1 | The family tests one clear skill, described in a sentence. | Yes — route the payment to the approver at the right level (lowest limit covering the amount), and obey the decision. |
| 2 | The variants differ in ways that change the reasoning, not only in names and numbers. | Yes — two at the AP-manager level (T-0A0D10 $62,037 ≤ $90k; T-8979C8 $19,992 ≤ $30k), two at the controller level (T-0A802E $184,779 vs controller $300k; T-2D6100 $119,925 vs controller $200k), two where the right approver declines for budget (T-DC7A6B, T-8E32C6) → on_hold/awaiting_approval with no proposal. |
| 3 | Some variants should end in payment and others in a hold or follow-up; an agent that always does one thing would fail. | Yes — 4 payable + 2 budget-decline holds. Previously all 6 were payable (first-review weakness); fixed. |
| 4 | The policy wording is consistent across the variants. | Yes — §8 reads the same shape: self-limit, "lowest limit that still covers", declines for other levels, decline ⇒ on_hold/awaiting_approval. |
| 5 | Boundary cases are covered (for example, a price exactly at the tolerance limit) and the correct handling is stated. | Yes — the decisive boundaries are exercised: amounts just under the next level up (e.g., $62,037 vs ap_manager $90k), and the two decline tasks sit at the lowest approver level where "route down" is impossible. |
| 6 | The failing examples include the most likely realistic mistakes. | Yes — asking too senior (cfo/controller → "route to ap_manager"), asking a non-approver, paying after a decline, under-amount approval; all confirmed FAIL in the recheck attacks. |
| 7 | No variant relies on a trick: unclear IDs, hidden requirements, padding, or random failures. | Yes — the decline reason is only revealed after asking (by design, stated in §8: use check_inbox); nothing hidden. |
| 8 | Train, development, and test variants come from different fictional companies. | Yes — hearthmoor / juniperfold / marrowind / bramblewood / quillfeather / tamsin. |
| 9 | *(Domain reviewer)* This situation occurs in real AP work, and the handling matches common practice. | Yes — delegated authority levels + budget-hold declines are realistic; "route to the right level" is how real approval matrices behave. |

## Missing cases

Realistic situations in this family that no variant covers:

- A task where the CFO is the *correct* approver (no instance exceeds the controller limit).
- A decline at the controller level specifically (both decline tasks sit at ap_manager).
- A correct-approval-then-second-approver-needed case (joint/split approval) — out of scope of the written policy, noted only.

## Notes

Fixed-habit analysis (the first-review blocker):

- "Always ask CFO and pay in full" → CFO declines on all six ("route to ap_manager"/"route to controller"); paying unapproved fails all 6.
- "Always ask AP manager and pay" → correct only for the two ap-manager pays; fails the two controller-level tasks (routing decline) and the two budget declines = 2/6.
- "Always hold" → correct on 2/6.
- No fixed habit passes the family. The first-review F06 blocker is resolved.

Policy §8 states the routing rule and the decline outcome plainly; both observed decline
messages ("route to ap_manager", "keep it on hold") are unambiguous for a careful agent.

## Decision

- [x] **Approve family**
- [ ] **Approve with changes**
- [ ] **Reject:** revise and review again
