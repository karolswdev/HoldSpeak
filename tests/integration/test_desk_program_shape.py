"""PG-LANG LANG3 over REST and MCP: shaping by a typed sentence.

``GET /api/programs/{id}/shape`` names the engine that shapes (the bar
says it while it reads); ``POST /api/programs/{id}/shape`` {sentence,
apply} answers the change rows in the ``text_apply`` shape, the engine and
its time; at YOLO with apply the allowed rows land and Decided for you holds
the Overturn. The engine replays REAL qwen3.8-27b replies through the
runner (tests/unit/test_program_shaper.py, RecordedEngine). The face replays
the answers stored here (web/src/desk/programs/__fixtures__/program.shape.json;
``HOLDSPEAK_WIRE_WRITE=1`` rewrites it, else this test fences its shape).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from holdspeak.mcp.families import program as program_family
from holdspeak.mcp.tool_authority import TOOL_AUTHORITY, WORK
from tests.integration.program_rig import Rig
from tests.integration.program_shape_seed import SENTENCES, seed
from tests.integration.test_desk_programs import _client, _fixture
from tests.unit.test_program_shaper import reply, wire_engine


def _ok(response: Any, status: int = 200) -> Any:
    assert response.status_code == status, (response.request.url, response.status_code, response.text[:600])
    return response.json()


def test_shape_over_rest_preview_apply_yolo_and_overturn(tmp_path, monkeypatch) -> None:
    out: dict[str, Any] = {}
    # A Normal program: the rows wait for Apply; the control row lowers the bar.
    rig = Rig(tmp_path / "normal")
    engine = wire_engine(rig, monkeypatch)
    pid = seed(rig, control="normal")
    client = _client(rig, monkeypatch)
    program_before = _ok(client.get(f"/api/programs/{pid}"))
    out["engine"] = _ok(client.get(f"/api/programs/{pid}/shape"))
    assert out["engine"]["engine"] == "Home Engine" and out["engine"]["capability"] == "agent.plan"
    engine.replies = [reply("shape")]
    shaped = _ok(client.post(f"/api/programs/{pid}/shape", json={"sentence": SENTENCES["shape"], "apply": True}))
    assert shaped["applied"] is False and shaped["engine"] == "qwen3.8-27b" and shaped["say"]
    assert [row["verdict"] for row in shaped["changes"]].count("lowers") == 1
    applied = _ok(client.post(f"/api/programs/{pid}/text", json={
        "text": shaped["proposed_text"], "base": shaped["base"], "dry_run": False, "allow_lower": shaped["lowers"]}))
    assert applied["applied"] is True
    assert [step["title"] for step in applied["program"]["steps"]] == [
        "Indexes", "People routes", "Loop watch", "The fan-out"]
    out["normal"] = {"program": program_before, "shape": shaped, "applied": applied}

    # A question back.
    rig_q = Rig(tmp_path / "question")
    engine_q = wire_engine(rig_q, monkeypatch)
    pid_q = seed(rig_q)
    client_q = _client(rig_q, monkeypatch)
    engine_q.replies = [reply("question")]
    out["question"] = _ok(client_q.post(f"/api/programs/{pid_q}/shape", json={"sentence": SENTENCES["question"]}))
    assert out["question"]["question"] and out["question"]["changes"] == []

    # YOLO: the allowed row lands, the glance review waits, Overturn puts it back.
    rig_y = Rig(tmp_path / "yolo")
    engine_y = wire_engine(rig_y, monkeypatch)
    pid_y = seed(rig_y)
    client_y = _client(rig_y, monkeypatch)
    yolo_before = _ok(client_y.get(f"/api/programs/{pid_y}"))
    engine_y.replies = [reply("mixed")]
    yolo = _ok(client_y.post(f"/api/programs/{pid_y}/shape", json={"sentence": SENTENCES["mixed"], "apply": True}))
    assert yolo["applied"] is True and yolo["decision"]["rule"] == "YOLO applies a shaped change"
    assert yolo["program"]["decided_for_you"][-1]["overturnable"] is True
    overturned = _ok(client_y.post(f"/api/programs/{pid_y}/decisions/{yolo['decision']['id']}/overturn"))
    assert overturned["program"]["steps"][0]["profile"] != "codex-default"
    out["yolo"] = {"program": yolo_before, "shape": yolo, "overturned": overturned}

    # No engine: the refusal by name.
    rig_n = Rig(tmp_path / "none")
    pid_n = seed(rig_n, control="normal")
    client_n = _client(rig_n, monkeypatch)
    none = client_n.post(f"/api/programs/{pid_n}/shape", json={"sentence": SENTENCES["shape"]})
    assert none.status_code == 409 and none.json()["code"] == "no_engine"
    out["no_engine"] = {"program": _ok(client_n.get(f"/api/programs/{pid_n}")), "status": none.status_code, "body": none.json(),
                        "engine": _ok(client_n.get(f"/api/programs/{pid_n}/shape"))}
    assert out["no_engine"]["engine"]["engine"] is None
    _fixture("program.shape.json", out, tmp_path)


def test_program_shape_is_an_mcp_tool_of_work_authority(tmp_path, monkeypatch) -> None:
    names = [tool["name"] for tool in program_family.TOOLS]
    assert "program.shape" in names and TOOL_AUTHORITY["program.shape"] == WORK
    schema = next(tool for tool in program_family.TOOLS if tool["name"] == "program.shape")["inputSchema"]
    assert schema["required"] == ["program_id", "sentence"]
    rig = Rig(tmp_path)
    engine = wire_engine(rig, monkeypatch)
    pid = seed(rig)
    from holdspeak.services import program_service as program_module
    from tests.integration.program_rig import OWNER

    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    engine.replies = [reply("glance")]
    answer = program_family.dispatch("program.shape", {"program_id": pid, "sentence": SENTENCES["glance"]}, OWNER)
    assert [row["verdict"] for row in answer["changes"]] == ["lowers"] and answer["applied"] is False
