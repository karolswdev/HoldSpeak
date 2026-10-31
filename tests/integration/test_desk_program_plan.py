"""PG-LANG LANG6 over REST and MCP: the planning draft.

``POST /api/programs/{id}/plan/draft`` {goal?, template?, budget?} answers
the draft's change rows in the ``text_apply`` shape (source ``plan``, an
added step's ``size``), the engine and its time; Apply is ``POST …/text``;
Split on a too-big row is the same route with {text, split}. The engine
replays REAL qwen3.8-27b replies through the runner (tests/unit/
test_program_planner.py). The face replays the answers stored here
(web/src/desk/programs/__fixtures__/program.plan_draft.json;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites it, else this test fences its shape).
"""
from __future__ import annotations

from typing import Any

from holdspeak.mcp.families import program as program_family
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
from tests.integration.program_plan_seed import CASES, create
from tests.integration.program_rig import OWNER, Rig
from tests.integration.test_desk_programs import _client, _fixture
from tests.unit.test_program_planner import case, replies, split_replies
from tests.unit.test_program_shaper import wire_engine


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.request.url, response.status_code, response.text[:600])
    return response.json()


def _desk(tmp_path, monkeypatch, key: str, *, engine: bool = True) -> tuple[Rig, Any, str, Any]:
    """The case's Program with its budget set (the text's ``budget 64k``):
    the face sends no budget, the hub reads the Program's."""
    rig = Rig(tmp_path / key)
    recorded = wire_engine(rig, monkeypatch) if engine else None
    pid = create(rig, CASES[key], file_bytes=case(key)["file_bytes"])
    return rig, recorded, pid, _client(rig, monkeypatch)


def test_plan_draft_over_rest_apply_and_split(tmp_path, monkeypatch) -> None:
    out: dict[str, Any] = {}
    # J1: two paragraphs become four steps, each sized to the 64k budget.
    rig, engine, pid, client = _desk(tmp_path, monkeypatch, "j1")
    before = _ok(client.get(f"/api/programs/{pid}"))
    out["engine"] = _ok(client.get(f"/api/programs/{pid}/shape"))
    engine.replies = replies("j1")
    draft = _ok(client.post(f"/api/programs/{pid}/plan/draft", json={"goal": CASES["j1"]["goal"]}))
    assert draft["source"] == "plan" and draft["engine"] == "qwen3.8-27b" and draft["applied"] is False
    assert draft["counts"] == {"steps": 4, "requirements": 6, "too_big": 0} and draft["share"] == 32768
    assert [row["size"]["words"] for row in draft["changes"] if row["size"]] == [
        "7k of 32k", "4k of 32k", "5k of 32k", "3k of 32k"]
    assert _ok(client.get(f"/api/programs/{pid}"))["steps"] == []
    applied = _ok(client.post(f"/api/programs/{pid}/text", json={
        "text": draft["allowed_text"], "base": draft["base"], "dry_run": False}))
    assert applied["applied"] is True
    assert [step["estimate"]["words"] for step in applied["program"]["steps"]] == [
        "7k of 32k", "4k of 32k", "5k of 32k", "3k of 32k"]
    out["j1"] = {"program": before, "draft": draft, "applied": applied}

    # A file over the working share: split once; what still does not fit is marked, with Split.
    rig_b, engine_b, pid_b, client_b = _desk(tmp_path, monkeypatch, "big_file")
    big_before = _ok(client_b.get(f"/api/programs/{pid_b}"))
    engine_b.replies = replies("big_file")
    big = _ok(client_b.post(f"/api/programs/{pid_b}/plan/draft", json={}))
    assert big["counts"]["too_big"] == 1 and big["split"][0]["place"] == 1
    too_big = [row for row in big["changes"] if row["size"] and row["size"]["code"] == "step_too_big"]
    assert [row["size"]["words"] for row in too_big] == ["Too big for Claude Code · 61k of 32k"]
    # Split on the row still too big: the draft he sees and the step's place.
    engine_b.replies = split_replies("big_file")
    split = _ok(client_b.post(f"/api/programs/{pid_b}/plan/draft", json={"text": big["proposed_text"], "split": 2}))
    assert [row["size"]["words"] for row in split["changes"] if row["size"]] == [
        "1k of 32k", "Too big for Claude Code · 61k of 32k", "Too big for Claude Code · 61k of 32k"]
    out["big_file"] = {"program": big_before, "draft": big, "split": split}

    # No engine: the refusal by name.
    rig_n = Rig(tmp_path / "none")
    pid_n = create(rig_n, CASES["j1"])
    client_n = _client(rig_n, monkeypatch)
    none = client_n.post(f"/api/programs/{pid_n}/plan/draft", json={})
    assert none.status_code == 409 and none.json()["code"] == "no_engine"
    out["no_engine"] = {"program": _ok(client_n.get(f"/api/programs/{pid_n}")), "status": none.status_code,
                        "body": none.json(), "engine": _ok(client_n.get(f"/api/programs/{pid_n}/shape"))}
    _fixture("program.plan_draft.json", out, tmp_path)


def test_program_plan_draft_is_an_mcp_tool_of_work_authority(tmp_path, monkeypatch) -> None:
    names = [tool["name"] for tool in program_family.TOOLS]
    assert "program.plan_draft" in names and TOOL_AUTHORITY["program.plan_draft"] == WORK
    schema = next(tool for tool in program_family.TOOLS if tool["name"] == "program.plan_draft")["inputSchema"]
    assert schema["required"] == ["program_id"]
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = create(rig, CASES["j1"], file_bytes=case("j1")["file_bytes"])
    from holdspeak.services import program_service as program_module

    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    engine.replies = replies("j1")
    answer = program_family.dispatch("program.plan_draft", {"program_id": pid}, OWNER)
    assert answer["counts"]["steps"] == 4 and answer["applied"] is False
    assert rig.service.get(OWNER, pid)["steps"] == []


def test_a_program_made_from_a_note_is_planned_from_the_note(tmp_path, monkeypatch) -> None:
    """Run as a program (``program.create`` with ``from note:``) keeps
    working; with no goal typed, the Note's words ground the plan."""
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    rig.db.notes.upsert(note_id="note-recap", title="Recap", body_markdown=CASES["j1"]["goal"], tags=[])
    pid = rig.service.create(OWNER, title="Meeting recap in the Note", repository=str(rig.repo), check_command="true",
                             template="build-and-review", control="normal", origin_ref="note:note-recap")["id"]
    assert rig.service.get(OWNER, pid)["origin_ref"] == "note:note-recap"
    engine.replies = replies("j1")
    answer = rig.service.plan_draft(OWNER, pid, budget="64k")  # a Program with no budget line: he names one
    assert "THE NOTE THE PROGRAM CAME FROM\n" + CASES["j1"]["goal"] in engine.prompts[0]["user_prompt"]
    assert answer["counts"]["steps"] == 4
