#!/usr/bin/env python3
"""Record the hub's own answers for the Needs-you face tests (the test diet, 2026-10-11).

The face tests in ``web/src/desk/__tests__/needsYou.app.test.tsx`` and
``needsChair.app.test.tsx`` replay these answers through a mocked ``apiFetch``.
Every answer here comes from the real hub (``MeetingWebServer`` through
``TestClient``) on an isolated HOME and database, seeded with the browser
tests' own seeds (``tests/unit/test_desk_needs_you.py``). Nothing is typed by
hand, so no field the face reads can be invented (the SCAR LAW).

Run it again when a producer's answer shape changes:

    HOME=$(mktemp -d) uv run python scripts/record_needs_you_fixture.py

It writes ``web/src/desk/__tests__/fixtures/needsYou.recorded.json``.

``--rows`` records only the Needs-you rows scenario (the owner's own action
items an agent titled ``Must fix:``, ``Should fix:``, ``Noted:``, one plain
and one a person owes; Done on the first) into
``web/src/desk/needs/__fixtures__/needs_you.rows.json``, and beside it the
Program row scenario (a Program step that waits for his Merge, on the
Programs rig behind the same hub; Merge pressed, the read after) under
``program``, and the one Done scenario (a Room commitment and a People
promise, Done on each) under ``done``.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests" / "unit"))

import test_desk_brief as brief_seeds  # noqa: E402
import test_desk_needs_you as seeds  # noqa: E402

from holdspeak.runtime import composition  # noqa: E402

OUT = REPO / "web" / "src" / "desk" / "__tests__" / "fixtures" / "needsYou.recorded.json"
ROWS_OUT = REPO / "web" / "src" / "desk" / "needs" / "__fixtures__" / "needs_you.rows.json"

# The reads the Chair and the Settings window make (found by replaying the
# face with an empty table and listing every path it asked for).
COMMON_GETS = ("/api/desk/needs-you?fresh=1", "/api/door", "/api/inference/assignments")
SETTINGS_GETS = (
    "/api/settings",
    "/api/settings/hub",
    "/api/authority/policy",
    "/api/connections",
)


def _get(hub: Any, path: str) -> Any:
    response = hub.client.get(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _post(hub: Any, path: str, body: dict[str, Any] | None = None) -> Any:
    response = hub.client.post(path, json=body) if body is not None else hub.client.post(path)
    assert response.status_code == 200, (path, response.status_code, response.text[:300])
    return response.json()


def _gets(hub: Any, paths: tuple[str, ...]) -> dict[str, Any]:
    return {path: _get(hub, path) for path in paths}


def _boot(name: str, mp: pytest.MonkeyPatch, **kwargs: Any) -> Any:
    root = Path(tempfile.mkdtemp(prefix=f"needs-you-{name}-"))
    return seeds._boot(root, mp, **kwargs)


def _close() -> None:
    from holdspeak.db import reset_database

    reset_database()
    composition.install(composition.bare(label="record"))


def _seed_waiting_meeting(hub: Any) -> None:
    """Betterment daily D8: one recorded meeting with words and no summary, so
    "No engine for summaries" has a meeting to ask for (a fresh desk with no
    meeting has no row)."""
    from datetime import datetime

    from holdspeak.meeting_session.models import MeetingState, TranscriptSegment

    start = datetime.now().replace(microsecond=0) - timedelta(hours=1)
    hub.db.meetings.save_meeting(MeetingState(
        id="m-cold-waits", started_at=start, ended_at=start + timedelta(minutes=20),
        title="Cutover check-in",
        segments=[TranscriptSegment(text="We freeze ledger writes on Friday.", speaker="Me",
                                    start_time=0.0, end_time=5.0)],
        intel_status="pending"))


def cold() -> dict[str, Any]:
    """A fresh HOME: no engine assigned; one meeting waits for its summary."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("cold", mp)
        try:
            _seed_waiting_meeting(hub)
            return {"gets": _gets(hub, COMMON_GETS)}
        finally:
            _close()


def unfiled() -> dict[str, Any]:
    """PHILO-15 08: an unfiled meeting's action and decision proposals, one hub boot.

    Confirm the action, then Defer the decision; every answer is read after each press."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("unfiled", mp)
        try:
            ids = seeds._seed_unfiled(hub)
            before = _gets(hub, COMMON_GETS)
            decision = next(
                row["proposalId"] for row in before["/api/desk/needs-you?fresh=1"]["items"]
                if row.get("proposalKind") == "decision"
            )
            confirm_path = f"/api/proposals/{ids['proposal_id']}/confirm"
            confirmed = _post(hub, confirm_path)
            after_confirm = _gets(hub, COMMON_GETS)
            defer_path = f"/api/proposals/{decision}/defer"
            deferred = _post(hub, defer_path, {})
            after_defer = _gets(hub, COMMON_GETS)
            return {
                "action": seeds.ACTION,
                "decision": seeds.DECISION,
                "steps": [
                    {"name": "before", "gets": before},
                    {"name": "confirm", "post": confirm_path, "answer": confirmed, "gets": after_confirm},
                    {"name": "defer", "post": defer_path, "answer": deferred, "gets": after_defer},
                ],
            }
        finally:
            _close()


def arrival() -> dict[str, Any]:
    """HS-172: a Room's ran meeting with an action and a decision proposal, one hub boot.

    The read before Confirm, Confirm on the action, the read after."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("arrival", mp)
        try:
            seeds._seed_hs172(hub)
            before = _gets(hub, COMMON_GETS)
            action = next(
                row for row in before["/api/desk/needs-you?fresh=1"]["items"]
                if row.get("proposalKind") == "action"
            )
            confirm_path = f"/api/proposals/{action['proposalId']}/confirm"
            confirmed = _post(hub, confirm_path)
            return {
                "action": action["title"],
                "steps": [
                    {"name": "before", "gets": before},
                    {"name": "confirm", "post": confirm_path, "answer": confirmed,
                     "gets": _gets(hub, COMMON_GETS)},
                ],
            }
        finally:
            _close()


def grouped() -> dict[str, Any]:
    """PHILO-17: 30 signed-out GitHub sources (the producer's baseline errors), plus Settings' reads."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("grouped", mp, gh_runner=seeds._signed_out_gh)
        try:
            rooms = {}
            for key, name in (("a", "Payments ledger"), ("b", "Staff hiring")):
                created = _post(hub, "/api/projects", {
                    "name": name, "description": "PHILO-17 grouped sources", "command_id": f"p17-room-{key}"})
                rooms[key] = created["project"]["id"]
            for n in range(30):
                room = rooms["a"] if n % 2 == 0 else rooms["b"]
                seeds._insert_watch(hub, f"w-gh-{n}", room, "gh", "pull_requests",
                                    {"repository": f"acme/repo-{n:02d}"})
                assert hub.client.post(f"/api/watches/w-gh-{n}/baseline", json={}).status_code >= 400
            seeds._insert_watch(hub, "w-gh-paused", rooms["b"], "gh", "pull_requests",
                                {"repository": "acme/paused"},
                                last_success_at=seeds._utc_naive(-timedelta(minutes=5)))
            _post(hub, "/api/watches/w-gh-paused/pause", {})
            return {"gets": _gets(hub, COMMON_GETS + SETTINGS_GETS)}
        finally:
            _close()


BRIEF_GETS = COMMON_GETS + ("/api/brief/latest",)


def _summaries(name: str, *, off: bool) -> dict[str, Any]:
    """PHILO-15 01: the LAN model as the global default (and, when `off`, an
    imported meeting with summaries turned off). The reads before Generate,
    Generate on the Brief, the reads after (one hub boot)."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot(name, mp)
        try:
            brief_seeds.assign_lan_default()
            if off:
                brief_seeds.seed_imported_meeting()
                brief_seeds.turn_summaries_off()
            before = _gets(hub, BRIEF_GETS)
            generated = _post(hub, "/api/brief/generate")
            return {"steps": [
                {"name": "before", "gets": before},
                {"name": "generate", "post": "/api/brief/generate", "answer": generated,
                 "gets": _gets(hub, BRIEF_GETS)},
            ]}
        finally:
            _close()


def calendar() -> dict[str, Any]:
    """HS-145: the meeting path pinned; no calendar (the Connect calendar offer,
    with the Settings window's reads), then one source whose only event is
    two hours ago, applied by the real ingest conductor (the quiet arrival)."""
    from datetime import datetime, timezone

    sys.path.insert(0, str(REPO))
    from tests.e2e.glass_infra import seed_meeting_engines

    from holdspeak.calendar_ingest_conductor import CalendarIngestConductor

    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("calendar", mp)
        try:
            seed_meeting_engines()
            none = _gets(hub, COMMON_GETS + SETTINGS_GETS + ("/api/calendar/sources",))
            past = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(hours=2)
            ics = Path(tempfile.mkdtemp(prefix="needs-you-ics-")) / "empty-calendar.ics"
            ics.write_text("\r\n".join([
                "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//HoldSpeak//HS-145 polish//EN",
                "BEGIN:VEVENT", "UID:hs145-past-only",
                f"DTSTART:{past.strftime('%Y%m%dT%H%M%SZ')}",
                f"DTEND:{(past + timedelta(minutes=30)).strftime('%Y%m%dT%H%M%SZ')}",
                "SUMMARY:Past event only", "END:VEVENT", "END:VCALENDAR", "",
            ]), encoding="utf-8")
            response = hub.client.put("/api/settings", json={"calendar": {"sources": [
                {"id": "hs145-fixture", "label": "Polish", "url": str(ics), "enabled": True}]}})
            assert response.status_code == 200, response.text
            assert CalendarIngestConductor().refresh() is True
            return {"none": {"gets": none}, "quiet": {"gets": _gets(hub, COMMON_GETS)}}
        finally:
            _close()


def eval_error() -> dict[str, Any]:
    """PHILO-17 (evalerror): two live GitHub Watches, gh signed out with secrets
    in its stderr; the owner's Evaluate (route) and an agent's (MCP), one boot."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("eval-error", mp, gh_runner=seeds._signed_out_gh_with_secrets)
        try:
            sys.path.insert(0, str(REPO))
            from tests.e2e.glass_infra import seed_meeting_engines

            seed_meeting_engines()
            seeds.seed_eval_error_room(hub)
            before = _gets(hub, COMMON_GETS)
            route, mcp = seeds.evaluate_both(hub)
            assert route.status_code == 400 and mcp.status_code == 200, (route.text, mcp.text)
            return {"secrets": list(seeds.EVAL_SECRETS),
                    "steps": [{"name": "before", "gets": before},
                              {"name": "evaluated", "gets": _gets(hub, COMMON_GETS)}]}
        finally:
            _close()


#: The rows the owner saw on 2026-11-08: an agent's findings, titled by
#: their weight, all his own (owner ``me``, no due date: the hub says YOURS).
ROWS = (
    ("rows-noted", "Noted: the Dock badge reads the count twice", "me"),
    ("rows-should", "Should fix: the walk sheet keeps its old height", "me"),
    ("rows-plain", "Book the cutover dry run", "me"),
    ("rows-must", "Must fix: openSystemShade() fires an event nobody hears", "me"),
    ("rows-theirs", "Send the vendor contract", "Bea"),
)


def rows() -> dict[str, Any]:
    """The Needs-you rows scenario: one synced meeting with the ROWS above,
    the read, Done on the Must fix row (the row's one verb), the read after."""
    from datetime import datetime, timezone

    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("rows", mp)
        try:
            now = datetime.now(timezone.utc)
            meeting_id = "rows-findings-meeting"
            pushed = _post(hub, "/api/sync/push", {"meetings": [{
                "meta": {"id": meeting_id, "kind": "meeting", "last_modified": now.isoformat(), "deleted": False},
                "value": {
                    "id": meeting_id, "started_at": (now - timedelta(minutes=30)).isoformat(),
                    "ended_at": now.isoformat(), "title": "Audit findings", "tags": [], "segments": [],
                    "bookmarks": [], "capture_status": "finalized", "transcription_status": "active",
                    "provenance": "native",
                    "intel": {
                        "timestamp": now.timestamp(), "topics": [], "summary": "The audit's findings.",
                        "action_items": [
                            {"id": item_id, "task": task, "owner": owner, "due": None,
                             "status": "pending", "review_state": "accepted", "created_at": now.isoformat()}
                            for item_id, task, owner in ROWS
                        ],
                    },
                },
            }]})
            assert pushed["received"]["meetings"] == 1, pushed
            before = _gets(hub, COMMON_GETS)
            must = next(row for row in before["/api/desk/needs-you?fresh=1"]["items"]
                        if str(row.get("title", "")).startswith("Must fix:"))
            done = {"card_id": str(must.get("actionItemId") or must.get("ref")), "verb": "done", "payload": {}}
            answer = _post(hub, "/api/follow-through/complete", done)
            return {
                "must": must["title"],
                "steps": [
                    {"name": "before", "gets": before},
                    {"name": "done", "post": "/api/follow-through/complete", "body": done, "answer": answer,
                     "gets": _gets(hub, COMMON_GETS)},
                ],
            }
        finally:
            _close()


def done_rows() -> dict[str, Any]:
    """The one Done scenario (2026-11-08): a Room commitment (a kept meeting
    action, the browser seed of tests/unit/test_desk_needs_you.py) and a
    People promise (I owe Priya), each a Needs-you row. The read, Done on
    each through the route its row names, the read after each."""
    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("done", mp)
        try:
            seeds._seed_hs172(hub)
            action = next(p for p in _get(hub, "/api/projects/proj-a/proposals")["proposals"]
                          if p["kind"] == "action" and p["state"] == "proposed")
            # His own promise with a day: the row's one verb is Done.
            _post(hub, f"/api/proposals/{action['id']}/confirm", {"owner": "me"})
            _post(hub, "/api/people/setup", {})
            rid = hub.client.post("/api/people/relationships", json={"display_name": "Priya Raman"}).json()["relationship"]["id"]
            request = hub.client.post(f"/api/people/relationships/{rid}/requests", json={
                "body": "Send Priya the rollout plan", "visibility": "shared_intent", "source": {"kind": "manual"},
            }).json()["request"]
            _post(hub, f"/api/people/requests/{request['id']}/accept", {})
            before = _gets(hub, COMMON_GETS)
            items = before["/api/desk/needs-you?fresh=1"]["items"]
            commitment = next(row for row in items if row.get("source") == "commitment")
            promise = next(row for row in items if row.get("source") == "people_commitment")
            card = promise["_doorCard"]
            people_verb = next(v for v in card["lawful_verbs"] if v["name"] == "people.commitment.transition"
                               and v["arguments"]["verb"] == "done")
            steps: list[dict[str, Any]] = [{"name": "before", "gets": before}]
            done = {"card_id": str(commitment["actionItemId"]), "verb": "done", "payload": {}}
            steps.append({"name": "commitment-done", "post": "/api/follow-through/complete", "body": done,
                          "answer": _post(hub, "/api/follow-through/complete", done), "gets": _gets(hub, COMMON_GETS)})
            path = f"/api/people/commitments/{people_verb['arguments']['commitment_id']}/transition"
            body = {"verb": "done"}
            steps.append({"name": "people-done", "post": path, "body": body,
                          "answer": _post(hub, path, body), "gets": _gets(hub, COMMON_GETS)})
            return {"commitment": commitment["title"], "promise": promise["title"], "steps": steps}
        finally:
            _close()


def program_merge() -> dict[str, Any]:
    """The Program row scenario: the hub of the rows scenario, its Program
    service the Programs rig (real git, a fake agent and reviewer at the
    process edge): one secure step built, checked and reviewed waits for his
    Merge. The read, Merge on the row (its one verb), the read after."""
    sys.path.insert(0, str(REPO))
    from holdspeak.services import program_service as program_module
    from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

    with pytest.MonkeyPatch.context() as mp:
        hub = _boot("program", mp)
        try:
            rig = Rig(Path(tempfile.mkdtemp(prefix="needs-you-program-rig-")))
            mp.setattr(program_module, "default_program_service", lambda db=None: rig.service)
            pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Make the hub stop stalling.",
                                     repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                                     template="build-and-review", control="secure",
                                     reviewer_profile="codex-default")["id"]
            rig.service.plan(OWNER, pid, steps=[
                {"title": "Indexes", "brief": "Add the three indexes.", "owns": ["holdspeak/db/schema.py"]}])
            rig.service.start(OWNER, pid)
            rig.agent.finish(rig.step(pid, 1)["launch_id"], {"holdspeak/db/schema.py": "-- indexes\n"})
            rig.tick(2)
            for reviewer in [record for record in rig.ledger.list() if record.get("helper_of")]:
                rig.words[reviewer["launch_id"]] = "MUST: none"
                rig.states[reviewer["launch_id"]] = {"state": "done", "turn_id": "r"}
            rig.tick(2)
            step = rig.step(pid, 1)
            assert step["state"] == "merge_ask", step["state"]
            before = _gets(hub, COMMON_GETS)
            merge = next(row for row in before["/api/desk/needs-you?fresh=1"]["items"]
                         if row.get("source") == "program")
            body = {"kind": merge["program"]["kind"], "choice": "merge"}
            answer = _post(hub, merge["program"]["decide"], body)
            rig.tick(2)
            text = json.dumps({"title": merge["group"], "steps": [
                {"name": "before", "gets": before},
                {"name": "merge", "post": merge["program"]["decide"], "body": body, "answer": answer,
                 "gets": _gets(hub, COMMON_GETS)},
            ]}, default=str)
            # The rig's temporary paths are not the face's business.
            root = rig.repo.parent
            return json.loads(text.replace(str(root.resolve()), "/tmp/rig").replace(str(root), "/tmp/rig"))
        finally:
            _close()


def main() -> int:
    if "--rows" in sys.argv[1:]:
        ROWS_OUT.parent.mkdir(parents=True, exist_ok=True)
        ROWS_OUT.write_text(json.dumps({"schema": "needs-you-rows@1", "recordedBy": "scripts/record_needs_you_fixture.py --rows",
                                        **rows(), "program": program_merge(), "done": done_rows()}, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(f"wrote {ROWS_OUT.relative_to(REPO)} ({ROWS_OUT.stat().st_size} bytes)")
        return 0
    fixture = {
        "schema": "needs-you-recorded@1",
        "recordedBy": "scripts/record_needs_you_fixture.py",
        "cold": cold(),
        "unfiled": unfiled(),
        "arrival": arrival(),
        "grouped": grouped(),
        "lanDefault": _summaries("lan-default", off=False),
        "summariesOff": _summaries("summaries-off", off=True),
        "calendar": calendar(),
        "evalError": eval_error(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(fixture, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
