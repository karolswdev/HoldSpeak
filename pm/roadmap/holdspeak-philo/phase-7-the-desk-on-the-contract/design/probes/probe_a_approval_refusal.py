"""PROBE (a), PHILO-7-02 lifecycle beat: a refusal at approval leaves the
operation in `awaiting_decision` with NO receipt (broker.py:197-204).

Real code paths: the configured kernel broker (kernel/runtime.py `_configure`)
over an isolated Database; a real registered spec (`tool.call` v1, the same
request shape as tests/unit/test_kernel_broker.py:22-41). No doubles.
Run: HOME=$(mktemp -d) uv run pytest -q -s <this file>
"""
from __future__ import annotations

import pytest

from holdspeak import kernel
from holdspeak.db import Database
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _as_principal, _configure
from holdspeak.principals import Principal, PrincipalKind

AGENT = Principal(PrincipalKind.AGENT, "agent:probe")


def test_probe_a_refusal_at_approval_leaves_no_receipt(tmp_path, monkeypatch) -> None:
    import holdspeak.db.core as db_core

    database = Database(tmp_path / "probe.db")
    monkeypatch.setattr(db_core, "_db", database)
    broker = _configure(database, clock=lambda: 1_000.0)
    raw = {
        "request_schema": 1, "request_id": "request-probe", "idempotency_key": "key-probe",
        "operation": {"name": "tool.call", "version": 1},
        "subject_refs": ["story:PHILO-7-02"], "target": {"ref": "gate:proposal-probe"},
        "arguments": {"proposal_id": "proposal-probe", "tool": "Bash", "args_sha256": "a" * 64,
                      "args_head": "git status", "cwd": "/workspace", "ttl_seconds": 60},
        "placement": "node:node_proof",
    }
    with _as_principal(AGENT):
        handle = kernel.submit(raw)
    print(f"\nsubmit -> state={handle['state']} operation_id={handle['operation_id']}")
    with _as_principal(AGENT), pytest.raises(KernelRefused) as caught:
        kernel.decide(handle["operation_id"], "approve", handle["revision"])
    print(f"decide(agent) -> KernelRefused reason={caught.value.reason}")
    operation = broker.store.operation(handle["operation_id"])
    receipt = broker.store.receipt(handle["operation_id"])
    print(f"after refusal: operation.state={operation['state']} receipt={receipt}")
    with database._connection() as conn:
        n = conn.execute("SELECT COUNT(*) FROM kernel_receipts WHERE operation_id=?",
                         (handle["operation_id"],)).fetchone()[0]
    print(f"kernel_receipts rows for the operation = {n}")
    assert operation["state"] == "awaiting_decision"
    assert receipt is None and n == 0
