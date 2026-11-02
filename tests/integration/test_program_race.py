"""PG-JOURNEYS J5 "The race": the hub's halves not built before (2026-11-01).

- The Verification round asks by rule, before any engine call, when a race
  step has no review: "Review each contender?" (Each reviews the other · No
  review). Each reviews the other turns the review on for the race step (the
  contenders copy it at Start) and plants the template's Review requirement.
- The winner's Decided for you row: "Codex won the race · 34 min" with its
  rule, and ``facts.race_won`` on the winner.
- Both contenders red after their rounds: the race fails as ONE step: one
  Parked row on the race step with both logs, one ledger line; Resume on it
  sends every contender back.
"""
from __future__ import annotations

from pathlib import Path

from holdspeak.services import program_rounds
from tests.integration.program_rig import OWNER, Rig
from tests.integration.test_desk_programs import _client, _fixture

RED_CHECK = "sh -c 'echo FAILED: tests/test_x.py::test_it; exit 1'"


def _no_engine(_payload):  # noqa: ANN001
    raise AssertionError("the race question is asked by rule, with no engine call")


def _race(rig: Rig, *, control: str = "normal", check: str | None = None) -> str:
    pid = rig.service.create(OWNER, title="Mermaid words in Notes search", goal="Find words in fences.",
                             repository=str(rig.repo), check_command=check or "sh -c 'echo ok'", template="race",
                             control=control)["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Find words inside Mermaid fences", "brief": "Search fences."}])
    return pid


def test_the_verification_round_asks_by_rule_and_each_reviews_the_other_turns_the_review_on(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    pid = _race(rig)
    asked = program_rounds.ask(rig.service, OWNER, pid, "Verification", invoke_fn=_no_engine)
    question = asked["question"]
    _fixture("program.race_round.json", rig.program(pid), tmp_path)
    assert question["text"] == "Review each contender?" and question["rule"] == "race_review"
    assert question["choices"] == ["Each reviews the other", "No review"] and asked["engine"] is None
    wire_round = next(r for r in rig.program(pid)["rounds"] if r["name"] == "Verification")
    assert wire_round["questions"][0]["rule"] == "race_review"
    # His press through the route (the face's answer); the rule needs no engine.
    monkeypatch.setattr(program_rounds.shaper, "invoke", lambda *a, **k: _no_engine(None))
    pressed = _client(rig, monkeypatch).post(f"/api/programs/{pid}/rounds/Verification/answer",
                                             json={"question_id": question["id"], "option": "Each reviews the other"})
    assert pressed.status_code == 200, pressed.text
    answered = _fixture("program.race_round.answered.json", pressed.json(), tmp_path)
    assert answered["round_question"]["became"] == ["step 1 review"]
    # The face asks the round's next question at once: the rig has no engine, so the hub refuses.
    nxt = _client(rig, monkeypatch).post(f"/api/programs/{pid}/rounds/Verification/next")
    assert nxt.status_code == 409 and nxt.json()["code"] == "no_engine", nxt.text
    _fixture("program.race_round.next.json", nxt.json(), tmp_path)
    step = rig.step(pid, 1)
    assert step["gate"]["review"] == "agent"
    assert "The change does only what its brief says." in [r["text"] for r in rig.service.requirements(pid)]
    # Asked once: the next Ask goes to the engine (here the rig has none: refused).
    from holdspeak.services.program_service import ProgramRefused

    try:
        program_rounds.ask(rig.service, OWNER, pid, "Verification", invoke_fn=_no_engine)
    except ProgramRefused as exc:
        assert exc.code == "no_engine"
    else:
        raise AssertionError("the rule question was asked twice")
    rig.service.start(OWNER, pid)
    lead = rig.step(pid, 1)
    assert lead["contenders"][0]["gate"]["review"] == "agent"


def test_no_review_changes_nothing(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _race(rig)
    program_rounds.ask(rig.service, OWNER, pid, "Verification", invoke_fn=_no_engine)
    answered = program_rounds.answer(rig.service, OWNER, pid, "Verification", choice="No review", invoke_fn=_no_engine)
    assert answered["round_question"]["became"] == [] and rig.step(pid, 1)["gate"]["review"] == "none"


def test_the_winner_row_says_who_and_how_long(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _race(rig)
    rig.service.start(OWNER, pid)
    contender = rig.step(pid, 1)["contenders"][0]
    rig.agent.finish(contender["launch_id"], {"fast.py": "codex\n"})
    rig.tick()
    [row] = [r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "race_winner"]
    assert row["line"].startswith("Codex won the race · ") or row["line"] == "Codex won the race", row
    assert row["rule"] == "Normal: the first green, reviewed contender wins" and not row["overturnable"]
    assert rig.step(pid, 1)["race_both_red"] is False
    winner = rig.service.store.get_step(contender["id"])
    assert winner["facts"]["race_won"]["by"] == "Codex"
    _fixture("program.race_won.json", rig.program(pid), tmp_path)


def _red_rounds(rig: Rig, pid: str) -> None:
    """Every contender commits and goes red until its rounds end."""
    for turn in range(8):
        live = [row for row in [rig.step(pid, 1), *rig.step(pid, 1)["contenders"]]
                if row["state"] in ("briefed", "working", "check_failed")]
        if not live:
            return
        for row in live:
            rig.agent.finish(row["launch_id"], {f"try{turn}-{row['id'][-3:]}.py": "x\n"}, message=f"try {turn}")
        rig.tick(2)


def test_both_contenders_red_fail_as_one_step_with_both_logs(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    pid = _race(rig, check=RED_CHECK)
    rig.service.start(OWNER, pid)
    _red_rounds(rig, pid)
    lead, contender = rig.step(pid, 1), rig.step(pid, 1)["contenders"][0]
    assert lead["state"] == "parked" and contender["state"] == "parked", (lead["state"], contender["state"])
    [row] = [item for item in rig.program(pid)["your_turn_items"] if item["kind"] == "parked"]
    assert row["step_id"] == lead["id"] and row["race"] is True and row["race_both_red"] is True
    assert lead["race_both_red"] is True  # the step wire says it too (the row's state word reads it)
    assert row["title"] == ("Parked step 1 “Find words inside Mermaid fences”: both contenders are red "
                            "after their rounds")
    assert [log["agent"] for log in row["logs"]] == ["Claude Code", "Codex"] and all(log["log"] for log in row["logs"])
    lines = [c for c in rig.program(pid)["checkpoints"] if c["line"] == "Both contenders are red after their rounds"]
    assert len(lines) == 1 and "Claude Code: " in lines[0]["undo"]["detail"] and "Codex: " in lines[0]["undo"]["detail"]
    # The face's answers: the wire with the one Parked row, and Resume through the route.
    client = _client(rig, monkeypatch)
    _fixture("program.race_parked.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    resumed = client.post(f"/api/programs/{pid}/steps/{lead['id']}/decide", json={"kind": "parked", "choice": "resume"})
    assert resumed.status_code == 200, resumed.text
    _fixture("program.race_resumed.json", resumed.json(), tmp_path)
    assert {rig.step(pid, 1)["state"], rig.step(pid, 1)["contenders"][0]["state"]} <= {"ready", "briefed", "working"}
