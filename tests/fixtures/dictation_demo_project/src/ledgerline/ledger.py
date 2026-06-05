"""Double-entry posting engine. Entries are append-only (see .hs/memory.md)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entry:
    account: str
    amount_minor: int  # integer cents; debit > 0, credit < 0


def post_charge(customer: str, amount_minor: int) -> list[Entry]:
    """Post a balanced charge: debit the customer, credit revenue."""
    if amount_minor <= 0:
        raise ValueError("amount_minor must be positive cents")
    entries = [
        Entry(account=f"customer:{customer}", amount_minor=amount_minor),
        Entry(account="revenue", amount_minor=-amount_minor),
    ]
    assert sum(e.amount_minor for e in entries) == 0, "ledger must balance"
    return entries
