# Environment Card: InvoiceOps

## Summary

A stateful accounts-payable environment in which a tool-using agent resolves one supplier invoice per episode for a fictional company. The agent reads records, follows the company's written policy, and records a decision. A trusted verifier grades the resulting system state and history. It does not grade the agent's prose.

**Status:** environment, tasks, verifier, adapters, and containers are complete and tested locally. No model has been evaluated or trained on it yet. Tasks are builder-authored and have not yet been reviewed by an accounts-payable practitioner, so the environment is a **fictional policy simulator**.

## Intended use

- Evaluating tool-using language-model agents on policy-following, multi-step business work.
- Reinforcement learning with a strict outcome reward (TRL `environment_factory`, OpenEnv).
- Demonstrating environment and verifier engineering.

**Not intended for:** real accounting, payments, or compliance decisions. Not a measure of professional AP competence.

## Interface

| Surface | How |
|---|---|
| Python | `invoiceops.episode.Episode(world).step(tool, arguments)` |
| TRL | `GRPOTrainer(environment_factory=invoiceops.adapters.trl_env.InvoiceOpsToolEnv, ...)`; dataset rows carry `task_id` |
| OpenEnv | `invoiceops.adapters.openenv_app:app`; MCP tools (`ListToolsAction`, `CallToolAction`) over the `/ws` session; `reset(task_id=...)` |
| OpenAI-compatible models | `invoiceops evaluate --agent model --base-url ... --model ...` |
| Humans | `invoiceops play --task <id>` |

There are 15 tools: 8 read tools and 7 write tools (`set_disposition`, `create_clarification`, `request_approval`, `check_inbox`, `propose_payment`, `withdraw_payment_proposal`, and `submit_case`). Clarifications are structured: the agent chooses a recipient and a `request_type`, and the message is generated from the type. Errors use structured codes: `unknown_tool`, `invalid_arguments`, `not_found`, `forbidden`, `stale_version`, `retryable`, `step_limit_reached`, `episode_finished`. Each episode allows 50 tool calls.

## State and transitions

- Each episode gets its own in-memory SQLite database. Source records (invoices, POs, receipts, suppliers, payments, credit notes, documents) are protected by triggers, so no code path can modify them.
- Writes are transactional, versioned (optimistic locking on cases), and idempotent (keys on requests and proposals).
- Approvals come only from simulated approvers, after a request, and only within each approver's limit. Scripted replies are released by `check_inbox`, and only after the clarification that triggers them.
- Every step is logged with the state hash before and after. Replaying a log reproduces the same final state.

## Reward

The reward is strict 0/1. It is 1 only if all of the following hold:

- the case was submitted;
- no source record changed;
- no other invoice was touched;
- at most one payment proposal was ever created for the invoice (withdrawing one does not undo it);
- the submission matches the system state;
- at least one accepted outcome is fully met: status and reason, payment amount and credits (or no proposal ever), required clarifications with citations, approval before payment, and disposition evidence.

If the verifier itself fails, the result is *unscorable*, with no reward, and it is reported separately from a failed attempt. The verifier also reports critical violations, such as paying an invoice that must not be paid, paying without approval, overpaying, or creating duplicate proposals.

## Verifier validation

- On every task, the oracle's solution passes, every accepted alternative passes (reordered reads, alternative reason codes), and every mutation fails. There are 975 cases with 0 unexpected results; see `reports/local/verifier_mutations.md`. The mutations include the escapes found in the first pre-GPU review (withdrawing a wrong proposal, proposing before approval, the wrong approval level, the wrong request type), and the review's own attack scripts are replayed as regression tests.
- Scripted policies score as intended. The oracle scores 100% on every split. No-op and random score 0%. Always-hold scores at most 17% and always-pay at most 33%, each on any split. See `reports/local/scripted_baselines.md`.

## Isolation

- The agent-facing container holds only the public task files. It contains no private specs, verifier, task-family builders, or oracle, and it runs as a non-root user.
- A separate verifier container with no network grades episode exports.
- Concurrent sessions are isolated, and the public state response exposes only `episode_id`, `step_count`, and `task_id`. Checked by `scripts/container_check.py`.

## Limitations

- Fictional companies and policies; not reviewed by an AP practitioner yet.
- One currency (USD), integer cents, physical goods, and one invoice per episode.
- Twelve task families. The test split holds out *companies*, not kinds of task.
- Task files are public, so test tasks are not secret from future models.
- Scripted colleagues are deterministic and simple. There is no free-form dialogue.
