"""Task specifications.

A task has two parts kept in separate files:

* ``PublicTask`` (``public.json``): what the environment needs to run an episode. The world it
  contains is the same information an agent could read through tools, plus scripted replies
  that only become visible after the agent triggers them.
* ``PrivateTask`` (``private.json``): what the verifier needs. Never reachable through a tool and
  never copied into the agent-facing container image.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from invoiceops.domain.records import CaseStatus, ReasonCode, Record, RecordId
from invoiceops.domain.world import World

CiteGroups = tuple[tuple[RecordId, ...], ...]
"""Each inner tuple is a group; at least one id from every group must be cited."""


class ClarificationRequirement(Record):
    recipient_roles: tuple[RecordId, ...]
    cite: CiteGroups = ()


class PaymentExpectation(Record):
    amount_minor: int = Field(gt=0)
    credit_note_ids: tuple[RecordId, ...] = ()


class Outcome(Record):
    """One acceptable end state. A task passes if any of its outcomes is fully met."""

    label: str
    status: CaseStatus
    reason_codes: tuple[ReasonCode, ...]
    payment: PaymentExpectation | None
    clarifications: tuple[ClarificationRequirement, ...] = ()
    approval_required: bool = False
    evidence: CiteGroups = ()


class Expectation(Record):
    invoice_id: RecordId
    outcomes: tuple[Outcome, ...] = Field(min_length=1)


class PublicTask(Record):
    task_id: RecordId
    prompt: str
    max_steps: int = 50
    world: World


class PrivateTask(Record):
    task_id: RecordId
    family: str
    family_name: str
    variant: int
    split: Literal["train", "dev", "test"]
    world_id: RecordId
    difficulty_hypothesis: Literal["introductory", "intermediate", "advanced"]
    rationale: str
    expectation: Expectation
    oracle_hint: str = ""


class TaskBundle(Record):
    public: PublicTask
    private: PrivateTask
