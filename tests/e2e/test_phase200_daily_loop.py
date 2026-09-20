"""HS-200-16 -- the two-working-day daily loop, end to end on glass.

The MACHINE half of the story.  One Project carries useful work across a
day boundary, driven through the product's NORMAL CONTROLS in a real
browser against a REAL booted hub on an isolated HOME with its own
temporary database (R16-2: the rig writes nothing the owner can see).
The named historical-proposal seeding step is fixture setup, not an owner
control; the surrounding summary and continuity steps use the real controls.

  DAY 1 (hub #1, owner claim held so the intel drainer runs)
    S1 prepare   -- 11's preparation brief: the Room's `Prepare a brief`
                    well, a purpose by hand, the coverage ledger, `Keep`.
    S2 capture   -- 12's path: a transcript IMPORTED with a DAY-1
                    `started_at_ms`, linked to the Room, and `Run
                    intelligence` through the current ANALYSIS-ONLY route.
                    The summary is proved with no plugin calls and no
                    proposals; a separately labelled HISTORICAL FIXTURE then
                    exercises the retained review/day-2 chain through the real
                    plugins, artifact store and bridge.
    S3 review    -- the Review wing: one decision and one commitment from the
                    HISTORICAL FIXTURE are confirmed through the face's own
                    `Confirm`.
    S4 attention -- 15's arrival: the commitment is a real attention row.

  THE DAY BOUNDARY
    Hub #1 is stopped and a SECOND hub boots on the SAME HOME and the
    SAME database file -- story 13's own seam
    (`test_hs200_continuity_glass.py::test_chain_survives_a_hub_restart`,
    AC5 "the chain survives a restart and a later preparation session").
    The product exposes NO clock-injection seam; the earlier working day
    is real, not simulated: the meeting is imported with a day-1
    `started_at_ms` through the product's own import control, and the
    faces date its records from that meeting
    (`holdspeak/services/recall_service.py:249-251` -- the DEC token is
    "the source meeting's day, not the day the record row was written").
    Nothing in this rig mutates a timestamp behind a face's back.

  DAY 2 (hub #2 on the same database)
    S5 recall    -- 13's Desk memory face: the current decision comes
                    back FIRST with its rationale and its source, and its
                    DEC/MTG tokens read DAY 1, not today.  `Carry into
                    brief`.
    S6 people    -- 14's Room PEOPLE section: the person carries the open
                    commitment made yesterday.
    S7 complete  -- the commitment is completed by EXPLICIT acts through
                    the recall face (`Set a date`, then `Mark done`).
    S8 carry     -- 14 again (the person no longer owes it) and 11's
                    prepare face on day 2, whose `CARRIED FORWARD` ledger
                    names yesterday's decision.

R16-1: no live model.  The brief's drafting route is a controlled
OpenAI-compatible adapter on 127.0.0.1 (the HS-200-11 `FakeLLM` probe
pattern). The current summary route runs against a scripted engine
(`ScriptedIntel`) and deliberately does not call the proposal plugins.
Only the summary words are canned; the kernel, the wire, the receipts and
every face are the product's own. The two proposals used to retain the
downstream day-2 assertions are an explicitly marked HISTORICAL FIXTURE:
real `decision_capture` and `action_owner_enforcer` calls on the imported
transcript, their actual outputs recorded as artifacts, and the real bridge.
These fixture rows are not summary output.
The current first-use summary path does not create the decision or
commitment that day 2 carries. No current owner creation path is proven by
this rig.

R16-5: this is the fixture-proven leg ONLY.  The owner's attended leg
("the user completes the path through normal controls without
implementation guidance") is NOT performed here and is not claimed.  The
owner ACCEPTED it by ruling on 2026-09-19 ("all walks may be considered
as passed"); accepted is not observed, and nothing in this rig or its
record may be read as a human having walked the path.
Everything measured lands in
``assets/story-16-shots/loop-facts.json`` (+ a Markdown twin), which
keeps fixture-proven results, live-model results and the owner's
usefulness judgment in three separate places.

Shots (1440 and 393 at every station) land in
``assets/story-16-shots/`` ONLY with ``HOLDSPEAK_WRITE_SHOTS=1``: they
are tracked evidence and a plain suite run never rewrites them (the
388-PNG scar).
"""
from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from .glass_infra import (
    REPO,
    _api,
    _assert_clean,
    _boot,
    _ensure_build,
    _normal_chair,
    _settle,
)

pytest.importorskip("playwright.sync_api", reason="The daily-loop walk needs Playwright")

SHOTS = REPO / "pm/roadmap/holdspeak/phase-200-the-working-practice/assets/story-16-shots"
WRITE_SHOTS = os.environ.get("HOLDSPEAK_WRITE_SHOTS") == "1"

TOKEN = "hs200-16-loop"
WIDE, NARROW = 1440, 393

PROJECT_NAME = "Q4 Platform"
PURPOSE_D1 = "Architecture review, cut-over sequencing"
PURPOSE_D2 = "Day two: the cut-over decision and what it still owes"

DECISION_TEXT = "Rollback runbook is rehearsed on the read replica first"
DECISION_WHY = "The replica absorbs the first cut-over without touching writes"
COMMITMENT_TEXT = "Draft the rollback runbook"
OWNER_HINT = "Marek"
PERSON_NAME = "Marek Kubiak"
RECALL_QUERY = "rollback runbook"

DEC_PLUGIN = "decision_capture"
ACT_PLUGIN = "action_owner_enforcer"

#: Day 1 is a real earlier calendar day: the meeting is imported with this
#: start through the product's own `started_at_ms` import control.
DAY1_START = (datetime.now() - timedelta(days=1)).replace(
    hour=11, minute=0, second=0, microsecond=0,
)

TRANSCRIPT_SRT = """1
00:00:00,000 --> 00:02:00,000
Karol: Let's start with the cut-over sequencing for the payments platform.

2
00:18:00,000 --> 00:21:00,000
Priya: Rollback runbook is rehearsed on the read replica first.

3
00:31:00,000 --> 00:33:00,000
Marek: I'll draft the rollback runbook before the freeze.
"""

DECISIONS_JSON = json.dumps({
    "decisions": [
        {"decision": DECISION_TEXT, "rationale": DECISION_WHY, "source_timestamp": 1100.0},
    ],
    "open_questions": [],
})
ACTIONS_JSON = json.dumps({
    "action_items": [
        {"task": COMMITMENT_TEXT, "owner": OWNER_HINT, "due": None},
    ],
})

pytestmark = [pytest.mark.e2e, pytest.mark.requires_meeting]


# ── the one composition root (R16-6) ─────────────────────────────────


def _db() -> Any:
    """The database of the process's ONE composition root (HS-200-45).

    Never ``get_database()``: inside a booted hub the root holds the live
    handle every route writes through, and that is the handle this rig
    must read.
    """
    from holdspeak.runtime import composition

    return composition.current().db


# ── the two controlled adapters (R16-1: no live model) ───────────────


def _scripted_engine() -> Any:
    """The meeting extractors' provider seam, scripted (12's pattern)."""
    from tests.unit.test_meeting_deferred_admission import FakeIntel

    class ScriptedIntel(FakeIntel):
        def __init__(self) -> None:
            super().__init__()
            self.plugin_calls: list[str] = []
            # `FakeIntel` ships a default analysis ("Send the deck") that
            # otherwise lands on the arrival as a sixth attention row the
            # walk never asked for.  The extractors below are the only
            # scripted content this rig admits.
            from holdspeak.intel import IntelResult

            self.result = IntelResult(
                topics=[], action_items=[],
                summary="The cut-over plan has one recorded decision and one open commitment.",
                raw_response="{}",
            )

        def _chat_completion_text(self, messages: Any, *, temperature: float, max_tokens: int) -> str:
            system = str(messages[0].get("content") or "") if messages else ""
            plugin = DEC_PLUGIN if "decisions and open questions" in system else ACT_PLUGIN
            self.plugin_calls.append(plugin)
            return DECISIONS_JSON if plugin == DEC_PLUGIN else ACTIONS_JSON

    return ScriptedIntel()


def _wire_provider(monkeypatch: pytest.MonkeyPatch, engine: Any) -> None:
    """Only the provider seam is replaced; the queue, executor, plugin host,
    bridge and routes are the product's own."""
    from tests.unit.test_meeting_deferred_admission import (
        _Route,
        _assign_deferred_queue_routes,
    )

    _assign_deferred_queue_routes(_db())
    monkeypatch.setattr("holdspeak.intel.engine.MeetingIntel", lambda **kwargs: engine)
    monkeypatch.setattr("holdspeak.intel.providers._configured_engine", lambda: engine)
    monkeypatch.setattr(
        "holdspeak.plugins.router.preview_route_from_transcript",
        lambda **kwargs: _Route((DEC_PLUGIN, ACT_PLUGIN)),
    )


def _brief_reply(body: str) -> str:
    """The brief drafter's answer, cited to the REAL refs the prompt carried.

    One priority cites the GitHub source the Room actually read; one
    question cites nothing (so the face draws a real UNSUPPORTED claim).
    """
    import re

    prompt = json.loads(body).get("messages", [{}])[-1].get("content", "") if body.startswith("{") else body
    refs = re.findall(r"(decision_record:[A-Za-z0-9_:\-]+|source:[A-Za-z0-9_\-]+)", prompt)
    gh = next((r for r in refs if r.startswith("source:w_gh")), next(iter(refs), ""))
    decision = next((r for r in refs if r.startswith("decision_record:")), "")
    priorities = [{"text": "Two open pull requests wait on the runbook", "cited_refs": [gh] if gh else []}]
    if decision:
        priorities.insert(0, {"text": DECISION_TEXT, "cited_refs": [decision]})
    return json.dumps({
        "priorities": priorities,
        "questions": [{"text": "Sprint velocity improved over the trailing average", "cited_refs": []}],
        "obligations": [],
    })


# ── seeds that no route can write (a Watch's READ) ───────────────────


def _seed_gh_source(project_id: str) -> None:
    """One readable GitHub Watch and one Jira Watch that cannot check.

    A source's coverage STATE is a recorded fact of its Watch row and no
    route sets ``last_error`` by hand (HS-200-11's note), so the rows are
    written the way stories 11, 14 and 15 write them -- and read back
    through story 07's REAL coverage projection.
    """
    from datetime import timezone

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    rows = (
        (
            "w_gh_loop", "gh", "pull_requests",
            {"repository": "karolswdev/HoldSpeak"},
            [
                {"number": 612, "title": "Cut-over runbook", "state": "OPEN",
                 "url": "https://github.com/karolswdev/HoldSpeak/pull/612",
                 "reviewRequests": ["karolswdev"], "checks": "passing",
                 "updatedAt": (now - timedelta(days=2)).isoformat()},
                {"number": 613, "title": "Replica failover", "state": "OPEN",
                 "url": "https://github.com/karolswdev/HoldSpeak/pull/613",
                 "reviewRequests": ["karolswdev"], "checks": "passing",
                 "updatedAt": (now - timedelta(days=1)).isoformat()},
            ],
            (now - timedelta(minutes=4)).isoformat(timespec="seconds"), None,
        ),
        (
            "w_jira_loop", "jira", "issues",
            {"jql": "project = KAN AND due < now()"}, [],
            (now - timedelta(minutes=31)).isoformat(timespec="seconds"),
            "JQL parse error: The value 'KAN' does not exist for the field 'project'.",
        ),
    )
    db = _db()
    with db._connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watch_provider_connections "
            "(id, provider_id, external_connection_ref, state, "
            " last_connected_at, created_at, updated_at) "
            "VALUES ('wpc-gh', 'github', 'karolswdev', 'connected', "
            " datetime('now'), datetime('now'), datetime('now'))",
        )
        for wid, connector, kind, query, snapshot, success_at, error in rows:
            conn.execute(
                "INSERT INTO connector_watches "
                "(id, connector_id, query_kind, name, query_json, snapshot_json, "
                " enabled, last_success_at, last_error, project_id, "
                " created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, datetime('now'), datetime('now'))",
                (wid, connector, kind, f"{connector} {kind}",
                 json.dumps(query, sort_keys=True), json.dumps(snapshot),
                 success_at, error, project_id),
            )


# ── browser helpers (the conventions of the 11/12/13/14/15 rigs) ─────


def _arrive(page: Any, url: str) -> None:
    page.goto(f"{url}/?token={TOKEN}", wait_until="load")
    _api(page, "POST", "/api/desk/seed", token=TOKEN)
    _api(page, "PUT", "/api/setup/onboarding", {"disposition": "completed"}, token=TOKEN)
    _normal_chair(page)


def _open_room(page: Any, project_id: str) -> None:
    page.evaluate(
        """([key, scope]) => {
          sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key, scope}));
        }""",
        ["open-project-memory", f"project:{project_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("room-body").wait_for(timeout=20000)
    _settle(page)


def _open_desk_memory(page: Any) -> None:
    """Go -> Desk memory, staged with NO scope (13's own helper)."""
    page.evaluate(
        """([key]) => {
          localStorage.removeItem("hs.desk.workspace.v1");
          localStorage.removeItem("hs.desk-memory.recall.v1");
          sessionStorage.setItem("hs.desk.staged-surface-open", JSON.stringify({key}));
        }""",
        ["open-project-memory"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".desk-surface-window").first.wait_for(timeout=15000)
    page.get_by_role("searchbox", name="Search the Desk").wait_for(timeout=10000)
    _settle(page)


def _search_memory(page: Any, query: str) -> None:
    page.get_by_role("searchbox", name="Search the Desk").fill(query)
    page.locator(".desk-surface-window").get_by_role(
        "button", name="Search desk memory", exact=True,
    ).click()
    page.get_by_test_id("recall-results").wait_for(timeout=10000)
    _settle(page)


def _enter_prepare(page: Any) -> None:
    page.get_by_test_id("room-ask-result").locator("select").select_option("brief")
    page.get_by_test_id("prepare-posture").wait_for(timeout=15000)
    page.get_by_test_id("prepare-coverage").wait_for(timeout=15000)
    _settle(page)


def _open_review_wing(page: Any, meeting_id: str) -> None:
    page.evaluate(
        """([scope]) => {
          sessionStorage.setItem(
            "hs.desk.staged-surface-open",
            JSON.stringify({key: "review-meetings", scope})
          );
        }""",
        [f"meeting:{meeting_id}"],
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.locator(".desk-surface-window").first.wait_for(timeout=15000)
    page.locator(".surface-split-detail .surface-display").first.wait_for(timeout=15000)
    page.get_by_role("tab", name="Review").click()
    page.locator("[data-testid='meeting-review']").wait_for(timeout=15000)
    _settle(page)


def _reload_arrival(page: Any) -> None:
    """Land on the ARRIVAL with nothing staged over it.

    A staged surface and the saved workspace both survive a reload, so a
    plain reload after the Review wing leaves the Meetings window on top
    and the shot does not show the face it claims (caught by reading the
    first run's `day1-attention` shot).
    """
    page.evaluate(
        "() => { sessionStorage.removeItem('hs.desk.staged-surface-open');"
        " localStorage.removeItem('hs.desk.workspace.v1'); }"
    )
    page.reload(wait_until="load")
    _normal_chair(page)
    page.get_by_test_id("arrival-headline").wait_for(timeout=15000)
    assert page.locator(".desk-surface-window").count() == 0, (
        "a surface window is staged over the arrival: "
        + str(page.locator(".desk-window-title").all_inner_texts())
    )
    _settle(page)


def _import_transcript(page: Any, title: str, started: datetime) -> str:
    """The REAL import route (multipart), with a REAL earlier start."""
    result = page.evaluate(
        """async ([token, title, body, startedMs]) => {
          const form = new FormData();
          form.append("file", new Blob([body], {type: "text/plain"}), "architecture-review.srt");
          form.append("title", title);
          form.append("started_at_ms", String(startedMs));
          const response = await fetch("/api/meetings/import", {
            method: "POST",
            headers: {authorization: `Bearer ${token}`},
            body: form,
          });
          return {status: response.status, payload: await response.json()};
        }""",
        [TOKEN, title, TRANSCRIPT_SRT, int(started.timestamp() * 1000)],
    )
    assert result["status"] == 202, result
    meeting_id = str(result["payload"]["meeting_id"])
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        detail = _api(page, "GET", f"/api/meetings/{meeting_id}", token=TOKEN)
        if len(detail.get("segments") or []) == 3:
            return meeting_id
        time.sleep(0.2)
    raise AssertionError("the import never produced three segments")


def _run_intelligence(page: Any, meeting_id: str) -> dict[str, Any]:
    """Post the hash the existing SERVICE route fixture discloses."""
    detail = _api(page, "GET", f"/api/meetings/{meeting_id}", token=TOKEN)
    planned = detail["planned_route"]
    assert planned["status"] == "ready" and planned["legs"], planned
    assert planned["selection_hash"], planned
    return _api(
        page,
        "POST",
        f"/api/meetings/{meeting_id}/intelligence/run",
        {"expected_selection_hash": planned["selection_hash"]},
        token=TOKEN,
    )


def _seed_historical_proposal_fixture(
    meeting_id: str, engine: Any,
) -> list[Any]:
    """Seed the retained day-2 path from a HISTORICAL FIXTURE.

    The current Phase 201 law ends the summary route after analysis. This
    helper is deliberately outside that route: it calls both real extractor
    plugins on the imported transcript through an admitted dispatch, records
    each real output, and invokes the real bridge. The resulting proposals are
    historical continuity data for S3-S8. The current first-use summary path
    does not create the decision or commitment that day 2 carries. No current
    owner creation path is proven by this rig.
    """
    from holdspeak.plugins.builtin.action_owner_enforcer import ActionOwnerEnforcerPlugin
    from holdspeak.plugins.builtin.decision_capture import DecisionCapturePlugin
    from holdspeak.plugins.intelligence import PLUGIN_DISPATCH_KEY
    from holdspeak.services.proposal_bridge_service import ProposalBridgeService
    from tests.unit.plugin_dispatch_rig import admitted_dispatch, unbind

    meeting = _db().meetings.get_meeting(meeting_id)
    assert meeting is not None
    segments = list(meeting.segments)
    transcript_segments = [
        {
            "text": segment.text,
            "speaker": segment.speaker,
            "start_time": segment.start_time,
            "end_time": segment.end_time,
        }
        for segment in segments
    ]
    context = {
        "transcript": "\n".join(str(segment.text) for segment in segments),
        "transcript_segments": transcript_segments,
        "project_name": PROJECT_NAME,
        "active_intents": [],
    }

    def _run(plugin: Any) -> dict[str, Any]:
        dispatch, bound_engine, dispatch_context = admitted_dispatch(engine=engine)
        try:
            return plugin.run({**context, PLUGIN_DISPATCH_KEY: dispatch})
        finally:
            unbind(bound_engine, dispatch_context)

    decision_plugin = DecisionCapturePlugin()
    action_plugin = ActionOwnerEnforcerPlugin()
    decision_output = _run(decision_plugin)
    action_output = _run(action_plugin)
    assert decision_output.get("decisions"), decision_output
    assert action_output.get("action_items"), action_output

    db = _db()
    db.plugins.record_artifact(
        artifact_id=f"historical-{meeting_id}-decision",
        meeting_id=meeting_id,
        artifact_type="decisions",
        title="HISTORICAL FIXTURE decision output",
        structured_json=decision_output,
        confidence=float(decision_output.get("confidence_hint") or 0.0),
        status="draft",
        plugin_id=decision_plugin.id,
        plugin_version=decision_plugin.version,
    )
    db.plugins.record_artifact(
        artifact_id=f"historical-{meeting_id}-action",
        meeting_id=meeting_id,
        artifact_type="action_items",
        title="HISTORICAL FIXTURE action output",
        structured_json=action_output,
        confidence=float(action_output.get("confidence_hint") or 0.0),
        status="draft",
        plugin_id=action_plugin.id,
        plugin_version=action_plugin.version,
    )
    created = ProposalBridgeService(db).bridge_meeting_artifacts(meeting_id)
    assert len(created) == 2, created
    return created


def _action_item_id(page: Any) -> str:
    """The follow-through card behind the confirmed commitment, by its text.

    The outcome-review payload names the durable ``commitment_id`` but not
    the follow-through card; the board is the product's own read of it.
    """
    board = _api(page, "GET", "/api/follow-through/board", token=TOKEN)
    for lane in board.values():
        if not isinstance(lane, list):
            continue
        for card in lane:
            if str(card.get("title") or card.get("text") or "").strip() == COMMITMENT_TEXT:
                return str(card["id"])
    raise AssertionError(f"no follow-through card for {COMMITMENT_TEXT!r}: {board}")


def _wait_for_document(page: Any, llm: Any, timeout: float = 90.0) -> None:
    """Wait for the drafted brief, and name the refusal if one comes instead.

    A bare ``wait_for`` on the document reports "not visible" and hides the
    reason the hub gave; a failing rig must name its mechanism.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if page.get_by_test_id("prepare-document").count():
            page.get_by_test_id("prepare-document").wait_for(timeout=5000)
            return
        posture = page.locator('[data-testid="prepare-posture"]').first
        if (posture.get_attribute("data-posture") or "") == "refused":
            head = page.get_by_test_id("prepare-head").inner_text()
            raise AssertionError(
                "the brief was refused instead of drafted:\n"
                f"  head: {head!r}\n"
                f"  llm posts: {len(llm.posts)}\n"
                f"  last body: {(llm.posts[-1]['body'][:1500] if llm.posts else '(none)')!r}"
            )
        time.sleep(0.25)
    raise AssertionError(
        "no brief document and no refusal within "
        f"{timeout:.0f}s; llm posts={len(llm.posts)}"
    )


def _wait(predicate: Any, *, timeout: float = 90.0, step: float = 0.25) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(step)
    return bool(predicate())


# ── the measured record ──────────────────────────────────────────────


class Walk:
    """Active time, corrections, abandoned paths and source coverage, per
    station and in total -- plus the exact build and model identity read
    from the RUNNING product."""

    def __init__(self, width: int) -> None:
        self.width = width
        self.started_at = datetime.now()
        self.stations: list[dict[str, Any]] = []
        self.shots: list[dict[str, Any]] = []
        self.facts: list[dict[str, Any]] = []
        self.identity: dict[str, Any] = {}
        self.model: dict[str, Any] = {}
        self.errors: list[str] = []
        self.defects: list[str] = []
        self.surprises: list[str] = []
        self._open: dict[str, Any] | None = None

    # -- stations ------------------------------------------------------
    def begin(self, name: str, day: int, what: str) -> None:
        assert self._open is None, f"station {self._open} is still open"
        self._open = {
            "station": name, "day": day, "what": what,
            "t0": time.monotonic(), "corrections": 0, "abandoned": 0,
        }

    def correction(self, why: str) -> None:
        assert self._open is not None
        self._open["corrections"] += 1
        self._open.setdefault("correction_notes", []).append(why)

    def abandoned(self, why: str) -> None:
        assert self._open is not None
        self._open["abandoned"] += 1
        self._open.setdefault("abandoned_notes", []).append(why)

    def end(self, coverage: dict[str, Any] | None = None) -> None:
        assert self._open is not None
        row = self._open
        row["active_seconds"] = round(time.monotonic() - row.pop("t0"), 2)
        row["coverage"] = coverage or {}
        self.stations.append(row)
        self._open = None

    # -- facts ---------------------------------------------------------
    def fact(self, face: str, field: str, expected: Any, observed: Any,
             verdict: str, why: str) -> None:
        self.facts.append({
            "face": face, "field": field, "expected": str(expected),
            "observed": str(observed), "verdict": verdict, "why": why,
        })

    @staticmethod
    def _cell(value: Any) -> str:
        """One Markdown table cell: a pipe in the data never splits a row."""
        return str(value).replace("|", "/").replace("\n", " ")

    def shot(self, page: Any, name: str) -> None:
        """One station, at this walk's own viewport.

        The walk runs once per width rather than resizing mid-walk: a desk
        window keeps the width it was last laid out at, so a viewport
        flipped 1440 -> 393 -> 1440 leaves later 1440 shots drawn at the
        narrow window's size -- a shot that does not show the face it
        claims.
        """
        width = self.width
        self.shots.append({"station": name, "width": width, "path": f"{name}-{width}.png"})
        if not WRITE_SHOTS:
            return
        SHOTS.mkdir(parents=True, exist_ok=True)
        page.mouse.move(2, 2)
        _settle(page)
        path = SHOTS / f"{name}-{width}.png"
        page.screenshot(path=str(path), full_page=False)
        assert path.stat().st_size > 2_000, f"Shot {name}-{width} too small ({path.stat().st_size})"

    # -- totals --------------------------------------------------------
    def totals(self) -> dict[str, Any]:
        return {
            "stations": len(self.stations),
            "active_seconds": round(sum(s["active_seconds"] for s in self.stations), 2),
            "active_minutes": round(sum(s["active_seconds"] for s in self.stations) / 60.0, 2),
            "corrections": sum(s["corrections"] for s in self.stations),
            "abandoned_paths": sum(s["abandoned"] for s in self.stations),
        }

    def to_json(self) -> dict[str, Any]:
        return {
            "story": "HS-200-16",
            "what": "the two-working-day daily loop, machine half",
            "viewport_width": self.width,
            "generated_at": self.started_at.isoformat(timespec="seconds"),
            "attended_by_owner": False,
            "legs": {
                "fixture_proven": (
                    "everything in `stations`, `facts` and `shots`: a real hub, "
                    "real faces, controlled adapters, no live model"
                ),
                "live_model": (
                    "NOT RUN. R16-1 keeps the live-model leg out of this rig; no "
                    "measured semantic result below comes from a real model."
                ),
                "owner_usefulness_judgment": (
                    "ACCEPTED BY OWNER RULING 2026-09-19, NOT OBSERVED. The "
                    "owner ruled \"all walks may be considered as passed\", "
                    "which closes AC3 (the user completes the path through "
                    "normal controls without implementation guidance) as "
                    "ACCEPTED. Nobody watched a human complete this loop: no "
                    "attended walk happened, none is simulated here, and no "
                    "measurement below comes from one. Acceptance is the "
                    "owner's judgment; it is not evidence that the path was "
                    "walked."
                ),
            },
            "identity": self.identity,
            "model": self.model,
            "day_boundary": {
                "seam": "hub restart onto the same HOME and the same database file",
                "same_seam_as": (
                    "tests/e2e/test_hs200_continuity_glass.py::"
                    "TestContinuityGlass::test_chain_survives_a_hub_restart"
                ),
                "earlier_day": (
                    "the day-1 meeting is imported through the product's own "
                    "`started_at_ms` control; the faces date its records from the "
                    "meeting (holdspeak/services/recall_service.py:249-251)"
                ),
                "clock_mutation": "none -- the product exposes no clock-injection seam",
                "day1_meeting_started_at": DAY1_START.isoformat(timespec="seconds"),
            },
            "totals": self.totals(),
            "stations": self.stations,
            "facts": self.facts,
            "shots": self.shots,
            "page_errors": self.errors,
            "surprises": self.surprises,
            "defects": self.defects,
        }

    def to_md(self) -> str:
        data = self.to_json()
        out: list[str] = []
        out.append("# HS-200-16 loop facts -- the two-working-day daily loop\n")
        twin = "`loop-facts-393.json` / `.md`" if self.width == WIDE else "`loop-facts.json` / `.md`"
        out.append(f"Viewport: **{data['viewport_width']}px** "
                   f"(the walk runs once per width; its twin is {twin})")
        out.append(f"Generated: {data['generated_at']}")
        out.append(f"Attended by the owner: **{data['attended_by_owner']}**\n")
        out.append("## Three legs, kept apart\n")
        out.append("| Leg | State |")
        out.append("|-----|-------|")
        for key, value in data["legs"].items():
            out.append(f"| {key} | {value} |")
        out.append("\n## Identity (read from the running product)\n")
        out.append("| Field | Value |")
        out.append("|-------|-------|")
        for key in sorted(data["identity"]):
            out.append(f"| {key} | `{data['identity'][key]}` |")
        out.append("\n## Model identity\n")
        out.append("| Field | Value |")
        out.append("|-------|-------|")
        for key in sorted(data["model"]):
            out.append(f"| {key} | `{data['model'][key]}` |")
        out.append("\n## The day boundary\n")
        out.append("| Field | Value |")
        out.append("|-------|-------|")
        for key in sorted(data["day_boundary"]):
            out.append(f"| {key} | {data['day_boundary'][key]} |")
        out.append("\n## Stations\n")
        out.append("| Day | Station | Active s | Corrections | Abandoned | Source coverage |")
        out.append("|-----|---------|----------|-------------|-----------|-----------------|")
        for station in data["stations"]:
            cov = station.get("coverage") or {}
            cov_text = (
                f"{cov.get('available', '-')} of {cov.get('expected', '-')} available"
                f" · complete={cov.get('complete')}"
                if cov else "(not read here)"
            )
            out.append(
                f"| {station['day']} | {station['station']} — {station['what']} "
                f"| {station['active_seconds']} | {station['corrections']} "
                f"| {station['abandoned']} | {cov_text} |"
            )
        totals = data["totals"]
        out.append(
            f"\n**Totals:** {totals['stations']} stations · "
            f"{totals['active_seconds']} s active ({totals['active_minutes']} min) · "
            f"{totals['corrections']} corrections · "
            f"{totals['abandoned_paths']} abandoned paths.\n"
        )
        out.append("## Facts\n")
        out.append("| Face | Field | Expected | Observed | Verdict | Why |")
        out.append("|------|-------|----------|----------|---------|-----|")
        for fact in data["facts"]:
            out.append(
                f"| {self._cell(fact['face'])} | {self._cell(fact['field'])} "
                f"| {self._cell(fact['expected'])} | {self._cell(fact['observed'])} "
                f"| {self._cell(fact['verdict'])} | {self._cell(fact['why'])} |"
            )
        out.append("\n## Shots\n")
        for shot in data["shots"]:
            out.append(f"- {shot['station']} @ {shot['width']}: `{shot['path']}`")
        for label, rows in (("Page errors", data["page_errors"]),
                            ("Surprises", data["surprises"]),
                            ("Defects", data["defects"])):
            out.append(f"\n## {label}\n")
            out.append("\n".join(f"- {row}" for row in rows) if rows else "None.")
        out.append("")
        return "\n".join(out)

    def write(self) -> None:
        """Write the record -- ONLY when the evidence flag is set.

        `loop-facts.json` / `.md` are tracked evidence exactly like the
        shots, and a plain suite run must never rewrite them (the 388-PNG
        scar; counsel hit this one and restored from backup).
        """
        if not WRITE_SHOTS:
            return
        SHOTS.mkdir(parents=True, exist_ok=True)
        suffix = "" if self.width == WIDE else f"-{self.width}"
        (SHOTS / f"loop-facts{suffix}.json").write_text(
            json.dumps(self.to_json(), indent=2, sort_keys=False) + "\n", encoding="utf-8",
        )
        (SHOTS / f"loop-facts{suffix}.md").write_text(self.to_md(), encoding="utf-8")


def _coverage(page: Any) -> dict[str, Any]:
    """Story 07's REAL coverage projection, read from the product, never
    recomputed (`/api/desk/needs-you?fresh=1`; the C4 vocabulary lives in
    holdspeak/services/needs_you_aggregate.py:52)."""
    wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
    records = wire.get("coverage") or []
    by_state: dict[str, int] = {}
    for record in records:
        state = str(record.get("state") or "unknown")
        by_state[state] = by_state.get(state, 0) + 1
    return {
        "expected": len(records),
        "available": by_state.get("available", 0),
        "by_state": by_state,
        "complete": bool(wire.get("complete")),
        "items": int(wire.get("count") or 0),
        "computed_at": wire.get("computedAt"),
    }


# ── the walk ─────────────────────────────────────────────────────────


@pytest.mark.timeout(1800)
@pytest.mark.parametrize("width", [WIDE, NARROW])
def test_a_project_carries_work_across_two_working_days(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, width: int,
) -> None:
    from holdspeak.runtime_lock import claim_database, current_lock, release_database
    from playwright.sync_api import sync_playwright

    from .test_hs200_preparation_brief_glass import FakeLLM, _define_route

    _ensure_build()
    walk = Walk(width)
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    (home / ".holdspeak").mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(home / "people-dev-key.json"))

    llm = FakeLLM()
    llm.reply = _brief_reply
    engine = _scripted_engine()

    # The owner claim: the intel drainer is scheduled work that runs in the
    # owner alone (HS-200-42); the in-process glass server does not run the
    # hub command's claim step.
    assert current_lock() is None, "this process already owns a database"
    lock = claim_database(tmp_path / "holdspeak.db")
    assert lock.held, "the rig could not claim its own tmp database"

    state: dict[str, Any] = {}
    try:
        # ══ DAY 1 ══════════════════════════════════════════════════════
        server, url = _boot(tmp_path, monkeypatch, token=TOKEN)
        try:
            from holdspeak import intel_queue_conductor as conductor

            assert conductor.drainer_state() == "running", "the hub lifespan started no drainer"

            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": width, "height": 1000 if width >= WIDE else 852})
                page.on("pageerror", lambda e: walk.errors.append(f"day1: {e}"))
                _arrive(page, url)

                # The runtime identity of THIS process, read from the product.
                identity = _api(page, "GET", "/api/system/identity", token=TOKEN)
                # R16-7, the honest identity block.  `capture_runtime_identity`
                # caches `_IDENTITY` for the OS PROCESS and returns the first
                # capture forever after (holdspeak/runtime_identity.py:204,
                # 214-222).  This rig boots both hubs -- and both
                # parametrizations -- inside ONE pytest process, so every
                # product-reported identity field below describes the FIRST
                # capture in this process, not necessarily this run.  The
                # fields that are genuinely per-build (version, revision,
                # bundle, schema, config) are the same either way; the
                # database is NOT, so it is measured separately through the
                # uncached seam.
                walk.identity = {
                    "backend_version": identity["identity"]["backend_version"],
                    "backend_revision": identity["identity"]["backend_revision"],
                    "frontend_build": identity["identity"]["frontend_build"],
                    "schema_version_loaded": identity["identity"]["schema_version_loaded"],
                    "config_revision": identity["identity"]["config_revision"],
                    "repair": identity["repair"],
                    "process_start_reported": identity["identity"]["process_start"],
                    "database_id_reported": identity["identity"]["database_id"],
                    "capture_caveat": (
                        "process_start_reported and database_id_reported come "
                        "from a capture cached once per OS PROCESS "
                        "(holdspeak/runtime_identity.py:204,214-222); with both "
                        "viewport runs in one pytest process they describe the "
                        "first run, NOT necessarily this one. The database this "
                        "run actually used is database_id_this_run below, taken "
                        "from the uncached `database_identity()`."
                    ),
                }
                assert identity["repair"] == [], identity["repair"]

                # The uncached seam: a pure function of the resolved path plus
                # the file's device+inode, so a replaced file reads as a
                # different database (runtime_identity.py:96-112).
                from holdspeak.runtime_identity import database_identity

                db_path = tmp_path / "holdspeak.db"
                other_path = tmp_path / "not-the-database.db"
                other_path.write_bytes(b"")
                day1_db_id = database_identity(db_path)
                walk.identity["database_id_this_run"] = day1_db_id
                # The instrument must DISCRIMINATE, which is exactly what the
                # cached `database_id` failed to do: counsel found both
                # viewport runs reporting one id over two different files.
                walk.fact("day1-identity", "database_identity_discriminates",
                          "a different file yields a different identity",
                          "different" if database_identity(other_path) != day1_db_id
                          else "SAME -- the instrument is a constant",
                          "MATCH" if database_identity(other_path) != day1_db_id
                          else "MISMATCH",
                          "an identity that cannot tell two files apart proves "
                          "nothing about which file was opened")
                assert database_identity(other_path) != day1_db_id
                other_path.unlink()

                project_id = _api(page, "POST", "/api/projects", {
                    "name": PROJECT_NAME,
                    "description": "The HS-200-16 two-day loop.",
                    "command_id": f"hs200-16-{uuid.uuid4().hex[:8]}",
                }, token=TOKEN)["project"]["id"]
                state["project_id"] = project_id
                _seed_gh_source(project_id)
                _define_route(home, llm.endpoint, "loop-llm", 1)
                _api(page, "POST", "/api/people/setup", {}, token=TOKEN)
                person = _api(page, "POST", "/api/people/relationships",
                              {"display_name": PERSON_NAME}, token=TOKEN)["relationship"]["id"]
                _api(page, "POST", f"/api/people/relationships/{person}/owner-aliases",
                     {"alias": OWNER_HINT.lower()}, token=TOKEN)
                _api(page, "POST", f"/api/people/relationships/{person}/projects/{project_id}",
                     {}, token=TOKEN)
                state["person"] = person

                route = _api(page, "GET", f"/api/projects/{project_id}/briefs/route",
                             token=TOKEN)["route"]
                walk.model = {
                    "brief_route_state": route["state"],
                    "brief_model": route["model"],
                    "brief_host": route["host"],
                    "brief_boundary": route["boundary"],
                    "brief_adapter": "controlled OpenAI-compatible probe on 127.0.0.1 (R16-1)",
                    "meeting_extractor_provider": type(engine).__name__,
                    "meeting_extractor_model": getattr(engine, "active_model", "unknown"),
                    "live_model": False,
                }
                assert route["state"] == "ready", route

                # ── S1: the preparation brief (11) ─────────────────────
                walk.begin("day1-brief", 1, "prepare and keep the preparation brief")
                _open_room(page, project_id)
                _enter_prepare(page)
                coverage_chip = (page.get_by_test_id("prepare-coverage")
                                 .locator(".surface-state-chip").first)
                chip_words = (coverage_chip.get_attribute("aria-label")
                              or coverage_chip.inner_text()).strip()
                walk.fact("day1-brief", "coverage_chip", "COVERAGE · 1 OF 2", chip_words,
                          "MATCH" if chip_words == "COVERAGE · 1 OF 2" else "MISMATCH",
                          "the Jira Watch cannot check; the face says so before the run")
                assert chip_words == "COVERAGE · 1 OF 2", chip_words
                page.get_by_role("textbox", name="Purpose").fill(PURPOSE_D1)
                page.get_by_test_id("prepare-verb").click()
                _wait_for_document(page, llm)
                _settle(page)
                assert len(llm.posts) == 1, llm.requests
                page.get_by_test_id("prepare-keep").click()
                page.locator(
                    '[data-testid="prepare-lifecycle"] .surface-state-chip[aria-label="KEPT"]'
                ).wait_for(timeout=15000)
                _settle(page)
                kept = _api(page, "GET", f"/api/projects/{project_id}/briefs?lifecycle=kept",
                            token=TOKEN)["briefs"]
                assert len(kept) == 1, kept
                brief = _api(page, "GET", f"/api/briefs/{kept[0]['id']}", token=TOKEN)["brief"]
                walk.model["brief_generator"] = brief["generator"]
                walk.model["brief_generator_model"] = brief["generator_model"]
                walk.model["brief_generator_host"] = brief["generator_host"]
                walk.fact("day1-brief", "lifecycle", "kept", brief["lifecycle"],
                          "MATCH" if brief["lifecycle"] == "kept" else "MISMATCH",
                          "the brief is kept work, not a draft that evaporates")
                walk.end(_coverage(page))
                walk.shot(page, "day1-brief")

                # The meeting extractors' scripted provider is installed only
                # NOW: `holdspeak.intel.providers._configured_engine` is a
                # PROCESS-WIDE seam, and a scripted meeting engine installed
                # earlier also answers the brief's model route (it has no
                # `run_prompt`, so the brief refuses).  Each controlled adapter
                # stays scoped to the station that needs it.
                _wire_provider(monkeypatch, engine)

                # ── S2: the meeting, captured on DAY 1 (12) ────────────
                walk.begin("day1-meeting", 1, "import, link and read the day-1 meeting")
                meeting_id = _import_transcript(page, "Architecture review", DAY1_START)
                state["meeting_id"] = meeting_id
                _api(page, "POST", f"/api/projects/{project_id}/meetings/{meeting_id}", token=TOKEN)
                run = _run_intelligence(page, meeting_id)
                assert run["state"] == "queued" and run["drainer"] == "running", run

                def _review() -> dict[str, Any]:
                    return _api(page, "GET", f"/api/meetings/{meeting_id}/outcome-review",
                                token=TOKEN)

                # Phase 201's current law: this route produces the analysis
                # summary only. The proposal plugins are not called, and the
                # Review face says NOT RUN. These exact empty assertions are
                # the negative canary: forcing one plugin call or one
                # proposal into the summary path must fail this walk.
                assert _wait(
                    lambda: (_review().get("job") or {}).get("status") == "succeeded",
                    timeout=120.0,
                ), (_review(), engine.plugin_calls)
                review = _review()
                assert review["job"]["status"] == "succeeded", review["job"]
                assert review["coverage"] == {
                    "turns": 3,
                    "read": 3,
                    "state": "available",
                    "observed_at": review["coverage"]["observed_at"],
                }, review["coverage"]
                assert review["proposals"] == [], review["proposals"]
                assert engine.plugin_calls == [], engine.plugin_calls
                detail = _api(page, "GET", f"/api/meetings/{meeting_id}", token=TOKEN)
                assert detail["intel"]["summary"] == engine.result.summary, detail["intel"]
                _open_review_wing(page, meeting_id)
                not_run = page.get_by_test_id("review-not-run")
                not_run.wait_for(timeout=15000)
                assert (not_run.text_content() or "").strip() == "PROPOSALS · NOT RUN"
                review_words = page.locator(".desk-surface-window").first.inner_text()
                assert "EXTRACTED" not in review_words.upper(), review_words
                assert "Nothing to review" not in review_words, review_words
                walk.fact(
                    "day1-review-not-run", "proposal_origin",
                    "HISTORICAL FIXTURE only",
                    "summary route: no proposals; Review: PROPOSALS · NOT RUN",
                    "MATCH",
                    "the current analysis-only route does not create proposals",
                )
                walk.fact(
                    "day1-review-not-run", "historical_fixture_label",
                    "HISTORICAL FIXTURE; not summary output",
                    "HISTORICAL FIXTURE; not summary output",
                    "MATCH",
                    "the retained day-2 path is seeded separately below",
                )
                walk.fact(
                    "day1-review-not-run", "current_first_use_summary_scope",
                    "Day 2 continuity is proven from a seeded day-1 state. "
                    "The current first-use summary path does not create the "
                    "decision or commitment that day 2 carries. No current "
                    "owner creation path is proven by this rig.",
                    "Day 2 continuity is proven from a seeded day-1 state. "
                    "The current first-use summary path does not create the "
                    "decision or commitment that day 2 carries. No current "
                    "owner creation path is proven by this rig.",
                    "MATCH",
                    "D5 records the retained historical continuity boundary",
                )
                walk.shot(page, "day1-review-not-run")

                # Retain S3-S8 from a disclosed historical path. The real
                # plugin outputs are produced from this imported transcript,
                # recorded as artifacts, and bridged by production service
                # code. This does not turn the analysis-only summary into a
                # proposal-producing route.
                historical = _seed_historical_proposal_fixture(meeting_id, engine)
                assert len(historical) == 2, historical
                review = _review()
                kinds = sorted(p["kind"] for p in review["proposals"])
                assert kinds == ["action", "decision"], kinds
                started_at = detail.get("started_at") or (detail.get("meeting") or {}).get("started_at")
                started_day = str(started_at)[:10]
                walk.fact("day1-meeting", "meeting_started_at", DAY1_START.date().isoformat(),
                          started_day,
                          "MATCH" if started_day == DAY1_START.date().isoformat() else "MISMATCH",
                          "day 1 is a real earlier calendar day, set through the import control")
                assert started_day == DAY1_START.date().isoformat(), started_at

                # THE FENCE for the defect this walk found: the Room's
                # proposal caption dates the row to the MEETING it came from.
                # Before the fix (holdspeak/services/project_service.py, the
                # needs-you proposal row, and
                # web/src/features/project-room/ProjectRoomCore.tsx's caption)
                # it formatted the proposal's own `created_at`, so a meeting
                # read the next morning was captioned `from Architecture
                # review <today>` while the review wing and recall both said
                # the meeting's own day.  Invisible on a same-day desk.
                _open_room(page, project_id)
                page.get_by_test_id("proposal-caption").first.wait_for(timeout=20000)
                captions = [c.strip() for c in
                            page.get_by_test_id("proposal-caption").all_inner_texts()]
                day1_mmdd = DAY1_START.strftime("%m-%d")
                today_mmdd = datetime.now().strftime("%m-%d")
                assert day1_mmdd != today_mmdd, "the fence needs two distinct days"
                walk.fact("day1-room", "proposal_caption_date",
                          f"from Architecture review {day1_mmdd}",
                          " | ".join(captions),
                          "MATCH" if all(f"Architecture review {day1_mmdd}" in c
                                         for c in captions) else "MISMATCH",
                          "a proposal is dated by its meeting, not by the row's write time")
                assert captions, "no proposal caption on the Room"
                for caption in captions:
                    assert f"Architecture review {day1_mmdd}" in caption, caption
                    assert today_mmdd not in caption, caption
                # THE THIRD FENCE: the Room counts in the singular.  It read
                # `WAITING ON YOUR REVIEW · 1 DAYS` where the arrival read
                # `1 DAY` for the same row (`_format_age`,
                # holdspeak/services/project_service.py:253-277).
                room_text = page.get_by_test_id("room-body").inner_text()
                # The POSITIVE half (a negative-only fence passes when the
                # string is merely absent): the one-day-old PR row must
                # actually render `1 DAY`.  `_pr` seeds #612 two days back and
                # #613 eighteen hours back, so exactly one row is one day old.
                # "1 DAY" is a substring of "1 DAYS", so the positive half
                # must exclude the plural or the bug satisfies it.
                one_day_rows = [line.strip() for line in room_text.split("\n")
                                if "1 DAY" in line and "1 DAYS" not in line]
                walk.fact("day1-room", "singular_day_positive",
                          "a one-day-old row renders `… · 1 DAY`",
                          " / ".join(one_day_rows) or "(no `1 DAY` row)",
                          "MATCH" if one_day_rows else "MISMATCH",
                          "the fence must see the singular, not just miss the plural")
                assert one_day_rows, room_text[:500]
                walk.fact("day1-room", "singular_day",
                          "no `1 DAYS` / `1 HOURS` anywhere on the Room",
                          "1 DAYS" if "1 DAYS" in room_text
                          else ("1 HOURS" if "1 HOURS" in room_text else "(none)"),
                          "MATCH" if ("1 DAYS" not in room_text
                                      and "1 HOURS" not in room_text) else "MISMATCH",
                          "one day is a day; the arrival already said so")
                assert "1 DAYS" not in room_text, room_text[:400]
                assert "1 HOURS" not in room_text, room_text[:400]

                # P1-2's fence: the TARGET chip counts in the singular too.
                # No product route writes `target_at` (the Room-fields writer
                # holdspeak/db/projects.py:526 has no caller), so the target
                # is seeded on the row the way the Watch snapshots are -- a
                # recorded fact no route sets.
                _db().projects.update_project_room_fields(
                    project_id,
                    target_at=(datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                )
                _open_room(page, project_id)
                chip = (page.get_by_test_id("room-target-chip").inner_text() or "").strip()
                walk.fact("day1-room", "target_chip_singular",
                          "TARGET <date> · 1 DAY", chip,
                          "MATCH" if chip.endswith("· 1 DAY") else "MISMATCH",
                          "the target chip counts one day in the singular")
                assert chip.endswith("· 1 DAY"), chip
                _db().projects.update_project_room_fields(project_id, target_at=None)
                _open_room(page, project_id)
                assert page.get_by_test_id("room-target-chip").count() == 0
                # FOR THE CANVAS, measured not impressionistic: how many
                # filled primaries the Room draws while proposals are pending.
                primaries = page.evaluate(
                    """() => {
                      const win = document.querySelector('.desk-surface-window');
                      if (!win) return [];
                      return Array.from(win.querySelectorAll('.btn--primary'))
                        .filter((b) => b.getBoundingClientRect().width > 0)
                        .map((b) => (b.textContent || '').trim());
                    }"""
                )
                walk.fact("day1-room", "filled_primaries", "1 (UX-CANON A.2)",
                          f"{len(primaries)}: " + ", ".join(primaries),
                          "DATA" if len(primaries) <= 1 else "FINDING",
                          "measured on the Room while two proposals are pending")
                if len(primaries) > 1:
                    walk.surprises.append(
                        "FOR THE CANVAS: with two proposals pending the Room "
                        f"draws {len(primaries)} filled primaries at once -- "
                        + ", ".join(f"`{p}`" for p in primaries)
                        + " (see day1-room-proposals-1440.png). UX-CANON asks "
                        "for one filled primary per face. HS-200-14's Room "
                        "fence never saw it because its seed had no pending "
                        "proposal. Not touched: which verb keeps the fill is a "
                        "design call (R16-4)."
                    )
                walk.shot(page, "day1-room-proposals")
                walk.defects.append(
                    "FOUND AND FIXED by this walk: the Room read "
                    "`WAITING ON YOUR REVIEW · 1 DAYS` where the arrival read "
                    "`1 DAY` for the same row. Fix: `_count_unit` in "
                    "holdspeak/services/project_service.py:253-259, used by "
                    "`_format_age` and by the `OVERDUE` / `REVIEW WAITING` "
                    "reasons. Fence: the `day1-room` `singular_day` assertion "
                    "here, which fails pre-fix with "
                    "`assert '1 DAYS' not in room_text`."
                )
                walk.defects.append(
                    "FOUND AND FIXED by this walk: the Room's proposal caption "
                    "`from <meeting> <MM-DD>` formatted the PROPOSAL's write "
                    "time, not the meeting's start "
                    "(web/src/features/project-room/ProjectRoomCore.tsx, the "
                    "caption builder). A meeting reviewed the next morning was "
                    "captioned with today's date while the review wing "
                    "(`MTG 09-17`) and recall (`DEC 09-17`) both said the "
                    "meeting's own day. Invisible on a same-day desk. Fix: "
                    "holdspeak/services/project_service.py now carries "
                    "`meeting_started_at` on the needs-you proposal row and the "
                    "caption formats it. Fence: the `day1-room` "
                    "`proposal_caption_date` assertion in this rig, which fails "
                    "pre-fix with `assert 'Architecture review 09-17' in "
                    "'from Architecture review 09-18'`."
                )
                walk.end(_coverage(page))

                # ── S3: the review (12) ────────────────────────────────
                walk.begin("day1-review", 1, "confirm one decision and one commitment")
                _open_review_wing(page, meeting_id)
                headline = page.locator("[data-testid='review-headline']").text_content()
                walk.fact("day1-review", "headline", "2 to review", headline,
                          "MATCH" if headline == "2 to review" else "MISMATCH",
                          "the two proposals the extractors produced")
                assert headline == "2 to review", headline
                walk.shot(page, "day1-review")
                decision_row = page.locator("[data-testid='review-row-decision']").first
                decision_row.locator("[data-testid='review-confirm']").click()
                page.locator("[data-testid='review-receipt']").filter(
                    has_text="CONFIRMED").wait_for(timeout=15000)
                action_row = page.locator("[data-testid='review-row-action']").first
                action_row.locator("[data-testid='review-confirm']").click()
                _wait(lambda: len([p for p in _review()["proposals"]
                                   if p["state"] == "confirmed"]) == 2, timeout=30.0)
                _settle(page)
                confirmed = [p for p in _review()["proposals"] if p["state"] == "confirmed"]
                assert len(confirmed) == 2, confirmed
                decision = next(p for p in confirmed if p["kind"] == "decision")
                commitment = next(p for p in confirmed if p["kind"] == "action")
                assert decision["decision_record_id"], decision
                assert commitment["commitment_id"], commitment
                state["decision_record_id"] = decision["decision_record_id"]
                state["commitment_id"] = commitment["commitment_id"]
                state["action_item_id"] = commitment.get("action_item_id") or _action_item_id(page)
                assert state["action_item_id"], commitment
                walk.end(_coverage(page))
                walk.shot(page, "day1-reviewed")

                # ── S4: attention (15) ─────────────────────────────────
                walk.begin("day1-attention", 1, "the commitment is a real attention row")
                _reload_arrival(page)
                page.get_by_test_id("arrival-needs-you").wait_for(timeout=15000)
                _settle(page)
                wire = _api(page, "GET", "/api/desk/needs-you?fresh=1", token=TOKEN)
                rows = [i for i in wire["items"]
                        if i["source"] == "commitment" and i["title"] == COMMITMENT_TEXT]
                walk.fact("day1-attention", "commitment_row", "1", len(rows),
                          "MATCH" if len(rows) == 1 else "MISMATCH",
                          "yesterday's commitment is attention, not a buried row")
                assert len(rows) == 1, [i["title"] for i in wire["items"]]
                walk.fact("day1-attention", "coverage_complete", "False",
                          wire["complete"], "MATCH" if wire["complete"] is False else "MISMATCH",
                          "one source cannot check; an empty partial is never an all-clear (C4)")
                assert wire["complete"] is False, wire["coverage"]
                walk.end(_coverage(page))
                walk.shot(page, "day1-attention")

                _assert_clean(page, walk.errors)
                browser.close()
        finally:
            from holdspeak import intel_queue_conductor as conductor

            hub_thread = server._thread
            server.stop()
            if hub_thread is not None:
                hub_thread.join(120)
                assert not hub_thread.is_alive(), "the hub thread outlived its stop"
            conductor.stop_intel_queue_conductor()
            release_database()

        # ══ THE DAY BOUNDARY: a SECOND hub, the SAME database ══════════
        lock2 = claim_database(tmp_path / "holdspeak.db")
        assert lock2.held
        server2, url2 = _boot(tmp_path, monkeypatch, token=TOKEN)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                page = browser.new_page(viewport={"width": width, "height": 1000 if width >= WIDE else 852})
                page.on("pageerror", lambda e: walk.errors.append(f"day2: {e}"))
                page.goto(f"{url2}/?token={TOKEN}", wait_until="load")
                _normal_chair(page)

                # R16-7: the same-file claim, proved through the UNCACHED
                # seam.  `/api/system/identity` would hand back hub #1's
                # cached capture here whatever file hub #2 opened, so it
                # cannot witness this; `database_identity()` reads the path's
                # device+inode now.
                from holdspeak.runtime_identity import database_identity

                day2_db_id = database_identity(tmp_path / "holdspeak.db")
                walk.identity["day2_database_id_this_run"] = day2_db_id
                walk.fact("day-boundary", "same_database_file",
                          walk.identity["database_id_this_run"], day2_db_id,
                          "MATCH" if day2_db_id == walk.identity["database_id_this_run"]
                          else "MISMATCH",
                          "device+inode of the file hub #2 opened, read fresh "
                          "(runtime_identity.py:96-112) -- a replaced file "
                          "would read as a different database")
                assert day2_db_id == walk.identity["database_id_this_run"]
                # And the behavioural proof that outranks it: hub #2's recall
                # returns day-1 records, which is impossible from another
                # file.  Asserted at the day2-recall station below.
                walk.fact("day-boundary", "same_data_behaviourally",
                          "hub #2 returns day 1's decision and commitment",
                          "asserted at day2-recall (current_decision, dec_token, "
                          "owed_rows)", "DATA",
                          "the load-bearing evidence for the boundary: records "
                          "written before the restart come back after it")
                # The hub really restarted: a second MeetingWebServer on its own
                # port, after the first was stopped and its thread joined.  It
                # is the SAME OS process (the glass rig hosts the hub
                # in-process, exactly as 13's restart leg does), so
                # `process_start` -- captured once per process by C1's
                # capture-at-start law -- is unchanged, and this row says so
                # rather than claiming a new process.
                walk.fact("day-boundary", "hub_restarted",
                          f"a second hub on a new port (day 1 was {url})", url2,
                          "MATCH" if url2 != url else "MISMATCH",
                          "the day boundary is a real hub restart; the OS process "
                          "is shared by the rig, so process_start does not move")

                project_id = state["project_id"]

                # ── S5: recall (13) ────────────────────────────────────
                walk.begin("day2-recall", 2, "recall yesterday's decision and commitment")
                _open_desk_memory(page)
                _search_memory(page, RECALL_QUERY)
                cards = page.locator("[data-testid='recall-card']")
                assert cards.count() >= 1, cards.count()
                # Confirming EITHER kind writes the full chain (decision record
                # + commitment) by design (holdspeak/services/
                # proposal_bridge_service.py:588-590), so both of yesterday's
                # confirmations come back as current records.  The decision is
                # the one this station is about.
                titles = [t.strip() for t in
                          page.get_by_test_id("recall-card-title").all_inner_texts()]
                assert DECISION_TEXT in titles, titles
                current = cards.nth(titles.index(DECISION_TEXT))
                assert current.get_attribute("data-state") == "current"
                title = (current.get_by_test_id("recall-card-title").text_content() or "").strip()
                walk.fact("day2-recall", "current_decision", DECISION_TEXT, title,
                          "MATCH" if title == DECISION_TEXT else "MISMATCH",
                          "AC1: recall returns the current decision first")
                assert title == DECISION_TEXT, title
                rationale = (current.get_by_test_id("recall-rationale").text_content() or "").strip()
                walk.fact("day2-recall", "rationale", DECISION_WHY, rationale,
                          "MATCH" if rationale == DECISION_WHY else "MISMATCH",
                          "AC1: the rationale travels with the decision")
                assert rationale == DECISION_WHY, rationale
                expected_dec = f"DEC {DAY1_START.strftime('%m-%d')}"
                dec_token = (current.get_by_test_id("recall-dec-token").text_content() or "").strip()
                walk.fact("day2-recall", "dec_token", expected_dec, dec_token,
                          "MATCH" if dec_token == expected_dec else "MISMATCH",
                          "the decision is dated to DAY 1, proving the boundary was crossed")
                assert dec_token == expected_dec, dec_token
                source_token = (current.get_by_test_id("recall-source-token").text_content()
                                or "").strip()
                walk.fact("day2-recall", "source_token",
                          f"MTG {DAY1_START.strftime('%m-%d')} · …", source_token,
                          "MATCH" if source_token.startswith(f"MTG {DAY1_START.strftime('%m-%d')}")
                          else "MISMATCH",
                          "AC1: the original source is still reachable on day 2")
                assert source_token.startswith(f"MTG {DAY1_START.strftime('%m-%d')}"), source_token
                owed = page.get_by_test_id("recall-owed-row")
                walk.fact("day2-recall", "owed_rows", "1", owed.count(),
                          "MATCH" if owed.count() == 1 else "MISMATCH",
                          "yesterday's commitment is still owed today")
                assert owed.count() == 1, owed.count()
                assert (owed.get_by_test_id("recall-owed-title").text_content()
                        or "").strip() == COMMITMENT_TEXT
                walk.shot(page, "day2-recall")
                current.get_by_role("button", name="Carry into brief", exact=True).click()
                page.locator("[data-testid='recall-carry'][data-carried]").wait_for(timeout=15000)
                _settle(page)
                walk.end(_coverage(page))
                walk.shot(page, "day2-carried")

                # ── S6: People preparation (14), before completion ─────
                walk.begin("day2-people", 2, "the person still carries yesterday's commitment")
                _open_room(page, project_id)
                page.get_by_test_id("room-people-head-verb").wait_for(timeout=20000)
                section = page.locator("section.surface-section").filter(
                    has=page.get_by_test_id("room-people-head-verb")).first
                section.evaluate("el => el.scrollIntoView({block: 'start'})")
                _settle(page)
                body = section.inner_text()
                walk.fact("day2-people", "person_named", PERSON_NAME,
                          PERSON_NAME if PERSON_NAME in body else "(absent)",
                          "MATCH" if PERSON_NAME in body else "MISMATCH",
                          "AC: People preparation reflects the commitment's owner")
                assert PERSON_NAME in body, body[:400]
                walk.fact("day2-people", "open_commitment", "1 OPEN COMMITMENT",
                          "1 OPEN COMMITMENT" if "1 OPEN COMMITMENT" in body.upper()
                          else "(absent)",
                          "MATCH" if "1 OPEN COMMITMENT" in body.upper() else "MISMATCH",
                          "the obligation made yesterday is on the person today")
                assert "1 OPEN COMMITMENT" in body.upper(), body[:400]
                assert COMMITMENT_TEXT in body, body[:400]
                # FOR THE CANVAS, measured: the Room's RECEIPTS ledger.
                receipts = page.evaluate(
                    """() => Array.from(document.querySelectorAll(
                         '[data-testid="receipt-row"]')).map((row) => ({
                        label: ((row.querySelector('.surface-primary') || {})
                                 .textContent || '').trim(),
                        cells: Array.from(row.querySelectorAll('.surface-token'))
                                 .map((t) => (t.textContent || '').trim())
                                 .filter(Boolean),
                      }))"""
                )
                labels = [r["label"] for r in receipts]
                distinct = sorted(set(labels))
                timed = [r for r in receipts if r["cells"]]
                walk.fact("day2-people", "receipt_rows",
                          "rows a reader can tell apart",
                          f"{len(receipts)} rows, {len(distinct)} distinct labels "
                          f"({', '.join(distinct) or 'none'}), "
                          f"{len(timed)} carrying any token",
                          "DATA", "measured on the Room's RECEIPTS ledger")
                if receipts and (len(distinct) < len(receipts) or not timed):
                    walk.surprises.append(
                        "FOR THE CANVAS: the Room's RECEIPTS ledger draws "
                        f"{len(receipts)} rows with only {len(distinct)} "
                        "distinct labels ("
                        + ", ".join(f"`{d}`" for d in distinct)
                        + f") and {len(timed)} of them carry any token at all "
                        "-- no time, outcome or egress chip -- so a reader "
                        "cannot tell one receipt from another (see "
                        "day2-people-owes-1440.png). The row HAS slots for "
                        "outcome, egress and time "
                        "(ProjectRoomCore.tsx, ReceiptsSection ~:1145-1153); "
                        "they are empty because the receipt records carry no "
                        "timestamp. Not touched: what a receipt row should say "
                        "is a design call (R16-4)."
                    )
                walk.end(_coverage(page))
                walk.shot(page, "day2-people-owes")

                # ── S7: completion by an EXPLICIT act (13) ─────────────
                walk.begin("day2-complete", 2, "complete the commitment by explicit acts")
                _open_desk_memory(page)
                _search_memory(page, RECALL_QUERY)
                row = page.get_by_test_id("recall-owed-row")
                guard = 0
                while True:
                    next_action = row.get_attribute("data-next-action")
                    if next_action == "mark_done":
                        break
                    guard += 1
                    assert guard <= 3, f"the owed row never reached mark_done ({next_action})"
                    row.get_by_test_id("recall-owed-verb").click()
                    page.get_by_test_id("recall-owed-well").wait_for(timeout=10000)
                    assert page.get_by_role("dialog").count() == 0, "no modals (A.4)"
                    well = page.get_by_test_id("recall-owed-well")
                    if next_action == "name_owner":
                        well.locator("input").first.fill(PERSON_NAME)
                    else:
                        due = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
                        state["due_day"] = due
                        well.locator("input").first.fill(due)
                    page.get_by_test_id("recall-owed-save").click()
                    page.locator(
                        f"[data-testid='recall-owed-row']:not([data-next-action='{next_action}'])"
                    ).wait_for(timeout=15000)
                    _settle(page)
                    walk.correction(f"the commitment arrived with no {next_action.split('_')[-1]}")
                walk.shot(page, "day2-mark-done")
                board_before = _api(page, "GET", "/api/follow-through/board", token=TOKEN)
                open_before = [c for lane in board_before.values() if isinstance(lane, list)
                               for c in lane if c.get("id") == state["action_item_id"]]
                assert open_before and open_before[0]["status"] in ("open", "pending"), open_before
                row.get_by_test_id("recall-owed-verb").click()
                page.wait_for_function(
                    "() => document.querySelectorAll('[data-testid=\"recall-owed-row\"]').length === 0",
                    timeout=15000,
                )
                _settle(page)
                board_after = _api(page, "GET", "/api/follow-through/board", token=TOKEN)
                after = [c for lane in board_after.values() if isinstance(lane, list)
                         for c in lane if c.get("id") == state["action_item_id"]]
                status_after = after[0]["status"] if after else "(gone from the board)"
                walk.fact("day2-complete", "commitment_status", "completed", status_after,
                          "MATCH" if status_after in ("completed", "done", "(gone from the board)")
                          else "MISMATCH",
                          "completion is an explicit act with a receipt, never a side effect")
                assert status_after in ("completed", "done", "(gone from the board)"), board_after
                walk.end(_coverage(page))
                walk.shot(page, "day2-completed")

                # ── S8: the loop closes -- day 2's preparation ─────────
                walk.begin("day2-carry", 2, "day 2's preparation carries day 1's decision")
                _open_room(page, project_id)
                page.get_by_test_id("room-people-head-verb").wait_for(timeout=20000)
                section = page.locator("section.surface-section").filter(
                    has=page.get_by_test_id("room-people-head-verb")).first
                section.evaluate("el => el.scrollIntoView({block: 'start'})")
                _settle(page)
                body = section.inner_text()
                walk.fact("day2-carry", "people_after_completion",
                          "no OPEN COMMITMENT for the completed work",
                          "present" if "OPEN COMMITMENT" in body.upper() else "absent",
                          "MATCH" if "OPEN COMMITMENT" not in body.upper() else "MISMATCH",
                          "the completed commitment stops being owed on the People section")
                assert "OPEN COMMITMENT" not in body.upper(), body[:400]
                walk.shot(page, "day2-people-clear")
                _enter_prepare(page)
                captions = page.evaluate(
                    """() => Array.from(document.querySelectorAll(
                         '[data-testid="prepare-posture"] .surface-section-head h3'))
                       .map(el => el.textContent.trim())"""
                )
                carried = [c for c in captions if c.startswith("CARRIED FORWARD")]
                carried_text = page.get_by_test_id("prepare-carried").inner_text()
                walk.fact("day2-carry", "carried_forward_names_the_decision",
                          DECISION_TEXT,
                          DECISION_TEXT if DECISION_TEXT in carried_text else "(absent)",
                          "MATCH" if DECISION_TEXT in carried_text else "MISMATCH",
                          "day 2's preparation carries yesterday's decision: the loop closed")
                assert DECISION_TEXT in carried_text, carried_text
                # Four rows, not two: confirming EITHER kind writes the full
                # chain (decision record + commitment) by design
                # (holdspeak/services/proposal_bridge_service.py:588-590), so
                # each of yesterday's two confirmations is carried twice.
                walk.fact("day2-carry", "carried_forward_caption", "CARRIED FORWARD 4",
                          carried[0] if carried else "(absent)",
                          "MATCH" if carried == ["CARRIED FORWARD 4"] else "MISMATCH",
                          "2 decision records + 2 commitments from 2 confirmations")
                assert carried == ["CARRIED FORWARD 4"], captions
                carried_rows = [r.strip() for r in
                                page.get_by_test_id("prepare-carried")
                                .locator("li").all_inner_texts()]
                # THE SECOND FENCE this walk earned: the carried commitment's
                # DUE token is a DAY, not a wall clock.  Before the fix this
                # ledger called `clockToken` on a date-only value, so
                # `2026-09-20` was drawn `DUE 18:00` -- a date shown as a
                # time, and in a negative-offset zone the wrong day.
                due_expected = f"DUE {state['due_day'][5:]}"
                due_tokens = [t.strip() for t in
                              page.get_by_test_id("prepare-carried")
                              .locator(".surface-token").all_inner_texts()
                              if t.strip().startswith("DUE")]
                walk.fact("day2-carry", "carried_commitment_due",
                          due_expected, " / ".join(due_tokens) or "(none)",
                          "MATCH" if due_tokens == [due_expected] else "MISMATCH",
                          "a due DATE is drawn as a day, the way recall draws it")
                assert due_tokens == [due_expected], due_tokens
                walk.defects.append(
                    "FOUND AND FIXED by this walk: the preparation brief's "
                    "CARRIED FORWARD ledger drew a commitment's due DATE as a "
                    "wall clock -- `2026-09-20` rendered `DUE 18:00` "
                    "(web/src/features/project-room/prepare/PreparePosture.tsx "
                    "called `clockToken` on a date-only value, and "
                    "`new Date('2026-09-20')` is UTC midnight, so a "
                    "negative-offset desk also saw the wrong day). Recall says "
                    "`DUE 09-20` for the same commitment "
                    "(holdspeak/services/recall_service.py:93-105). Fix: "
                    "`dueDayToken` in "
                    "web/src/features/project-room/prepare/model.ts. Fence: the "
                    "`day2-carry` `carried_commitment_due` assertion here, "
                    "which fails pre-fix with "
                    "`assert ['DUE 18:00'] == ['DUE 09-20']`."
                )
                walk.fact("day2-carry", "carried_forward_rows",
                          "2 confirmed outcomes", " / ".join(carried_rows),
                          "DATA",
                          "read beside the shot: the emblems cross over "
                          "(`DEC Draft the rollback runbook`, "
                          "`CMT Rollback runbook is rehearsed ...`)")
                # THE FOURTH FENCE: no row is drawn as the wrong kind.  Each
                # CARRIED FORWARD row's emblem must match the kind of the
                # record it draws, whichever list it arrived in.  Before the
                # fix the emblem came from the list, so the commitment read
                # `DEC ... CURRENT` -- an action item presented as an
                # accepted decision.
                swapped = page.evaluate(
                    """([decisionText, commitmentText]) =>
                      Array.from(document.querySelectorAll(
                        '[data-testid="prepare-carried"] li')).map((li) => {
                        const emblem = (li.querySelector('.prepare-emblem')
                                        || {}).textContent || '';
                        const text = (li.querySelector('.surface-primary')
                                      || {}).textContent || '';
                        const wantsDec = text.trim() === decisionText;
                        const ok = wantsDec ? emblem.trim() === 'DEC'
                                            : emblem.trim() === 'CMT';
                        return ok ? null : emblem.trim() + ' :: ' + text.trim();
                      }).filter(Boolean)""",
                    [DECISION_TEXT, COMMITMENT_TEXT],
                )
                walk.fact("day2-carry", "carried_forward_kinds",
                          "every row drawn as the kind of record it is",
                          " / ".join(swapped) if swapped else "(no swapped row)",
                          "MATCH" if not swapped else "MISMATCH",
                          "a commitment drawn `DEC · CURRENT` presents an action "
                          "item as an accepted decision (ACCEPTANCE, critical "
                          "defects: invented decision acceptance)")
                assert swapped == [], swapped
                lifecycle_chips = page.evaluate(
                    """([commitmentText]) =>
                      Array.from(document.querySelectorAll(
                        '[data-testid="prepare-carried"] li'))
                        .filter((li) => ((li.querySelector('.surface-primary')
                                          || {}).textContent || '').trim()
                                        === commitmentText)
                        .flatMap((li) => Array.from(
                          li.querySelectorAll('.surface-state-chip'))
                          .map((c) => (c.getAttribute('aria-label')
                                       || c.textContent || '').trim()))""",
                    [COMMITMENT_TEXT],
                )
                assert "CURRENT" not in lifecycle_chips, lifecycle_chips
                walk.defects.append(
                    "FOUND AND FIXED by this walk: the preparation brief's "
                    "CARRIED FORWARD ledger drew each row as the kind of the "
                    "LIST it arrived in, not the kind of the record -- the "
                    "commitment read `DEC ... ✓ CURRENT` and the decision read "
                    "`CMT`. Presenting an action item as an accepted decision "
                    "is ACCEPTANCE's `Invented decision acceptance` line. The "
                    "kind was lost in the Room's own projection, which is "
                    "where it is now carried: "
                    "holdspeak/services/project_service.py "
                    "`_read_room_decisions` / `_read_room_commitments` add "
                    "`kind` from the confirmed proposal (the column "
                    "RecallService already reads, recall_service.py:193-196), "
                    "`build_manifest` "
                    "(holdspeak/services/preparation_brief_service.py) carries "
                    "it, and PreparePosture draws the emblem and the CURRENT "
                    "chip from it. Fence: the `day2-carry` "
                    "`carried_forward_kinds` assertion here, which fails "
                    "pre-fix with "
                    "`assert ['DEC :: Draft the rollback runbook', "
                    "'CMT :: Rollback runbook is rehearsed on the read replica "
                    "first'] == []`."
                )
                walk.surprises.append(
                    "FOR THE OWNER TO RULE: day two's brief lists yesterday's "
                    "two confirmed outcomes FOUR times -- each one appears once "
                    "as a decision and once as a commitment. That is not a bug: "
                    "confirming either kind deliberately records both "
                    "(holdspeak/services/proposal_bridge_service.py:588-590), so "
                    "the Room holds two entries per outcome and the brief lists "
                    "both. Each row is now labelled truthfully (DEC / CMT), so "
                    "the question left is only whether the brief should show the "
                    "pair or fold it into one row. Left as built."
                )
                walk.surprises.append(
                    "PRODUCT GAP, not a rig limit: no owner can choose a "
                    "DETERMINISTIC brief today. "
                    "`POST /api/projects/{id}/briefs/prepare` accepts "
                    "`generator: \"deterministic\"` "
                    "(holdspeak/services/preparation_brief_service.py:890-912) "
                    "and the face never sends it "
                    "(web/src/features/project-room/prepare/api.ts), so every "
                    "brief prepared through the Room goes to a model route. This "
                    "walk therefore proves the model path with a CONTROLLED "
                    "adapter on 127.0.0.1, never a live model; the deterministic "
                    "path is unreachable without a face change (R16-4) and is "
                    "unproved on glass."
                )
                page.get_by_role("textbox", name="Purpose").fill(PURPOSE_D2)
                assert not page.get_by_test_id("prepare-verb").is_disabled()
                walk.end(_coverage(page))
                walk.shot(page, "day2-prepare")

                _assert_clean(page, walk.errors)
                browser.close()
        finally:
            hub_thread = server2._thread
            server2.stop()
            if hub_thread is not None:
                hub_thread.join(120)
            release_database()
    finally:
        llm.stop()
        walk.write()

    assert walk.errors == [], walk.errors
    assert [f for f in walk.facts if f["verdict"] == "MISMATCH"] == []
