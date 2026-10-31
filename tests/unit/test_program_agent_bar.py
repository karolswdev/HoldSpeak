"""An agent never lowers the bar (PROGRAM-LANGUAGE-2026-10-31 §4.5, §7.2;
PROGRAMS-REQUIREMENTS §14.7): agents propose; only the owner lowers the bar
or waives. Every path that writes a change from text is held: the text
(``text_apply``), a sentence (``shape`` with apply at YOLO), a round's answer
and a draft. A Planned step's lower gate from an agent goes to the owner as a
``step_change`` proposal at every level; any other lower bar or core question
is refused with ``owner_required``. The owner's path is as it was."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services import program_planner, program_rounds
from holdspeak.services.program_service import ProgramRefused, _creator
from holdspeak.services.program_text import print_program
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

AGENT = Principal(PrincipalKind.AGENT, "agent:orchestrator")


def _agents_program(tmp_path: Path, control: str = "yolo") -> tuple[Rig, str]:
    rig = Rig(tmp_path)
    pid = rig.service.create(AGENT, title="Mine", goal="G.", repository=str(rig.repo), control=control,
                             check_command=f"sh {FAKE_CHECK}", reviewer_profile="codex-default")["id"]
    rig.service.plan(AGENT, pid, steps=[
        {"title": "A", "brief": "Do A.", "owns": ["a.py"]},
        {"title": "B", "brief": "Do B.", "gate_merge": "owner", "gate_review": "agent", "review_depth": "standard"},
    ])
    rig.service.require(OWNER, pid, text="`true` is green", step_id=rig.step(pid, 2)["id"])
    return rig, pid


def _hand_to_agent(rig: Rig, pid: str, control: str = "yolo") -> None:
    program = rig.service._program(pid)
    program["created_by"], program["control"] = _creator(AGENT), control
    rig.service.store.save_program(program)


def _edit(text: str, *pairs: tuple[str, str]) -> str:
    for old, new in pairs:
        assert old in text, old
        text = text.replace(old, new, 1)
    return text


LOWER = ("  review agent at standard · merge owner", "  review agent at glance · merge level")


def _gates(rig: Rig, pid: str) -> tuple[str, str]:
    step = rig.service.store.get_step(rig.step(pid, 2)["id"])
    return step["gate_merge"], step["review_depth"]


# ── the text ─────────────────────────────────────────────────────────

def test_an_agents_allow_lower_is_refused_by_name(tmp_path) -> None:
    rig, pid = _agents_program(tmp_path)
    text = _edit(rig.service.text_get(AGENT, pid)["text"], LOWER)
    for dry_run in (True, False):
        with pytest.raises(ProgramRefused) as refused:
            rig.service.text_apply(AGENT, pid, text, dry_run=dry_run, allow_lower=["step-2.merge", "step-2.depth"])
        assert refused.value.code == "owner_required"
        assert refused.value.detail == "Only the owner lowers the bar. You named: step-2.merge, step-2.depth."
        assert refused.value.context["rows"] == ["step-2.merge", "step-2.depth"]
    assert _gates(rig, pid) == ("owner", "standard")


def test_an_agents_lower_gate_goes_to_the_owner_as_a_proposal_even_at_yolo(tmp_path) -> None:
    rig, pid = _agents_program(tmp_path, control="yolo")
    text = _edit(rig.service.text_get(AGENT, pid)["text"], LOWER, ("step 1 A ", "step 1 A, renamed "))
    dry = rig.service.text_apply(AGENT, pid, text)
    rows = {row["id"]: row for row in dry["changes"]}
    assert {key: (row["verdict"], row["code"]) for key, row in rows.items() if key.startswith("step-2")} == {
        "step-2.depth": ("lowers", "owner_proposal"), "step-2.merge": ("lowers", "owner_proposal")}
    assert dry["proposed"] == ["step-2.depth", "step-2.merge"] and dry["applied"] is False
    answer = rig.service.text_apply(AGENT, pid, text, dry_run=False)
    assert answer["applied"] is True and len(answer["proposals"]) == 1
    assert rig.step(pid, 1)["title"] == "A, renamed"  # the allowed row applies at once
    assert _gates(rig, pid) == ("owner", "standard")  # the lower bar waits for him
    # YOLO decided the rename for him; nothing decided the lower bar.
    assert [row["line"] for row in rig.service.decided_for_you(pid)] == ["The orchestrator changes step 1: title"]
    item = next(i for i in rig.program(pid)["your_turn_items"] if i["kind"] == "step_change")
    assert item["title"] == "The orchestrator changes step 2: review_depth, gate_merge (this lowers the bar)"
    rig.service.decide(OWNER, pid, rig.step(pid, 2)["id"], kind="step_change", choice="apply",
                       proposal_id=item["proposal_id"])
    assert _gates(rig, pid) == ("level", "glance")


def test_an_agents_lower_bar_on_the_program_or_a_requirement_is_refused(tmp_path) -> None:
    rig, pid = _agents_program(tmp_path, control="normal")
    text = rig.service.text_get(AGENT, pid)["text"]
    lowered = _edit(text, ("  control normal", "  control yolo"), ("  reviewer Codex", "  reviewer none"),
                    ("  R1 check: `true` is green", "  R1 check optional: `true` is green"))
    answer = rig.service.text_apply(AGENT, pid, lowered, dry_run=False)
    rows = {row["id"]: (row["verdict"], row["code"]) for row in answer["changes"]}
    assert rows == {"program.control": ("refused", "owner_required"), "program.reviewer": ("refused", "owner_required"),
                    "R1.requirement": ("refused", "owner_required")}
    assert answer["applied"] is False and answer["proposed"] == []
    reason = next(row["reason"] for row in answer["changes"] if row["id"] == "program.control")
    assert reason == "Only the owner lowers the bar (program, control)."
    program = rig.service._program(pid)
    assert program["control"] == "normal" and program["reviewer_profile"] == "codex-default"
    waived = _edit(text, ("  R1 check: `true` is green", "  R1 check: `true` is green\n    waived: it is slow"))
    row = next(row for row in rig.service.text_apply(AGENT, pid, waived)["changes"] if row["id"] == "R1.waive")
    assert (row["verdict"], row["code"]) == ("refused", "owner_required")


def test_an_agents_core_question_waits_for_the_owner(tmp_path) -> None:
    rig, pid = _agents_program(tmp_path)
    text = rig.service.text_get(AGENT, pid)["text"]
    core = _edit(text, ("  owns a.py", "  owns /etc/hosts\n  may call"))
    answer = rig.service.text_apply(AGENT, pid, core, dry_run=False)
    rows = {row["id"]: (row["verdict"], row["code"], row["reason"]) for row in answer["changes"]}
    assert rows["step-1.owns"] == ("lowers", "owner_proposal", "A file outside the repository. Only the owner "
                                   "lowers the bar. This goes to him as a proposal.")
    assert rows["step-1.may-call"][:2] == ("lowers", "owner_proposal")
    one = rig.service.store.get_step(rig.step(pid, 1)["id"])
    assert answer["applied"] is True and one["owns"] == ["a.py"] and not one["may_call"]
    added = text.rstrip("\n") + "\n\nstep + Reach out\n  owns /etc/hosts\n  brief\n  > Read the hosts file.\n"
    row = next(row for row in rig.service.text_apply(AGENT, pid, added)["changes"] if row["op"] == "add")
    assert (row["verdict"], row["code"]) == ("refused", "owner_required")
    assert row["reason"] == "A file outside the repository. Only the owner answers this."


def test_the_owner_lowers_the_bar_as_before(tmp_path) -> None:
    rig, pid = _agents_program(tmp_path)
    text = _edit(rig.service.text_get(OWNER, pid)["text"], LOWER)
    dry = rig.service.text_apply(OWNER, pid, text)
    assert dry["lowers"] == ["step-2.depth", "step-2.merge"] and "proposed" not in dry
    held = rig.service.text_apply(OWNER, pid, text, dry_run=False)
    assert held["applied"] is False
    answer = rig.service.text_apply(OWNER, pid, text, dry_run=False, allow_lower=dry["lowers"])
    assert answer["applied"] is True and "proposals" not in answer
    assert _gates(rig, pid) == ("level", "glance")


# ── a sentence, a round, a draft ─────────────────────────────────────

def test_an_agents_shaped_lower_bar_never_applies_at_yolo(tmp_path, monkeypatch) -> None:
    from tests.integration.program_shape_seed import SENTENCES, seed
    from holdspeak.services import program_shaper
    from tests.unit.test_program_shaper import MODEL, reply, wire_engine

    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch)
    pid = seed(rig)
    _hand_to_agent(rig, pid)
    before = print_program(rig.service.get(OWNER, pid))
    answer = program_shaper.shape_program(rig.service, AGENT, pid, SENTENCES["glance"], apply=True,
                                          invoke_fn=lambda _payload: (reply("glance"), MODEL))
    assert answer["applied"] is False and answer["lowers"] == ["step-1.depth"]
    assert print_program(rig.service.get(OWNER, pid)) == before
    with pytest.raises(ProgramRefused) as refused:
        rig.service.text_apply(AGENT, pid, answer["proposed_text"], dry_run=False, base=answer["base"],
                               allow_lower=answer["lowers"])
    assert refused.value.code == "owner_required"
    proposed = rig.service.text_apply(AGENT, pid, answer["proposed_text"], dry_run=False, base=answer["base"])
    assert proposed["proposed"] == ["step-1.depth"] and len(proposed["proposals"]) == 1
    assert rig.service.store.get_step(rig.step(pid, 1)["id"])["review_depth"] != "glance"


def test_an_agents_round_answer_never_applies_at_yolo(tmp_path, monkeypatch) -> None:
    from tests.integration.program_rounds_seed import drafted
    from tests.unit.test_program_rounds import ask_reply, said, shape_reply
    from tests.unit.test_program_rounds import MODEL
    from tests.unit.test_program_shaper import wire_engine

    rig = Rig(tmp_path)
    rig.engine = wire_engine(rig, monkeypatch)
    pid = drafted(rig)
    _hand_to_agent(rig, pid)
    rig.engine.replies = [ask_reply("Architecture")]
    program_rounds.ask(rig.service, OWNER, pid, "Architecture")
    before = [step["brief"] for step in rig.program(pid)["steps"]]
    out = program_rounds.answer(rig.service, AGENT, pid, "Architecture", None, choice=said("Architecture"), apply=True,
                                invoke_fn=lambda _payload: (shape_reply("Architecture"), MODEL))
    assert out["applied"] is False and out["applied_rows"] == []
    assert [step["brief"] for step in rig.program(pid)["steps"]] == before


def test_an_agents_draft_that_reaches_outside_is_refused(tmp_path, monkeypatch) -> None:
    from tests.unit.test_program_planner import CASES, desk_for

    rig = desk_for(tmp_path, monkeypatch, "j1")
    _hand_to_agent(rig, rig.pid)
    base = program_planner.shaper.stripped_text(print_program(rig.service.get(OWNER, rig.pid)))
    fake = base + "\nstep + Reach out\n  owns /etc/hosts\n  may call\n  brief\n  > Read the hosts file.\n"
    result = program_planner.plan(rig.service, AGENT, rig.pid, budget=CASES["j1"]["budget"],
                                  invoke_fn=lambda _payload: (json.dumps({"say": "1 step", "text": fake}), "fake"))
    answer = rig.service.text_apply(AGENT, rig.pid, result.proposed_text, dry_run=False, base=result.base_text)
    row = next(row for row in answer["changes"] if row["op"] == "add")
    assert (row["verdict"], row["code"]) == ("refused", "owner_required") and answer["applied"] is False
    assert rig.program(rig.pid)["steps"] == []
    # The owner's apply of the same draft is as it was (the text names no lower bar).
    owner = rig.service.text_apply(OWNER, rig.pid, result.proposed_text, dry_run=True, base=result.base_text)
    assert next(row for row in owner["changes"] if row["op"] == "add")["verdict"] == "allowed"
