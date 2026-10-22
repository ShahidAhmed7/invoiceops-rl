from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st

from invoiceops.domain.money import apply_bps, format_minor, line_total


def test_apply_bps_rounds_half_up() -> None:
    assert apply_bps(12_345, 200) == 247  # 246.9 -> 247
    assert apply_bps(25, 200) == 1  # 0.5 -> 1
    assert apply_bps(24, 200) == 0  # 0.48 -> 0


@pytest.mark.parametrize("bad", [1.0, "100", True])
def test_floats_strings_and_bools_are_rejected(bad: object) -> None:
    with pytest.raises(TypeError):
        apply_bps(bad, 100)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        line_total(bad, 100)  # type: ignore[arg-type]


def test_negative_inputs_rejected() -> None:
    with pytest.raises(ValueError):
        apply_bps(-1, 100)


@given(st.integers(min_value=0, max_value=10**12), st.integers(min_value=0, max_value=10_000))
def test_apply_bps_is_within_half_a_cent(amount: int, bps: int) -> None:
    exact_twice = 2 * amount * bps  # 2 * 10_000 * true value
    result = apply_bps(amount, bps)
    assert abs(2 * 10_000 * result - exact_twice) <= 10_000


def test_format_minor() -> None:
    assert format_minor(1_200_000, "USD") == "USD 12,000.00"
    assert format_minor(-5, "USD") == "USD -0.05"
