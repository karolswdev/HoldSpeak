"""The drafters read memory (inventory C, gap 2).

Before this, nothing that drafts read memory.  Each test mints data through
the real producers (the Decide route, the project service), runs the drafter
with the recorded-runner the drafter's own tests use, and asserts on the
prompt the drafter SENT and on the refs it recorded.
"""
from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.db import Database, reset_database
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.memory_grounding import memory_context
from holdspeak.services.project_update_service import Claim
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_decisions_router, build_primitives_router
from tests.unit.test_update_drafter import (
    _good_model_output,
    _make_model_service,
    _make_service,
    _seed_items,
)

OWNER = Principal(PrincipalKind.OWNER, "memory-drafter-test")


@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "memory_drafters.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    yield db
    reset_database()


def _client(db: Database) -> TestClient:
    app = FastAPI()

    @app.middleware("http")
    async def owner(request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_decisions_router(None))
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    return TestClient(app, raise_server_exceptions=False)


def _decide(db: Database, title: str, decision: str) -> str:
    """Mint a decision through the Decide route (POST /api/decisions)."""
    created = _client(db).post("/api/decisions", json={
        "title": title, "status": "accepted", "decision_markdown": decision,
    })
    assert created.status_code == 201, created.text
    return str(created.json()["decision"]["id"])


def _project_with_decision(db: Database, *, items: bool = True) -> tuple[str, str]:
    """A project that holds one earlier decision; one more decision outside it."""
    svc = _make_service(db)
    project_id = svc._project_service.create_project(OWNER, {"name": "Atlas"})["id"]
    if items:
        _seed_items(db, project_id)
    inside = _decide(
        db, "Adopt quorumdb for the ledger",
        "We adopt quorumdb for the Atlas ledger. Postgres stays for reports.",
    )
    svc._project_service.add_resource(OWNER, project_id, f"desk_decision:{inside}")
    _decide(db, "Move the Borealis office", "Borealis moves to the harbour site.")
    return project_id, inside


# ── The shared helper ────────────────────────────────────────────────

def test_helper_returns_project_memory_with_refs_and_stays_in_scope(rig):
    project_id, inside = _project_with_decision(rig)

    memory = memory_context(rig, project_id=project_id, query="weekly update")

    assert f"desk_decision:{inside}" in memory.refs
    block = memory.prompt_block("PROJECT MEMORY")
    assert block.startswith("[PROJECT MEMORY]") and block.endswith("[END PROJECT MEMORY]")
    assert "quorumdb" in block
    assert "Borealis" not in block  # another project's decision stays out


def test_helper_is_bounded_and_empty_without_scope(rig):
    project_id, inside = _project_with_decision(rig)

    assert not memory_context(rig)  # no project, no query: nothing
    assert memory_context(rig).prompt_block() == ""
    bounded = memory_context(rig, project_id=project_id, excerpt_chars=20)
    assert all(len(e.text) <= 20 + len(" [cut]") for e in bounded.excerpts)
    held = memory_context(
        rig, project_id=project_id, exclude_refs=[f"desk_decision:{inside}"],
    )
    assert f"desk_decision:{inside}" not in held.refs  # the drafter already holds it


# ── The project update drafter ───────────────────────────────────────

def _model_draft(db: Database, project_id: str):
    det = _make_service(db).draft_update(OWNER, project_id)
    claims = [Claim(**c) for c in json.loads(det["claims_json"])]
    svc, runner = _make_model_service(db, runner_output=_good_model_output(claims))
    return det, svc.draft_update(OWNER, project_id, generator="model"), runner


def test_update_draft_prompt_carries_the_earlier_decision_and_keeps_its_ref(rig):
    project_id, inside = _project_with_decision(rig)

    _det, draft, runner = _model_draft(rig, project_id)

    assert draft["generator"].startswith("model:")
    prompt = runner.invoke_calls[0].payload["user_prompt"]
    assert "[PROJECT MEMORY]" in prompt and "[END PROJECT MEMORY]" in prompt
    assert "We adopt quorumdb for the Atlas ledger" in prompt
    assert f"desk_decision:{inside}" in prompt
    assert "Borealis" not in prompt
    manifest = json.loads(draft["source_manifest_json"])
    assert manifest["memory_refs"] == [f"desk_decision:{inside}"]


def test_update_draft_may_cite_a_memory_ref(rig):
    project_id, inside = _project_with_decision(rig)
    ref = f"desk_decision:{inside}"
    output = json.dumps({"sections": [{"key": "decisions", "sentences": [
        {"text": "The ledger moves to quorumdb.", "cited_refs": [ref]},
    ]}]})
    svc, _runner = _make_model_service(rig, runner_output=output)

    draft = svc.draft_update(OWNER, project_id, generator="model")

    cited = [c for c in json.loads(draft["claims_json"]) if ref in c["refs"]]
    assert cited
    assert cited[0]["support"] == "source_linked"  # linked, never "supported"


def test_update_draft_without_memory_or_engine_is_as_before(rig):
    svc = _make_service(rig)
    project_id = svc._project_service.create_project(OWNER, {"name": "Bare"})["id"]
    _seed_items(rig, project_id)

    det, draft, runner = _model_draft(rig, project_id)

    prompt = runner.invoke_calls[0].payload["user_prompt"]
    assert "MEMORY" not in prompt  # no hits: the prompt of before
    assert "memory_refs" not in json.loads(draft["source_manifest_json"])
    assert draft["source_manifest_json"] == det["source_manifest_json"]

    # No engine: the deterministic draft reads no memory and records none.
    with_memory, _inside = _project_with_decision(rig, items=False)
    plain = _make_service(rig).draft_update(OWNER, with_memory)
    assert "memory_refs" not in json.loads(plain["source_manifest_json"])
    assert "quorumdb" not in plain["body_md"]


# ── The Prep brief ───────────────────────────────────────────────────

def _prep_service(db: Database, runner):
    from holdspeak.services.preparation_brief_service import (
        PREPARATION_BRIEF_CAPABILITY,
        PreparationBriefService,
    )
    from tests.unit.test_update_drafter import _MockBroker, _seed_assignment

    _seed_assignment(db, PREPARATION_BRIEF_CAPABILITY)
    return PreparationBriefService(
        db, project_service=_make_service(db)._project_service,
        broker=_MockBroker(db, runner),
    )


def test_prep_prompt_carries_the_earlier_decision_and_keeps_its_ref(rig):
    from tests.unit.test_update_drafter import _MockRunner

    project_id, inside = _project_with_decision(rig)
    ref = f"desk_decision:{inside}"
    runner = _MockRunner(output=json.dumps({
        "priorities": [{"text": "Confirm quorumdb for the ledger", "cited_refs": [ref]}],
        "questions": [], "obligations": [],
    }))

    brief = _prep_service(rig, runner).prepare(
        OWNER, project_id, "ledger review with the team", generator="model",
    )

    prompt = runner.invoke_calls[0].payload["user_prompt"]
    assert "[PROJECT MEMORY]" in prompt and "[END PROJECT MEMORY]" in prompt
    assert "We adopt quorumdb for the Atlas ledger" in prompt
    assert "Borealis" not in prompt
    assert brief["manifest"]["memory_refs"] == [ref]
    cited = [c for c in json.loads(brief["claims_json"]) if ref in c["refs"]]
    assert cited and cited[0]["support"] == "source_linked"


def test_prep_without_memory_is_as_before(rig):
    from tests.unit.test_update_drafter import _MockRunner

    svc = _make_service(rig)
    project_id = svc._project_service.create_project(OWNER, {"name": "Bare"})["id"]
    runner = _MockRunner(output=json.dumps(
        {"priorities": [], "questions": [], "obligations": []}))

    brief = _prep_service(rig, runner).prepare(
        OWNER, project_id, "first sync", generator="model",
    )

    assert "MEMORY" not in runner.invoke_calls[0].payload["user_prompt"]
    assert "memory_refs" not in brief["manifest"]
    # No engine: the deterministic brief reads no memory.
    with_memory, _inside = _project_with_decision(rig, items=False)
    plain = _prep_service(rig, _MockRunner(output="{}")).prepare(
        OWNER, with_memory, "ledger review", generator="deterministic",
    )
    assert "memory_refs" not in plain["manifest"]
