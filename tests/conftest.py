from __future__ import annotations

from functools import cache

import pytest

from invoiceops.tasks.build import build_suite
from invoiceops.tasks.model import TaskBundle


@cache
def suite() -> tuple[TaskBundle, ...]:
    return tuple(build_suite())


@pytest.fixture(scope="session")
def bundles() -> tuple[TaskBundle, ...]:
    return suite()


def bundle_ids() -> list[str]:
    return [b.public.task_id for b in suite()]


def by_family(family: str, variant: int | None = None) -> TaskBundle:
    for b in suite():
        if b.private.family == family and (variant is None or b.private.variant == variant):
            return b
    raise LookupError(family)
