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
    bounded = memory_context(rig, project_id=project_id, excerpt_chars=80)
    assert bounded and all(len(e.line()) <= 80 for e in bounded.excerpts)
    held = memory_context(
        rig, project_id=project_id, exclude_refs=[f"desk_decision:{inside}"],
    )
    assert f"desk_decision:{inside}" not in held.refs  # the drafter already holds it


def test_a_huge_title_cannot_grow_the_block(rig):
    """Astra #768 finding 3: only the text was capped; a long decision title
    made a 22,648-character prompt.  The whole rendered excerpt and the whole
    block are bounded."""
    from holdspeak.services.memory_grounding import (
        MEMORY_BLOCK_CHARS,
        MEMORY_EXCERPT_CHARS,
    )

    svc = _make_service(rig)
    project_id = svc._project_service.create_project(OWNER, {"name": "Atlas"})["id"]
    for index in range(12):
        huge = _decide(rig, f"Ledger {index} " + "very long title " * 1500, "Short body.")
        svc._project_service.add_resource(OWNER, project_id, f"desk_decision:{huge}")

    memory = memory_context(rig, project_id=project_id, query="ledger")

    assert memory
    assert all(len(e.line()) <= MEMORY_EXCERPT_CHARS for e in memory.excerpts)
    assert len(memory.prompt_block("PROJECT MEMORY")) <= MEMORY_BLOCK_CHARS
    assert sum(len(t) for t in memory.texts.values()) <= MEMORY_BLOCK_CHARS
    small = memory_context(rig, project_id=project_id, query="ledger", block_chars=900)
    assert small and len(small.prompt_block("PROJECT MEMORY")) <= 900


def test_every_ref_the_helper_returns_is_one_the_desk_opens(rig):
    """Astra #768 finding 1.  The kinds are fenced against the real opener in
    web/src/desk/__tests__/memoryRefsOpen.test.ts; here: real mixed memory
    gives only those kinds, under the Desk's names."""
    from datetime import datetime

    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment
    from holdspeak.services.memory_grounding import DESK_REF_KINDS

    project_id, inside = _project_with_decision(rig)  # desk decision + project items
    projects = _make_service(rig)._project_service
    rig.meetings.save_meeting(MeetingState(
        id="m-ledger", started_at=datetime(2026, 9, 1, 9, 0), ended_at=datetime(2026, 9, 1, 9, 30),
        title="Ledger sync",
        segments=[TranscriptSegment(text="the ledger launch needs a vendor review", speaker="Me",
                                    start_time=0.0, end_time=4.0)],
        intel=IntelSnapshot(
            timestamp=1.0, topics=["ledger"], summary="Ledger launch reviewed.",
            action_items=[ActionItem(task="Draft the ledger vendor checklist", owner="Dana")],
        ),
    ))
    projects.associate_meeting(OWNER, project_id, "m-ledger")

    memory = memory_context(
        rig, project_id=project_id, query="ledger launch vendor checklist backend",
    )

    kinds = {e.kind for e in memory.excerpts}
    assert kinds <= set(DESK_REF_KINDS), kinds
    assert {"desk_decision", "meeting", "action_item"} <= kinds, memory.refs
    assert f"desk_decision:{inside}" in memory.refs
    assert all(ref.split(":", 1)[0] in DESK_REF_KINDS for ref in memory.refs)
    assert not any(ref.startswith(("action:", "project_item:", "transcript:")) for ref in memory.refs)


def test_exclusions_apply_before_the_selection_limit(rig):
    """Astra #768 finding 2: 17 meetings the drafter already holds filled the
    16 selected sources, and the one older relevant transcript never arrived."""
    from datetime import datetime, timedelta

    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

    svc = _make_service(rig)
    projects = svc._project_service
    project_id = projects.create_project(OWNER, {"name": "Atlas"})["id"]
    start = datetime(2026, 9, 1, 9, 0)

    def meeting(meeting_id: str, when: datetime, text: str, summary: str | None) -> None:
        rig.meetings.save_meeting(MeetingState(
            id=meeting_id, started_at=when, ended_at=when + timedelta(minutes=30),
            title=f"Atlas ledger sync {meeting_id}",
            segments=[TranscriptSegment(text=text, speaker="Me", start_time=0.0, end_time=4.0)],
            intel=IntelSnapshot(timestamp=1.0, topics=["ledger"], summary=summary, action_items=[])
            if summary else None,
        ))
        projects.associate_meeting(OWNER, project_id, meeting_id)

    # The older, relevant transcript: no summary, so no drafter inventory holds it.
    meeting("m-old", start - timedelta(days=30),
            "the atlas ledger cutover rehearsal failed on the quorumdb replica", None)
    held = []
    for index in range(17):
        meeting(f"m-{index:02d}", start + timedelta(days=index),
                "atlas ledger status sync", f"Atlas ledger status sync {index}.")
        held.append(f"meeting:m-{index:02d}")

    memory = memory_context(
        rig, project_id=project_id, query="Atlas ledger status sync", exclude_refs=held,
    )
    assert "meeting:m-old" in memory.refs, memory.refs

    # And through the drafter: the older transcript reaches the prompt.
    det, draft, runner = _model_draft(rig, project_id)
    inventory = {ref for c in json.loads(det["claims_json"]) for ref in c["refs"]}
    assert set(held) <= inventory and "meeting:m-old" not in inventory
    prompt = runner.invoke_calls[0].payload["user_prompt"]
    assert "cutover rehearsal failed on the quorumdb replica" in prompt
    assert "meeting:m-old" in json.loads(draft["source_manifest_json"])["memory_refs"]


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
