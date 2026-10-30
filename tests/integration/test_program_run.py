"""Programs, end to end on the rig (design §12, row PG-HUB; §6 Control).

A Program of three steps (the third after the other two) runs against the
fake agent: both first steps are handed into real worktrees, their real
commits pass the fake gate (a quick-check-shaped log the verifier reads),
the reviewer fake passes; at Secure the merge ask lands in Needs you and
``decide merge`` moves them to merged (the follow-through fake); at Normal
the engine merges without a press and says so under Decided for you; the
third step dispatches; the handover note is rewritten at each change. A red
gate goes to round 2, then parks; a race of 2 parks the loser;
``HOLDSPEAK_PROGRAMS=off`` ticks nothing. PG12: a coder frame for a step's
launch ticks its Program at once (a debounce, never the 30 s tick).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from holdspeak.services.needs_you_membership import program_items
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git


def _program(rig: Rig, *, title="The hub stops stalling", template="build-and-review", check=None,
             control="secure", **kw):
    made = rig.service.create(
        OWNER, title=title, goal="Make the hub stop stalling.", repository=str(rig.repo),
        check_command=check or f"sh {FAKE_CHECK}", template=template, control=control, **kw,
    )
    return made["id"]


def _section(note: str, heading: str) -> str:
    part = note.split(f"## {heading}\n", 1)[1]
    return part.split("\n## ", 1)[0]


def _plan_three(rig: Rig, pid: str) -> None:
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Indexes", "brief": "Add the three indexes.", "owns": ["holdspeak/db/schema.py"]},
        {"title": "Retention", "brief": "Prune read receipts.", "owns": ["holdspeak/db/retention.py"]},
        {"title": "The fan-out", "brief": "Fan out the reads.", "after": [1, 2]},
    ])


def _build_and_review_first_two(rig: Rig, pid: str, words: str) -> tuple[dict, dict]:
    one, two = rig.step(pid, 1), rig.step(pid, 2)
    rig.agent.finish(one["launch_id"], {"holdspeak/db/schema.py": "-- indexes\n"})
    rig.agent.finish(two["launch_id"], {"holdspeak/db/retention.py": "# prune\n"})
    rig.tick()
    one = rig.step(pid, 1)
    assert one["check"]["verdict"] == "green", one["check"]
    assert [s["state"] for s in one["check"]["sections"]] == ["green"] * 6
    assert Path(one["check"]["log"]).is_file() and ".tmp/program-check/" in one["check"]["log"]
    assert one["state"] == "review"
    rig.tick()  # AG12 starts the reviewers (helpers of the builders)
    reviewers = [record for record in rig.ledger.list() if record.get("helper_of")]
    assert len(reviewers) == 2 and all(r["profile_id"] == "codex-default" for r in reviewers)
    for reviewer in reviewers:
        rig.words[reviewer["launch_id"]] = words
        rig.states[reviewer["launch_id"]] = {"state": "done", "turn_id": "r"}
    rig.tick(2)
    return rig.step(pid, 1), rig.step(pid, 2)


def test_three_steps_at_secure_wait_for_his_merge(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, reviewer_profile="codex-default", control="secure")
    _plan_three(rig, pid)
    assert rig.program(pid)["state"] == "drafting"
    assert "Drafting · 0 of 3 steps done" in rig.note(pid)

    rig.service.start(OWNER, pid)
    one, two, three = (rig.step(pid, n) for n in (1, 2, 3))
    assert one["state"] in ("briefed", "working") and two["state"] in ("briefed", "working")
    assert three["state"] == "planned"
    assert one["branch"] == "program/the-hub-stops-stalling/1-indexes"
    assert one["worktree"] == f"hs-program-{one['id']}"
    base = git(rig.repo, "rev-parse", "main")
    assert git(Path(rig.ledger.get(one["launch_id"])["worktree_path"]), "rev-parse", "HEAD") == base
    note = rig.note(pid)
    assert "1. Indexes — Briefed · Claude Code" in _section(note, "Steps")
    assert "3. The fan-out — Planned (after 1, 2)" in _section(note, "Steps")

    one, two = _build_and_review_first_two(rig, pid, "MUST: none")
    assert one["review"]["verdict"] == "pass"
    assert one["state"] == "merge_ask" and one["pr"]["number"], one
    assert two["state"] == "merge_ask"
    assert git(rig.repo, "ls-remote", "origin", one["branch"])  # really pushed

    program = rig.program(pid)
    assert program["state"] == "waiting" and program["your_turn"] == 2
    rows = program_items(rig.service.needs_you_items())
    assert [row["why"] for row in rows] == ["TO MERGE", "TO MERGE"]
    assert rows[0]["group"] == "The hub stops stalling" and rows[0]["dueWord"] == "now"
    assert rows[0]["program"]["choices"] == ["merge", "not_yet"]
    turn = _section(rig.note(pid), "Your turn")
    assert f"Merge step 1 “Indexes”? (PR #{one['pr']['number']}, check green, review passed)" in turn

    for ordinal in (1, 2):
        rig.service.decide(OWNER, pid, rig.step(pid, ordinal)["id"], kind="merge", choice="merge")
    assert ["gh", "pr", "merge", str(one["pr"]["number"]), "--squash"] in rig.gh.calls
    rig.tick()
    one, two, three = (rig.step(pid, n) for n in (1, 2, 3))
    assert one["state"] in ("merged", "done") and two["state"] in ("merged", "done")
    assert three["state"] in ("briefed", "working"), three
    assert rig.hand.calls[-1][:2] == ("program_step", three["id"])
    assert "(nothing)" in _section(rig.note(pid), "Your turn")
    lines = [c["line"] for c in rig.program(pid)["checkpoints"]]
    assert any(line.startswith("Handed to Claude Code") for line in lines)
    assert any(line.startswith("Checked · green") for line in lines)
    assert any(line.startswith("Merged PR #") for line in lines)
    assert any(frame == "program_changed" for frame, _ in rig.frames)
    # Secure: Done is his press too.
    rig.agent.finish(three["launch_id"], {"fan.py": "x\n"})
    rig.tick(3)
    for record in rig.ledger.list():
        if record.get("helper_of") == three["launch_id"]:
            rig.words[record["launch_id"]] = "MUST: none"
            rig.states[record["launch_id"]] = {"state": "done", "turn_id": "r3"}
    rig.tick(2)
    rig.service.decide(OWNER, pid, rig.step(pid, 3)["id"], kind="merge", choice="merge")
    rig.tick()
    items = rig.service.get(OWNER, pid)["your_turn_items"]
    assert [item["kind"] for item in items] == ["close"]
    rig.service.close(OWNER, pid)
    assert rig.program(pid)["state"] == "done"


def test_three_steps_at_normal_merge_without_a_press_and_say_so(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, reviewer_profile="codex-default", control="normal")
    _plan_three(rig, pid)
    rig.service.start(OWNER, pid)
    one, two = _build_and_review_first_two(rig, pid, "SHOULD: name the index.\nNOTE: a nice touch.\nMUST: none")
    rig.tick()
    one, two, three = (rig.step(pid, n) for n in (1, 2, 3))
    assert one["state"] in ("merged", "done") and two["state"] in ("merged", "done"), (one, two)
    assert three["state"] in ("briefed", "working")
    assert program_items(rig.service.needs_you_items()) == []
    decided = rig.program(pid)["decided_for_you"]
    kinds = [row["kind"] for row in decided]
    assert kinds.count("merge") == 2
    assert kinds.count("finding_should") == 2 and kinds.count("finding_note") == 2
    merge = next(row for row in decided if row["kind"] == "merge")
    assert merge["rule"] == "Normal merges on a green check and a passed review" and not merge["overturnable"]
    later = next(row for row in decided if row["kind"] == "finding_should")
    assert later["choice"] == "later" and later["overturnable"]
    section = _section(rig.note(pid), "Decided for you")
    assert "Merged PR #" in section and "→ Later (a Door task)" in section and "· Overturn" in section
    # His Overturn of a Later: the finding is his again.
    rig.service.overturn(OWNER, pid, later["id"])
    after = rig.program(pid)
    row = next(r for r in after["decided_for_you"] if r["id"] == later["id"])
    assert row["overturned_at"] and not row["overturnable"]
    with pytest.raises(Exception) as refused:
        rig.service.overturn(OWNER, pid, merge["id"])
    assert getattr(refused.value, "code", "") == "not_overturnable"


@pytest.mark.parametrize("control, row_now", [("secure", True), ("normal", True)])
def test_a_red_gate_gets_round_two_then_parks(tmp_path, control, row_now) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, title="Red", template="fast-cycle", control=control,
                   check=f"FAKE_CHECK_RED=1 sh {FAKE_CHECK}")
    rig.service.plan(OWNER, pid, steps=[{"title": "Break it", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"a.txt": "1\n"})
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "check_failed" and step["rounds"] == 1
    assert "the section pytest is red" in step["check"]["reasons"]
    launch, text = rig.prompts[-1]
    assert launch == step["launch_id"] and "the check is red" in text and step["check"]["log"] in text
    assert "FAILED tests/unit/test_fake.py" in text  # the log tail
    rig.agent.start_turn(step["launch_id"])
    rig.tick()
    assert rig.step(pid, 1)["state"] == "working"
    rig.agent.finish(step["launch_id"], {"a.txt": "2\n"})
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "parked" and step["parked_by"] == "engine"
    assert step["parked_reason"].startswith("The check failed 2 times")
    rows = program_items(rig.service.needs_you_items())
    assert [row["why"] for row in rows] == (["TO RESUME"] if row_now else [])
    assert "Parked step 1 “Break it”: The check failed 2 times" in _section(rig.note(pid), "Your turn")
    rig.service.decide(OWNER, pid, step["id"], kind="parked", choice="skip")
    if control == "secure":
        rig.service.close(OWNER, pid)
    assert rig.program(pid)["state"] == "done"
    assert "You skipped this step" in _section(rig.note(pid), "Parked")


def test_normal_parks_a_failed_step_and_carries_on(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, title="Carry on", template="fast-cycle", control="normal",
                   check=f"FAKE_CHECK_RED_FILE={tmp_path}/red sh {FAKE_CHECK}")
    rig.service.plan(OWNER, pid, steps=[{"title": "Fails", "brief": "x"}, {"title": "Works", "brief": "y"}])
    rig.service.start(OWNER, pid)
    first, second = rig.step(pid, 1), rig.step(pid, 2)
    (tmp_path / "red").write_text("1")
    rig.agent.finish(first["launch_id"], {"a.txt": "1\n"})
    rig.tick()
    rig.agent.start_turn(first["launch_id"])
    rig.tick()
    rig.agent.finish(first["launch_id"], {"a.txt": "2\n"})
    rig.tick()
    assert rig.step(pid, 1)["state"] == "parked"
    # The other step still runs: the park is not his turn yet.
    assert rig.program(pid)["state"] == "running"
    assert program_items(rig.service.needs_you_items()) == []
    park = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "step_failed")
    assert park["choice"] == "park" and park["overturnable"]
    (tmp_path / "red").unlink()
    rig.agent.finish(second["launch_id"], {"b.txt": "1\n"})
    rig.tick(3)
    assert rig.step(pid, 2)["state"] in ("merged", "done")
    # Nothing else runs: one row to him at the end.
    assert [row["why"] for row in program_items(rig.service.needs_you_items())] == ["TO RESUME"]


def test_a_race_of_two_parks_the_loser(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, title="Race", template="race", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Fast path", "brief": "Make it fast."}])
    rig.service.start(OWNER, pid)
    lead = rig.step(pid, 1)
    assert lead["race"] == 2 and len(lead["contenders"]) == 1
    contender = lead["contenders"][0]
    assert (lead["profile"], contender["profile"]) == ("claude-default", "codex-default")
    assert lead["branch"] != contender["branch"]
    rig.agent.finish(contender["launch_id"], {"fast.py": "codex\n"})
    rig.tick()
    lead, contender = rig.step(pid, 1), rig.step(pid, 1, contender=1)
    assert contender["state"] in ("pr_open", "merge_ask", "merged", "done"), contender
    assert lead["state"] == "parked" and lead["parked_by"] == "race"
    assert lead["parked_reason"] == "Lost the race to Codex"
    assert any(r["kind"] == "race_winner" and "Codex won the race" in r["line"]
               for r in rig.program(pid)["decided_for_you"])
    assert not [row for row in program_items(rig.service.needs_you_items()) if row["why"] == "TO RESUME"]


def test_programs_off_ticks_nothing(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, title="Off", template="fast-cycle")
    rig.service.plan(OWNER, pid, steps=[{"title": "Nothing", "brief": "x"}])
    monkeypatch.setenv("HOLDSPEAK_PROGRAMS", "off")
    rig.service.start(OWNER, pid)
    assert rig.runner.tick() == []
    assert rig.hand.calls == []
    assert rig.step(pid, 1)["state"] == "planned"
    from holdspeak.services.program_runner import tick

    assert tick() == []


def _bind(rig: Rig, launch_id: str, session_key: str) -> None:
    """The launch's work attempt bound to its agent session, as the real
    hand binds it (``factory_launch._bind_session``)."""
    attempt = rig.db.work_attempts.create(
        source_id="src", worktree_id="wt", project="app", story_id=launch_id, kind="launch", exact=True,
        session_id=session_key, claimed_by="launch:claude-default", state="working",
    )
    rig.ledger.update(launch_id, attempt_id=attempt.attempt_id)


def _wait_for(predicate, seconds: float) -> float:
    import time

    start = time.monotonic()
    while time.monotonic() - start < seconds:
        if predicate():
            return time.monotonic() - start
        time.sleep(0.02)
    raise AssertionError(f"not within {seconds} s")


def test_pg12_a_coder_frame_moves_the_step_to_checking_at_once(tmp_path) -> None:
    from holdspeak.services.program_runner import TICK_SECONDS, programs_of_sessions, tick_on_frames

    rig = Rig(tmp_path)
    pid = _program(rig, title="Frames", template="fast-cycle", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    _bind(rig, step["launch_id"], "claude:s-frame")
    assert programs_of_sessions(rig.db, ["claude:s-frame", "codex:other"], ledger=rig.ledger) == [pid]
    assert programs_of_sessions(rig.db, ["codex:other"], ledger=rig.ledger) == []
    rig.agent.finish(step["launch_id"], {"one.txt": "1\n"})
    import time

    start = time.monotonic()
    assert tick_on_frames(["claude:s-frame"], runner=rig.runner, ledger=rig.ledger, delay=0.2) == [pid]
    lines = lambda: [row["line"] for row in rig.service.store.list_checkpoints(pid)]  # noqa: E731
    _wait_for(lambda: any(line.startswith("New commit") for line in lines()), 5)
    elapsed = time.monotonic() - start
    # The frame's tick, not the conductor's: well inside one second.
    assert elapsed < 1.0 < TICK_SECONDS, elapsed
    assert rig.step(pid, 1)["state"] != "working"


def test_pg12_frames_inside_the_window_give_one_tick(tmp_path, monkeypatch) -> None:
    from holdspeak.services import program_runner

    rig = Rig(tmp_path)
    pid = _program(rig, title="Debounce", template="fast-cycle", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    _bind(rig, rig.step(pid, 1)["launch_id"], "claude:s-deb")
    ticks: list[str] = []
    real = rig.runner._tick_program
    monkeypatch.setattr(rig.runner, "_tick_program", lambda program_id: (ticks.append(program_id), real(program_id))[1])
    first = program_runner.tick_on_frames(["claude:s-deb"], runner=rig.runner, ledger=rig.ledger, delay=0.3)
    second = program_runner.tick_on_frames(["claude:s-deb"], runner=rig.runner, ledger=rig.ledger, delay=0.3)
    third = program_runner.tick_on_frames(["claude:s-deb"], runner=rig.runner, ledger=rig.ledger, delay=0.3)
    assert (first, second, third) == ([pid], [], [])
    _wait_for(lambda: ticks == [pid] and pid not in program_runner._FRAME_TIMERS, 3)
    # After the window a new frame schedules a new tick.
    assert program_runner.tick_on_frames(["claude:s-deb"], runner=rig.runner, ledger=rig.ledger, delay=0.05) == [pid]
    _wait_for(lambda: ticks == [pid, pid], 3)


def test_pg12_a_frame_waits_for_a_tick_in_flight(tmp_path) -> None:
    from holdspeak.services import program_runner

    rig = Rig(tmp_path)
    pid = _program(rig, title="One at a time", template="fast-cycle", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    _bind(rig, step["launch_id"], "claude:s-lock")
    rig.agent.finish(step["launch_id"], {"one.txt": "1\n"})
    lock = program_runner._program_lock(pid)
    lock.acquire()  # a tick of this Program is in flight
    try:
        assert program_runner.tick_on_frames(["claude:s-lock"], runner=rig.runner, ledger=rig.ledger, delay=0.05) == [pid]
        import time

        time.sleep(0.4)
        assert rig.step(pid, 1)["state"] in ("briefed", "working")  # never two ticks at once
    finally:
        lock.release()
    _wait_for(lambda: rig.step(pid, 1)["state"] not in ("briefed", "working"), 5)


def test_pg12_programs_off_schedules_nothing(tmp_path, monkeypatch) -> None:
    from holdspeak.services import program_runner

    rig = Rig(tmp_path)
    pid = _program(rig, title="Off frames", template="fast-cycle", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "One", "brief": "x"}])
    rig.service.start(OWNER, pid)
    _bind(rig, rig.step(pid, 1)["launch_id"], "claude:s-off")
    monkeypatch.setenv("HOLDSPEAK_PROGRAMS", "off")
    assert program_runner.tick_on_frames(["claude:s-off"], runner=rig.runner, ledger=rig.ledger, delay=0.01) == []
    assert program_runner.schedule_tick(pid, runner=rig.runner, delay=0.01) is False
    assert pid not in program_runner._FRAME_TIMERS


def test_pg12_the_hub_coder_watcher_hands_its_frames_to_the_programs(monkeypatch) -> None:
    from holdspeak import web_server
    from holdspeak.services import program_runner

    seen: list[list[str]] = []
    monkeypatch.setattr(program_runner, "tick_on_frames", lambda keys: (seen.append(list(keys)), ["p-1"])[1])
    assert web_server._program_frame_ticks(["claude:s1"]) == ["p-1"]
    assert seen == [["claude:s1"]]
    monkeypatch.setattr(program_runner, "tick_on_frames", lambda keys: 1 / 0)
    assert web_server._program_frame_ticks(["claude:s1"]) == []


def test_a_person_review_holds_the_merge_until_their_approval(tmp_path) -> None:
    class People:
        def display_names(self):
            return {"p-alice": "Alice"}

        def get_relationship(self, principal, person_id):
            return {"display_name": "Alice Smith", "owner_aliases": ["alice-gh"]}

    rig = Rig(tmp_path, people=lambda: People())
    pid = _program(rig, title="Reviewed", template="fast-cycle", for_person_id="p-alice", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Ask Alice", "brief": "x", "gate_review": "person"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"b.txt": "b\n"})
    rig.tick(2)
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open", step
    items = rig.service.needs_you_items()
    assert [item["kind"] for item in items] == ["ask_review"]
    assert items[0]["title"] == f"Ask Alice to review PR #{step['pr']['number']}"
    asked = rig.service.decide(OWNER, pid, step["id"], kind="ask_review", choice="prepare")
    assert "could you review PR" in asked["draft"]
    assert not [call for call in rig.gh.calls if call[1:3] == ["pr", "merge"]]  # the engine sends nothing
    rig.gh.prs[step["pr"]["number"]]["approved_by"] = ["bob"]
    rig.tick()
    assert rig.step(pid, 1)["state"] == "pr_open"
    with pytest.raises(Exception) as refused:
        rig.service.decide(OWNER, pid, step["id"], kind="merge", choice="merge")
    assert getattr(refused.value, "code", "") == "person_review_missing"
    # Alice (by her GitHub alias) approves: Normal merges.
    rig.gh.prs[step["pr"]["number"]]["approved_by"] = ["Alice-GH"]
    rig.tick(2)
    assert rig.step(pid, 1)["state"] in ("merged", "done")


def test_a_diff_outside_the_owned_files_is_a_core_question(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, title="Shape", template="fast-cycle", control="yolo")
    rig.service.plan(OWNER, pid, steps=[{"title": "Owned", "brief": "x", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"src/a.py": "a\n", "other/b.py": "b\n"})
    rig.tick()
    items = rig.service.needs_you_items()
    assert [item["kind"] for item in items] == ["core"]
    assert "files no step owns (other/b.py)" in items[0]["title"]
    assert program_items(items)[0]["why"] == "TO DECIDE"
    rig.service.decide(OWNER, pid, step["id"], kind="core", choice="go_on")
    rig.tick()
    assert rig.step(pid, 1)["state"] in ("pr_open", "merged", "done")


def test_from_the_desk_closes_its_action_on_merge(tmp_path) -> None:
    from holdspeak.delivery.follow_through import FollowThroughObserver
    from holdspeak.services.program_service import step_origin

    rig = Rig(tmp_path)
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-1', 'App')")
        conn.execute("INSERT INTO meetings (id, started_at, title) VALUES ('m1', '2026-10-27T10:00:00', 'Sync')")
        conn.execute("INSERT INTO meeting_projects (meeting_id, project_id, confidence) VALUES ('m1', 'proj-1', 0.9)")
        conn.execute("INSERT INTO action_items (id, meeting_id, task, owner, status) "
                     "VALUES ('ai_1', 'm1', 'Fix the login timeout', 'Me', 'open')")
    pid = _program(rig, title="From the desk", template="from-the-desk", project_id="proj-1")
    made = rig.service.plan_from_project(OWNER, pid)
    step = made["steps"][0]
    assert step["origin_ref"] == "action:ai_1" and step["title"] == "Fix the login timeout"
    assert step_origin(rig.db, step["id"]) == ("action", "ai_1")
    with rig.db._connection() as conn:
        filed = conn.execute("SELECT 1 FROM project_resources WHERE project_id='proj-1' AND resource_ref=?",
                             (f"note:program-{pid}",)).fetchone()
    assert filed is not None  # the handover note is filed to the Project
    observer = FollowThroughObserver(rig.db, ledger=rig.ledger, registry=None, receipts=None, attempts=None)
    evidence = {"pr_url": "https://github.com/acme/app/pull/7", "pr_number": "7", "pr_title": "x",
                "merged_sha": "abc", "merged_at": "2026-10-28T10:00:00Z", "attempt_id": "", "launch_id": "L1"}
    launch = {"launch_id": "L1", "origin_ref": {"kind": "program_step", "id": step["id"]}}
    assert observer._close_or_confirm(OWNER, launch, {}, evidence, "yolo") == "closed"
    with rig.db._connection() as conn:
        status = conn.execute("SELECT status FROM action_items WHERE id='ai_1'").fetchone()[0]
    assert status == "done"
    from holdspeak.services.project_service import ProjectService

    room = ProjectService(rig.db).room(OWNER, "proj-1")
    assert room["programs"]["state"] == "ok"
    assert room["programs"]["programs"][0]["id"] == pid


def test_the_one_on_one_brief_lists_a_merged_step_to_show(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, title="For Alice", template="fast-cycle", for_person_id="p-alice", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Her ask", "brief": "x"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    rig.agent.finish(step["launch_id"], {"c.txt": "c\n"})
    rig.tick(3)
    step = rig.step(pid, 1)
    assert step["state"] in ("merged", "done")
    from holdspeak.services.people_service import PeopleService

    lines = PeopleService._brief_programs(rig.db, "p-alice", "2026-01-01T00:00:00+00:00")
    assert lines and lines[0]["title"] == "For Alice"
    assert lines[0]["to_show"][0]["title"] == "Her ask"
    assert lines[0]["to_show"][0]["pr_number"] == step["pr"]["number"]
    assert lines[0]["line"].startswith("For Alice · 1 of 1")
    later = PeopleService._brief_programs(rig.db, "p-alice", "2999-01-01T00:00:00+00:00")
    assert later[0]["to_show"] == []
