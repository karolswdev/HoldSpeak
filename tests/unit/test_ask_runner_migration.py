"""HS-131-03 Ask runner migration and mechanical bypass fence."""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path

import pytest

from holdspeak.db import Database
from holdspeak.kernel.ask_projection import materialize
from holdspeak.kernel.model import KernelRefused
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.ask_service import ASK_PAYLOAD_SCHEMA_VERSION, ASK_SERVICE_CONTRACT, ASK_SERVICE_SCHEMA_VERSION, AskService

OWNER = Principal(PrincipalKind.OWNER, "owner")


class Engine:
    active_provider = "test-provider"
    active_model = "test-model"

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def run_prompt(self, **kwargs):
        self.calls.append(kwargs)
        return "runner answer"


@pytest.fixture
def rig(tmp_path: Path, monkeypatch):
    db = Database(tmp_path / "ask-runner.db")
    monkeypatch.setattr("holdspeak.inference_targets._this_machine_readiness", lambda: ("ready", ""))
    engine = Engine()
    # HS-131-13: an admitted `this_machine` child builds `MeetingIntel` from its
    # FROZEN revision, so the same double is installed on the engine class too.
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **_kw: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    broker = _configure(db)
    return db, broker, engine


def test_ask_uses_versioned_contract_hash_runner_and_staged_projection(rig):
    db, broker, engine = rig
    service = AskService(db, broker=broker)
    before_artifacts = len(db.plugins.list_run_artifacts())
    result = asyncio.run(service.ask(OWNER, "What changed?", lens="Brief"))
    assert result["output"] == "runner answer"
    assert result["provider"] == "test-provider"
    assert len(engine.calls) == 1
    with db._connection() as conn:
        stage = conn.execute("SELECT * FROM kernel_projection_stages").fetchone()
        ask = conn.execute("SELECT * FROM ask_results").fetchone()
        operation = conn.execute("SELECT * FROM kernel_operations WHERE operation_id=?", (stage["operation_id"],)).fetchone()
        receipt = conn.execute("SELECT * FROM kernel_receipts WHERE operation_id=?", (stage["operation_id"],)).fetchone()
    assert stage["state"] == "PUBLISHED"
    assert receipt["outcome"] == "succeeded"
    assert receipt["result_ref"] == stage["result_ref"]
    assert ask["projection_stage_id"] == stage["stage_id"]
    assert result["invocation_id"] == stage["invocation_id"]
    assert operation["native_id"] == stage["invocation_id"]
    assert ASK_SERVICE_CONTRACT == "holdspeak.ask"
    assert ASK_SERVICE_SCHEMA_VERSION == "1"
    assert ASK_PAYLOAD_SCHEMA_VERSION == 1
    assert len(db.plugins.list_run_artifacts()) == before_artifacts


def test_profile_ask_persists_revision_before_claim_without_preseed(rig, monkeypatch):
    db, broker, engine = rig
    with db._connection() as conn:
        before_revisions = conn.execute("SELECT COUNT(*) FROM deployment_revisions").fetchone()[0]
    db.profiles.upsert(profile_id="profile", name="Profile", kind="openAICompatible", base_url="http://profile", model="model")
    # Admission, codec authorization, claim, and runner revision lookup all use
    # real database reads; only the final provider adapter is fake.
    #
    # HS-131-13: through `monkeypatch`, not a bare module assignment. The bare
    # form leaked this stub into every LATER test in the process, so any suite
    # that legitimately builds a profile-shaped engine silently received Ask's
    # fake instead — an ordering landmine that only fires in a combined run.
    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile", lambda **_: engine
    )
    result = asyncio.run(AskService(db, broker=broker).ask(OWNER, "profile", inference_target_id="profile"))
    assert result["output"] == "runner answer"
    with db._connection() as conn:
        # Startup may lawfully create the migrated local speech deployment;
        # this Ask still creates exactly its own frozen profile revision.
        assert conn.execute("SELECT COUNT(*) FROM deployment_revisions").fetchone()[0] == before_revisions + 1
        assert conn.execute("SELECT outcome FROM kernel_receipts WHERE operation_id=?", (result["operation_id"],)).fetchone()[0] == "succeeded"


def test_ask_service_ast_fence_and_ask_materializer_forged_permit(rig):
    db, broker, _ = rig
    source = Path(__file__).parents[2] / "holdspeak" / "services" / "ask_service.py"
    tree = ast.parse(source.read_text())
    ask = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "AskService")
    method = next(node for node in ask.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "ask")
    calls = {node.func.attr for node in ast.walk(method) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
    imports = {alias.name for node in ast.walk(method) if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    assert not ({"run_prompt", "build_intel_for_target", "build_intel_for_revision", "record_artifact"} & calls)
    assert "RunLifecycle" not in imports
    with db._connection() as conn:
        with pytest.raises(KernelRefused, match="projection_publication_permit_invalid"):
            materialize(conn, object(), object())
