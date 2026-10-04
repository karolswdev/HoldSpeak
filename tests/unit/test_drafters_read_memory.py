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


# ── The meeting summary ──────────────────────────────────────────────

def _summary_rig(tmp_path, monkeypatch):
    """The deferred-admission queue rig, with an engine that records the
    prompt the real builder makes from what the queue hands it."""
    from holdspeak.intel.parsing import _json_only_messages
    from tests.unit.test_meeting_deferred_admission import FakeIntel, _queue_rig

    class PromptIntel(FakeIntel):
        def __init__(self) -> None:
            super().__init__()
            self.prompts: list[str] = []

        def analyze(self, transcript, *, stream=False, memory_context=""):
            self.prompts.append(_json_only_messages(transcript, memory_context)[1]["content"])
            return super().analyze(transcript, stream=stream)

    db, _broker, _engine, _host, _requests = _queue_rig(tmp_path, monkeypatch)
    engine = PromptIntel()
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    return db, engine


def _staged_material(db: Database) -> list[dict]:
    with db._connection() as conn:
        rows = conn.execute(
            "SELECT payload_json FROM inference_adoption_material_snapshots "
            "WHERE capability_id='meeting.deferred_analysis'"
        ).fetchall()
    return [json.loads(row[0]) for row in rows]


def test_meeting_summary_prompt_carries_the_projects_earlier_decision(tmp_path, monkeypatch):
    from holdspeak.intel_queue import process_next_intel_job
    from tests.unit.test_meeting_deferred_admission import _queued_meeting

    db, engine = _summary_rig(tmp_path, monkeypatch)
    project_id, inside = _project_with_decision(db, items=False)
    state = _queued_meeting(db, "m-memory", text="we reviewed the ledger rollout plan")
    _make_service(db)._project_service.associate_meeting(OWNER, project_id, state.id)

    assert process_next_intel_job() is True

    prompt = engine.prompts[0]
    assert "[PROJECT MEMORY]" in prompt and "[END PROJECT MEMORY]" in prompt
    assert "We adopt quorumdb for the Atlas ledger" in prompt
    assert "Borealis" not in prompt
    assert prompt.index("[END PROJECT MEMORY]") < prompt.index("we reviewed the ledger rollout plan")
    # The refs stay on the operation's staged material.
    staged = [m for m in _staged_material(db) if m.get("memory_refs")]
    assert staged and staged[0]["memory_refs"] == [f"desk_decision:{inside}"]
    assert db.meetings.get_meeting(state.id).intel.summary == "The team reviewed the budget."


def test_meeting_summary_on_no_project_is_as_before(tmp_path, monkeypatch):
    from holdspeak.intel.parsing import _json_only_messages
    from holdspeak.intel_queue import process_next_intel_job
    from tests.unit.test_meeting_deferred_admission import _queued_meeting

    db, engine = _summary_rig(tmp_path, monkeypatch)
    _project_with_decision(db, items=False)  # memory exists, on a project
    _queued_meeting(db, "m-plain", text="we reviewed the ledger rollout plan")

    assert process_next_intel_job() is True

    assert "MEMORY" not in engine.prompts[0]
    assert all("memory_refs" not in m and "memory_material" not in m for m in _staged_material(db))
    # No memory: the prompt is the prompt of before, byte for byte.
    assert _json_only_messages("t", "") == _json_only_messages("t")


def test_the_real_engine_sends_the_memory_block(monkeypatch):
    from holdspeak.intel.engine import MeetingIntel

    sent: list[list[dict]] = []
    intel = MeetingIntel.__new__(MeetingIntel)
    intel.temperature, intel.max_tokens = 0.0, 64

    def _text(messages, **_kwargs):
        sent.append(messages)
        return '{"summary": "s", "topics": [], "action_items": []}'

    monkeypatch.setattr(intel, "_chat_completion_text", _text, raising=False)

    result = intel.analyze(
        "Me: hello", memory_context="[PROJECT MEMORY]\n- desk_decision:d1: quorumdb\n[END PROJECT MEMORY]",
    )

    assert result.summary == "s"
    assert "- desk_decision:d1: quorumdb" in sent[0][1]["content"]


def test_meeting_summary_retry_after_memory_changed_still_runs(tmp_path, monkeypatch):
    """A failed attempt, then a new decision on the project, then the retry:
    the changed memory must not wedge the job."""
    from holdspeak.intel_queue import process_next_intel_job
    from tests.unit.test_meeting_deferred_admission import _queued_meeting

    db, engine = _summary_rig(tmp_path, monkeypatch)
    project_id, _inside = _project_with_decision(db, items=False)
    projects = _make_service(db)._project_service
    state = _queued_meeting(db, "m-retry", text="we reviewed the ledger rollout plan")
    projects.associate_meeting(OWNER, project_id, state.id)

    engine.error = "engine asleep"
    process_next_intel_job(retry_base_seconds=0, retry_max_seconds=0)
    later = _decide(db, "Freeze the ledger schema", "The ledger schema is frozen until May.")
    projects.add_resource(OWNER, project_id, f"desk_decision:{later}")
    engine.error = None
    process_next_intel_job(include_scheduled=True)

    refreshed = db.meetings.get_meeting(state.id)
    assert refreshed.intel_status == "ready", refreshed.intel_status
    assert "The ledger schema is frozen until May" in engine.prompts[-1]


# ── The 1:1 brief ────────────────────────────────────────────────────

def _people(tmp_path):
    from holdspeak.people import EncryptedPeopleStore
    from holdspeak.people.keys import FileKeyStore
    from holdspeak.services.people_service import PeopleService

    store = EncryptedPeopleStore(tmp_path / "people.sqlite3", FileKeyStore(tmp_path / "people.key"))
    store.initialize()
    return PeopleService(store)


def test_one_on_one_brief_carries_the_memory_of_the_persons_projects(rig, tmp_path):
    project_id, inside = _project_with_decision(rig, items=False)
    people = _people(tmp_path)
    priya = people.create_relationship(OWNER, {"display_name": "Priya"})["id"]
    people.link_project(OWNER, priya, project_id)

    memory = people.one_on_one_brief(OWNER, priya, db=rig)["memory"]

    assert memory["refs"] == [f"desk_decision:{inside}"]
    assert "quorumdb" in memory["excerpts"][0]["text"]
    assert memory["excerpts"][0]["project_id"] == project_id
    assert "Borealis" not in json.dumps(memory)


def test_one_on_one_brief_memory_is_empty_without_a_project_and_indexes_nothing(rig, tmp_path):
    _project_with_decision(rig, items=False)
    people = _people(tmp_path)
    sam = people.create_relationship(OWNER, {"display_name": "Samwise Quillfeather"})["id"]
    people.create_note(OWNER, sam, {"body": "Quillfeather wants the harbour role."})

    brief = people.one_on_one_brief(OWNER, sam, db=rig)

    assert brief["memory"] == {"excerpts": [], "refs": []}
    assert people.one_on_one_brief(OWNER, sam)["memory"] == {"excerpts": [], "refs": []}
    # Custody: the People store stays out of memory.
    assert rig.memory.search("Quillfeather").hits == []
# ── The wire fixture for the web click test ──────────────────────────

UPDATE_FIXTURE = "tests/fixtures/update_draft_action_citation.json"
_VOLATILE = ("id", "created_at", "updated_at")


def _real_draft_with_an_action_citation(db: Database) -> dict:
    """A draft the real drafter makes over a project whose meeting left one
    owned, open action item: its claim cites ``action_item:<id>``."""
    from datetime import datetime

    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

    svc = _make_service(db)
    project_id = svc._project_service.create_project(OWNER, {"name": "Atlas"})["id"]
    db.meetings.save_meeting(MeetingState(
        id="m-fixture", started_at=datetime(2026, 9, 1, 9, 0), ended_at=datetime(2026, 9, 1, 9, 30),
        title="Ledger sync",
        segments=[TranscriptSegment(text="dana drafts the checklist", speaker="Me",
                                    start_time=0.0, end_time=4.0)],
        intel=IntelSnapshot(
            timestamp=1.0, topics=["ledger"], summary="Ledger launch reviewed.",
            action_items=[ActionItem(id="act-fixture-01", task="Draft the ledger vendor checklist", owner="Dana")],
        ),
    ))
    svc._project_service.associate_meeting(OWNER, project_id, "m-fixture")
    row = json.loads(
        json.dumps(dict(svc.draft_update(OWNER, project_id)), default=str)
        .replace(project_id, "proj-fixture")
    )
    return {key: ("<volatile>" if key in _VOLATILE else value) for key, value in row.items()}


def test_the_web_click_fixture_is_what_the_real_drafter_makes(rig):
    """web/.../UpdatePostureCitationOpens.test.tsx clicks a citation on this
    draft.  The fixture must stay the real drafter's output."""
    from pathlib import Path

    real = _real_draft_with_an_action_citation(rig)
    refs = [ref for claim in json.loads(real["claims_json"]) for ref in claim["refs"]]
    assert "action_item:act-fixture-01" in refs
    fixture = Path(__file__).resolve().parents[2] / UPDATE_FIXTURE
    assert json.loads(fixture.read_text()) == real
