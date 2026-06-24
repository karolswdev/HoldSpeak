"""Tests for the posting engine and the idempotent charge path."""
import sqlite3

import pytest

from ledgerline import ledger
from ledgerline.db.entries import EntriesRepo
from ledgerline.db.idempotency import IdempotencyStore


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:", isolation_level=None)
    c.row_factory = sqlite3.Row
    return c


@pytest.fixture()
def entries(conn):
    return EntriesRepo(conn)


def test_posting_sums_to_zero(entries):
    posting = ledger.post(entries, "cust:42", "revenue:usd", 1500)
    rows = entries.rows_for_group(posting.group_id)
    assert len(rows) == 2
    assert sum(r["amount_minor"] for r in rows) == 0
    assert entries.total_balance() == 0


def test_reversal_restores_zero_balance(entries):
    posting = ledger.post(entries, "cust:42", "revenue:usd", 1500)
    assert entries.balance_of("cust:42") == 1500

    ledger.reversal(entries, posting.group_id)
    # Original rows untouched; reversal appended. Net is zero again.
    assert entries.balance_of("cust:42") == 0
    assert entries.total_balance() == 0
    assert len(entries.rows_for_group(posting.group_id)) == 2  # original intact


def test_rejects_non_integer_amount(entries):
    with pytest.raises(ledger.UnbalancedPosting):
        ledger.post(entries, "cust:42", "revenue:usd", 15.0)  # type: ignore[arg-type]


def test_idempotent_replay_does_not_double_post(conn):
    entries = EntriesRepo(conn)
    idem = IdempotencyStore(conn)
    key = "idem-abc-123"

    def charge_once():
        with idem.lock(key):
            existing = idem.get(key)
            if existing:
                return existing["group_id"], True
            p = ledger.post(entries, "cust:7", "revenue:usd", 999)
            idem.record(key, group_id=p.group_id, amount_minor=p.amount_minor)
            return p.group_id, False

    g1, replayed1 = charge_once()
    g2, replayed2 = charge_once()

    assert g1 == g2
    assert replayed1 is False
    assert replayed2 is True
    # Exactly one posting (two rows) despite two attempts.
    assert len(entries.rows_for_group(g1)) == 2
    assert entries.total_balance() == 0
