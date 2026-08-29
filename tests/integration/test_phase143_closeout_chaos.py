"""HS-143-14 S1 — one-restart production-composition closeout runbook.

This deliberately joins one routed Recipe chat, one durable Model Library command,
and one assignment mutation.  It uses real SQLite/application/broker objects; only
the local engine and the download response are bounded external-wire adapters.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from typing import Any

import pytest

from holdspeak.config import Config
from holdspeak.db import Database
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.agent_turn_service import AgentTurnService
from holdspeak.services.errors import ServiceError, ValidationError
from holdspeak.services.inference_acquisition_service import InferenceAcquisitionApplicationService
from holdspeak.services.inference_assignment_service import InferenceAssignmentService
from holdspeak.services.inference_fallback_controller import INFERENCE_FALLBACK_AUTHORITY
from holdspeak.services.inference_route_plan_service import ROUTE_PLANNING_AUTHORITY
from holdspeak.services.inference_setup_service import InferenceSetupApplicationService
from holdspeak.services.recipe_service import RecipeService
from holdspeak.services.sync_service import SyncService
from holdspeak.services.tool_turn_controller import TOOL_TURN_AUTHORITY
from tests.unit.test_phase143_inference_assignments import _profile, _result_claim
from tests.unit.test_phase143_tool_turn_routing import _qualified_manifest


OWNER = Principal(PrincipalKind.OWNER, "closeout-chaos-owner")


def _canonical_sha(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _assignment_heads_bytes(db: Database) -> bytes:
    """Exact durable assignment-head evidence, not a current Config projection."""
    with db._connection() as conn:
        rows = [dict(row) for row in conn.execute(
            "SELECT * FROM inference_assignment_heads ORDER BY assignment_key"
        ).fetchall()]
    return json.dumps(rows, sort_keys=True, separators=(",", ":")).encode("utf-8")


class _BlockingRecipeEngine:
    active_provider = "closeout-local"
    active_model = "closeout-old"

    def __init__(self) -> None:
        self.entered, self.release = Event(), Event()
        self.calls = 0

    def run_prompt(self, **_kwargs: object) -> str:
        self.calls += 1
        self.entered.set()
        assert self.release.wait(5), "the closeout runbook did not release the admitted Recipe call"
        return "closeout recipe answer"


class _UnknownRecipeEngine:
    active_provider = "closeout-local"
    active_model = "closeout-new"

    def __init__(self) -> None:
        self.calls = 0

    def run_prompt(self, **_kwargs: object) -> str:
        self.calls += 1
        # The provider boundary has accepted dispatch intent but cannot attest an
        # outcome. This is an external-wire failure, never a route/controller fake.
        raise RuntimeError("closeout wire disconnected after dispatch")


class _BlockingDownloadResponse:
    """One bounded download wire. The application still owns every state change."""

    status = 200
    headers: dict[str, str] = {}

    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.entered, self.release = Event(), Event()
        self._sent = False

    def __enter__(self) -> "_BlockingDownloadResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def geturl(self) -> str:
        return "https://huggingface.co/holdspeak/closeout/resolve/r1/closeout.gguf"

    def read(self, _size: int) -> bytes:
        if self._sent:
            return b""
        self.entered.set()
        assert self.release.wait(5), "the closeout runbook did not release the durable library command"
        self._sent = True
        return self._payload


def _download_catalog(payload: bytes) -> tuple[dict[str, object], dict[str, object]]:
    digest = "sha256:" + hashlib.sha256(payload).hexdigest()
    manifest = {"files": [{"path": "closeout.gguf", "sha256": digest, "size": len(payload)}]}
    source = {
        "repository": "holdspeak/closeout",
        "revision": "r1",
        "filename": "closeout.gguf",
        "file_sha256": digest,
        "download_bytes": len(payload),
        "peak_free_bytes": 1,
        "manifest_sha256": _canonical_sha(manifest),
        "license": "test-only",
    }
    catalog = {
        "catalog_revision": 1,
        "entries": [{
            "id": "closeout-local", "kind": "local_artifact_preset", "activation": "download",
            "format": "gguf", "runtime_id": "llama_cpp_prompt_v1", "runtime_min_revision": "0",
            "label": "Closeout local", "context": {"recommended_tokens": 1024}, "source": source,
        }],
    }
    return catalog, {"request_id": "closeout-download", "catalog_id": "closeout-local", "catalog_revision": 1}


def _acquisition(db: Database, root: Path, response: _BlockingDownloadResponse, *, recover: bool) -> InferenceAcquisitionApplicationService:
    setup = InferenceSetupApplicationService(db, config_provider=Config, home_provider=lambda: root / "home")
    catalog, _body = _download_catalog(response._payload)
    return InferenceAcquisitionApplicationService(
        db,
        setup_service=setup,
        model_root=root / "models",
        home_provider=lambda: root / "home",
        catalog_provider=lambda: catalog,
        opener=lambda *_args, **_kwargs: response,
        auto_recover=recover,
    )


def _set_tool_assignment(
    assignments: InferenceAssignmentService, *, command_id: str, expected_revision: int, profile_ids: tuple[str, ...],
) -> dict[str, Any]:
    return assignments.set_assignment(OWNER, {
        "command_id": command_id,
        "expected_revision": expected_revision,
        "scope": {"kind": "capability", "capability_id": "agent.tool_turn"},
        "entries": [
            {"profile_id": profile_id, "profile_revision": 1}
            for profile_id in profile_ids
        ],
    })


@pytest.mark.skip(reason="HS-150-02: recipe.chat retired from registry; RecipeService.chat() unavailable until HS-150-04")
@pytest.mark.timeout(30)
def test_one_restart_cross_product_preserves_frozen_recipe_receipt_library_and_assignment_truth(
    tmp_path: Path,
) -> None:
    """A logical hub crash/restart has one durable truth, never a second router.

    This is intentionally not SIGKILL theatre.  The durable SQLite records plus a
    fresh production composition are the recovery boundary the hub actually owns.
    """
    db_path = tmp_path / "closeout-chaos.db"
    db = Database(db_path)
    broker = _configure(db)
    agent = AgentTurnService.compose(broker)
    claims = ("language", _result_claim("agent.tool_turn"), "tool_turn")
    manifest = _qualified_manifest(*claims)
    _profile(db, "closeout-old", claims=claims, capability_manifest=manifest)
    _profile(db, "closeout-new", claims=claims, capability_manifest=manifest)
    assignments = InferenceAssignmentService(db, tool_capability_foundation=agent._foundation._foundation)
    initial = _set_tool_assignment(
        assignments,
        command_id="closeout-initial-assignment",
        expected_revision=0,
        profile_ids=("closeout-old", "closeout-new"),
    )
    assert initial["revision"] == 1
    recipe = db.recipes.upsert(recipe_id="closeout-recipe", name="Closeout", system_prompt="system")
    engine = _BlockingRecipeEngine()
    broker.inference_runner._engine_factory = lambda _revision, **_kwargs: engine

    payload = b"GGUF"
    response = _BlockingDownloadResponse(payload)
    acquisition = _acquisition(db, tmp_path, response, recover=False)
    _catalog, download_body = _download_catalog(payload)

    with ThreadPoolExecutor(max_workers=1) as executor:
        chat_future = executor.submit(
            lambda: asyncio.run(RecipeService(db, broker=broker).chat(OWNER, recipe.id, question="What survived?"))
        )
        assert engine.entered.wait(5), "RecipeService.chat never reached its admitted production engine"

        # The library command has persisted its replayable request before its one
        # external wire is allowed to finish. Its state may not select a model.
        started_download = acquisition.download(OWNER, download_body)
        assert started_download["acquisition"]["state"] in {"requested", "resolving_source", "downloading"}
        assert response.entered.wait(5), "Model Library command never reached its durable download boundary"
        heads_before_mutation = _assignment_heads_bytes(db)

        mutation = _set_tool_assignment(
            assignments,
            command_id="closeout-assignment-mutation",
            expected_revision=1,
            profile_ids=("closeout-new", "closeout-old"),
        )
        assert mutation["revision"] == 2
        heads_after_mutation = _assignment_heads_bytes(db)
        assert heads_after_mutation != heads_before_mutation

        # Both owner jobs were already admitted when the assignment changed. They
        # finish only under their frozen/durable facts, then this composition stops.
        engine.release.set()
        response.release.set()
        recipe_result = chat_future.result(timeout=10)

    acquisition._executor.shutdown(wait=True)
    assert engine.calls == 1
    assert recipe_result["route_execution_receipt"]["outcome"] == "succeeded"
    kernel_calls_before_restart = 0
    with db._connection() as conn:
        kernel_calls_before_restart = conn.execute(
            "SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchone()[0]
        acquisition_row = conn.execute(
            "SELECT state,receipt_json FROM inference_model_acquisitions WHERE request_id='closeout-download'"
        ).fetchone()
    assert acquisition_row is not None and acquisition_row["state"] == "ready"
    assert "/models/" not in str(acquisition_row["receipt_json"])

    # One fresh production composition, same durable database. It reconstructs
    # receipts and replay effects; it does not resolve the current assignment.
    restarted_db = Database(db_path)
    restarted_broker = _configure(restarted_db)
    restarted_agent = AgentTurnService.compose(restarted_broker)
    restarted_assignments = InferenceAssignmentService(
        restarted_db, tool_capability_foundation=restarted_agent._foundation._foundation
    )
    replay = _set_tool_assignment(
        restarted_assignments,
        command_id="closeout-assignment-mutation",
        expected_revision=1,
        profile_ids=("closeout-new", "closeout-old"),
    )
    assert replay["committed_effect"] == mutation["committed_effect"]
    assert replay["current"]["revision"] == mutation["revision"]
    assert _assignment_heads_bytes(restarted_db) == heads_after_mutation

    turn_id = "turn-recipe_chat_"  # locate the real Recipe-owned durable turn, never synthesize one.
    with restarted_db._connection() as conn:
        row = conn.execute(
            "SELECT turn_id FROM tool_turns WHERE turn_id LIKE ? ORDER BY created_at", (turn_id + "%",)
        ).fetchone()
        after_restart_calls = conn.execute(
            "SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchone()[0]
    assert row is not None
    assert after_restart_calls == kernel_calls_before_restart
    receipt = restarted_agent._foundation.controller.receipt(TOOL_TURN_AUTHORITY, turn_id=str(row["turn_id"]))
    reconstructed = restarted_agent._foundation.controller.reconstruct(TOOL_TURN_AUTHORITY, turn_id=str(row["turn_id"]))
    assert reconstructed["state"] == "result_ready"
    assert receipt["state"] == "result_ready" and receipt["terminal_code"] == "model_answer_ready"
    assert len(receipt["model_steps"]) == 1
    attempts = receipt["model_steps"][0]["model_attempts"]
    assert len(attempts) == 1
    assert attempts[0]["profile_id"] == "closeout-old"
    assert attempts[0]["boundary"] == "local"
    assert attempts[0]["purpose"] == "primary"
    assert attempts[0]["fallback_reason"] == ""
    assert attempts[0]["receipt_sha256"]
    assert receipt["route_plan_id"] and receipt["route_plan_sha256"]
    frozen_plan = restarted_agent._foundation._adoption.plans.get_route_plan(
        ROUTE_PLANNING_AUTHORITY, receipt["route_plan_id"]
    )
    assert [(entry["profile_id"], entry["boundary"]) for entry in frozen_plan["entries"]] == [
        ("closeout-old", "local"), ("closeout-new", "local"),
    ]

    # Unknown dispatch is terminal even with a frozen fallback in the current
    # chain. The real Recipe façade reaches the external engine once; the shared
    # controller must not turn that unknown outcome into a second egress.
    unknown_engine = _UnknownRecipeEngine()
    restarted_broker.inference_runner._engine_factory = lambda _revision, **_kwargs: unknown_engine
    with pytest.raises(ServiceError) as unknown:
        asyncio.run(
            RecipeService(restarted_db, broker=restarted_broker).chat(
                OWNER, recipe.id, question="Was that provider outcome known?"
            )
        )
    assert unknown.value.code == "inference_route_failed"
    with restarted_db._connection() as conn:
        turns = conn.execute(
            "SELECT turn_id FROM tool_turns ORDER BY created_at"
        ).fetchall()
        kernel_calls_after_unknown = conn.execute(
            "SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'"
        ).fetchone()[0]
    assert len(turns) == 2 and unknown_engine.calls == 1
    assert kernel_calls_after_unknown == kernel_calls_before_restart + 1
    unknown_receipt = restarted_agent._foundation.controller.receipt(
        TOOL_TURN_AUTHORITY, turn_id=str(turns[-1]["turn_id"])
    )
    unknown_attempts = unknown_receipt["model_steps"][0]["model_attempts"]
    unknown_route = restarted_broker.inference_adoption_service.controller.get_route_execution_receipt(
        INFERENCE_FALLBACK_AUTHORITY,
        execution_id=unknown_receipt["model_steps"][0]["route_execution_id"],
    )
    # The generic controller owns dispatch-unknown terminality. The ToolTurn
    # receiver therefore remains a durable, non-continuable model boundary, not
    # a second fallback authority.
    assert unknown_receipt["state"] == "model_running"
    assert (unknown_route["state"], unknown_route["disposition"]) == (
        "terminal", "dispatch_outcome_unknown"
    )
    assert unknown_route["considerations"][0]["status"] == "possibly_started"
    assert len(unknown_attempts) == 1
    assert unknown_attempts[0]["profile_id"] == "closeout-new"
    assert unknown_attempts[0]["purpose"] == "primary"
    assert unknown_attempts[0]["disposition"] == "dispatch_outcome_unknown"

    # A restarted library service can only replay its immutable command. It cannot
    # expose a custody path or alter the assignment-head bytes it found on disk.
    replay_response = _BlockingDownloadResponse(payload)
    restarted_acquisition = _acquisition(restarted_db, tmp_path, replay_response, recover=False)
    replayed_download = restarted_acquisition.download(OWNER, download_body)
    restarted_acquisition._executor.shutdown(wait=True)
    assert replayed_download["acquisition"]["id"] == started_download["acquisition"]["id"]
    assert replayed_download["receipt"]["kind"] == "model_acquisition"
    assert "models/" not in json.dumps(replayed_download, sort_keys=True)
    assert _assignment_heads_bytes(restarted_db) == heads_after_mutation

    # Existing hostile-sync law is exercised in this same recovered composition:
    # v2 router-shaped bytes refuse before they can mint authority or egress.
    with pytest.raises(ValidationError) as hostile:
        SyncService(restarted_db, hub_model_name=lambda: "").push(OWNER, {
            "inference_assignments": [{"poison": "must-not-import"}],
        })
    assert hostile.value.code == "sync_hub_local_bucket_forbidden"
    with restarted_db._connection() as conn:
        assert conn.execute("SELECT COUNT(*) FROM kernel_operations WHERE name='inference.invoke'").fetchone()[0] == kernel_calls_after_unknown
