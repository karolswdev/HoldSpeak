"""The owner's BRIEF RULE (2026-10-31), on the Programs rig.

"I saw this briefing. And to be honest? It didn't even make sense to me. I
didn't get enough context plus I felt like I answered, so why is there
more…?"

For each kind he answers from a page (parked with no remote, a red check, a
reviewer's finding, a core question, a held commit, his word, a merge) the
package reads like a note from a chief of staff: the goal, the step, what
happened in plain words, the question in one sentence, each choice with its
consequence in his terms. The fence: no question, consequence, brief line or
changed line holds ``fatal:``, ``error:``, ``Traceback``, a path, a shell
command or a 7+ hex hash. After his press the page settles to one line. The
same lines feed Telegram and the call (one truth).
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from holdspeak.calls.decide import package_words
from holdspeak.services import brief_words as words
from holdspeak.services.briefing_service import BriefingService
from holdspeak.services.telegram_reach import render
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git


class Clock:
    def __init__(self) -> None:
        self.now = datetime(2026, 10, 31, 22, 18, tzinfo=timezone.utc)

    def __call__(self) -> str:
        return self.now.isoformat()


def _program(rig: Rig, *, template: str = "fast-cycle", control: str = "secure", check: str | None = None) -> str:
    return rig.service.create(OWNER, title="README touch", goal="Show the repo has a friendly README.",
                              repository=str(rig.repo), check_command=check or f"sh {FAKE_CHECK}",
                              template=template, control=control)["id"]


def _body(rig: Rig, pid: str, kind: str) -> dict[str, Any]:
    item = next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == kind)
    body = BriefingService(rig.db, programs=lambda: rig.service, clock=Clock()).compose(f"program:{pid}:{item['id']}")
    assert body is not None, item
    return body


def _fenced(body: dict[str, Any]) -> None:
    """The fence over every line he reads."""
    lines = [*body["note"], body["question"], body["blocked_words"], body["place"],
             *(row["consequence"] for row in body["choices"]), *(row["line"] for row in body["changed"])]
    for line in lines:
        assert words.fence_hits(line) == [], (line, words.fence_hits(line))
    assert len(body["changed"]) <= 3
    assert body["question"].endswith("?") and body["question"].count("?") == 1
    assert body["note"] == [body["goal"], body["doing"], body["happened"]]
    assert body["goal"] == "Goal: Show the repo has a friendly README."


def _no_remote(tmp_path: Path) -> tuple[Rig, str]:
    rig = Rig(tmp_path)
    pid = _program(rig)
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Add one line to the README", "brief": "Append one line under the title."},
        {"title": "Link the README", "brief": "Link it from the docs.", "after": [1]},
        {"title": "Announce it", "brief": "Say so in the changelog.", "after": [2]},
    ])
    rig.service.start(OWNER, pid)
    git(rig.repo, "remote", "remove", "origin")  # after Start: its precheck refuses a repository with no remote
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"README.md": "# app\nHello.\n"})
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] == "parked" and "does not appear to be a git repository" in step["parked_reason"], step
    return rig, pid


def test_a_parked_push_with_no_remote_reads_in_his_terms(tmp_path) -> None:
    rig, pid = _no_remote(tmp_path)
    body = _body(rig, pid, "parked")
    _fenced(body)
    assert body["doing"] == "Step 1, “Add one line to the README”: Append one line under the title."
    assert body["happened"] == "The step could not push its branch: this repository has no remote."
    assert body["question"] == "Start the step again, or stop it?"
    said = {row["id"]: row["consequence"] for row in body["choices"]}
    assert said == {"resume": "Try the step again. It will fail the same way until the repository has a remote.",
                    "skip": "Stop this step. The 2 steps that wait on it wait too."}
    assert body["blocked_words"] == "2 steps wait on this: 2 Link the README, 3 Announce it."
    assert [row["mark"] for row in body["track"]] == ["here", "blocked", "blocked"]
    assert body["place"].startswith("Step 1 of 3 · started ")
    # The raw reason is the fold "The error", first, and never a line.
    assert body["evidence"][0] == {"pane": "error", "label": "The error", "token": ""}
    assert "fatal:" in body["error"]
    assert [row["label"] for row in body["evidence"]] == ["The error", "Check log", "Brief", "Program text"]
    assert [row["line"] for row in body["changed"]][:1] == ["The check ran green in under a minute."]


def test_after_his_press_the_page_settles_to_one_line(tmp_path) -> None:
    rig, pid = _no_remote(tmp_path)
    briefing = BriefingService(rig.db, programs=lambda: rig.service, clock=Clock())
    item = next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "parked")
    ref = f"program:{pid}:{item['id']}"
    made = briefing.make(OWNER, [ref])
    page = briefing.read(made["token"])
    assert "error" not in page["items"][0]  # the raw reason opens as its fold only
    assert briefing.evidence(made["token"], ref, "error")["text"].startswith("git push failed: fatal:")
    done = briefing.answer(made["token"], ref, "resume")["item"]
    assert done["state"] == "decided"
    assert re.fullmatch(r"Resume · \d\d:\d\d\. The step starts again\. Nothing else waits on you\.",
                        done["outcome"]["words"]), done["outcome"]["words"]
    assert "error" not in done


def test_later_settles_to_its_one_line(tmp_path) -> None:
    rig, pid = _no_remote(tmp_path)
    clock = Clock()
    clock.now = datetime(2026, 10, 31, 6, 30, tzinfo=timezone.utc)  # 13:00 is later today
    briefing = BriefingService(rig.db, programs=lambda: rig.service, clock=clock)
    item = next(row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "parked")
    made = briefing.make(OWNER, [f"program:{pid}:{item['id']}"])
    later = briefing.answer(made["token"], f"program:{pid}:{item['id']}", "later", later="at_13")["item"]
    assert re.fullmatch(r"Later · back at \d\d:\d\d\.", later["outcome"]["words"]), later["outcome"]


def test_a_red_check_names_the_section(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, check=f"FAKE_CHECK_RED=1 sh {FAKE_CHECK}")
    rig.service.plan(OWNER, pid, steps=[{"title": "Break it", "brief": "Change the parser."}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    for text in ("1\n", "2\n"):
        rig.agent.finish(step["launch_id"], {"a.txt": text})
        rig.tick()
        if rig.step(pid, 1)["state"] == "check_failed":
            rig.agent.start_turn(step["launch_id"])
            rig.tick()
    body = _body(rig, pid, "parked")
    _fenced(body)
    assert body["happened"] == "The check went red on pytest."
    assert body["choices"][0]["consequence"] == "Try the step again."
    assert body["blocked_words"] == "Nothing else waits on this."


def test_a_core_question_reads_the_agent_s_question(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, control="yolo")
    rig.service.plan(OWNER, pid, steps=[{"title": "Owned", "brief": "Store the stall reason.", "owns": ["src/a.py"]}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"src/a.py": "a\n", "holdspeak/db/schema.py": "b\n"})
    rig.tick()
    body = _body(rig, pid, "core")
    _fenced(body)
    assert body["happened"] == "The step's change touches files no step owns (schema.py)."
    assert body["question"] == "Let the step go on with this, or park it?"
    assert [row["consequence"] for row in body["choices"]] == [
        "The step goes on with this change.", "Stop this step. The program has no other step to run."]


def test_a_held_commit(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, control="normal")
    rig.service.plan(OWNER, pid, steps=[{"title": "Add one line to the README", "brief": "Append one line."}])
    rig.service.start(OWNER, pid)
    rig.gate.hold_commit(rig.step(pid, 1)["launch_id"])
    rig.tick()
    body = _body(rig, pid, "commit")
    _fenced(body)
    assert body["happened"] == "The agent wants to commit its change."
    assert body["question"] == "Allow the commit, or stop the step?"
    assert body["choices"][0]["consequence"] == "The change is committed and the check runs."


def test_his_word_then_the_merge(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="")
    rig.service.plan(OWNER, pid, steps=[{"title": "Projections off the loop", "brief": "Move them off."}])
    sid = rig.step(pid, 1)["id"]
    rid = rig.service.require(OWNER, pid, text="I tried it on my desk", kind="word", step_id=sid)["requirement_id"]
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(3)
    word = _body(rig, pid, "requirement_word")
    _fenced(word)
    assert word["happened"] == "A requirement waits for your word: R1 · I tried it on my desk."
    assert word["question"] == "Is the requirement met?"
    rig.service.decide_requirement(OWNER, pid, rid, "met")
    rig.tick()
    merge = _body(rig, pid, "merge")
    _fenced(merge)
    assert merge["happened"].startswith("The step is ready to merge. PR #")
    assert merge["question"] == "Merge the PR, or keep it open?"
    assert [row["consequence"] for row in merge["choices"]] == ["HoldSpeak merges the PR.",
                                                                "The PR stays open. Nothing merges."]


def test_a_reviewer_s_required_finding(tmp_path) -> None:
    rig = Rig(tmp_path)
    pid = _program(rig, template="build-and-review")
    rig.service.plan(OWNER, pid, steps=[{"title": "Indexes", "brief": "Add the three indexes.",
                                         "owns": ["holdspeak/db/schema.py"]}])
    rig.service.start(OWNER, pid)
    launch = rig.step(pid, 1)["launch_id"]
    rig.agent.finish(launch, {"holdspeak/db/schema.py": "-- indexes\n"})
    seen: set[str] = set()
    for round_ in range(12):  # the reviewer finds the same MUST until the rounds end; then it is his
        rig.tick()
        for record in [r for r in rig.ledger.list() if r.get("helper_of") and r["launch_id"] not in seen]:
            seen.add(record["launch_id"])
            rig.words[record["launch_id"]] = "MUST: the index in holdspeak/db/schema.py drops a column"
            rig.states[record["launch_id"]] = {"state": "done", "turn_id": f"r-{round_}"}
        if any(row["kind"] == "finding" for row in rig.program(pid)["your_turn_items"]):
            break
        if rig.step(pid, 1)["state"] == "findings":
            rig.agent.finish(launch, {"holdspeak/db/schema.py": f"-- {round_}\n"})
    body = _body(rig, pid, "finding")
    _fenced(body)
    assert body["happened"] == "The reviewer found a required fix: the index in schema.py drops a column."
    assert body["question"] == "Fix it now, make it a task, or go on without it?"


@pytest.mark.parametrize("line, plain", [
    ("Checked · green · under a minute · /private/tmp/x/.tmp/program-check/step-1/20261031T212944Z.log",
     "The check ran green in under a minute."),
    ("Running the check: sh -c 'echo QUICK CHECK GREEN'", ""),
    ("New commit 67147874; the check runs", "The agent made a new commit."),
    ("git push failed; parked", ""),
])
def test_what_changed_is_plain(line, plain) -> None:
    assert words.changed_line(line) == plain


@pytest.mark.parametrize("raw", [
    "fatal: 'origin' does not appear to be a git repository",
    "see /tmp/a/b.log", "src/a.py broke", "sh -c 'echo hi'", "commit 67147874ab", "Traceback (most recent call last)",
    "error: the thing", "git push -u origin x",
])
def test_the_fence_catches_every_raw_shape(raw) -> None:
    assert words.fence_hits(raw), raw
    assert words.fence_hits(words.scrub(raw)) == []


def test_plain_lines_pass_the_fence() -> None:
    for line in ("The step could not push its branch: this repository has no remote.", "Opened PR #12.",
                 "The fix needs holdspeak/db/, outside what the program owns.", "R1/R2 are met.",
                 "Step 3 of 6 · started 17:59 · waited 1 h 20"):
        assert words.fence_hits(line) == [], line


def test_telegram_and_the_call_read_the_same_lines_in_the_same_order(tmp_path) -> None:
    rig, pid = _no_remote(tmp_path)
    body = _body(rig, pid, "parked")
    lines = words.brief_lines(body)
    assert lines == [*body["note"], body["question"], body["blocked_words"]]
    message = render(body, "https://hub.tail.ts.net/b/x", datetime.now(timezone.utc)).split("\n")
    assert message[0].startswith("README touch · step 1 · waits ")
    assert message[1:1 + len(lines)] == lines
    assert message[1 + len(lines):-1] == [f"{row['label']}: {row['consequence']}" for row in body["choices"]]
    assert len(message) <= 10 and message[-1] == "Open the page: https://hub.tail.ts.net/b/x"
    spoken = package_words(body)
    at = [spoken.index(line.rstrip(".?")) for line in lines]
    assert at == sorted(at), spoken
    assert "Changed" not in spoken and "fatal" not in spoken
