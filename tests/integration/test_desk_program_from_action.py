"""JRN13: Run as a program on a project's action row.

``POST /api/programs/from-action`` {action_id, project_id?} makes a Drafting
Program from one action: its goal is the action's words, its origin
``action:<id>`` (its merge closes the action), its Project the action's
(the Project's repository), and its person the owner only when exactly one
person has that name. Recorded for the Room's verb
(``web/src/desk/programs/__fixtures__/program.from_action*.json``).
"""
from __future__ import annotations

from types import SimpleNamespace

from holdspeak.timestamps import utc_now_iso
from tests.integration.program_rig import Rig
from tests.integration.test_desk_programs import _client, _fixture


def _action(rig: Rig, words: str, owner: str | None = None) -> str:
    now = utc_now_iso()
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
        conn.execute("INSERT INTO meetings (id, title, started_at, created_at) VALUES ('m-standup', 'Standup', ?, ?)",
                     (now, now))
        conn.execute("INSERT INTO meeting_projects (meeting_id, project_id) VALUES ('m-standup', 'proj-holdspeak')")
        conn.execute(
            "INSERT INTO action_items (id, meeting_id, task, owner, due, status, review_state, created_at, "
            "delegated_at, source_type, source_ref) VALUES ('ai_runme', 'm-standup', ?, ?, NULL, 'open', 'accepted', ?, "
            "NULL, 'meeting', '')", (words, owner, now))
    return "ai_runme"


def test_run_as_a_program_makes_a_drafting_program_from_the_action(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    # The project's repository is the rig's (the registry is the hand
    # service's, not in this rig).
    monkeypatch.setattr(rig.service, "_project_source", lambda project_id: SimpleNamespace(primary_path=str(rig.repo)))
    client = _client(rig, monkeypatch)
    action = _action(rig, "Move the People routes off the event loop and prove no handler holds it over 100 ms",
                     owner="Nobody we know")
    made = client.post("/api/programs/from-action", json={"action_id": action})
    assert made.status_code == 201, made.text
    pid = str(made.json().get("id") or (made.json().get("program") or {}).get("id"))
    wire = client.get(f"/api/programs/{pid}").json()
    assert wire["state"] == "drafting" and wire["origin_ref"] == f"action:{action}"
    assert wire["goal"].startswith("Move the People routes off the event loop")
    assert wire["place"]["project"] == {"id": "proj-holdspeak", "name": "HoldSpeak"}
    assert wire["place"]["origin"]["kind"] == "action" and wire["place"]["origin"]["title"]
    # An owner nobody has is never attributed.
    assert wire["for_person_id"] is None
    assert len(wire["title"]) <= 80
    _fixture("program.from_action.json", made.json(), tmp_path)
    _fixture("program.from_action.program.json", wire, tmp_path)

    unknown = client.post("/api/programs/from-action", json={"action_id": "ai_none"})
    assert unknown.status_code == 404 and unknown.json()["code"] == "action_unknown"
    _fixture("program.from_action.refused.json", {"status": unknown.status_code, "body": unknown.json()}, tmp_path)


def _needs(wire: dict) -> list[tuple[str, str]]:
    return [(str(row["id"]), step["id"]) for step in wire["steps"] for row in step.get("requirements") or []]


def _rows(wire: dict) -> dict[str, dict]:
    return {step["id"]: {"origin": step["origin_ref"], "gate": step["gate"]} for step in wire["steps"]}


def test_action_binding_wire(tmp_path, monkeypatch) -> None:
    """HS-S21 (D14/G21 = A): Add appends one row; only the row he binds
    carries the action. The rows before it keep their ids, origins, gates and
    step requirements. Recorded for the Add well and the fold's line
    (``program.action_binding.unbound.json`` / ``.bound.json``)."""
    rig = Rig(tmp_path)
    monkeypatch.setattr(rig.service, "_project_source", lambda project_id: SimpleNamespace(primary_path=str(rig.repo)))
    client = _client(rig, monkeypatch)
    action = _action(rig, "Move the People routes off the event loop", owner="Nobody we know")
    pid = client.post("/api/programs/from-action", json={"action_id": action}).json()
    pid = str(pid.get("id") or (pid.get("program") or {}).get("id"))
    # Made from the action: no step yet, and nothing carries it.
    made = client.get(f"/api/programs/{pid}").json()
    assert made["steps"] == [] and made["origin_ref"] == f"action:{action}"

    # An ordinary Add: one row, no origin (the Program's origin is not copied).
    first = client.post(f"/api/programs/{pid}/plan", json={"steps": [{
        "title": "Step 1", "brief": "", "gate_merge": "none"}], "replace": False, "size": None})
    assert first.status_code == 200, first.text
    step_one = client.get(f"/api/programs/{pid}").json()["steps"][0]
    assert step_one["origin_ref"] is None
    need = client.post(f"/api/programs/{pid}/requirements", json={"text": "No handler holds the loop", "step_id": step_one["id"]})
    assert need.status_code == 201, need.text
    unbound = client.get(f"/api/programs/{pid}").json()
    before = _rows(unbound)
    needs_before = _needs(unbound)
    assert any(step_id == step_one["id"] for _, step_id in needs_before), needs_before
    _fixture("program.action_binding.unbound.json", unbound, tmp_path)

    # The bound Add: the new row only carries the action.
    bound = client.post(f"/api/programs/{pid}/plan", json={"steps": [{
        "title": "Step 2", "brief": "", "origin_ref": f"action:{action}"}], "replace": False, "size": None})
    assert bound.status_code == 200, bound.text
    after = client.get(f"/api/programs/{pid}").json()
    rows = _rows(after)
    new = [step for step in after["steps"] if step["id"] not in before]
    assert len(new) == 1 and new[0]["origin_ref"] == f"action:{action}"
    assert {key: rows[key] for key in before} == before
    assert _needs(after) == needs_before
    _fixture("program.action_binding.bound.json", after, tmp_path)

    # A later ordinary Add stays unbound; the bound row keeps its origin.
    client.post(f"/api/programs/{pid}/plan", json={"steps": [{"title": "Step 3", "brief": ""}], "replace": False, "size": None})
    last = client.get(f"/api/programs/{pid}").json()
    assert [step["origin_ref"] for step in last["steps"]] == [None, f"action:{action}", None]
    assert [step["id"] for step in last["steps"]][:2] == [step["id"] for step in after["steps"]]
    # The action stays open: binding is not completion.
    status = next(str(row.status) for row in rig.db.meetings.list_action_items(include_completed=True) if str(row.id) == action)
    assert status == "open"
