"""Programs PG-REQ (2026-10-31): the owner's requirements on the rig.

PROGRAMS-REQUIREMENTS-2026-10-31.md §4 to §6, §10, §15: a requirement of
each kind is stored, read on the wire and counted; an edit of a Met one is
Not yet; a check requirement is judged at CHECK by its log (red once, Met on
round 2), a new commit sets Not yet; the reviewer's ``REQ R2: UNMET`` sends a
round back and ``MET`` sets Met with its line; no answer re-asks once; his
word holds the merge at every level; a requirement left after the rounds
parks the step at Normal and the rest goes on; the end check runs on the
base branch; the brief lists each requirement and how it is proven; the
templates plant theirs.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.principals import AgentCredentialStore, Principal
from holdspeak.services.program_brief import compose
from holdspeak.services.program_requirements import counts, guess, parse_review
from holdspeak.services.program_service import ProgramRefused
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git

PASS_CMD = "echo 12 passed"


def _program(rig: Rig, *, control: str = "normal", template: str = "fast-cycle", **kw) -> str:
    return rig.service.create(OWNER, title="The hub stops stalling", goal="Stop the stalls.", repository=str(rig.repo),
                              check_command=f"sh {FAKE_CHECK}", control=control, template=template, **kw)["id"]


def _req(rig: Rig, pid: str, rid: str) -> dict:
    wire = rig.program(pid)
    rows = list(wire["requirements"]) + [row for step in wire["steps"] for row in step["requirements"]]
    return next(row for row in rows if row["id"] == rid)


def _red_file(tmp_path: Path) -> Path:
    return tmp_path / "red-flag"


def _red_cmd(flag: Path) -> str:
    """A check command that is red while ``flag`` exists (round 1), green after."""
    return f"if [ -f {flag} ]; then echo '1 failed, 3 passed'; exit 1; fi; echo '4 passed'"


# ── the rule (decision 5) and the parse ──────────────────────────────

def test_the_kind_is_guessed_by_rule_never_by_a_model() -> None:
    assert guess("`uv run pytest -q tests/unit/test_program_rules.py` is green") == (
        "check", {"command": "uv run pytest -q tests/unit/test_program_rules.py"})
    assert guess("The People window at 393 has no clipped text") == ("shot", {"case": "people", "width": 393})
    assert guess("No new route skips the residual set") == ("review", {})
    # Read from the REVIEW RESULT block only (Astra post-merge 2026-11-01).
    assert parse_review("REQ R2: UNMET · projects.py adds a route\nREQ R3: MET · ok\nMUST: none") == {}
    assert parse_review("REVIEW RESULT\nREQ R2: UNMET · projects.py adds a route\nREQ R3: MET · ok\nMUST: none\n"
                        "END REVIEW RESULT") == {
        2: {"answer": "UNMET", "line": "projects.py adds a route", "raw": "REQ R2: UNMET · projects.py adds a route"},
        3: {"answer": "MET", "line": "ok", "raw": "REQ R3: MET · ok"},
    }


# ── REQ1: stored, on the wire, counted; an edit resets ───────────────

def test_a_requirement_of_each_kind_is_stored_read_and_counted(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="")
    rig.service.plan(OWNER, pid, steps=[{"title": "Indexes"}, {"title": "Retention"}])
    one, two = rig.step(pid, 1), rig.step(pid, 2)
    check = rig.service.require(OWNER, pid, text=f"`{PASS_CMD}` is green", step_id=one["id"])
    review = rig.service.require(OWNER, pid, text="No new route skips the residual set", step_id=two["id"])
    word = rig.service.require(OWNER, pid, text="I tried it on my desk", kind="word", step_id=two["id"])
    every = rig.service.require(OWNER, pid, text="The change does only what its brief says.", each_step=True)
    whole = rig.service.require(OWNER, pid, text="The desk opens", kind="word")
    with pytest.raises(ProgramRefused) as refused:  # no shot command in this repository: a core question
        rig.service.require(OWNER, pid, text="The People window at 393 has no clipped text", step_id=one["id"])
    assert refused.value.code == "requirement_unprovable"
    assert "No shot command" in refused.value.detail

    wire = rig.program(pid)
    first = _req(rig, pid, check["requirement_id"])
    assert (first["kind"], first["kind_word"], first["label"], first["scope"], first["state_word"]) == (
        "check", "Check", "R1", "step", "Not yet")
    assert first["spec"] == {"command": PASS_CMD} and first["choices"] == ["waive"]
    assert _req(rig, pid, review["requirement_id"])["kind_word"] == "Review"
    assert _req(rig, pid, word["requirement_id"])["choices"] == ["met", "unmet", "waive"]
    parent = _req(rig, pid, every["requirement_id"])
    assert parent["scope"] == "every_step" and [row["ordinal"] for row in parent["steps"]] == [1, 2]
    assert _req(rig, pid, whole["requirement_id"])["scope"] == "program"
    # Counted once each: 1 + 2 own, two copies of the every-step one, one of the program's own.
    assert wire["requirements_met"] == {"met": 0, "total": 6, "unmet": 0, "waived": 0, "his": 0}
    assert [row["label"] for row in wire["steps"][1]["requirements"]] == ["R2", "R3", "R4"]
    assert wire["steps"][1]["requirements_met"]["total"] == 3
    assert rig.service.list(OWNER)["programs"][0]["requirements_met"]["total"] == 6
    assert wire["can_prove"]["shot"] is False and wire["can_prove"]["shot_reason"] == "No shot command in this repository"

    # His word Met, then an edit of the sentence: Not yet again.
    rig.service.decide_requirement(OWNER, pid, word["requirement_id"], "met")
    assert _req(rig, pid, word["requirement_id"])["state"] == "met"
    rig.service.edit_requirement(OWNER, pid, word["requirement_id"], text="I tried it on my desk at 393")
    row = _req(rig, pid, word["requirement_id"])
    assert row["state"] == "not_yet" and row["text"] == "I tried it on my desk at 393"
    lines = [c for c in rig.program(pid)["checkpoints"] if c["kind"] == "requirement"]
    assert lines and all(c["undo"].get("requirement_id") or c["undo"].get("requirement_ids") for c in lines)


def test_a_waive_needs_his_line_and_stays_on_the_list(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="")
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}])
    rid = rig.service.require(OWNER, pid, text="It reads well", step_id=rig.step(pid, 1)["id"])["requirement_id"]
    with pytest.raises(ProgramRefused) as refused:
        rig.service.decide_requirement(OWNER, pid, rid, "waive")
    assert refused.value.code == "line_required"
    rig.service.decide_requirement(OWNER, pid, rid, "waive", line="The copy lane owns this")
    row = _req(rig, pid, rid)
    assert (row["state"], row["state_word"], row["waived_reason"], row["choices"]) == (
        "waived", "Waived", "The copy lane owns this", [])
    met = rig.program(pid)["requirements_met"]
    assert met["met"] == 1 and met["waived"] == 1
    assert "Waived: The copy lane owns this" in rig.note(pid)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.decide_requirement(OWNER, pid, rid, "met")
    assert refused.value.code == "requirement_waived"


def test_an_agent_proposes_and_only_the_owner_waives(tmp_path, monkeypatch) -> None:
    from holdspeak.mcp import palettes
    from holdspeak.mcp.families import program as family

    rig = Rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    pid = _program(rig, control="normal", template="")
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}])
    rig.service.start(OWNER, pid)
    one = rig.step(pid, 1)
    store = AgentCredentialStore()
    agent: Principal = store.issue(f"agent:launch:{one['launch_id']}", palette=palettes.resolve_palette("CONDUCTOR"),
                                   palette_name="CONDUCTOR", launch_id=one["launch_id"]).principal
    monkeypatch.setattr("holdspeak.principals.agent_credentials", store)
    assert {"program.require", "program.step_update", "program.amend"} <= palettes.resolve_palette("CONDUCTOR")

    answer = family.dispatch("program.require", {"program_id": pid, "text": "The empty state has words",
                                                 "step_id": one["id"]}, agent)
    assert answer["proposed"] and not rig.program(pid)["steps"][0]["requirements"]
    item = next(i for i in rig.program(pid)["your_turn_items"] if i["kind"] == "requirement_proposed")
    assert item["choices"] == ["add", "skip"] and "The empty state has words" in item["title"]
    with pytest.raises(ProgramRefused) as refused:
        family.dispatch("program.decide", {"program_id": pid, "kind": "requirement_proposed", "choice": "add",
                                           "proposal_id": item["proposal_id"]}, agent)
    assert refused.value.code == "owner_required"
    family.dispatch("program.decide", {"program_id": pid, "kind": "requirement_proposed", "choice": "add",
                                       "proposal_id": item["proposal_id"]}, OWNER)
    rows = rig.program(pid)["steps"][0]["requirements"]
    assert [(row["text"], row["by"]) for row in rows] == [("The empty state has words", "agent")]
    with pytest.raises(ProgramRefused) as refused:
        family.dispatch("program.decide", {"program_id": pid, "kind": "requirement", "choice": "waive",
                                           "requirement_id": rows[0]["id"], "reason": "x"}, agent)
    assert refused.value.code == "owner_required"
    # YOLO adds it and says so under Decided for you (Overturn sets it aside).
    rig.service.update(OWNER, pid, control="yolo")
    family.dispatch("program.require", {"program_id": pid, "text": "The title is plain", "step_id": one["id"]}, agent)
    decided = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "requirement_proposed")
    assert decided["overturnable"]
    rig.service.overturn(OWNER, pid, decided["id"])
    plain = next(r for r in rig.program(pid)["steps"][0]["requirements"] if r["text"] == "The title is plain")
    assert plain["state"] == "waived" and plain["required"] is False


# ── REQ2: check requirements at CHECK; staleness ────────────────────

def test_a_red_check_requirement_is_a_check_round_and_met_on_round_two(tmp_path) -> None:
    rig = Rig(tmp_path)
    flag = _red_file(tmp_path)
    flag.write_text("1")
    pid = _program(rig, template="", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Indexes", "brief": "Add the indexes."}])
    one = rig.step(pid, 1)
    rid = rig.service.require(OWNER, pid, text="The tests are green", kind="check",
                              spec={"command": _red_cmd(flag), "expect": r"\b4 passed\b"},
                              step_id=one["id"])["requirement_id"]
    rig.service.start(OWNER, pid)
    one = rig.step(pid, 1)
    rig.agent.finish(one["launch_id"], {"a.py": "1\n"})
    rig.tick()
    step = rig.step(pid, 1)
    row = _req(rig, pid, rid)
    assert step["state"] == "check_failed" and step["check"]["verdict"] == "green", step["state"]
    assert row["state"] == "unmet" and row["rounds"] == 1 and row["evidence"]["kind"] == "log"
    assert row["evidence"]["url"] == f"/api/programs/{pid}/requirements/{rid}/evidence"
    assert Path(row["evidence"]["ref"]).name.endswith("-R1.log")
    prompt = rig.prompts[-1][1]
    assert "R1 is red" in prompt and "1 failed" in prompt
    assert any(r["kind"] == "requirement_red" for r in rig.program(pid)["decided_for_you"])

    flag.unlink()
    first_commit = rig.agent.finish(one["launch_id"], {"a.py": "2\n"})
    rig.tick(3)
    row = _req(rig, pid, rid)
    assert row["state"] == "met" and row["judged_commit"] == first_commit
    assert row["evidence"]["line"] == "4 passed"
    step = rig.step(pid, 1)
    assert step["state"] in ("merged", "done"), step["state"]


def test_a_new_commit_sets_not_yet_and_his_word_stays(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="secure")
    rig.service.plan(OWNER, pid, steps=[{"title": "Indexes"}])
    sid = rig.step(pid, 1)["id"]
    check = rig.service.require(OWNER, pid, text=f"`{PASS_CMD}`", step_id=sid)["requirement_id"]
    word = rig.service.require(OWNER, pid, text="I tried it", kind="word", step_id=sid)["requirement_id"]
    rig.service.start(OWNER, pid)
    one = rig.step(pid, 1)
    rig.agent.finish(one["launch_id"], {"a.py": "1\n"})
    rig.tick(2)
    assert _req(rig, pid, check)["state"] == "met"
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open", step["state"]  # Secure, and his word holds the merge ask
    assert [i["kind"] for i in rig.program(pid)["your_turn_items"]] == ["requirement_word"]
    rig.service.decide_requirement(OWNER, pid, word, "met")
    # A new commit (the moved head) on the PR: the check requirement goes back to Not yet.
    program = rig.service.store.get_program(pid)
    raw = rig.service.store.get_step(sid)
    rig.service.transition(program, raw, "working", by="engine")
    head = rig.agent.finish(one["launch_id"], {"a.py": "2\n"})
    rig.service.transition(program, rig.service.store.get_step(sid), "checking", head_commit=head)
    assert _req(rig, pid, check)["state"] == "not_yet" and _req(rig, pid, check)["stale"]
    assert _req(rig, pid, word)["state"] == "met"
    assert any("The commit moved: R1" in c["line"] for c in rig.program(pid)["checkpoints"])


# ── REQ3: the reviewer's REQ lines ───────────────────────────────────

def _reviewed_step(rig: Rig, pid: str) -> dict:
    rig.service.start(OWNER, pid)
    one = rig.step(pid, 1)
    rig.agent.finish(one["launch_id"], {"routes.py": "x\n"})
    rig.tick(2)  # the check, then the reviewer starts
    return one


def _answer(rig: Rig, words: str, *, turn: str = "r") -> str:
    reviewer = [r for r in rig.ledger.list() if r.get("helper_of")][-1]["launch_id"]
    rig.words[reviewer] = words
    rig.states[reviewer] = {"state": "done", "turn_id": turn}
    rig.tick(2)
    return reviewer


def test_the_reviewers_unmet_sends_a_round_back_and_met_sets_met(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="build-and-review", reviewer_profile="codex-default")
    rig.service.plan(OWNER, pid, steps=[{"title": "Projects routes", "brief": "Through the threadpool."}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="No new route skips the residual set", step_id=sid)["requirement_id"]
    label = _req(rig, pid, rid)["label"]
    one = _reviewed_step(rig, pid)
    helper = [r for r in rig.ledger.list() if r.get("helper_of")][-1]
    assert f"{label} · No new route skips the residual set" in helper["review"]["acceptance"]
    _answer(rig, f"MUST: none\nREQ R1: MET · ok\nREQ R2: MET · has tests\nREQ {label}: UNMET · projects.py adds /fold with no entry")
    row = _req(rig, pid, rid)
    assert row["state"] == "unmet" and "projects.py adds /fold" in row["evidence"]["line"]
    assert any(f"MUST: {label} is unmet" in text for _launch, text in rig.prompts), rig.prompts
    assert rig.step(pid, 1)["state"] == "findings"
    finding = rig.step(pid, 1)["findings"][0]
    assert finding["requirement_id"] == rid and finding["level"] == "REQUIRED"

    rig.agent.finish(one["launch_id"], {"routes.py": "y\n"})
    rig.tick(2)
    _answer(rig, f"MUST: none\nREQ R1: MET · ok\nREQ R2: MET · has tests\nREQ {label}: MET · the entry is there", turn="r2")
    rig.tick(2)
    row = _req(rig, pid, rid)
    assert row["state"] == "met" and row["evidence"]["line"] == "the entry is there"
    assert rig.step(pid, 1)["state"] in ("merged", "done")


def test_no_answer_asks_the_reviewer_once_more_then_him(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="normal", reviewer_profile="codex-default")
    rig.service.plan(OWNER, pid, steps=[{"title": "Projects routes"}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="No new route skips the residual set", step_id=sid)["requirement_id"]
    _reviewed_step(rig, pid)  # a Review requirement brings the reviewer to a step with no review gate
    reviewer = _answer(rig, "MUST: none\nREQ R9: MET · something else")
    assert rig.step(pid, 1)["state"] == "review"
    assert any(launch == reviewer and "you gave no answer for R1" in text for launch, text in rig.prompts)
    assert any(r["kind"] == "requirement_unanswered" for r in rig.program(pid)["decided_for_you"])
    # The second answer still names nothing: his row (Send back / Waive).
    rig.words[reviewer] = "REQ: I looked."  # names no requirement by its id
    rig.states[reviewer] = {"state": "done", "turn_id": "r-second"}
    rig.tick()
    items = [i for i in rig.program(pid)["your_turn_items"] if i["kind"] == "requirement_left"]
    assert [(i["requirement_id"], i["choices"]) for i in items] == [(rid, ["send_back", "waive"])]
    assert _req(rig, pid, rid)["state_word"] == "Waits for you"
    rig.service.decide_requirement(OWNER, pid, rid, "waive", line="The census covers it")
    rig.tick(2)
    assert rig.step(pid, 1)["state"] in ("merged", "done")


# ── REQ4: the gate and the rules by level ────────────────────────────

@pytest.mark.parametrize("control", ["secure", "normal", "yolo"])
def test_his_word_holds_the_merge_at_every_level(tmp_path, control) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control=control)
    rig.service.plan(OWNER, pid, steps=[{"title": "Projections off the loop"}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="I tried it on my desk", kind="word", step_id=sid)["requirement_id"]
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(3)
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open", (control, step["state"])
    item = next(i for i in rig.program(pid)["your_turn_items"] if i["kind"] == "requirement_word")
    assert item["title"] == "Step 1 · Projections off the loop: R1 · I tried it on my desk"
    assert item["choices"] == ["met", "unmet"]
    if control == "secure":
        with pytest.raises(ProgramRefused) as refused:
            rig.service.decide(OWNER, pid, sid, kind="merge", choice="merge")
        assert refused.value.code in ("requirements_not_met", "not_mergeable")
    rig.service.decide_requirement(OWNER, pid, rid, "met")
    rig.tick()
    step = rig.step(pid, 1)
    if control == "secure":
        assert step["state"] == "merge_ask"
    else:
        assert step["state"] in ("merged", "done"), step["state"]


def test_unmet_word_sends_it_back_with_his_line(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Dock"}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="I tried it on my desk", kind="word", step_id=sid)["requirement_id"]
    rig.service.start(OWNER, pid)
    launch = rig.step(pid, 1)["launch_id"]
    rig.agent.finish(launch, {"a.py": "1\n"})
    rig.tick(3)
    rig.service.decide_requirement(OWNER, pid, rid, "unmet", line="The dock still jumps at 393")
    step = rig.step(pid, 1)
    assert step["state"] == "working"
    assert "The owner: The dock still jumps at 393" in rig.prompts[-1][1]
    # The fix: a new commit; the same PR comes back, and his word is asked again.
    rig.agent.finish(launch, {"a.py": "2\n"})
    rig.tick(3)
    step = rig.step(pid, 1)
    assert step["state"] == "pr_open" and step["pr"]["number"] == 101, step
    assert len(rig.gh.prs) == 1


@pytest.mark.parametrize("control, parked", [("secure", True), ("normal", True), ("yolo", False)])
def test_a_requirement_left_after_the_rounds(tmp_path, control, parked) -> None:
    rig = Rig(tmp_path)
    flag = _red_file(tmp_path)
    flag.write_text("1")
    pid = _program(rig, template="", control=control)
    rig.service.plan(OWNER, pid, steps=[{"title": "Projects routes"}, {"title": "People routes"}])
    one, two = rig.step(pid, 1), rig.step(pid, 2)
    rid = rig.service.require(OWNER, pid, text="Green", kind="check", spec={"command": _red_cmd(flag)},
                              step_id=one["id"])["requirement_id"]
    rig.service.start(OWNER, pid)
    launch = rig.step(pid, 1)["launch_id"]
    rig.agent.finish(launch, {"a.py": "1\n"})
    rig.tick()
    rig.agent.finish(launch, {"a.py": "2\n"})
    rig.tick()
    step = rig.step(pid, 1)
    if parked:
        assert step["state"] == "parked" and "R1 is unmet after 2 rounds" in step["parked_reason"], step["state"]
        item = next(i for i in rig.program(pid)["your_turn_items"] if i["kind"] == "requirement_left")
        assert item["requirement_id"] == rid and item["choices"] == ["send_back", "waive"]
        assert not any(i["kind"] == "parked" for i in rig.program(pid)["your_turn_items"])
        rules = {r["kind"] for r in rig.program(pid)["decided_for_you"]}
        assert ("requirement_left" in rules) is (control == "normal")
        # The rest goes on: step 2 works.
        assert rig.step(pid, 2)["state"] in ("briefed", "working")
        # His Waive: the step goes on to its PR.
        rig.service.decide_requirement(OWNER, pid, rid, "waive", line="Flaky on this box")
        assert rig.step(pid, 1)["state"] in ("pr_open", "merge_ask", "merged", "done")
    else:
        # YOLO: three rounds, then one smaller brief that names the
        # requirement, then (three rounds later) the step parks.
        assert step["state"] == "check_failed"
        rig.agent.finish(launch, {"a.py": "3\n"})
        rig.tick()
        assert "smallest change that meets R1" in rig.prompts[-1][1]
        for n in (4, 5, 6):
            rig.agent.finish(launch, {"a.py": f"{n}\n"})
            rig.tick()
        assert rig.step(pid, 1)["state"] == "parked"
        assert any(i["kind"] == "requirement_left" for i in rig.program(pid)["your_turn_items"])


def test_send_back_gives_one_more_round_after_the_rounds(tmp_path) -> None:
    rig = Rig(tmp_path)
    flag = _red_file(tmp_path)
    flag.write_text("1")
    pid = _program(rig, template="", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Projects routes"}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="Green", kind="check", spec={"command": _red_cmd(flag)},
                              step_id=sid)["requirement_id"]
    rig.service.start(OWNER, pid)
    launch = rig.step(pid, 1)["launch_id"]
    for n in (1, 2):
        rig.agent.finish(launch, {"a.py": f"{n}\n"})
        rig.tick()
    assert rig.step(pid, 1)["state"] == "parked"
    rig.service.decide_requirement(OWNER, pid, rid, "send_back", line="Run it on the new index")
    assert rig.step(pid, 1)["state"] == "working"
    assert "R1 is unmet" in rig.prompts[-1][1] and "Run it on the new index" in rig.prompts[-1][1]
    flag.unlink()
    rig.agent.finish(launch, {"a.py": "3\n"})
    rig.tick(3)
    assert _req(rig, pid, rid)["state"] == "met"
    assert rig.step(pid, 1)["state"] in ("merged", "done")


def test_the_end_check_runs_on_the_base_branch_and_his_word_waits(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Indexes"}])
    end = rig.service.require(OWNER, pid, text=f"`{PASS_CMD}` on main")["requirement_id"]
    word = rig.service.require(OWNER, pid, text="The desk feels fast", kind="word")["requirement_id"]
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(4)
    row = _req(rig, pid, end)
    assert row["state"] == "met" and row["evidence"]["end_check"] is True
    assert row["judged_commit"] == git(rig.repo, "rev-parse", "origin/main")
    assert (tmp_path / f"hs-program-{pid}-end").is_dir()
    wire = rig.program(pid)
    assert wire["state"] == "waiting" and not wire["closed_at"]
    item = next(i for i in wire["your_turn_items"] if i["kind"] == "requirement_word")
    assert item["step_id"] == "" and item["title"] == "The program: R2 · The desk feels fast"
    rig.service.decide_requirement(OWNER, pid, word, "met")
    wire = rig.program(pid)
    assert wire["state"] == "done" and wire["closed_at"]


# ── REQ5: the builder's brief ────────────────────────────────────────

def test_the_brief_lists_the_requirements_and_how_each_is_proven(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="")
    rig.service.plan(OWNER, pid, steps=[{"title": "People routes", "brief": "31 handlers."}])
    sid = rig.step(pid, 1)["id"]
    rig.service.require(OWNER, pid, text="The People routes take no lock on the event loop", step_id=sid)
    rig.service.require(OWNER, pid, text="`uv run pytest -q tests/unit/test_hub_loop_budget.py` is green", step_id=sid)
    rig.service.require(OWNER, pid, text="The owner tried it on his desk", kind="word", step_id=sid)
    waived = rig.service.require(OWNER, pid, text="Not this one", step_id=sid)["requirement_id"]
    rig.service.decide_requirement(OWNER, pid, waived, "waive", line="no")
    rig.service.require(OWNER, pid, text="The desk opens", kind="word")
    text = compose(rig.db, sid)["text"]
    assert "What must be true (the owner's requirements; HoldSpeak checks each one):" in text
    assert "- R1 · The People routes take no lock on the event loop · the reviewer judges it" in text
    assert "- R2 · `uv run pytest -q tests/unit/test_hub_loop_budget.py` is green · HoldSpeak runs it on your commit" in text
    assert "- R3 · The owner tried it on his desk · the owner says it" in text
    assert "Not this one" not in text
    assert "For the whole program (judged after the last step): R5 · The desk opens" in text
    assert "Do not claim a requirement is met. HoldSpeak judges each one on your commit." in text
    assert text.index("This step:") < text.index("What must be true") < text.index("The rules and the proof:")


# ── REQ6: templates ──────────────────────────────────────────────────

def test_each_template_plants_its_every_step_requirements(tmp_path) -> None:
    rig = Rig(tmp_path)
    wanted = {
        "build-and-review": ["The change does only what its brief says.", "Each new behaviour has a test."],
        "overnight": ["The change does only what its brief says.", "Each new behaviour has a test."],
        # No reviewer on their steps: a Review has no one to answer it (§2).
        "fast-cycle": [], "race": [], "from-the-desk": [],
    }
    for template, texts in wanted.items():
        pid = rig.service.create(OWNER, title=template, repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                                 template=template, control="normal")["id"]
        rig.service.plan(OWNER, pid, steps=[{"title": "A"}, {"title": "B"}])
        wire = rig.program(pid)
        assert [(row["text"], row["scope"], row["by"]) for row in wire["requirements"]] == [
            (text, "every_step", "template") for text in texts], template
        for step in wire["steps"]:
            assert [row["text"] for row in step["requirements"]] == texts, template


def test_the_repository_names_its_own_defaults(tmp_path) -> None:
    rig = Rig(tmp_path)
    (rig.repo / ".holdspeak").mkdir()
    (rig.repo / ".holdspeak" / "program.json").write_text(json.dumps({
        "shot": "echo shot {case} {width}", "shot_image": ".tmp/shots/{case}-{width}.png",
        "requirements": [{"text": f"`{PASS_CMD}`", "kind": "check", "each_step": True}],
    }))
    pid = _program(rig, template="fast-cycle")
    rig.service.plan(OWNER, pid, steps=[{"title": "A"}])
    wire = rig.program(pid)
    assert [(row["kind"], row["by"]) for row in wire["requirements"]] == [("check", "template")]
    assert wire["can_prove"]["shot"] is True
    shot = rig.service.require(OWNER, pid, text="The People window at 393 has no clipped text",
                               step_id=rig.step(pid, 1)["id"])["requirement_id"]
    assert _req(rig, pid, shot)["spec"] == {"case": "people", "width": 393}


def test_a_shot_is_met_with_its_image(tmp_path) -> None:
    rig = Rig(tmp_path)
    (rig.repo / ".holdspeak").mkdir()
    (rig.repo / ".holdspeak" / "program.json").write_text(json.dumps({
        "shot": "mkdir -p .tmp/shots && printf png > .tmp/shots/{case}-{width}.png && echo '1 passed'",
        "shot_image": ".tmp/shots/*{case}-{width}*.png"}))
    git(rig.repo, "add", "-A")
    git(rig.repo, "commit", "-m", "shot config")
    git(rig.repo, "push", "origin", "main")
    pid = _program(rig, template="")
    rig.service.plan(OWNER, pid, steps=[{"title": "People"}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="The People window at 393 has no clipped text", step_id=sid)["requirement_id"]
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick()
    row = _req(rig, pid, rid)
    assert row["state"] == "met" and row["evidence"]["kind"] == "shot", row
    assert row["evidence"]["ref"].endswith("people-393.png") and row["evidence"]["width"] == 393
    found = rig.service.requirement_evidence(OWNER, pid, rid)
    assert found["media"] == "image/png"


def test_counts_draw_no_zero() -> None:
    assert counts([]) is None
    rows = [{"required": True, "state": "met", "step_id": "s"}, {"required": True, "state": "waived", "step_id": "s"},
            {"required": True, "state": "unmet", "step_id": "s"}, {"required": False, "state": "not_yet", "step_id": "s"},
            {"required": True, "state": "not_yet", "each_step": True}]  # a parent counts through its copies
    assert counts(rows, 1) == {"met": 2, "total": 3, "unmet": 1, "waived": 1, "his": 1}


# ── PG-LANG LANG11: the Measure kind, and a walk on Your word ────────

def _measure(rig: Rig, pid: str, sid: str, command: str, bound: dict) -> str:
    return rig.service.require(OWNER, pid, text="The People routes answer fast", kind="measure", step_id=sid,
                               spec={"command": command, **bound})["requirement_id"]


def test_a_measure_under_its_bound_is_met_with_its_value_in_his_words(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="yolo")
    rig.service.plan(OWNER, pid, steps=[{"title": "People routes"}])
    sid = rig.step(pid, 1)["id"]
    rid = _measure(rig, pid, sid, "echo 'warm 900 ms'; echo 'p95 84 ms'",
                   {"metric": "p95", "op": "<", "bound": 100, "unit": "ms"})
    row = _req(rig, pid, rid)
    assert (row["state"], row["state_word"]) == ("not_yet", "Not measured yet")
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(3)
    row = _req(rig, pid, rid)
    assert row["state"] == "met", row
    assert row["evidence"]["line"] == "Measured 84 ms, under 100 ms" and row["evidence"]["value"] == 84
    assert rig.step(pid, 1)["state"] in ("merged", "done")
    lines = [c["line"] for c in rig.program(pid)["checkpoints"]]
    assert "R1 · Met · Measured 84 ms, under 100 ms" in lines


def test_a_measure_over_its_bound_is_a_red_round_for_the_builder(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "People routes"}])
    sid = rig.step(pid, 1)["id"]
    rid = _measure(rig, pid, sid, "echo 'total 2.4 s'", {"metric": "total", "op": "<", "bound": 2, "unit": "s"})
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick()
    row = _req(rig, pid, rid)
    assert row["state"] == "unmet" and row["evidence"]["line"] == "Measured 2.4 s, not under 2 s"
    step = rig.step(pid, 1)
    assert step["state"] == "check_failed" and step["rounds"] == 1, step
    launch, text = rig.prompts[-1]
    assert launch == step["launch_id"] and "R1" in text


def test_a_measure_that_cannot_run_is_unmet_with_the_reason_in_words(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "People routes"}])
    sid = rig.step(pid, 1)["id"]
    rid = _measure(rig, pid, sid, "sh no-such-bench.sh", {"metric": "files", "op": "<=", "bound": 3})
    other = _measure(rig, pid, sid, "echo nothing to see", {"metric": "errors", "op": "=", "bound": 0})
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick()
    row = _req(rig, pid, rid)
    assert row["state"] == "unmet" and row["evidence"]["line"].startswith("Not measured: the command ended with exit ")
    row = _req(rig, pid, other)
    assert row["state"] == "unmet" and row["evidence"]["line"] == "Not measured: the command printed no errors number"


def test_a_walk_is_his_word_only_and_his_row_shows_its_lines(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="", control="yolo")
    rig.service.plan(OWNER, pid, steps=[{"title": "Board"}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="I used the board", kind="word", step_id=sid,
                              spec={"walk": ["Open Programs at 393", "Press Plan it"]})["requirement_id"]
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(3)
    item = next(item for item in rig.program(pid)["your_turn_items"] if item.get("requirement_id") == rid)
    # PG-IMPORT IMP2: a walk is a to-do (Done, Can't do it), with its lines.
    assert item["kind"] == "todo" and item["walk"] == ["Open Programs at 393", "Press Plan it"]
    assert item["choices"] == ["done", "cant"]
    assert _req(rig, pid, rid)["state"] == "not_yet"  # never run, never judged by the engine


def test_a_measure_needs_a_command_and_a_bound(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    with pytest.raises(ProgramRefused) as refused:
        rig.service.require(OWNER, pid, text="It is fast", kind="measure", spec={"command": "sh bench.sh"})
    assert (refused.value.code, refused.value.detail) == ("requirement_unprovable", "A measure needs a command and a bound.")
    with pytest.raises(ProgramRefused) as refused:
        rig.service.require(OWNER, pid, text="It is fast", kind="measure",
                            spec={"command": "sh bench.sh", "metric": "p95", "op": "about", "bound": 3})
    assert refused.value.code == "bound_invalid"


def test_walk_lines_are_kept_on_your_word(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rid = rig.service.require(OWNER, pid, text="I used the board for a morning", kind="word",
                              spec={"walk": ["Open Programs at 393", "  Press   Plan it ", ""]})["requirement_id"]
    row = _req(rig, pid, rid)
    assert (row["kind"], row["spec"]) == ("word", {"walk": ["Open Programs at 393", "Press Plan it"]})
    with pytest.raises(ProgramRefused) as refused:
        rig.service.require(OWNER, pid, text="I tried it", kind="word", spec={"walk": "Open it"})
    assert refused.value.code == "walk_invalid"
