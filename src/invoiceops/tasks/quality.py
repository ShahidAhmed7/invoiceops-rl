"""Suite-level quality checks: split leakage and outcome balance."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable

from invoiceops.tasks.model import TaskBundle


def leakage_problems(bundles: Iterable[TaskBundle]) -> list[str]:
    """Names, products, and document texts must never be shared across splits."""
    seen: dict[str, dict[str, str]] = defaultdict(dict)
    problems: list[str] = []
    for bundle in bundles:
        split = bundle.private.split
        world = bundle.public.world
        facts = {
            "company": [world.company.name],
            "vendor_name": [v.legal_name for v in world.vendors],
            "vendor_tax_id": [v.tax_id for v in world.vendors],
            "sku": [line.sku for po in world.purchase_orders for line in po.lines],
            "item_description": [
                line.description for po in world.purchase_orders for line in po.lines
            ],
            "document_body": [d.body for d in world.documents]
            + [d.body for e in world.events for d in e.effects.documents],
        }
        for kind, values in facts.items():
            for value in values:
                owner = seen[kind].setdefault(value, split)
                if owner != split:
                    problems.append(f"{kind} {value[:60]!r} appears in both {owner} and {split}")
    return sorted(set(problems))


def outcome_balance(bundles: Iterable[TaskBundle]) -> dict[str, Counter[str]]:
    """Primary outcome status counts per split."""
    balance: dict[str, Counter[str]] = defaultdict(Counter)
    for bundle in bundles:
        status = bundle.private.expectation.outcomes[0].status.value
        balance[bundle.private.split][status] += 1
    return dict(balance)
