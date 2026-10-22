from __future__ import annotations

from invoiceops.episode import Episode
from invoiceops.verification.verifier import verify

from .conftest import by_family


def test_broken_snapshot_is_unscorable_not_failed() -> None:
    b = by_family("F01")
    ep = Episode(b.public.world, b.public.task_id)
    result = verify(b.public.world, b.private, ep.initial_snapshot, {"cases": []})
    assert not result.scorable and result.reward is None and result.error


def test_unsubmitted_episode_fails() -> None:
    b = by_family("F01")
    ep = Episode(b.public.world, b.public.task_id)
    result = verify(b.public.world, b.private, ep.initial_snapshot, ep.snapshot())
    assert result.scorable and result.reward == 0.0
    assert any(c.name == "submitted" and not c.passed for c in result.global_checks)
