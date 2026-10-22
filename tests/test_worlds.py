from __future__ import annotations

from invoiceops.domain.money import format_minor
from invoiceops.tasks.build import build_task
from invoiceops.worlds.companies import COMPANIES, companies_in


def test_twelve_companies_split_six_two_four() -> None:
    assert len(COMPANIES) == 12
    assert [len(companies_in(s)) for s in ("train", "dev", "test")] == [6, 2, 4]
    assert len({c.name for c in COMPANIES}) == 12
    assert len({v.legal_name for c in COMPANIES for v in c.vendors}) == 48
    assert len({i.sku for c in COMPANIES for i in c.items}) == 60


def test_approval_limits_increase() -> None:
    for c in COMPANIES:
        assert (
            c.self_approval_limit_minor
            < c.manager_limit_minor
            < c.controller_limit_minor
            < c.cfo_limit_minor
        )


def test_policy_text_states_every_parameter() -> None:
    bundle = build_task(COMPANIES[0], "F01", 0)
    world = bundle.public.world
    policy = world.policies[0]
    body = next(d.body for d in world.documents if d.id == policy.document_id)
    p = policy.params
    assert format_minor(p.price_tolerance_cap_minor, "USD") in body
    assert format_minor(p.self_approval_limit_minor, "USD") in body
    assert "2%" in body  # Northstar tolerance is 200 bps
    for role in world.roles:
        if role.can_approve:
            assert format_minor(role.approval_limit_minor, "USD") in body


def test_same_seed_same_world() -> None:
    a = build_task(COMPANIES[3], "F09", 1)
    b = build_task(COMPANIES[3], "F09", 1)
    assert a.model_dump_json() == b.model_dump_json()
