"""Every AI job reads memory through one seam (owner goal 2026-10-04).

The fence: every built-in capability has an explicit memory policy, so a new
AI job forces a decision.  Then, per newly wired job, the prompt the job SENT
(captured at the engine, after the real admission path) carries the MEMORY
block on a hit, nothing on no hit or on a failing read, and never the job's
own source.  Memory is minted through the real producers (the Decide route,
the thought service, the meeting decision table the meeting pipeline writes).
"""
from __future__ import annotations

import asyncio
from typing import Any

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
import holdspeak.inference_memory_policy as policy_module
import holdspeak.services.memory_grounding as memory_grounding
from holdspeak.db import Database, reset_database
from holdspeak.inference_capabilities import builtin_capability_definitions
from holdspeak.inference_memory_policy import (
    DEFAULT_MEMORY_CHARS,
    DEFAULT_MEMORY_EXCERPTS,
    DEFAULT_POLICY,
    MEMORY_POLICIES,
    READERS,
    SCOPES,
    memory_policy,
)
from holdspeak.kernel.runtime import _configure
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.memory_grounding import (
    MEMORY_BLOCK_CHARS,
    MEMORY_MAX_EXCERPTS,
    memory_for,
)
from tests.unit.test_drafters_read_memory import _decide

OWNER = Principal(PrincipalKind.OWNER, "memory-every-job")
WEB_OWNER = Principal(PrincipalKind.OWNER, "owner-session")

# The capabilities the brief names as off.
_MUST_BE_OFF_PREFIXES = ("speech.", "internal.", "apple.")
_MUST_BE_OFF = {
    "memory.embed", "chat.guardrail", "chat.compact", "meeting.auto_title",
    "meeting.bookmark_label", "calendar.snapshot_extract",
    # Measured too slow for the live paths (see the policy row).
    "meeting.live_analysis", "voice.reference_resolve",
}


# ── The fence ─────────────────────────────────────────────────────────

def test_every_builtin_capability_has_an_explicit_memory_policy():
    builtin = {definition.id for definition in builtin_capability_definitions()}
    missing = sorted(builtin - set(MEMORY_POLICIES))
    stale = sorted(set(MEMORY_POLICIES) - builtin)
    assert not missing, f"decide a memory policy for: {missing}"
    assert not stale, f"policy rows for no capability: {stale}"


def test_every_policy_row_is_well_formed_and_within_the_drafter_bounds():
    assert DEFAULT_MEMORY_CHARS == MEMORY_BLOCK_CHARS
    assert DEFAULT_MEMORY_EXCERPTS == MEMORY_MAX_EXCERPTS
    for capability_id, row in MEMORY_POLICIES.items():
        assert row.scope in SCOPES and row.reader in READERS, capability_id
        assert row.why.strip(), capability_id
        assert 0 <= row.block_chars <= DEFAULT_MEMORY_CHARS, capability_id
        assert 0 <= row.max_excerpts <= DEFAULT_MEMORY_EXCERPTS, capability_id
        if row.enabled:
            assert row.block_chars > 0 and row.max_excerpts > 0, capability_id
        else:
            assert row.reader == "none", capability_id


def test_the_named_infrastructure_and_speech_jobs_are_off():
    for capability_id, row in MEMORY_POLICIES.items():
        if capability_id.startswith(_MUST_BE_OFF_PREFIXES) or capability_id in _MUST_BE_OFF:
            assert not row.enabled, capability_id


def test_an_unknown_capability_gets_the_default():
    assert memory_policy("meeting.plugin.some-plugin") is DEFAULT_POLICY
    assert DEFAULT_POLICY.enabled and DEFAULT_POLICY.reader == "memory_for"


# ── memory_for ────────────────────────────────────────────────────────

@pytest.fixture
def rig(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "every_job.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    yield db
    reset_database()


def test_memory_for_reads_on_policy_and_nothing_when_off(rig):
    inside = _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")

    on = memory_for("decision.promotion_draft", rig, query="quorumdb ledger")
    assert f"desk_decision:{inside}" in on.refs
    assert len(on.prompt_block()) <= MEMORY_POLICIES["decision.promotion_draft"].block_chars

    assert not memory_for("speech.rewrite", rig, query="quorumdb ledger")
    assert memory_for("some.future_job", rig, query="quorumdb ledger")  # the default is on


def test_memory_for_gives_empty_memory_when_the_read_raises(rig, monkeypatch):
    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")

    def boom(*_a, **_k):
        raise RuntimeError("memory index gone")

    monkeypatch.setattr(memory_grounding, "memory_context", boom)
    assert not memory_for("decision.promotion_draft", rig, query="quorumdb ledger")


def test_a_policy_switched_off_turns_off_a_grounding_job(rig, monkeypatch):
    """The table is authoritative for the grounding readers too (Ask here)."""
    from holdspeak.services.ask_service import AskService

    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    broker = _configure(rig)
    ask = AskService(rig, broker=broker)
    on, _ = ask._grounding(OWNER, None, "what about quorumdb", capability_id="ask.answer")
    assert "quorumdb" in on

    rows = dict(MEMORY_POLICIES)
    rows["ask.answer"] = policy_module._off("test")
    monkeypatch.setattr(policy_module, "MEMORY_POLICIES", rows)
    off, _ = ask._grounding(OWNER, None, "what about quorumdb", capability_id="ask.answer")
    assert "quorumdb" not in off


# ── Shared rig pieces ─────────────────────────────────────────────────

def _assign(db: Database, capability_id: str, profile: str) -> None:
    from holdspeak.services.inference_assignment_service import InferenceAssignmentService
    from tests.unit.test_phase143_inference_assignments import OWNER as ASSIGNMENT_OWNER, _profile

    _profile(db, profile)
    InferenceAssignmentService(db).set_assignment(ASSIGNMENT_OWNER, {
        "command_id": f"assign-{profile}", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": capability_id},
        "entries": [{"profile_id": profile, "profile_revision": 1}],
    })


class _Engine:
    """The physical-boundary fake: records the prompt the job sent."""

    active_provider = "local"
    active_model = "test-model"

    def __init__(self, output: str) -> None:
        self.output = output
        self.prompts: list[str] = []

    def run_prompt(self, **kwargs: Any) -> str:
        self.prompts.append(str(kwargs.get("user_prompt") or ""))
        return self.output


def _break_memory(monkeypatch) -> None:
    def boom(*_a, **_k):
        raise RuntimeError("memory index gone")

    monkeypatch.setattr(memory_grounding, "hydrate_refs_detailed", boom)


# ── background.cadence_draft ──────────────────────────────────────────

def _cadence_run(db: Database, tmp_path, monkeypatch, *, source_id: str = "a1") -> str:
    from holdspeak.cadence.models import OpenLoop
    from holdspeak.config.integrations import CadenceConfig
    from holdspeak.services.cadence_service import CadenceService
    from tests.unit.test_one_path_spine import _ready_this_machine

    _ready_this_machine(tmp_path, monkeypatch)
    loop = db.cadence.upsert_loop(OpenLoop(
        source_type="meeting_action", source_id=source_id,
        title="Ship the quorumdb ledger watchdog", owner="Karol",
    ))
    _assign(db, "background.cadence_draft", "cadence-profile")
    broker = _configure(db)
    engine = _Engine('{"kind":"create_issue","title":"Watchdog the queue","body_markdown":"body"}')
    broker.inference_runner._engine_factory = lambda _revision, **_: engine
    service = CadenceService(db, CadenceConfig(use_llm=True), kernel=broker)
    detail = asyncio.run(service.get_loop(WEB_OWNER, loop.id))
    assert detail["next_action"]["generated_by"] == "llm", detail["next_action"]
    assert len(engine.prompts) == 1
    return engine.prompts[0]


def _meeting_with_action(db: Database, meeting_id: str, task: str) -> str:
    """A meeting whose intel holds one action item (the meeting pipeline's write)."""
    from datetime import datetime

    from holdspeak.intel.models import ActionItem
    from holdspeak.meeting_session.models import IntelSnapshot, MeetingState, TranscriptSegment

    state = MeetingState(
        id=meeting_id, started_at=datetime(2026, 9, 1, 9), ended_at=datetime(2026, 9, 1, 10),
        title="Ledger sync",
        segments=[TranscriptSegment(text="we talked about the ledger", speaker="Me", start_time=0, end_time=5)],
        intel=IntelSnapshot(timestamp=1.0, topics=[], action_items=[
            ActionItem(id=f"{meeting_id}-a1", task=task, owner="Karol"),
        ], summary="Ledger sync."),
    )
    db.meetings.save_meeting(state)
    return f"{meeting_id}-a1"


def test_cadence_draft_carries_memory_on_a_hit(rig, tmp_path, monkeypatch):
    inside = _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    prompt = _cadence_run(rig, tmp_path, monkeypatch)
    assert "[MEMORY]" in prompt and f"desk_decision:{inside}" in prompt
    assert prompt.rstrip().endswith("Respond with the JSON object only.")  # instructions stay last


def test_cadence_draft_has_no_memory_on_no_hit(rig, tmp_path, monkeypatch):
    _decide(rig, "Repaint Borealis office", "Borealis repaints its harbour office.")
    assert "[MEMORY]" not in _cadence_run(rig, tmp_path, monkeypatch)


def test_cadence_draft_runs_without_memory_when_the_read_raises(rig, tmp_path, monkeypatch):
    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    _break_memory(monkeypatch)
    assert "[MEMORY]" not in _cadence_run(rig, tmp_path, monkeypatch)


def test_cadence_draft_never_reads_its_own_source(rig, tmp_path, monkeypatch):
    own = _meeting_with_action(rig, "m-ledger", "Ship the quorumdb ledger watchdog")
    other = _meeting_with_action(rig, "m-other", "Review the quorumdb ledger backups")
    prompt = _cadence_run(rig, tmp_path, monkeypatch, source_id=own)
    assert f"action_item:{other}" in prompt  # memory did run
    assert f"action_item:{own}" not in prompt


# ── decision.promotion_draft ──────────────────────────────────────────

def _promotion_run(db: Database) -> str:
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    from tests.unit.test_decision_record_service import _accepted_meeting_decision

    with db._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-127", "2026-08-07T00:00:00+00:00", "Records meeting"),
        )
    _accepted_meeting_decision(db, "dec-own")  # text: "Use record-backed decisions."
    _assign(db, "decision.promotion_draft", "decision-profile")
    broker = _configure(db)
    engine = _Engine("Adopt this.")
    broker.inference_runner._engine_factory = lambda _revision, **_: engine
    asyncio.run(
        DecisionLifecycleService(db, kernel=broker).draft_promoted_with_model(OWNER, "dec-own", "note", {})
    )
    assert len(engine.prompts) == 1
    return engine.prompts[0]


def test_promotion_draft_carries_memory_and_never_the_decision_itself(rig):
    inside = _decide(rig, "Record-backed decisions for the ledger", "Every decision is record-backed.")
    prompt = _promotion_run(rig)
    assert "[MEMORY]" in prompt and f"desk_decision:{inside}" in prompt
    assert "decision:dec-own" not in prompt
    assert "meeting:meeting-127" not in prompt


def test_promotion_draft_has_no_memory_on_no_hit(rig):
    _decide(rig, "Repaint Borealis office", "Borealis repaints its harbour office.")
    assert "[MEMORY]" not in _promotion_run(rig)


def test_promotion_draft_runs_without_memory_when_the_read_raises(rig, monkeypatch):
    _decide(rig, "Record-backed decisions for the ledger", "Every decision is record-backed.")
    _break_memory(monkeypatch)
    assert "[MEMORY]" not in _promotion_run(rig)


# ── delivery.pr_review_draft ──────────────────────────────────────────

class _ReviewRig:
    """The real PR-review route and admission, with a fake PR source."""

    def __init__(self, db: Database, tmp_path, monkeypatch, *, diff: str = "diff --git a/x b/x\n+hi") -> None:
        from holdspeak.web.context import WebContext
        from holdspeak.web.routes.delivery_prs import build_delivery_prs_router
        from tests.unit.test_one_path_spine import _ready_this_machine

        _ready_this_machine(tmp_path, monkeypatch)
        _assign(db, "delivery.pr_review_draft", "delivery-profile")
        self.engine = _Engine("Looks fine.")
        # _decide already built the broker; the engine is bound on its one runner.
        _configure(db).inference_runner._engine_factory = lambda _revision, **_: self.engine
        self.diff = diff
        self.linked: list[dict[str, str]] = []
        rig = self

        class _Delivery:
            def action_context(self, source_id, number):
                return {"status": "ok", "row": {
                    "verbs": {"draft_review": {"available": True}},
                    "title": "Move the ledger to quorumdb", "head_ref": "feat/ledger-quorumdb",
                }}

            def review_material(self, source_id, number):
                return {"status": "ok", "diff": rig.diff, "revision": "rev-1",
                        "linked": list(rig.linked), "story_id": ""}

        app = FastAPI()

        @app.middleware("http")
        async def principal(request: Request, call_next):
            request.state.principal = OWNER
            return await call_next(request)

        app.include_router(build_delivery_prs_router(
            WebContext(get_state=lambda: {}, delivery_service=object()), service=_Delivery(),
        ))
        self.client = TestClient(app, raise_server_exceptions=False)

    def post(self):
        return self.client.post("/api/delivery/prs/src/1/draft-review", json={})


def _review_run(db: Database, tmp_path, monkeypatch) -> str:
    rig = _ReviewRig(db, tmp_path, monkeypatch)
    response = rig.post()
    assert response.status_code == 200, response.text
    assert len(rig.engine.prompts) == 1
    return rig.engine.prompts[0]


def test_pr_review_draft_carries_memory_on_a_hit(rig, tmp_path, monkeypatch):
    inside = _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    prompt = _review_run(rig, tmp_path, monkeypatch)
    assert "[MEMORY]" in prompt and f"desk_decision:{inside}" in prompt
    assert "Diff:\ndiff --git" in prompt


def test_pr_review_draft_has_no_memory_on_no_hit(rig, tmp_path, monkeypatch):
    _decide(rig, "Repaint Borealis office", "Borealis repaints its harbour office.")
    assert "[MEMORY]" not in _review_run(rig, tmp_path, monkeypatch)


def test_pr_review_draft_runs_without_memory_when_the_read_raises(rig, tmp_path, monkeypatch):
    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    _break_memory(monkeypatch)
    assert "[MEMORY]" not in _review_run(rig, tmp_path, monkeypatch)


# ── background.rails_summary ──────────────────────────────────────────

def _rails_run(db: Database) -> tuple[str, dict[str, Any]]:
    from holdspeak import rails_observer

    _assign(db, "background.rails_summary", "rails")
    principal = Principal(
        PrincipalKind.SERVICE, "rails-observer",
        frozenset({("rails.observer-batch", 1), ("inference.invoke", 1), ("inference.cancel", 1)}),
        "rails-observer:journal-only",
    )
    broker = _configure(db)
    engine = _Engine("Only the observed facts.")
    broker.inference_runner._engine_factory = lambda _revision, **_: engine
    summarizer = rails_observer.build_profile_summarizer(db=db, broker=broker, principal=principal)
    batch = rails_observer.summarize_batch(
        [{"ts": "t1", "event": "gate_pass", "story": "", "repo": "code",
          "detail": {"subject": "quorumdb ledger"}}],
        summarize_fn=summarizer,
    )
    assert not batch["degraded"], batch
    assert len(engine.prompts) == 1
    return engine.prompts[0], batch


def test_rails_summary_carries_memory_and_keeps_its_replay_identity(rig):
    from holdspeak import rails_observer

    inside = _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    prompt, batch = _rails_run(rig)
    assert "[MEMORY]" in prompt and f"desk_decision:{inside}" in prompt
    # The batch identity hashes the events only, never the memory.
    rendered = rails_observer.format_events_for_model(batch["events"])
    import hashlib
    assert batch["event_batch_sha256"] == "sha256:" + hashlib.sha256(rendered.encode()).hexdigest()
    assert len(prompt) - len(rendered) <= MEMORY_POLICIES["background.rails_summary"].block_chars + 200


def test_rails_summary_has_no_memory_on_no_hit(rig):
    _decide(rig, "Repaint Borealis office", "Borealis repaints its harbour office.")
    assert "[MEMORY]" not in _rails_run(rig)[0]


def test_rails_summary_runs_without_memory_when_the_read_raises(rig, monkeypatch):
    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    _break_memory(monkeypatch)
    assert "[MEMORY]" not in _rails_run(rig)[0]


# ── thought.interview: a Thought never recalls itself ─────────────────

def test_a_thought_never_recalls_its_own_note(rig):
    from holdspeak.services.ask_service import AskService
    from holdspeak.services.refinement_coordinator import RefinementCoordinator
    from holdspeak.services.refinement_thought_service import (
        INBOX_DIRECTORY_ID,
        RefinementThoughtService,
    )

    rig.directories.upsert(directory_id=INBOX_DIRECTORY_ID, name="Inbox")
    broker = _configure(rig)
    other = _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    thought = RefinementThoughtService(rig).create(
        OWNER, request_id="req-thought-1",
        raw_text="Plan the quorumdb ledger migration and its rollback", source={"kind": "typed"},
    )
    own_note = str(thought["working_note"]["id"])
    coordinator = RefinementCoordinator(rig)
    sealed = coordinator._sealed_prompt(str(thought["working_note"]["body_markdown"]))

    without_exclusion = coordinator._routed_payload(sealed, None, [])
    assert f"note:{own_note}" in without_exclusion["user_prompt"]  # the risk is real

    payload = coordinator._routed_payload(sealed, None, coordinator._own_refs(thought))
    assert f"desk_decision:{other}" in payload["user_prompt"]
    assert f"note:{own_note}" not in payload["user_prompt"]

    # Ask builds the same bytes at dispatch from the same arguments.
    envelope, _echo = AskService(rig, broker=broker)._grounding(
        OWNER, None, sealed, capability_id="thought.interview",
        exclude_refs=coordinator._own_refs(thought),
    )
    assert payload["user_prompt"] == sealed + "\n\nGrounding:\n" + envelope


# ── Review round (Astra, PR #830) ─────────────────────────────────────

def _memory_block(prompt: str) -> str:
    """The MEMORY block of a sent prompt; ``""`` when there is none."""
    start = prompt.find("[MEMORY]")
    end = prompt.find("[END MEMORY]")
    return prompt[start:end] if start >= 0 and end > start else ""


def _executions(db: Database, capability_id: str) -> list[Any]:
    with db._connection() as conn:
        return conn.execute(
            """SELECT e.tokens_reserved, e.token_budget, e.terminal_outcome
                 FROM inference_route_executions e
                 JOIN inference_route_plans p ON p.id=e.route_plan_id
                WHERE p.capability_id=?""",
            (capability_id,),
        ).fetchall()


def _full_memory_would_not_fit(db: Database, capability_id: str, full: Any, reserved_output_tokens: int) -> bool:
    """The admitted payload with the WHOLE memory block instead of the fitted one."""
    from holdspeak.services.memory_grounding import admitted_memory_prefix, with_memory

    adoption = _configure(db).inference_adoption_service
    with db._connection() as conn:
        row = conn.execute(
            """SELECT s.operation_id, e.route_plan_id
                 FROM inference_adoption_material_snapshots s,
                      inference_route_executions e
                 JOIN inference_route_plans p ON p.id=e.route_plan_id
                WHERE s.capability_id=? AND p.capability_id=?""",
            (capability_id, capability_id),
        ).fetchone()
    sent = adoption.admitted_payload(row["operation_id"])
    own = sent["user_prompt"][len(admitted_memory_prefix(sent["user_prompt"])):]
    return adoption.payload_room(
        route_plan_id=row["route_plan_id"], capability_id=capability_id,
        operation_id=row["operation_id"], payload={**sent, "user_prompt": with_memory(own, full)},
        reserved_output_tokens=reserved_output_tokens,
    ) < 0


def _long_matching_decisions(db: Database, count: int = 5) -> list[str]:
    body = "We adopt quorumdb for the ledger. " + "The ledger keeps every quorumdb write. " * 20
    return [_decide(db, f"Quorumdb ledger decision {index}", body) for index in range(count)]


def test_memory_never_turns_a_fitting_pr_review_into_a_failing_one(rig, tmp_path, monkeypatch):
    """Astra P1 repro: an 11,915-char diff fits the 16,384-token budget alone;
    five matching notes used to push it to 17,502 tokens and a 500."""
    _long_matching_decisions(rig)
    diff = "diff --git a/x b/x\n" + ("+" + "x" * 99 + "\n") * 119
    diff = diff[:11915]
    review = _ReviewRig(rig, tmp_path, monkeypatch, diff=diff)

    response = review.post()

    assert response.status_code == 200, response.text
    assert len(review.engine.prompts) == 1
    (execution,) = _executions(rig, "delivery.pr_review_draft")
    assert execution["terminal_outcome"] == "succeeded"
    assert execution["tokens_reserved"] <= execution["token_budget"] == 16384
    full = memory_for("delivery.pr_review_draft", rig, query="Move the ledger to quorumdb feat/ledger-quorumdb")
    sent = _memory_block(review.engine.prompts[0])
    assert full.excerpts and sent.count("\n- ") < len(full.excerpts)  # the block was cut to fit
    assert _full_memory_would_not_fit(rig, "delivery.pr_review_draft", full, 1800)


def test_memory_never_turns_a_fitting_rails_batch_into_a_failing_one(rig):
    """The same law for a second job: a rails batch close to its budget."""
    from holdspeak import rails_observer

    _long_matching_decisions(rig)
    _assign(rig, "background.rails_summary", "rails")
    principal = Principal(
        PrincipalKind.SERVICE, "rails-observer",
        frozenset({("rails.observer-batch", 1), ("inference.invoke", 1), ("inference.cancel", 1)}),
        "rails-observer:journal-only",
    )
    broker = _configure(rig)
    engine = _Engine("Only the observed facts.")
    broker.inference_runner._engine_factory = lambda _revision, **_: engine
    filler = "quorumdb ledger " + "y" * 230
    events = [
        {"ts": f"t{index}", "event": "gate_pass", "story": "", "repo": "code", "detail": {"subject": filler}}
        for index in range(54)
    ]
    batch = rails_observer.summarize_batch(
        events,
        summarize_fn=rails_observer.build_profile_summarizer(db=rig, broker=broker, principal=principal),
    )

    assert not batch["degraded"], batch
    assert len(engine.prompts) == 1
    (execution,) = _executions(rig, "background.rails_summary")
    assert execution["tokens_reserved"] <= execution["token_budget"] == 16384
    full = memory_for("background.rails_summary", rig, query=rails_observer.format_events_for_model(events)[:2000])
    assert full.excerpts and _memory_block(engine.prompts[0]).count("\n- ") < len(full.excerpts)
    assert _full_memory_would_not_fit(rig, "background.rails_summary", full, 220)


def test_a_replay_rebuilds_the_reviews_own_material(rig, tmp_path, monkeypatch):
    """Astra P2 repro: the linked story changed between two reviews of the same
    commit and diff.  A replay may reuse only its MEMORY block, so the second
    review never returns the first review's stale artifact as a success."""
    _decide(rig, "Adopt quorumdb for the ledger", "We adopt quorumdb for the ledger.")
    review = _ReviewRig(rig, tmp_path, monkeypatch)
    review.linked = [{"ref": "file:story-02-ledger.md", "text": "Story 02: move the ledger."}]
    first = review.post()
    assert first.status_code == 200, first.text

    # The same request again is an exact replay: one model call, one artifact.
    again = review.post()
    assert again.status_code == 200 and again.json()["artifact_id"] == first.json()["artifact_id"]
    assert len(review.engine.prompts) == 1

    review.linked = [{"ref": "file:story-02-ledger.md", "text": "Story 02: move the ledger. EDITED."}]
    second = review.post()
    stale = second.status_code == 200 and second.json().get("artifact_id") == first.json()["artifact_id"]
    assert not stale, "a changed story returned the first review as a success"
    # What main does with a changed story under the same commit and diff (the
    # request identity leaves the story out): the second review fails, and
    # nothing reaches the model.  Memory does not change that.
    assert second.status_code == 500 and len(review.engine.prompts) == 1


def test_cadence_memory_never_carries_its_source_under_the_meeting(rig, tmp_path, monkeypatch):
    """Astra P2 repro: the parent meeting's digest repeats the action item."""
    own = _meeting_with_action(rig, "m-ledger", "Ship the quorumdb ledger watchdog")
    other = _meeting_with_action(rig, "m-other", "Review the quorumdb ledger backups")
    prompt = _cadence_run(rig, tmp_path, monkeypatch, source_id=own)
    block = _memory_block(prompt)
    assert f"action_item:{other}" in block  # memory did run
    assert "meeting:m-ledger" not in block
    assert "ship the quorumdb ledger watchdog" not in block.casefold()


def test_promotion_memory_never_carries_the_decision_under_another_name(rig):
    """The decision's own words under other refs: a decision record minted
    from it, and the accepted ADR its real promotion minted.  Neither ref is
    the decision's or its meeting's, so only the job's own-text exclusion
    (``exclude_texts=[decision.text]``) keeps them out.  Without it the ADR
    is in the block: this fails."""
    from holdspeak.services.decision_lifecycle_service import DecisionLifecycleService
    from holdspeak.services.decision_record_service import DecisionRecordService
    from tests.unit.test_decision_record_service import _accepted_meeting_decision

    with rig._connection() as conn:
        conn.execute(
            "INSERT INTO meetings (id, started_at, title) VALUES (?, ?, ?)",
            ("meeting-127", "2026-08-07T00:00:00+00:00", "Records meeting"),
        )
    _accepted_meeting_decision(rig, "dec-own")
    record = DecisionRecordService(rig).create_from_meeting(None, "dec-own")
    inside = _decide(rig, "Record-backed decisions for the ledger", "Every decision is record-backed.")
    _assign(rig, "decision.promotion_draft", "decision-profile")
    broker = _configure(rig)
    engine = _Engine("Adopt this.")
    broker.inference_runner._engine_factory = lambda _revision, **_: engine
    lifecycle = DecisionLifecycleService(rig, kernel=broker)

    # The real producer: an accepted ADR artifact that repeats the decision.
    adr = lifecycle.promote(OWNER, "dec-own", "adr")["artifact"]
    found = rig.memory.search("record-backed decisions", kinds="artifact")
    assert [hit.source_ref for hit in found.hits] == [f"artifact:{adr['id']}"]

    asyncio.run(lifecycle.draft_promoted_with_model(OWNER, "dec-own", "note", {}))
    block = _memory_block(engine.prompts[0])
    assert f"desk_decision:{inside}" in block  # memory did run
    assert str(record["id"]) not in block
    assert str(adr["id"]) not in block
    assert "use record-backed decisions" not in block.casefold()
