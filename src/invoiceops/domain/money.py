"""Exact money arithmetic in integer minor units (cents).

Floating-point values are rejected everywhere: every amount is an ``int`` number of
minor units and every rate is an ``int`` number of basis points (1 bps = 0.01%).
"""

from __future__ import annotations

BPS_DENOMINATOR = 10_000


def require_int(value: object, name: str) -> int:
    """Return ``value`` if it is a plain ``int`` (not ``bool``); raise ``TypeError`` otherwise."""
    if type(value) is not int:
        raise TypeError(f"{name} must be an int, got {type(value).__name__}")
    return value


def line_total(quantity: int, unit_price_minor: int) -> int:
    """Total of one line: quantity times unit price, in minor units."""
    require_int(quantity, "quantity")
    require_int(unit_price_minor, "unit_price_minor")
    return quantity * unit_price_minor


def apply_bps(amount_minor: int, bps: int) -> int:
    """``amount_minor * bps / 10_000`` rounded half-up to the nearest minor unit.

    Only non-negative inputs are meaningful for tolerances; negative inputs raise.
    """
    require_int(amount_minor, "amount_minor")
    require_int(bps, "bps")
    if amount_minor < 0 or bps < 0:
        raise ValueError("apply_bps expects non-negative amount and bps")
    return (amount_minor * bps + BPS_DENOMINATOR // 2) // BPS_DENOMINATOR


def format_minor(amount_minor: int, currency: str) -> str:
    """Human-readable amount, e.g. ``USD 12,000.00``."""
    require_int(amount_minor, "amount_minor")
    sign = "-" if amount_minor < 0 else ""
    major, minor = divmod(abs(amount_minor), 100)
    return f"{currency} {sign}{major:,}.{minor:02d}"
