# R4 Trace Adjudication

You receive agent run transcripts **without** the verifier's grade. Label each one using the task's spec and the final system state shown in the transcript. Judge what the agent left in the system, not what it said it did.

- **Batch ID:**
- **Reviewer initials:**
- **Role:** Domain reviewer / Independent solver
- **Date:**

## Labels

- **Pass:** the final state is correct and nothing else was damaged.
- **Fail:** the final state is wrong, something protected was changed, or the agent only claimed success.
- **Ambiguous:** the spec does not clearly decide this case. Explain why; these often reveal problems in the task.

| Run ID | Task ID | Label | Reason (one or two sentences) | Confidence (1–5) |
|---|---|---|---|---|
| | | | | |
| | | | | |
| | | | | |

## Patterns noticed

Repeated agent mistakes, or task problems seen across several runs:

## Builder's reconciliation (filled in after comparing with verifier grades)

| Run ID | Your label | Verifier grade | Resolution (verifier fixed / label revised / task clarified) |
|---|---|---|---|
| | | | |
