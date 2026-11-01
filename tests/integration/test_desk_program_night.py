"""PG-LANG LANG12 / JRN2 over REST and MCP: Add to tonight.

``POST /api/programs/tonight`` {kind, item_id, line?, program_id?} and the
MCP tool ``program.add_to_night`` reach the one ``ProgramService`` verb
(``tests/unit/test_program_night.py`` covers the rules): the answer names
the step and says it in his words; a refusal is a named code. The answers
are stored for the Tonight verb's face (``tonight.added.json``,
``tonight.refused.json`` under ``web/src/desk/programs/__fixtures__``).
"""
from __future__ import annotations

from typing import Any

from holdspeak.mcp import palettes
from holdspeak.mcp.families import program as program_family
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
from tests.integration.program_night_seed import door_task, make_night
from tests.integration.program_rig import OWNER, Rig
from tests.integration.test_desk_programs import _client, _fixture


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.request.url, response.status_code, response.text[:600])
    return response.json()


def test_add_to_tonight_over_rest_and_mcp(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    client = _client(rig, monkeypatch)
    none = client.post("/api/programs/tonight", json={"kind": "action", "item_id": door_task(rig, "x")})
    assert none.status_code == 409 and none.json()["code"] == "no_night_program"
    # The face's half (JRN2, the Tonight verb) replays these answers.
    _fixture("tonight.refused.json", {"status": none.status_code, "body": none.json()}, tmp_path)

    pid, sids = make_night(rig)
    task = door_task(rig, "The Notes toolbar wraps at 520.")
    added = _ok(client.post("/api/programs/tonight", json={"kind": "action", "item_id": task}))
    assert added["added"] is True and added["program_id"] == pid and added["ordinal"] == 4
    assert added["say"] == "Added to tonight: step 4 · The Notes toolbar wraps at 520."
    _fixture("tonight.added.json", added, tmp_path)
    step = next(row for row in added["program"]["steps"] if row["id"] == added["step_id"])
    assert step["origin_ref"] == f"action:{task}" and step["state"] in ("planned", "ready")
    again = _ok(client.post("/api/programs/tonight", json={"kind": "action", "item_id": task, "program_id": pid}))
    assert again["added"] is False and again["step_id"] == added["step_id"]
    bad = client.post("/api/programs/tonight", json={"kind": "meeting", "item_id": "m1"})
    assert bad.status_code == 400 and bad.json()["code"] == "night_kind_invalid"

    # MCP: the same verb, WORK (so CONDUCTOR offers it).
    assert TOOL_AUTHORITY["program.add_to_night"] == WORK
    assert "program.add_to_night" in palettes.resolve_palette(palettes.CONDUCTOR)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    other = door_task(rig, "The Line word lags 40 s.")
    over_mcp = program_family.dispatch("program.add_to_night", {"kind": "action", "item_id": other}, OWNER)
    assert over_mcp["added"] is True and over_mcp["ordinal"] == 5
    assert [step["ordinal"] for step in rig.program(pid)["steps"]] == [1, 2, 3, 4, 5]


def test_a_dreaming_program_in_drafting_is_recorded_for_its_face(tmp_path, monkeypatch) -> None:
    """#1697's Dreaming template, made through the real route and read in
    Drafting: the face's fixture (``program.dreaming.json``): its night line
    tells the window when it sleeps and what the night will do."""
    rig = Rig(tmp_path)
    client = _client(rig, monkeypatch)
    made = _ok(client.post("/api/programs", json={"title": "Dreaming · HoldSpeak", "template": "dreaming",
                                                   "repository": str(rig.repo)}), 201)
    pid = str(made.get("id") or (made.get("program") or {}).get("id"))
    wire = _ok(client.get(f"/api/programs/{pid}"))
    assert wire["state"] == "drafting" and wire["template"] == "dreaming" and wire["night"]
    _fixture("program.dreaming.json", wire, tmp_path)
