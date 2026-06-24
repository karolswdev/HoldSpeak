"""The double-entry posting engine.

This is the only module that writes to ``ledger_entries``. Every
``post`` appends exactly two balanced rows (a debit and an equal
credit) inside one transaction, so any posting group sums to zero. A
``reversal`` appends the mirror image of an existing group; we never
edit or delete the original.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from . import CREDIT, DEBIT
from .db.entries import EntriesRepo


@dataclass(frozen=True)
class Posting:
    group_id: str
    debit_account: str
    credit_account: str
    amount_minor: int


class UnbalancedPosting(ValueError):
    """Raised when a posting would not sum to zero."""


def _new_group_id() -> str:
    return uuid.uuid4().hex


def post(
    repo: EntriesRepo,
    debit_account: str,
    credit_account: str,
    amount_minor: int,
    *,
    group_id: str | None = None,
) -> Posting:
    """Append a balanced debit/credit pair. Returns the Posting.

    ``amount_minor`` must be a positive integer (minor units). The two
    rows are written in a single transaction so the ledger is never
    observed in a half-posted state.
    """
    if not isinstance(amount_minor, int):
        raise UnbalancedPosting("amount_minor must be an integer (minor units)")
    if amount_minor <= 0:
        raise UnbalancedPosting("amount_minor must be positive")
    if debit_account == credit_account:
        raise UnbalancedPosting("debit and credit accounts must differ")

    group_id = group_id or _new_group_id()
    with repo.transaction():
        repo.append(group_id, debit_account, DEBIT, amount_minor)
        repo.append(group_id, credit_account, CREDIT, -amount_minor)
    return Posting(group_id, debit_account, credit_account, amount_minor)


def reversal(repo: EntriesRepo, original_group_id: str) -> Posting:
    """Append the compensating mirror of an existing posting group.

    Reads the original group's rows and writes new rows with the sides
    swapped. The original is left untouched (append-only).
    """
    rows = repo.rows_for_group(original_group_id)
    if not rows:
        raise UnbalancedPosting(f"no posting group {original_group_id!r}")

    debit_row = next(r for r in rows if r["side"] == DEBIT)
    credit_row = next(r for r in rows if r["side"] == CREDIT)
    amount = abs(debit_row["amount_minor"])

    # Swap accounts: the original debit account is now credited.
    return post(
        repo,
        debit_account=credit_row["account"],
        credit_account=debit_row["account"],
        amount_minor=amount,
    )


def group_balance(repo: EntriesRepo, group_id: str) -> int:
    """Sum a posting group. A well-formed group returns 0."""
    return sum(r["amount_minor"] for r in repo.rows_for_group(group_id))
