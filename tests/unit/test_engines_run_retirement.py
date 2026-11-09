"""HS-143-10 — retired mutable inference.run is history-only."""
from __future__ import annotations

import time
from pathlib import Path

from holdspeak.db import Database
from holdspeak.kernel.inference import InferenceRunCodec
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.invocation_service import InvocationService


OWNER = Principal(PrincipalKind.OWNER, "inference-run-retirement-owner")


def _legacy_request(*, target_id: str) -> dict:
    return {
        "request_schema": 1,
        "request_id": "retired-inference-run",
        "idempotency_key": "retired-inference-run",
        "operation": {"name": "inference.run", "version": 1},
        "target": {},
        "arguments": {
            "invocation_id": "retired-invocation",
            "definition_ref": "persona:legacy",
            "definition_revision": "rev-1",
            "grounding_refs": [],
            "requested_target_id": target_id,
            "deadline_at": time.time() + 30,
            "input_snapshot": {"input": "must not dispatch"},
        },
    }


def test_mutable_legacy_target_refuses_before_resolution_or_physical_dispatch(
    tmp_path: Path, monkeypatch
) -> None:
    db = Database(tmp_path / "retired.db")
    broker = _configure(db)
    resolved: list[str] = []

    def forbidden_resolution(*_args, **_kwargs):
        resolved.append("resolved")
        raise AssertionError("retired operation reached mutable target resolution")

    monkeypatch.setattr(
        "holdspeak.inference_targets.resolve_inference_target", forbidden_resolution
    )
    refused = broker.submit(_legacy_request(target_id="changed-after-submit"), OWNER)

    assert refused["state"] == "refused"
    assert refused["receipt"]["outcome"] == "inference_run_retired"
    assert resolved == []
    assert db.capability_invocations.get("retired-invocation") is None
    with db._connection() as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchone()[0] == 0


def test_historical_terminal_inference_run_remains_viewable(tmp_path: Path) -> None:
    db = Database(tmp_path / "history.db")
    broker = _configure(db)
    db.capability_invocations.begin(
        invocation_id="old-terminal",
        definition_ref="persona:old",
        requested_placement="mutable-target-from-history",
        input_snapshot={"input": "old"},
    )
    db.capability_invocations.start_attempt(
        invocation_id="old-terminal",
        attempt_id="old-attempt",
        destination="old-target",
    )
    db.capability_invocations.finish_attempt("old-attempt", state="succeeded")
    db.capability_invocations.finish(
        "old-terminal", state="succeeded", result_ref="artifact:old"
    )

    projected = InferenceRunCodec(db).read_native("old-terminal")
    inspected = InvocationService(db, broker).get(OWNER, "old-terminal")

    assert projected is not None and projected["state"] == "succeeded"
    assert inspected["id"] == "old-terminal"
    assert inspected["state"] == "succeeded"
    assert inspected["requested_placement"] == "mutable-target-from-history"
