"""HS-131-03 remaining crash/race and Ask contract-drift obligations."""
from __future__ import annotations

import asyncio
import hashlib
import json
import threading
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database
from holdspeak.deployment_revisions import capture_deployment_revision
from holdspeak.inference_targets import resolve_inference_target
from holdspeak.kernel.ask_projection import materialize as materialize_ask
from holdspeak.kernel.ask_projection import register as register_ask
from holdspeak.kernel.inference_runner import InferenceRunner, InvocationRequest, ServiceContract
from holdspeak.kernel.recipe_projection import register as register_recipe
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
import holdspeak.services.ask_service as ask_service_module
from holdspeak.services.desk_service import DeskService
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router
from holdspeak.services.ask_service import (
    ASK_PAYLOAD_SCHEMA_VERSION,
    ASK_SERVICE_CONTRACT,
    ASK_SERVICE_SCHEMA_VERSION,
    AskService,
)

OWNER = Principal(PrincipalKind.OWNER, "owner")


class Adapter:
    def __init__(self, result: Any = "answer") -> None:
        self.result = result

    def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: threading.Event) -> Any:
        return self.result

    def cancel(self) -> str:
        return "cancelled"


class AskEngine:
    active_provider = "test-provider"
    active_model = "test-model"

    def run_prompt(self, **kwargs: Any) -> str:
        return "contract answer"


@pytest.fixture
def rig(tmp_path: Path) -> tuple[Database, Any, Any]:
    db = Database(tmp_path / "remaining-obligations.db")
    db.profiles.upsert(profile_id="local", name="Local", kind="onDevice", model_file="/model.gguf")
    revision = capture_deployment_revision(db, resolve_inference_target(db, "local"))
    return db, _configure(db), revision


def _request(revision: Any, invocation_id: str) -> InvocationRequest:
    payload = {"schema_version": 1, "question": invocation_id, "deployment_revision": revision.id}
    return InvocationRequest(
        revision.id,
        ServiceContract.for_payload("holdspeak.ask", "1", payload),
        time.time() + 30,
        payload,
        invocation_id,
    )


def _stage(rig: tuple[Database, Any, Any], invocation_id: str, kind: str, projection: dict[str, Any]) -> None:
    db, broker, revision = rig
    outcome = InferenceRunner(broker, db, engine_factory=lambda _revision, **_kw: object(), principal_provider=lambda: OWNER).invoke(
        _request(revision, invocation_id),
        Adapter(projection["output"]),
        publish=broker.projection_stager.publisher(invocation_id, kind, lambda _: projection),
    )
    assert outcome.outcome == "succeeded"


def test_real_migrated_ask_and_recipe_stages_finalize_concurrently_three_times(rig):
    """Two registered production materializers share SQLite's one-writer boundary."""
    db, broker, _ = rig
    stager = broker.projection_stager
    register_ask(stager)
    register_recipe(stager)

    for round_number in range(3):
        ask_id = f"concurrent_ask_{round_number}"
        recipe_id = f"concurrent_recipe_{round_number}"
        artifact_id = f"artifact_concurrent_{round_number}"
        _stage(rig, ask_id, "ask-result", {"output": f"ask-{round_number}"})
        _stage(rig, recipe_id, "recipe-run", {
            "artifact_id": artifact_id,
            "name": f"Recipe {round_number}",
            "output": f"recipe-{round_number}",
            "recipe_id": "r1",
            "sources": [],
            "created_at": "2026-08-09T00:00:00",
        })

        gate = threading.Barrier(3)
        results: dict[str, Any] = {}
        failures: list[BaseException] = []

        def finalize(invocation_id: str) -> None:
            try:
                gate.wait(2)
                results[invocation_id] = stager.finalize(invocation_id)
            except BaseException as exc:  # thread failures must fail the test thread
                failures.append(exc)

        ask_thread = threading.Thread(target=finalize, args=(ask_id,))
        recipe_thread = threading.Thread(target=finalize, args=(recipe_id,))
        ask_thread.start()
        recipe_thread.start()
        gate.wait(2)
        ask_thread.join(5)
        recipe_thread.join(5)
        assert not ask_thread.is_alive() and not recipe_thread.is_alive()
        assert not failures
        assert results[ask_id]["output"] == f"ask-{round_number}"
        assert results[recipe_id]["artifact_id"] == artifact_id

        with db._connection() as conn:
            ask = conn.execute("SELECT invocation_id,payload_json FROM ask_results WHERE invocation_id=?", (ask_id,)).fetchone()
            recipe = conn.execute("SELECT invocation_id,artifact_id FROM recipe_results WHERE invocation_id=?", (recipe_id,)).fetchone()
            artifact = conn.execute("SELECT id,body_markdown FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            states = conn.execute(
                "SELECT invocation_id,state FROM kernel_projection_stages WHERE invocation_id IN (?,?) ORDER BY invocation_id",
                (ask_id, recipe_id),
            ).fetchall()
        assert ask["invocation_id"] == ask_id and f"ask-{round_number}" in ask["payload_json"]
        assert recipe["invocation_id"] == recipe_id and recipe["artifact_id"] == artifact_id
        assert artifact["id"] == artifact_id and artifact["body_markdown"] == f"recipe-{round_number}"
        assert {row["state"] for row in states} == {"PUBLISHED"}


def test_recipe_materializer_rollback_leaves_no_partial_rows_then_retries(rig):
    db, broker, _ = rig
    stager = broker.projection_stager
    register_recipe(stager)
    invocation_id = "rollback_recipe"
    artifact_id = "artifact_rollback"
    _stage(rig, invocation_id, "recipe-run", {
        "artifact_id": artifact_id,
        "name": "Rollback recipe",
        "output": "must roll back",
        "recipe_id": "r1",
        "sources": [{"source_type": "recipe", "source_ref": "r1"}],
        "created_at": "2026-08-09T00:00:00",
    })

    real_materializer = stager._materializers["recipe-run"]

    def fail_after_domain_writes(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
        real_materializer(conn, stage, permit)
        raise RuntimeError("forced materializer failure after domain writes")

    stager._materializers["recipe-run"] = fail_after_domain_writes
    with pytest.raises(RuntimeError, match="forced materializer failure"):
        stager.finalize(invocation_id)

    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM artifacts WHERE id=?", (artifact_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM artifact_sources WHERE artifact_id=?", (artifact_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM recipe_results WHERE invocation_id=?", (invocation_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM ask_results").fetchone()[0] == 0
    assert stager.get(invocation_id).state == "STAGED"

    stager._materializers["recipe-run"] = real_materializer
    result = stager.finalize(invocation_id)
    assert result is not None and result["artifact_id"] == artifact_id
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM artifacts WHERE id=?", (artifact_id,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM artifact_sources WHERE artifact_id=?", (artifact_id,)).fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM recipe_results WHERE invocation_id=?", (invocation_id,)).fetchone()[0] == 1
    assert stager.get(invocation_id).state == "PUBLISHED"


def test_real_migrated_ask_cancellation_after_stage_is_completed_and_not_duplicated(rig, monkeypatch):
    db, broker, _ = rig
    stager = broker.projection_stager
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: AskEngine())
    monkeypatch.setattr("holdspeak.intel.providers.build_configured_meeting_intel", lambda: AskEngine())
    stage_committed = threading.Event()
    release_publish = threading.Event()
    staged_ids: list[str] = []
    replies: list[dict[str, Any]] = []
    failures: list[BaseException] = []

    class ChoreographedAdapter:
        def dispatch(self, engine: Any, payload: dict[str, Any], cancellation: threading.Event) -> dict[str, str]:
            return {"output": "late-but-staged", "provider": "test-provider", "model": "test-model"}

        def cancel(self) -> str:
            return "cancelled"

    real_publisher = stager.publisher

    def pause_after_stage(invocation_id: str, kind: str, encoder: Any) -> Any:
        publisher = real_publisher(invocation_id, kind, encoder)

        def stage_then_pause(output: Any) -> str:
            result_ref = publisher(output)
            staged_ids.append(invocation_id)
            stage_committed.set()
            assert release_publish.wait(2)
            return result_ref

        return stage_then_pause

    # The service uses the broker-owned shared runner; only the adapter and
    # the stager's publisher need choreography.
    monkeypatch.setattr(ask_service_module, "CanonicalPromptAdapter", ChoreographedAdapter)
    monkeypatch.setattr(stager, "publisher", pause_after_stage)
    service = AskService(db, broker=broker)

    def invoke_ask() -> None:
        try:
            replies.append(asyncio.run(service.ask(OWNER, "What changed?", lens="Brief")))
        except BaseException as exc:
            failures.append(exc)

    worker = threading.Thread(target=invoke_ask)
    worker.start()
    assert stage_committed.wait(2) and staged_ids
    stage = stager.get(staged_ids[0])
    assert stage is not None and stage.state == "STAGED"

    # The real Ask callback has committed the stage and runner is PUBLISHING:
    # Round-13 says this is completed, not a cancellation that may rewrite it.
    # Cancellation goes through the SERVICE seam — and through a SECOND
    # service instance, as a separate HTTP request would construct it: the
    # broker-owned runner is what makes the in-flight invocation reachable
    # across per-request service lifetimes.
    second_request_service = AskService(db, broker=broker)
    assert second_request_service is not service
    assert second_request_service.cancel(OWNER, stage.invocation_id)["disposition"] == "completed"
    release_publish.set()
    worker.join(5)
    assert not worker.is_alive() and not failures
    assert replies[0]["output"] == "late-but-staged"
    assert stager.finalize(stage.invocation_id) == replies[0]

    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results WHERE invocation_id=?", (stage.invocation_id,)).fetchone()[0] == 1
        assert conn.execute("SELECT state FROM kernel_projection_stages WHERE invocation_id=?", (stage.invocation_id,)).fetchone()[0] == "PUBLISHED"
    cancel_operations = [
        broker.store.operation(event["operation_id"])
        for event in broker.events(0, {}, OWNER)["events"]
        if broker.store.operation(event["operation_id"])["name"] == "inference.cancel"
    ]
    # A truthful completed disposition creates no cancellation child receipt to
    # race the successful invocation receipt.
    assert cancel_operations == []


_DECLARED_ASK_V1_SHAPE = {
    "schema_version": "int",
    "system_prompt": "str",
    "user_prompt": "str",
    "lens": "str",
    "context_ids": "list",
    "context_titles": "list",
    "grounding": "NoneType",
    "source_text": "str",
    "temperature": "NoneType",
    "max_tokens": "NoneType",
    "deployment_revision": "str",
    "selected_model": "str",
}
_DECLARED_ASK_V1_SHAPE_SHA256 = "sha256:1548b559f79b7bdccf43485c168abf04840bec37c26aedfa254582708083fdfa"


def test_ask_v1_contract_shape_hash_guards_service_payload_drift(rig, monkeypatch):
    db, broker, _ = rig
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: AskEngine())
    monkeypatch.setattr("holdspeak.intel.providers.build_configured_meeting_intel", lambda: AskEngine())
    captured: list[tuple[str, str, dict[str, Any]]] = []
    original = ServiceContract.for_payload.__func__

    def capture(cls: type[ServiceContract], contract: str, revision: str, payload: dict[str, Any]) -> ServiceContract:
        captured.append((contract, revision, dict(payload)))
        return original(cls, contract, revision, payload)

    monkeypatch.setattr(ServiceContract, "for_payload", classmethod(capture))
    result = asyncio.run(AskService(db, broker=broker).ask(OWNER, "What changed?", lens="Brief"))
    assert result["output"] == "contract answer"
    assert captured and captured[-1][0:2] == (ASK_SERVICE_CONTRACT, ASK_SERVICE_SCHEMA_VERSION)
    payload = captured[-1][2]
    actual_shape = {name: type(value).__name__ for name, value in payload.items()}
    missing = sorted(set(_DECLARED_ASK_V1_SHAPE) - set(actual_shape))
    unexpected = sorted(set(actual_shape) - set(_DECLARED_ASK_V1_SHAPE))
    assert not missing, f"holdspeak.ask@1 declared fields missing from service payload: {missing}"
    assert not unexpected, f"holdspeak.ask@1 service payload has undeclared fields: {unexpected}"
    assert actual_shape == _DECLARED_ASK_V1_SHAPE
    assert payload["schema_version"] == ASK_PAYLOAD_SCHEMA_VERSION == 1
    shape_hash = "sha256:" + hashlib.sha256(json.dumps(actual_shape, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert shape_hash == _DECLARED_ASK_V1_SHAPE_SHA256


_GOLDEN_ASK_V1_FIELDS = frozenset({
    "schema_version", "system_prompt", "user_prompt", "lens", "context_ids",
    "context_titles", "grounding", "source_text", "temperature", "max_tokens",
    "deployment_revision", "selected_model",
})


def _admit_without_receipt(broker: Any, revision: Any, invocation_id: str) -> str:
    submitted = broker.submit({
        "request_schema": 1, "request_id": invocation_id, "idempotency_key": invocation_id,
        "operation": {"name": "inference.invoke", "version": 1}, "target": {},
        "arguments": {"invocation_id": invocation_id, "deployment_revision": revision.id,
                      "definition_origin": {"kind": "service", "contract": "holdspeak.ask", "revision": "1", "payload_hash": "sha256:" + "0" * 64},
                      "deadline_at": time.time() + 30, "attempt_ordinal": 1},
    }, OWNER)
    approved = broker.decide(submitted["operation_id"], "approve", submitted["revision"], OWNER)
    node = Principal(PrincipalKind.NODE, broker.store.operation(approved["operation_id"])["placement"].removeprefix("node:"))
    assert broker.claim(node, invocation_id)["operations"]
    return approved["operation_id"]


def test_startup_recovers_orphaned_succeeded_stage_once(rig):
    db, broker, revision = rig
    invocation_id = "orphaned_succeeded_ask"
    _stage(rig, invocation_id, "ask-result", {"output": "recover me"})
    assert broker.projection_stager.get(invocation_id).state == "STAGED"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results").fetchone()[0] == 0

    # A process restart creates a new Database object over the same durable file.
    # _configure deliberately reuses the broker for repeated calls on one object.
    restarted = Database(db.db_path)
    booted = _configure(restarted)
    assert booted.projection_stager.get(invocation_id).state == "PUBLISHED"
    with restarted._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results WHERE invocation_id=?", (invocation_id,)).fetchone()[0] == 1
    _configure(restarted)
    with restarted._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results WHERE invocation_id=?", (invocation_id,)).fetchone()[0] == 1


def test_terminal_operation_without_receipt_is_surfaced_in_desk_health(rig, monkeypatch):
    db, broker, revision = rig
    invocation_id = "terminal_without_receipt"
    operation_id = _admit_without_receipt(broker, revision, invocation_id)
    broker.projection_stager.stage(invocation_id, "ask-result", {"output": "invisible"})
    with db._connection() as conn:
        conn.execute("UPDATE kernel_operations SET state='succeeded' WHERE operation_id=?", (operation_id,))
    report = broker.projection_stager.recover()
    assert report["healthy"] is False
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    health = DeskService(db).health()
    assert health["status"] == "unhealthy"
    assert health["projection_reconciliation_faults"] == [{
        "code": "terminal_operation_without_receipt", "operation_id": operation_id,
        "stage_id": broker.projection_stager.get(invocation_id).stage_id,
    }]


def test_real_materializer_rejects_raising_direct_writer_before_any_domain_write(rig):
    _db, broker, revision = rig
    invocation_id = "raising_spy"
    _stage(rig, invocation_id, "ask-result", {"output": "never written"})
    stage = broker.projection_stager.get(invocation_id)

    class RaisingConnection:
        def execute(self, *args: Any, **kwargs: Any) -> None:
            raise AssertionError("direct domain write escaped the permit fence")

    # The production Ask materializer validates the permit before it can issue
    # any domain SQL; a direct-write spy therefore remains untouched.
    with pytest.raises(Exception, match="projection_publication_permit_invalid"):
        materialize_ask(RaisingConnection(), stage, object())


def test_permit_is_single_use_and_migrated_callbacks_only_insert_stages(rig):
    db, broker, revision = rig
    stager = broker.projection_stager
    register_ask(stager)

    def use_permit_twice(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
        permit.use(conn)
        with pytest.raises(Exception, match="projection_publication_permit_invalid"):
            permit.use(conn)
        return {"output": stage.projection["output"]}

    stager.register("permit-twice", use_permit_twice)
    _stage(rig, "permit_twice", "permit-twice", {"output": "one use"})
    assert stager.finalize("permit_twice")["output"] == "one use"

    def counts() -> dict[str, int]:
        with db._connection() as conn:
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            return {row["name"]: conn.execute(f'SELECT COUNT(*) FROM "{row["name"]}"').fetchone()[0] for row in tables}

    for invocation_id, kind, projection in (
        ("callback_only_ask", "ask-result", {"output": "ask"}),
        ("callback_only_recipe", "recipe-run", {"artifact_id": "artifact_callback_only", "name": "Recipe", "output": "recipe", "recipe_id": "r1", "sources": [], "created_at": "2026-08-09T00:00:00"}),
    ):
        _admit_without_receipt(broker, revision, invocation_id)
        before = counts()
        callback = stager.publisher(invocation_id, kind, lambda _result, p=projection: p)
        assert callback("provider output").startswith("projection-stage:")
        after = counts()
        changed = {table: after[table] - before[table] for table in before if after[table] != before[table]}
        assert changed == {"kernel_projection_stages": 1}


def test_same_stage_concurrent_finalizers_replay_one_committed_projection(rig):
    db, broker, _ = rig
    stager = broker.projection_stager
    register_ask(stager)
    invocation_id = "same_stage_concurrent"
    _stage(rig, invocation_id, "ask-result", {"output": "one result"})
    real_materializer = stager._materializers["ask-result"]
    entered, release = threading.Event(), threading.Event()

    def held_materializer(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
        entered.set()
        assert release.wait(2)
        return real_materializer(conn, stage, permit)

    stager._materializers["ask-result"] = held_materializer
    results: list[dict[str, Any]] = []
    failures: list[BaseException] = []

    def finalize() -> None:
        try:
            results.append(dict(stager.finalize(invocation_id) or {}))
        except BaseException as exc:
            failures.append(exc)

    winner = threading.Thread(target=finalize)
    winner.start()
    assert entered.wait(2)
    contender_started = threading.Event()

    def contend() -> None:
        contender_started.set()
        finalize()

    loser = threading.Thread(target=contend)
    loser.start()
    assert contender_started.wait(2)
    release.set()
    winner.join(5)
    loser.join(5)
    assert not winner.is_alive() and not loser.is_alive() and not failures
    assert len(results) == 2 and results[0] == results[1]
    assert results[0]["output"] == "one result" and results[0]["invocation_id"] == invocation_id
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results WHERE invocation_id=?", (invocation_id,)).fetchone()[0] == 1


def test_real_ask_materializer_rollback_leaves_no_rows_then_retries(rig):
    db, broker, _ = rig
    stager = broker.projection_stager
    register_ask(stager)
    invocation_id = "rollback_ask"
    _stage(rig, invocation_id, "ask-result", {"output": "must roll back"})
    real_materializer = stager._materializers["ask-result"]

    def fail_after_ask_write(conn: Any, stage: Any, permit: Any) -> dict[str, Any]:
        real_materializer(conn, stage, permit)
        raise RuntimeError("force real Ask materializer rollback")

    stager._materializers["ask-result"] = fail_after_ask_write
    with pytest.raises(RuntimeError, match="force real Ask materializer rollback"):
        stager.finalize(invocation_id)
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results WHERE invocation_id=?", (invocation_id,)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM recipe_results").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM artifact_sources").fetchone()[0] == 0
    assert stager.get(invocation_id).state == "STAGED"
    stager._materializers["ask-result"] = real_materializer
    assert stager.finalize(invocation_id)["output"] == "must roll back"
    with db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM ask_results WHERE invocation_id=?", (invocation_id,)).fetchone()[0] == 1


def test_cancel_routes_delegate_to_migrated_services(rig, monkeypatch):
    db, _broker, _revision = rig
    monkeypatch.setattr(hsdb, "get_database", lambda *args, **kwargs: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    client = TestClient(app)
    ask = client.post("/api/ask/unknown-ask/cancel")
    recipe = client.post("/api/recipes/r1/invocations/unknown-recipe/cancel")
    assert ask.status_code == recipe.status_code == 200
    assert ask.json() == {"invocation_id": "unknown-ask", "disposition": "pending"}
    assert recipe.json() == {"invocation_id": "unknown-recipe", "disposition": "pending"}


def test_ask_v1_golden_field_names_and_schema_version_are_exact(rig, monkeypatch):
    db, broker, _ = rig
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: AskEngine())
    monkeypatch.setattr("holdspeak.intel.providers.build_configured_meeting_intel", lambda: AskEngine())
    captured: list[dict[str, Any]] = []
    original = ServiceContract.for_payload.__func__

    def capture(cls: type[ServiceContract], contract: str, revision: str, payload: dict[str, Any]) -> ServiceContract:
        if contract == ASK_SERVICE_CONTRACT and revision == ASK_SERVICE_SCHEMA_VERSION:
            captured.append(dict(payload))
        return original(cls, contract, revision, payload)

    monkeypatch.setattr(ServiceContract, "for_payload", classmethod(capture))
    asyncio.run(AskService(db, broker=broker).ask(OWNER, "Golden ask"))
    payload = captured[-1]
    missing = sorted(_GOLDEN_ASK_V1_FIELDS - set(payload))
    unexpected = sorted(set(payload) - _GOLDEN_ASK_V1_FIELDS)
    assert not missing, f"holdspeak.ask@1 golden fields missing: {missing}"
    assert not unexpected, f"holdspeak.ask@1 golden fields added or renamed: {unexpected}"
    assert payload["schema_version"] == 1
