"""PG-LANG LANG5 (§10): "change the stalling program: …" on a call.

The whole call through the hub with the fake ai-phone (as
``test_calls_turn.py``): the call's turn is the hub's real thread loop on
``calls.turn`` with the CALL palette; the turn's engine is SCRIPTED to do
what a model does (one ``program.shape`` with the Program's words and his
sentence, then it says the hub's ``spoken`` line). The shaping is the hub's
real shaper on ``agent.plan``, replaying the REAL qwen3.8-27b replies
(tests/fixtures/program_shape_reply.json, keys ``call`` and ``mixed``)
through the runner. Done when (§13 LANG5): the Calls rig applies a shape
after a spoken yes and never applies a row that lowers the bar from the
call (it waits on the desk); "later" puts every row on the desk; "no"
changes nothing.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.kernel.inference_stream import Delta
from tests.integration.program_shape_seed import SENTENCES, seed
from tests.integration.test_calls_turn import OWNER, REMOTE, _fake, _said, _service, _write_config
from tests.unit.test_desk_ask_ai import hub  # noqa: F401  (fixture)

pytestmark = pytest.mark.timeout(180, method="thread")

RECORDED = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "program_shape_reply.json").read_text())


class _ShapeOnACall:
    """The call's turn: one ``program.shape`` by his words, then the hub's
    ``spoken`` line. The shaper's one call (``run_prompt``) answers the
    recorded reply. Nothing in it answers for the hub."""

    active_provider = "fixture"

    def __init__(self, model: str, name: str, key: str, seen: list[dict[str, Any]]) -> None:
        self.active_model = model
        self._name, self._key, self._seen = name, key, seen

    def run_prompt_stream(self, *, messages=None, tools=None, **_kw: Any) -> Any:
        self._seen.append({"messages": [dict(m) for m in messages or []], "tools": tools})
        results = [m for m in messages or [] if m.get("role") == "tool"]
        if not results:
            call = {"id": "call_shape", "name": "program.shape",
                    "arguments": json.dumps({"name": self._name, "sentence": SENTENCES[self._key]})}
            yield Delta(kind="tool_calls", meta={"tool_calls": [call]})
            yield Delta(kind="done")
            return
        content = str(results[-1].get("content") or "")
        try:
            answer = json.loads(content)
        except ValueError:
            answer = {}
        yield Delta(kind="text", text=str((answer if isinstance(answer, dict) else {}).get("spoken") or content))
        yield Delta(kind="done")

    def run_prompt(self, **_kw: Any) -> str:
        return RECORDED["replies"][self._key]["reply_text"]


def _seed(hub: Any, tmp_path: Path, control: str) -> str:
    """The seed Program the replies were recorded on, on the hub's database."""
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from holdspeak.services.program_service import default_program_service
    from tests.integration.program_rig import make_repo
    from tests.unit.test_phase143_inference_assignments import _profile
    from tests.unit.test_phase200_readiness import _assign

    schema = process_inference_capability_registry().require("agent.plan")
    _profile(hub.db, "home-engine", claims=("language", f"result_schema:{schema.output_schema_sha256}"))
    _assign(hub.db, "agent.plan", ["home-engine"])
    service = default_program_service(hub.db)
    repo = make_repo(tmp_path / "seed-repo")
    shim = SimpleNamespace(db=hub.db, service=service, repo=repo)
    shim.step = lambda pid, n: next(s for s in service.get(OWNER, pid)["steps"] if s["ordinal"] == n)
    pid = seed(shim, control=control)
    (repo / ".holdspeak").mkdir(exist_ok=True)
    (repo / ".holdspeak" / "program.json").write_text(json.dumps({"shot": "true {case} {width}"}))
    return pid


def _call(hub, monkeypatch, tmp_path, *, key: str, control: str, answer: str) -> tuple[str, list[str], Any]:
    from holdspeak.services import program_spoken

    program_spoken.reset()
    monkeypatch.setenv("HOLDSPEAK_PROGRAMS", "off")  # no step is handed to an agent
    _write_config(control_mode="normal")
    state_file = _fake(tmp_path, monkeypatch, [
        {"kind": "incoming", "remote": REMOTE},
        {"kind": "heard", "text": "blue heron"},
        {"kind": "heard", "text": f"Change the stalling program: {SENTENCES[key]}."},
        {"kind": "heard", "text": answer},
        {"kind": "ended"},
    ])
    seen: list[dict[str, Any]] = []
    service = _service(hub, monkeypatch, lambda model: _ShapeOnACall(model, "stalling", key, seen), [])
    pid = _seed(hub, tmp_path, control)
    assert asyncio.run(service.serve_once(wait=5)) == "call"
    offered = {tool["function"]["name"] for tool in seen[0]["tools"]}
    assert "program.shape" in offered and not offered & {"program.text_apply", "program.decide"}
    return pid, _said(state_file), service


def _get(hub, pid: str) -> dict[str, Any]:
    from holdspeak.services.program_service import default_program_service

    return default_program_service(hub.db).get(OWNER, pid)


def test_his_spoken_yes_applies_the_shaped_change(hub, monkeypatch, tmp_path) -> None:
    pid, said, _service_ = _call(hub, monkeypatch, tmp_path, key="call", control="normal", answer="Yes, apply it.")
    asked = [line for line in said if line.endswith("Say yes, no, or later.")]
    assert "One moment. I am reading the program." in said, said
    assert asked == [
        "In the program The hub stops stalling: A new requirement on step 1: The People window fits at 393. "
        "A new requirement on step 2: The People window fits at 393. A new requirement on step 3: The People "
        "window fits at 393. Apply? Say yes, no, or later."], said
    program = _get(hub, pid)
    from holdspeak.services.program_service import default_program_service

    shots = [row for row in default_program_service(hub.db).requirements(pid) if row["kind"] == "shot"]
    assert len(shots) == 3 and {row["spec"].get("width") for row in shots} == {393}, shots
    assert "held_shape" not in program
    assert said[-1] == "Done: the program The hub stops stalling has three changes.", said


def test_a_row_that_lowers_the_bar_never_applies_from_the_call_it_waits_on_the_desk(hub, monkeypatch, tmp_path) -> None:
    pid, said, _service_ = _call(hub, monkeypatch, tmp_path, key="mixed", control="yolo", answer="Yes.")
    asked = [line for line in said if line.endswith("Say yes, no, or later.")]
    assert asked == [
        "In the program The hub stops stalling: Step 1's agents is now Codex, then Claude Code. One change lowers the "
        "bar and waits for you on the desk: Step 1's depth is now glance. Apply? Say yes, no, or later."], said
    program = _get(hub, pid)
    assert program["steps"][0]["profile"] == "codex-default"
    assert program["steps"][0].get("review_depth") in (None, "", "standard"), program["steps"][0]
    waiting = program["held_shape"]
    assert [row["id"] for row in waiting["changes"]] == ["step-1.depth"] and waiting["lowers"] == ["step-1.depth"]
    assert said[-1] == "Done: the program The hub stops stalling has one change. One waits for you on the desk.", said


@pytest.mark.parametrize("answer, on_desk", [("Later, put it on my desk.", True), ("No.", False)])
def test_later_leaves_the_rows_on_the_desk_and_no_changes_nothing(hub, monkeypatch, tmp_path, answer, on_desk) -> None:
    from holdspeak.services.program_text import print_program

    pid, said, _service_ = _call(hub, monkeypatch, tmp_path, key="call", control="normal", answer=answer)
    program = _get(hub, pid)
    assert not [row for row in program.get("steps") or [] if row.get("profile") == "codex-default"]
    from holdspeak.services.program_service import default_program_service

    assert not [row for row in default_program_service(hub.db).requirements(pid) if row["kind"] == "shot"]
    assert ("held_shape" in program) is on_desk
    if on_desk:
        assert len(program["held_shape"]["changes"]) == 3
        assert said[-1] == ("Nothing changed yet. The three changes wait for you in the program The hub stops "
                            "stalling on the desk."), said
    assert print_program(program).count("shot") == 0
