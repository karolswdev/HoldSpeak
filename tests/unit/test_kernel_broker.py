"""HS-106-04: the operation spine, without a driver-shaped exception."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import kernel
from holdspeak.db import Database
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _as_principal, _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.web.routes.system.kernel_routes import build_kernel_router

OWNER = Principal(PrincipalKind.OWNER, "owner-session")
AGENT = Principal(PrincipalKind.AGENT, "agent:proof")
NODE = Principal(PrincipalKind.NODE, "node_proof")


def _request(key: str = "one", **arguments):
    values = {
        "proposal_id": f"proposal-{key}",
        "tool": "Bash",
        "args_sha256": "a" * 64,
        "args_head": "git status",
        "cwd": "/workspace",
        "ttl_seconds": 60,
    }
    values.update(arguments)
    return {
        "request_schema": 1,
        "request_id": f"request-{key}",
        "idempotency_key": f"key-{key}",
        "operation": {"name": "tool.call", "version": 1},
        "subject_refs": ["story:HS-106-04"],
        "target": {"ref": f"gate:proposal-{key}"},
        "arguments": values,
        "placement": "node:node_proof",
    }


@pytest.fixture
def rig(tmp_path: Path, monkeypatch):
    import holdspeak.db.core as db_core

    now = [1_000.0]
    database = Database(tmp_path / "kernel.db")
    monkeypatch.setattr(db_core, "_db", database)
    broker = _configure(database, clock=lambda: now[0])
    return database, broker, now


def _submit(principal=AGENT, request=None):
    with _as_principal(principal):
        return kernel.submit(request or _request())


def _decide(handle, decision="approve"):
    with _as_principal(OWNER):
        return kernel.decide(handle["operation_id"], decision, handle["revision"])


def test_package_has_exactly_four_caller_and_three_executor_calls() -> None:
    assert kernel.__all__ == [
        "read", "submit", "decide", "events", "claim", "receipt", "reconcile"
    ]
    assert all(callable(getattr(kernel, name)) for name in kernel.__all__)


def test_codec_and_four_authority_layers_admit_in_order(rig) -> None:
    _, broker, _ = rig
    handle = _submit()
    assert handle["state"] == "awaiting_decision"
    assert broker.last_authority_layers == (
        "authenticated_principal",
        "declared_capability",
        "hard_prerequisites",
        "interruption_policy",
    )
    operation = broker.store.operation(handle["operation_id"])
    assert operation["principal_kind"] == "agent"
    assert operation["authority_basis"].split("+") == list(broker.last_authority_layers)
    assert operation["envelope_sha256"].startswith("sha256:")
    with _as_principal(AGENT):
        projection = kernel.read(
            [f"operation:{handle['operation_id']}"], "full", "committed"
        )["objects"][0]
    assert projection["canonical"]["id"] == "proposal-one"
    assert projection["process"]["generic_state"] == "waiting"
    assert projection["process"]["domain_state"] == "held"


def test_refused_submission_has_terminal_receipt_and_stream_content_is_forbidden(rig) -> None:
    refused = _submit(request=_request("audio", audio_frames=["never journal me"]))
    assert refused["state"] == "refused"
    assert refused["receipt"]["state"] == "refused"
    assert refused["receipt"]["outcome"] == "journal_content_forbidden"
    with _as_principal(AGENT):
        batch = kernel.events(0, {"operation_id": refused["operation_id"]})
    assert [event["event_type"] for event in batch["events"]] == [
        "operation.refused", "operation.receipt"
    ]
    rendered = str(batch)
    assert "never journal me" not in rendered

    malformed = _request("version")
    malformed["operation"]["version"] = "not-an-integer"
    malformed_refusal = _submit(request=malformed)
    assert malformed_refusal["receipt"]["outcome"] == "request_incomplete"


def test_journal_tamper_is_named_then_restores_green(rig) -> None:
    database, broker, _ = rig
    _submit()
    assert broker.store.verify() == {
        "ok": True, "stream": "operations", "records": 2,
        "head": broker.store.verify()["head"],
    }
    with database._connection() as conn:
        original = conn.execute(
            "SELECT head FROM kernel_journal WHERE stream_sequence=1"
        ).fetchone()[0]
        conn.execute(
            "UPDATE kernel_journal SET head='tampered' WHERE stream_sequence=1"
        )
    with pytest.raises(KernelRefused, match="journal_record_hash_mismatch") as caught:
        broker.store.verify()
    assert caught.value.reason == "journal_record_hash_mismatch"
    with database._connection() as conn:
        conn.execute(
            "UPDATE kernel_journal SET head=? WHERE stream_sequence=1", (original,)
        )
    assert broker.store.verify()["ok"] is True
    print(
        '{"tamper":"journal_record_hash_mismatch","restored":"ok"}'
    )


def test_agent_cannot_decide_and_http_decision_cannot_mutate_envelope(rig) -> None:
    _, _, _ = rig
    handle = _submit()
    with _as_principal(AGENT), pytest.raises(KernelRefused) as caught:
        kernel.decide(handle["operation_id"], "approve", handle["revision"])
    assert caught.value.reason == "owner_principal_required_to_decide"

    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_kernel_router())
    response = TestClient(app).post(
        f"/api/kernel/operations/{handle['operation_id']}/decide",
        json={
            "decision": "approve", "expected_revision": handle["revision"],
            "payload": {"changed": True}, "target": {"ref": "other"},
            "placement": "node:other",
        },
    )
    assert response.status_code == 409
    assert response.json() == {
        "error": "admitted_envelope_immutable",
        "fields": ["payload", "placement", "target"],
    }


def test_warrant_expiry_and_revocation_refuse_at_claim(rig) -> None:
    _, broker, now = rig
    expired = _decide(_submit(request=_request("expired")))
    now[0] += 31
    with _as_principal(NODE):
        claim = kernel.claim()
    assert claim["refusal"]["outcome"] == "warrant_expired"
    assert broker.store.receipt(expired["operation_id"])["state"] == "refused"

    current = _decide(_submit(request=_request("revoked")))
    broker.store.revoke_warrant(current["operation_id"])
    with _as_principal(NODE):
        claim = kernel.claim()
    assert claim["refusal"]["outcome"] == "warrant_revoked"


def test_claim_receipt_reconcile_and_cursor_projection(rig) -> None:
    handle = _decide(_submit(request=_request("execute")))
    with _as_principal(NODE):
        claimed = kernel.claim()["operations"][0]
        with pytest.raises(KernelRefused) as content:
            kernel.receipt(handle["operation_id"], "succeeded", "not domain content")
        terminal = kernel.receipt(handle["operation_id"], "indeterminate")
        reconciled = kernel.reconcile(handle["operation_id"])
    assert content.value.reason == "result_ref_invalid"
    assert claimed["state"] == "claimed"
    assert terminal["state"] == "indeterminate"
    with _as_principal(NODE):
        assert kernel.receipt(handle["operation_id"], "indeterminate") == terminal
        with pytest.raises(KernelRefused) as changed:
            kernel.receipt(handle["operation_id"], "succeeded")
    assert changed.value.reason == "receipt_immutable"
    assert reconciled["reconcile"] == "terminal"
    assert reconciled["receipt"]["outcome"] == "indeterminate"
    with _as_principal(OWNER):
        first = kernel.events(0, {})
        replay = kernel.events(0, {})
    assert first == replay
    assert first["cursor"] >= 1
