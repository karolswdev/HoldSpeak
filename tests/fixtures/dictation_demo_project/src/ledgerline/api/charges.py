"""POST /charges — the charge endpoint. Idempotency is NOT wired yet."""

from __future__ import annotations

from ..ledger import post_charge


def create_charge(customer: str, amount_minor: int) -> dict:
    # TODO: honor the Idempotency-Key header (see .hs/memory.md) before posting.
    entries = post_charge(customer, amount_minor)
    return {"posted": [e.__dict__ for e in entries]}
