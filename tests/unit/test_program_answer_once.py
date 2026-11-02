"""One answer per question, across every channel (Astra's post-merge check, 2026-11-01).

- a core question answered from the desk and a page at once: one "Go on";
- an agent's question answered from two pages: typed once.
"""
from __future__ import annotations

import threading

import pytest

from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER
from tests.unit.test_reach_telegram import Desk, keystore  # noqa: F401  (the autouse keystore)


def test_a_core_question_is_answered_once_when_two_channels_answer_at_once(tmp_path) -> None:
    desk = Desk(tmp_path)
    pid, item = desk.core()
    rig = desk.rig
    results: list = []
    start = threading.Barrier(2)

    def press(via: str) -> None:
        start.wait()
        try:
            results.append(rig.service.decide(OWNER, pid, item["step_id"], kind="core", choice="go_on", via=via))
        except ProgramRefused as exc:
            results.append(exc.code)

    threads = [threading.Thread(target=press, args=(via,)) for via in ("desk", "page")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    go_on = [row for row in rig.service.store.list_checkpoints(pid) if str(row["line"]).startswith("Go on:")]
    assert len(go_on) == 1, [row["line"] for row in go_on]
    assert results.count("no_core_question") == 1
    with pytest.raises(ProgramRefused) as again:
        rig.service.decide(OWNER, pid, item["step_id"], kind="core", choice="go_on")
    assert again.value.code == "no_core_question"


def test_an_agents_question_is_typed_once_from_two_pages(tmp_path) -> None:
    desk = Desk(tmp_path, control="normal")
    rig = desk.rig
    pid = rig.service.create(OWNER, title="Ask first", goal="Name it.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control="normal")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Name the column", "brief": "Ask which name."}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.states[step["launch_id"]] = {"state": "waiting", "turn_id": "turn-1"}
    rig.tick()
    item = next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "answer")
    ref = f"program:{pid}:{item['id']}"
    first = desk.briefing.make(OWNER, [ref])
    second = desk.briefing.make(OWNER, [ref])
    before = len(rig.prompts)
    desk.briefing.answer(first["token"], ref, "answer", reason="Use stall_reason.")
    with pytest.raises(Exception):
        desk.briefing.answer(second["token"], ref, "answer", reason="Use stall_reason.")
    typed = [text for _launch, text in rig.prompts[before:] if text == "Use stall_reason."]
    assert typed == ["Use stall_reason."]
    # The agent's next question (a new turn) takes an answer again.
    rig.states[step["launch_id"]] = {"state": "waiting", "turn_id": "turn-2"}
    rig.service.answer_agent(OWNER, pid, step["id"], "And the index name?")
    assert rig.prompts[-1][1] == "And the index name?"
