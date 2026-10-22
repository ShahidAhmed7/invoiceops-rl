from __future__ import annotations

import pytest
from pydantic import ValidationError

from invoiceops.domain.records import Invoice, InvoiceLine


def _invoice(**changes: object) -> dict[str, object]:
    data: dict[str, object] = {
        "id": "INV-1",
        "vendor_id": "VEN-1",
        "vendor_invoice_number": "A-1",
        "po_id": "PO-1",
        "invoice_date": "2026-01-02",
        "received_on": "2026-01-03",
        "remit_account": "x",
        "currency": "USD",
        "total_minor": 1000,
        "lines": [{"po_line_no": 1, "description": "d", "quantity": 10, "unit_price_minor": 100}],
    }
    data.update(changes)
    return data


def test_valid_invoice() -> None:
    assert Invoice.model_validate(_invoice()).total_minor == 1000


def test_total_must_equal_lines() -> None:
    with pytest.raises(ValidationError):
        Invoice.model_validate(_invoice(total_minor=999))


def test_float_amounts_rejected() -> None:
    with pytest.raises(ValidationError):
        InvoiceLine.model_validate(
            {"po_line_no": 1, "description": "d", "quantity": 1, "unit_price_minor": 1.5}
        )
    with pytest.raises(ValidationError):
        Invoice.model_validate(_invoice(total_minor=1000.0))


@pytest.mark.parametrize("bad", ["2026-1-2", "2026-02-30", "yesterday"])
def test_dates_must_be_iso(bad: str) -> None:
    with pytest.raises(ValidationError):
        Invoice.model_validate(_invoice(invoice_date=bad))


def test_records_are_frozen() -> None:
    inv = Invoice.model_validate(_invoice())
    with pytest.raises(ValidationError):
        inv.total_minor = 5  # type: ignore[misc]
