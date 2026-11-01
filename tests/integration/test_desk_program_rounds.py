"""PG-LANG LANG9 over REST and MCP: the interview rounds.

``POST /api/programs/{id}/rounds`` opens the rounds; ``…/rounds/{name}/next``
asks one question; ``…/answer`` {question_id, answer | option | skip |
not_this} stores the answer and answers its change rows (source
``round:<name>``) in the ``text_apply`` shape; ``…/decide`` {choice: done |
skip | reopen}. The walk is the face's own (``SEQUENCE`` of
tests/integration/program_rounds_seed.py), from journey J1 at station 1:
Plan it, Ask me first (the draft applied, the rounds opened), Architecture's
question, an offered answer, the next question, Apply, Skip question, Done
with Architecture, Product and Stack skipped, Verification answered and
done. The engine replays REAL qwen3.8-27b replies through the runner
(tests/fixtures/program_plan_reply.json, program_round_reply.json). The face
replays the answers stored here (web/src/desk/programs/__fixtures__/
program.rounds.json; ``HOLDSPEAK_WIRE_WRITE=1`` rewrites it, else this test
fences its shape).
"""
from __future__ import annotations

from typing import Any

from holdspeak.mcp.families import program as program_family
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
from tests.integration.program_plan_seed import CASES, create
from tests.integration.program_rig import OWNER, Rig, give_quick_check
from tests.integration.program_rounds_seed import SEQUENCE, drafted
from tests.integration.test_desk_programs import _client, _fixture
from tests.unit.test_program_planner import case, replies
from tests.unit.test_program_rounds import RECORDED, ask_reply
from tests.unit.test_program_shaper import wire_engine


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.request.url, response.status_code, response.text[:600])
    return response.json()


def _round(program: dict[str, Any], name: str) -> dict[str, Any]:
    return next(row for row in program["rounds"] if row["name"] == name)


def test_the_rounds_over_rest_in_the_faces_own_walk(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = create(rig, CASES["j1"], file_bytes=case("j1")["file_bytes"])
    client = _client(rig, monkeypatch)
    out: dict[str, Any] = {"program": _ok(client.get(f"/api/programs/{pid}")),
                           "engine": _ok(client.get(f"/api/programs/{pid}/shape"))}
    assert out["program"]["rounds"] == []
    # Plan it: the recorded draft.
    engine.replies = replies("j1")
    out["draft"] = _ok(client.post(f"/api/programs/{pid}/plan/draft", json={}))
    # Ask me first: the draft's allowed rows applied, then the rounds opened.
    out["applied"] = _ok(client.post(f"/api/programs/{pid}/text", json={
        "text": out["draft"]["allowed_text"], "base": out["draft"]["base"], "dry_run": False, "allow_lower": []}))
    assert out["applied"]["applied"] is True and len(out["applied"]["program"]["steps"]) == 4
    out["opened"] = _ok(client.post(f"/api/programs/{pid}/rounds", json={}))
    assert [(row["name"], row["state"]) for row in out["opened"]["program"]["rounds"]] == [
        ("Architecture", "open"), ("Product", "open"), ("Stack", "open"), ("Verification", "open"), ("Delivery", "open")]
    # The face's walk, each step one route; the engine's replies in the recorded order.
    engine.replies = [exchange["reply_text"] for row in RECORDED["sequence"] for exchange in row["exchanges"]]
    steps: dict[str, Any] = {}
    last_answer: dict[str, Any] = {}
    for label, _call in SEQUENCE:
        name = label.split(".", 1)[0].capitalize()
        verb = label.split(".", 1)[1]
        base = f"/api/programs/{pid}/rounds/{name}"
        if verb.startswith("next"):
            answer = _ok(client.post(f"{base}/next", json={}))
        elif verb == "answer":
            question = steps[f"{name.lower()}.next"]["question"]
            answer = _ok(client.post(f"{base}/answer", json={"question_id": question["id"],
                                                             "option": question["choices"][0], "apply": False}))
            last_answer = answer
        elif verb == "apply":
            answer = _ok(client.post(f"/api/programs/{pid}/text", json={
                "text": last_answer["allowed_text"], "base": last_answer["base"], "dry_run": False, "allow_lower": []}))
        elif verb == "skip_question":
            waiting = steps[f"{name.lower()}.next2"]["question"]
            answer = _ok(client.post(f"{base}/answer", json={"question_id": waiting["id"], "skip": True}))
        else:
            answer = _ok(client.post(f"{base}/decide", json={"choice": verb}))
        steps[label] = answer
    assert engine.replies == []

    first = steps["architecture.next"]
    assert first["question"]["text"] == RECORDED["sequence"][0]["question"]["text"] and first["engine"] == "qwen3.8-27b"
    assert _round(first["program"], "Architecture")["state"] == "asking"
    answered = steps["architecture.answer"]
    assert answered["source"] == "round:Architecture" and answered["applied"] is False
    assert [(row["where"], row["field"], row["verdict"], row["source"]) for row in answered["changes"]] == [
        ("step 3", "brief", "allowed", "round:Architecture")]
    assert answered["round_question"]["became"] == ["step 3 brief"]
    assert steps["architecture.apply"]["applied"] is True
    # Done with Architecture after the second question was skipped.
    arch = _round(steps["architecture.done"]["program"], "Architecture")
    assert arch["state"] == "done" and arch["answered"] == 1 and arch["became"] == 1
    assert [item["skipped"] for item in arch["questions"]] == [False, True]
    assert _round(steps["product.skip"]["program"], "Product")["state"] == "skipped"
    assert _round(steps["stack.skip"]["program"], "Stack")["state"] == "skipped"
    final = steps["verification.done"]["program"]
    assert [(row["name"], row["state"]) for row in final["rounds"]] == [
        ("Architecture", "done"), ("Product", "skipped"), ("Stack", "skipped"), ("Verification", "done"),
        ("Delivery", "open")]

    # Not this on an answer's rows: the answer stays, it became nothing.
    verification = steps["verification.next"]["question"]
    out["not_this"] = _ok(client.post(f"/api/programs/{pid}/rounds/Verification/answer",
                                      json={"question_id": verification["id"], "not_this": True}))
    assert _round(out["not_this"]["program"], "Verification")["became"] == 0
    # Rounds never gate Start; the strip stays while it runs.
    give_quick_check(rig.repo)  # the recorded plan's check: Start's precheck reads it
    out["started"] = _ok(client.post(f"/api/programs/{pid}/start", json={}))
    assert out["started"]["state"] == "running" and _round(out["started"], "Architecture")["state"] == "done"
    # A done round asks nothing; Ask more opens it again, while it runs.
    closed = client.post(f"/api/programs/{pid}/rounds/Architecture/next", json={})
    assert closed.status_code == 409 and closed.json()["code"] == "round_closed"
    out["reopened"] = _ok(client.post(f"/api/programs/{pid}/rounds/Architecture/decide", json={"choice": "reopen"}))
    assert _round(out["reopened"]["program"], "Architecture")["state"] == "open"
    # The engine fails on the next question: the refusal names it; nothing is asked.
    engine.fail = True
    failed = client.post(f"/api/programs/{pid}/rounds/Architecture/next", json={})
    assert failed.status_code == 502 and failed.json()["code"] == "engine_failed"
    out["ask_failed"] = {"status": failed.status_code, "body": failed.json()}
    # The face replays its own walk; the rest of the walk is fenced here.
    face = ("architecture.next", "architecture.answer", "architecture.next2", "architecture.apply",
            "architecture.skip_question", "architecture.done", "product.next", "product.skip", "stack.next")
    out["steps"] = {label: steps[label] for label in face}
    _fixture("program.rounds.json", out, tmp_path)


def test_done_is_withheld_while_a_question_waits(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = drafted(rig)
    client = _client(rig, monkeypatch)
    engine.replies = [ask_reply("Architecture")]
    asked = _ok(client.post(f"/api/programs/{pid}/rounds/Architecture/next", json={}))
    held = client.post(f"/api/programs/{pid}/rounds/Architecture/decide", json={"choice": "done"})
    assert held.status_code == 409 and held.json()["code"] == "round_question_waits"
    skipped = _ok(client.post(f"/api/programs/{pid}/rounds/Architecture/answer",
                              json={"question_id": asked["question"]["id"], "skip": True}))
    assert skipped["skipped"] == asked["question"]["id"]
    assert _ok(client.post(f"/api/programs/{pid}/rounds/Architecture/decide", json={"choice": "done"}))["state"] == "done"
    unknown = client.post(f"/api/programs/{pid}/rounds/Security/next", json={})
    assert unknown.status_code == 404 and unknown.json()["code"] == "round_unknown"


def test_program_round_is_an_mcp_tool_of_work_authority(tmp_path, monkeypatch) -> None:
    names = [tool["name"] for tool in program_family.TOOLS]
    assert "program.round" in names and TOOL_AUTHORITY["program.round"] == WORK
    schema = next(tool for tool in program_family.TOOLS if tool["name"] == "program.round")["inputSchema"]
    assert schema["required"] == ["program_id", "action"]
    assert schema["properties"]["action"]["enum"] == [
        "open", "next", "answer", "skip_question", "not_this", "done", "skip", "reopen"]
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = drafted(rig)
    from holdspeak.services import program_service as program_module

    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    opened = program_family.dispatch("program.round", {"program_id": pid, "action": "open"}, OWNER)
    assert len(opened["added"]) == 5
    engine.replies = [ask_reply("Architecture")]
    asked = program_family.dispatch("program.round", {"program_id": pid, "action": "next", "round": "Architecture"},
                                    OWNER)
    assert asked["question"]["text"] == RECORDED["sequence"][0]["question"]["text"]
    skipped = program_family.dispatch("program.round", {"program_id": pid, "action": "skip", "round": "Architecture"},
                                      OWNER)
    assert skipped["state"] == "skipped"
