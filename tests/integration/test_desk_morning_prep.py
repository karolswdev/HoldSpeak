"""Betterment daily D9: Morning prep (owner decision 3), against a real hub.

A real MeetingWebServer (``tests/e2e/glass_infra._boot``: isolated HOME and
DB, the rig switches). The recon's week (tests/fixtures/daily_week/) is seeded
through the product's own producers, with its day on the calendar (the 1:1
with Mira in 90 minutes). The engine with the desk's tools is the fake
``claude`` (tests/fixtures/fake_agent_cli.py): it replays its tool plan over
MCP to this hub and answers the Morning prep form. The owner's real CLIs never
run.

The face's half (web/src/desk/__tests__/today.app.test.tsx) renders the
answers this test records in fixtures/daily-week/today-prepared.json
(``HOLDSPEAK_WIRE_WRITE=1`` rewrites it; else its shape is fenced).
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.e2e.glass_infra import _boot
from tests.fixtures.fake_agent_cli import install_fake_agent_clis, mcp_runs, path_with, set_claude_answer, set_tool_plan

TOKEN = "desk-morning-prep"
WIRES = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "daily-week"

pytestmark = pytest.mark.timeout(240, method="thread")


class _HttpHub:
    """The fixture's Hub shape (``client`` + ``db``) over a listening hub, so
    the fake agent CLI can reach its MCP route."""

    def __init__(self, base: str) -> None:
        self.client = httpx.Client(base_url=base, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=120)

    @property
    def db(self) -> Any:
        from holdspeak.db import get_database

        return get_database()


@pytest.fixture()
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    bin_dir = install_fake_agent_clis(tmp_path / "home" / "bin")
    monkeypatch.setenv("PATH", path_with(bin_dir))
    monkeypatch.setenv("HOLDSPEAK_CLI_ENGINES", "on")
    rig = _HttpHub(base)
    rig.bin_dir = bin_dir  # type: ignore[attr-defined]
    try:
        yield rig
    finally:
        rig.client.close()
        server.stop()


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.status_code, response.text)
    return response.json()


def _connect_claude(hub: _HttpHub) -> None:
    """Claude Code as the automations' engine (``workbench.item``)."""
    connected = _ok(hub.client.post("/api/inference/model-library/connect-cli-engine", json={"draft": {
        "request_id": "connect-claude", "profile_id": "agent-claude", "expected_profile_revision": 0,
        "preset": "claude"}}))
    entry = {"profile_id": connected["provider"]["profile_id"],
             "profile_revision": int(connected["provider"]["profile_revision"])}
    _ok(hub.client.post("/api/inference/assignments/set", json={
        "command_id": "assign-workbench-item", "expected_revision": 0,
        "scope": {"kind": "capability", "capability_id": "workbench.item"}, "entries": [entry]}))


def _answer(mira_at: str) -> str:
    """What the agent answers: the Morning prep form (the starter's Do)."""
    return "\n".join([
        f"## {mira_at} 1:1 with Mira",
        "- Mira owes: Draft the rollback runbook (due Tue)",
        "- I owe: Nothing",
        "- Raise: Who owns read-only vs archive for the old ledger?",
        "## Mine today",
        "- Email Dana about the cutover window",
        "- Review design doc on settlement retries",
        "## Nudges",
        "- Theo: Are the load test numbers on track for Wednesday?",
    ])


def test_morning_prep_is_made_on_once_and_its_result_is_todays_prepared_block(hub: _HttpHub) -> None:
    """Done when (D9): with an engine that has the desk's tools, Morning prep
    exists, On, weekdays 07:30, made once; Run now (Prepare now) makes ONE
    result whose Put it in is Today; Today's read names the engine and what
    the agent looked at; Add on a suggested point puts it on Mira's agenda."""
    from holdspeak.services.automation_runs import ensure_morning_prep
    from holdspeak.workbench_templates import MORNING_PREP_ID
    from tests.fixtures.daily_week import WEEK, seed
    from tests.unit.test_desk_brief import _calendar_today, _ensured
    from tests.unit.test_desk_speak import _record

    seeded = seed(hub, monday=date.today(), engine=True)
    _calendar_today(hub, seeded["Mira"])  # type: ignore[arg-type]
    db = hub.db

    # No engine with the desk's tools (the LAN engine is an HTTP model): no
    # Morning prep, and Today has nothing to show.
    assert ensure_morning_prep(db) is None
    assert _ok(hub.client.get("/api/automations/prepared")) == {"prepared": None, "automation": None}

    _connect_claude(hub)
    assert ensure_morning_prep(db) == MORNING_PREP_ID
    made = _ok(hub.client.get(f"/api/workbenches/{MORNING_PREP_ID}"))["workbench"]
    assert (made["name"], made["output_target"], made["schedule"], made["schedule_enabled"]) == (
        "Morning prep", "today", "30 7 * * 1-5", True), made
    assert made["when_kind"] == "schedule" and made["next_run_at"], made
    assert made["assignment_summary"]["chain"], made["assignment_summary"]
    # Once only: made, it is never made again; turned off or deleted, it stays so.
    assert ensure_morning_prep(db) is None
    _ok(hub.client.put(f"/api/workbenches/{MORNING_PREP_ID}", json={"schedule_enabled": False}))
    assert ensure_morning_prep(db) is None
    assert _ok(hub.client.get(f"/api/workbenches/{MORNING_PREP_ID}"))["workbench"]["schedule_enabled"] is False
    # The starter is offered in New automation too, with Put it in Today.
    starters = _ok(hub.client.get("/api/workbench-templates"))["templates"]
    morning = next(s for s in starters if s["id"] == "morning-prep")
    assert (morning["schedule"], morning["output_target"]) == ("30 7 * * 1-5", "today")

    # Before a run: the automation is known (Prepare now), no block yet.
    before = _ok(hub.client.get("/api/automations/prepared"))
    assert before == {"prepared": None, "automation": {"id": MORNING_PREP_ID, "name": "Morning prep"}}, before

    door = _ok(hub.client.get("/api/door"))
    event = next(e for e in door["upcoming"] if e.get("title") == "1:1 with Mira")
    mira_at = datetime.fromisoformat(event["starts_at"].replace("Z", "+00:00")).astimezone().strftime("%H:%M")
    meetings = [m["id"] for m in WEEK["meetings"]]
    set_tool_plan(hub.bin_dir, "claude", [  # type: ignore[attr-defined]
        {"name": "desk.needs_you", "arguments": {}},
        {"name": "people.one_on_one.brief", "arguments": {"relationship_id": seeded["Mira"]}},
        *({"name": "meeting.get", "arguments": {"meeting_id": m}} for m in meetings),
    ], once=True)
    set_claude_answer(hub.bin_dir, _answer(mira_at))  # type: ignore[attr-defined]

    # Prepare now = Run now on the Morning prep automation.
    ran = _ok(hub.client.post(f"/api/workbenches/{MORNING_PREP_ID}/run", json={}))["run"]
    assert [d["target"] for d in ran.get("deliveries") or []] == ["today"], ran

    (run,) = mcp_runs(hub.bin_dir, "claude")  # type: ignore[attr-defined]
    assert [c["status"] for c in run["calls"]] == [200] * (2 + len(meetings)), run["calls"]
    after = _ok(hub.client.get("/api/automations/prepared"))
    prepared = after["prepared"]
    assert prepared is not None, after
    assert prepared["workbench_id"] == MORNING_PREP_ID and prepared["name"] == "Morning prep"
    assert prepared["engine"] == made["assignment_summary"]["chain"][0], (prepared["engine"], made["assignment_summary"])
    result = prepared["result"]
    assert result["status"] == "done" and result["new"] is True, result
    assert result["text"].startswith(f"## {mira_at} 1:1 with Mira"), result["text"]
    looked = [row["ref"] for row in (result["used"] or {}).get("looked_at", [])]
    assert looked == [f"meeting:{m}" for m in meetings], result["used"]
    # One result, nothing filed in the Inbox and no Needs-you row for it.
    assert len(_ok(hub.client.get(f"/api/workbenches/{MORNING_PREP_ID}"))["workbench"]["results"]) == 1
    assert result["note_id"] is None

    reads = {
        "/api/desk/needs-you?fresh=1": _ok(hub.client.get("/api/desk/needs-you?fresh=1")),
        "/api/door": _ok(hub.client.get("/api/door")),
        "/api/brief/latest?ensure=1": _ensured(hub),  # type: ignore[arg-type]
        "/api/meetings?limit=40": _ok(hub.client.get("/api/meetings?limit=40")),
        "/api/automations/new": _ok(hub.client.get("/api/automations/new")),
        "/api/automations/prepared": after,
        f"/api/people/relationships/{seeded['Mira']}": _ok(
            hub.client.get(f"/api/people/relationships/{seeded['Mira']}")),
    }

    # Add on the suggested point: the face's two writes (the 1:1, then the
    # agenda item), and Mira's brief lists it under To raise.
    point = "Who owns read-only vs archive for the old ledger?"
    sessions = reads[f"/api/people/relationships/{seeded['Mira']}"]["relationship"].get("sessions") or []
    session = sessions[0]["id"] if sessions else _ok(hub.client.post(
        f"/api/people/relationships/{seeded['Mira']}/one-on-ones", json={"visibility": "shared_intent"}),
        201)["one_on_one"]["id"]
    _ok(hub.client.post(f"/api/people/one-on-ones/{session}/agenda", json={
        "body": point, "visibility": "shared_intent", "state": "open", "source": {"kind": "manual"}}), 201)
    brief = _ok(hub.client.get(f"/api/people/relationships/{seeded['Mira']}/brief"))["brief"]
    assert point in [a["body"] for a in brief["agenda_items"]], brief["agenda_items"]

    text = json.dumps({"recordedAt": datetime.now().astimezone().isoformat(), "miraAt": mira_at, "gets": reads})
    text = text.replace(seeded["project"], "proj-daily-week")
    for name in ("Mira", "Theo", "Jun"):
        text = text.replace(seeded[name], f"rel-{name.lower()}")
    _record("today-prepared", json.loads(text), Path(db.db_path).parent,
            "tests/integration/test_desk_morning_prep.py", folder=WIRES)


def test_put_it_in_today_is_a_choice_and_a_wrong_target_names_it(hub: _HttpHub) -> None:
    """The Put it in editor's Today choice saves; a wrong value says the four."""
    made = _ok(hub.client.post("/api/workbenches", json={"name": "Day notes", "instruction": "Say hi."}), 201)
    wb = made["workbench"]["id"]
    saved = _ok(hub.client.put(f"/api/workbenches/{wb}", json={"output_target": "today"}))["workbench"]
    assert saved["output_target"] == "today"
    refused = hub.client.put(f"/api/workbenches/{wb}", json={"output_target": "elsewhere"})
    assert refused.status_code == 400 and "today" in refused.text, refused.text
    # The automation Prepare now runs is the live one whose Put it in is Today.
    assert _ok(hub.client.get("/api/automations/prepared"))["automation"] == {"id": wb, "name": "Day notes"}
