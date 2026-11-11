"""Programs LANG13: the delivery at Done (PG-LANG §8, default 9 approved).

A scratch repository with the real Delivery Workbench rails (this
repository's ``.githooks/dw`` and ``dw_pmo``, copied) and a bare origin. A
Program with ``delivery dw app/1`` runs to Done; the engine writes ONE PR
whose roadmap diff is one story and its evidence, marked done, never in the
working tree. A dw refusal is a Your turn row in words; Retry writes it
again; Skip leaves the Program Done.

The window's half (PG-WINDOW) replays the answers recorded here through the
real routes: ``program.delivery_failed.json``, ``program.delivery_merge.json``
(at Secure), ``program.delivery_merged.json`` (his Merge's answer) under
``web/src/desk/programs/__fixtures__`` (``HOLDSPEAK_WIRE_WRITE=1`` rewrites
them, else this test fences their shape).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from holdspeak.services import program_service as program_module
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git, owner_app

FIXTURES = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "programs" / "__fixtures__"


def _shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        return [_shape(value[0])] if value else []
    return type(value).__name__


def _fixture(name: str, answer: Any, tmp_path: Path) -> Any:
    """The hub's own answer, stored for the face (never typed by hand)."""
    scrubbed = json.loads(re.sub(re.escape(str(tmp_path)), "/tmp/rig", json.dumps(answer)))
    path = FIXTURES / name
    if os.environ.get("HOLDSPEAK_WIRE_WRITE") == "1":
        path.write_text(json.dumps(scrubbed, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    assert path.exists(), f"no stored answer {path}; run with HOLDSPEAK_WIRE_WRITE=1"
    assert _shape(json.loads(path.read_text())) == _shape(scrubbed), f"{name}: not the hub's shape"
    return scrubbed


def _client(rig: Rig, monkeypatch) -> TestClient:
    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    app = owner_app()
    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    from tests.integration.program_rig import QuestionClient
    return QuestionClient(TestClient(app),rig)

RAILS = Path(__file__).resolve().parents[2] / ".githooks"


def _rails(repo: Path) -> None:
    hooks = repo / ".githooks"
    hooks.mkdir(exist_ok=True)
    shutil.copy2(RAILS / "dw", hooks / "dw")
    shutil.copytree(RAILS / "dw_pmo", hooks / "dw_pmo", ignore=shutil.ignore_patterns("__pycache__"))
    readme = repo / "pm" / "roadmap" / "app" / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text("# App — Roadmap\n\n**Last updated:** 2026-11-01\n**Current phase:** none\n**Status:** active\n\n"
                      "## Phases\n\n| Phase | Title | Status |\n|---|---|---|\n", encoding="utf-8")
    subprocess.run([str(hooks / "dw"), "phase", "create", "app", "1", "The first"], cwd=repo, check=True,
                   capture_output=True)
    git(repo, "add", "-A")
    git(repo, "commit", "-m", "rails")
    git(repo, "push", "origin", "main")


def _done(tmp_path: Path, *, control: str = "yolo", delivery: str = "dw app/1", edge: Any = None,
          merge_mode: str = "merged") -> tuple[Rig, str]:
    rig = Rig(tmp_path, seed=_rails)
    if edge is not None:
        # HS-S32: a test's process edge over the rig's (a push or a create that fails).
        rig.runner._run = lambda argv, cwd=None, **kw: edge(rig.gh, argv, cwd=cwd, **kw)
    pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Stop the stalls.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control=control)["id"]
    rig.service.update(OWNER, pid, delivery=delivery)
    rig.service.plan(OWNER, pid, steps=[{"title": "Indexes", "brief": "Add the indexes."}])
    rig.service.start(OWNER, pid)
    rig.gh.merge_mode = merge_mode  # the delivery PR's merge only
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(3)
    if control == "secure":
        rig.service.decide(OWNER, pid, rig.step(pid, 1)["id"], kind="merge", choice="merge")
        rig.tick(2)
        rig.service.close(OWNER, pid)
    return rig, pid


def _press(rig: Rig, pid: str, choice: str) -> dict:
    """His press on the delivery row, naming the line the row shows."""
    [item] = [row for row in rig.program(pid)["your_turn_items"] if row["kind"] == "delivery"]
    return rig.service.decide(OWNER, pid, "", kind="delivery", choice=choice,
                              expected_delivery_checkpoint_id=item["expected_delivery_checkpoint_id"])





def _delivery_lines(rig: Rig, pid: str) -> list[dict]:
    return [row for row in rig.program(pid)["checkpoints"] if row.get("kind") == "delivery"]


def test_done_writes_one_delivery_pr_whose_diff_is_one_story_and_its_evidence(tmp_path) -> None:
    rig, pid = _done(tmp_path)
    program = rig.program(pid)
    assert program["state"] == "done" and program["closed_at"], program["status_line"]
    [line] = _delivery_lines(rig, pid)
    created = [call for call in rig.gh.calls if call[1:3] == ["pr", "create"]]
    delivery = created[-1]
    number = max(rig.gh.prs)
    # JRN5: a delivery to the whole phase closes it in the same PR.
    assert line["line"] == f"Delivered to dw app/1 (PR #{number}) · phase closed" and line["choice"] == "delivered"
    assert line["undo"]["phase"] == {"project": "app", "phase": "1", "closed": True}
    assert delivery[delivery.index("--title") + 1] == "Delivery: The hub stops stalling done"
    branch = delivery[delivery.index("--head") + 1]
    assert branch == "program/the-hub-stops-stalling/delivery"
    assert ["gh", "pr", "merge", str(number), "--squash"] in rig.gh.calls
    # The PR's diff is one story and its evidence, marked done, and the
    # phase's close (its final summary, the roadmap README's row).
    files = git(rig.repo, "diff", "--name-only", "origin/main", f"origin/{branch}").splitlines()
    assert sorted(files) == ["pm/roadmap/app/README.md",
                             "pm/roadmap/app/phase-1-the-first/current-phase-status.md",
                             "pm/roadmap/app/phase-1-the-first/evidence-story-01.md",
                             "pm/roadmap/app/phase-1-the-first/final-summary.md",
                             "pm/roadmap/app/phase-1-the-first/story-01-the-hub-stops-stalling.md"], files
    story = git(rig.repo, "show", f"origin/{branch}:pm/roadmap/app/phase-1-the-first/story-01-the-hub-stops-stalling.md")
    assert "**Status:** done" in story
    evidence = git(rig.repo, "show", f"origin/{branch}:pm/roadmap/app/phase-1-the-first/evidence-story-01.md")
    assert "## Program: The hub stops stalling — Done" in evidence and "- PRs: #" in evidence
    # Never in his working tree; nothing waits on him; it is written once.
    assert not (rig.repo / "pm" / "roadmap" / "app" / "phase-1-the-first" / "evidence-story-01.md").exists()
    assert rig.program(pid)["your_turn_items"] == []
    rig.service.changed(pid)
    assert len(_delivery_lines(rig, pid)) == 1


def test_a_dw_refusal_is_his_row_in_words_and_retry_or_skip_answers_it(tmp_path, monkeypatch) -> None:
    rig, pid = _done(tmp_path, delivery="dw app/1/07")  # story 07 is not there
    client = _client(rig, monkeypatch)
    wire = _fixture("program.delivery_failed.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    # PG-WINDOW: the held row's brief, in his terms.
    brief = wire["your_turn_items"][0]["brief"]
    assert brief["happened"] == "Could not deliver to dw app/1/07: Delivery Workbench did not take the evidence."
    assert brief["question"] == "Try the delivery again, or skip it?"
    assert brief["consequences"] == {"retry": "Try the delivery again.", "skip": "Skip it. The program stays Done, not delivered."}
    [line] = _delivery_lines(rig, pid)
    assert line["choice"] == "failed"
    assert line["line"] == "Could not deliver to dw app/1/07: Delivery Workbench did not take the evidence"
    assert line["undo"]["detail"]  # dw's own words, for the evidence fold
    # HS-S32 C32-02: the stage it stopped at, before any remote write.
    receipt = line["undo"]["receipt"]
    assert receipt["stage"] == "evidence" and receipt["remote"] is False
    assert receipt["target"] == {"ref": "dw:app/1/07", "words": "dw app/1/07"}
    [item] = rig.program(pid)["your_turn_items"]
    assert item["kind"] == "delivery" and item["choices"] == ["retry", "skip"]
    assert item["expected_delivery_checkpoint_id"] == line["id"]
    assert item["delivery"] == {"state": "retry", "words": "Not delivered"}
    assert item["title"] == ("Deliver “The hub stops stalling” to dw app/1/07: "
                             "it Delivery Workbench did not take the evidence")
    # C32-10/11: a press that names no line, or another line, changes nothing.
    for expected, code in ((None, "delivery_binding_required"), (line["id"] - 1, "delivery_changed")):
        try:
            rig.service.decide(OWNER, pid, "", kind="delivery", choice="retry", expected_delivery_checkpoint_id=expected)
        except program_module.ProgramRefused as exc:
            assert exc.code == code
        else:
            raise AssertionError(f"a delivery press with {expected!r} was taken")
    assert len(_delivery_lines(rig, pid)) == 1
    _press(rig, pid, "retry")
    assert [row["choice"] for row in _delivery_lines(rig, pid)] == ["failed", "failed"]
    # Retry never touches his working tree.
    assert not (rig.repo / "pm" / "roadmap" / "app" / "phase-1-the-first" / "evidence-story-01.md").exists()
    calls = len(rig.gh.calls)
    _press(rig, pid, "skip")
    assert _delivery_lines(rig, pid)[0]["line"] == "Skipped the delivery: Done, not delivered"
    assert rig.gh.calls[calls:] == []  # Skip calls nothing
    assert rig.program(pid)["your_turn_items"] == [] and rig.program(pid)["state"] == "done"


def test_at_secure_the_delivery_pr_waits_for_his_merge(tmp_path, monkeypatch) -> None:
    rig, pid = _done(tmp_path, control="secure")
    client = _client(rig, monkeypatch)
    wire = _fixture("program.delivery_merge.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    brief = wire["your_turn_items"][0]["brief"]
    assert brief["question"] == "Merge the delivery pull request, or skip the delivery?"
    assert brief["consequences"]["merge"] == (
        "Merge the delivery pull request. HoldSpeak then reads the result on GitHub.")
    assert brief["doing"] == "It delivers its record to dw app/1."
    [line] = _delivery_lines(rig, pid)
    number = max(rig.gh.prs)
    pr = rig.gh.prs[number]
    assert line["choice"] == "pr_open" and line["line"] == (
        f"The delivery PR #{number} to dw app/1 waits for your merge · it closes the phase")
    # HS-S32 C32-04: the acknowledged identity, kept on the line.
    assert line["undo"]["receipt"]["pr"] == {"url": pr["url"], "number": number, "branch": pr["branch"],
                                             "base": "main", "head": pr["head_sha"]}
    assert line["undo"]["pr_number"] == number and line["undo"]["branch"] == pr["branch"]
    assert [call for call in rig.gh.calls if call[1:3] == ["pr", "merge"] and call[3] in (str(number), pr["url"])] == []
    [item] = rig.program(pid)["your_turn_items"]
    assert item["kind"] == "delivery" and item["choices"] == ["merge", "check", "skip"]
    assert item["pr"] == {"number": number, "url": pr["url"]}
    assert item["delivery"]["words"] == f"PR #{number} open"
    # A press without the line it answers is refused by the route too.
    refused = client.post(f"/api/programs/{pid}/steps/program/decide", json={"kind": "delivery", "choice": "merge"})
    assert refused.status_code == 409 and len(_delivery_lines(rig, pid)) == 1
    # His Merge, through the window's route (the step id is not read for a delivery).
    calls = len(rig.gh.calls)
    answer = client.post(f"/api/programs/{pid}/steps/program/decide", json={
        "kind": "delivery", "choice": "merge", "expected_delivery_checkpoint_id": item["expected_delivery_checkpoint_id"]})
    assert answer.status_code == 200, answer.text
    _fixture("program.delivery_merged.json", answer.json(), tmp_path)
    # C32-10/16: read, one head-guarded merge by URL, read; the request line first.
    assert [call[1:4] for call in rig.gh.calls[calls:]] == [["pr", "view", pr["url"]], ["pr", "merge", pr["url"]],
                                                             ["pr", "view", pr["url"]]]
    assert rig.gh.calls[calls + 1] == ["gh", "pr", "merge", pr["url"], "--squash", "--match-head-commit",
                                       pr["head_sha"]]
    delivered, asked, _opened = _delivery_lines(rig, pid)
    assert asked["choice"] == "pr_open" and asked["by"] == "owner"
    assert asked["undo"]["receipt"]["merge_requested_at"] and asked["undo"]["receipt"]["merge_requested_by"] == "owner"
    assert delivered["line"] == f"Delivered to dw app/1 (PR #{number}) · phase closed"
    assert "merge_requested_at" not in delivered["undo"]["receipt"]  # merged: the request is answered
    assert delivered["undo"]["phase"] == {"project": "app", "phase": "1", "closed": True}
    assert rig.program(pid)["your_turn_items"] == []


def test_the_briefing_page_reads_the_delivery_in_the_same_words(tmp_path) -> None:
    """PG-WINDOW: a failed delivery is briefable; the page says what the
    window says, and Retry or Skip answer it."""
    from holdspeak.services import brief_words as words
    from holdspeak.services.briefing_service import BriefingService

    rig, pid = _done(tmp_path, delivery="dw app/1/07")
    [item] = rig.program(pid)["your_turn_items"]
    briefing = BriefingService(rig.db, programs=lambda: rig.service)
    body = briefing.compose(f"program:{pid}:{item['id']}")
    assert body["happened"] == item["brief"]["happened"]
    assert body["question"] == "Try the delivery again, or skip it?"
    assert [(row["label"], row["consequence"]) for row in body["choices"]] == [
        ("Retry", "Try the delivery again."), ("Skip", "Skip it. The program stays Done, not delivered.")]
    for line in [*body["note"], body["question"], *(row["consequence"] for row in body["choices"])]:
        assert words.fence_hits(line) == [], line
    # HS-S32: the page freezes the delivery line it shows.
    assert body["expected_delivery_checkpoint_id"] == item["expected_delivery_checkpoint_id"]
    made = briefing.make(OWNER, [f"program:{pid}:{item['id']}"])
    done = briefing.answer(made["token"], f"program:{pid}:{item['id']}", "skip", binding=body["binding"])["item"]
    assert done["state"] == "decided" and "The program stays Done." in done["outcome"]["words"]
    assert rig.program(pid)["your_turn_items"] == []


def test_a_briefing_page_made_before_a_newer_delivery_line_is_refused(tmp_path) -> None:
    """HS-S32 C32-10: the page answers the line it froze, never the latest."""
    from holdspeak.services.briefing_service import BriefingService, BriefingRefused

    rig, pid = _done(tmp_path, delivery="dw app/1/07")
    [item] = rig.program(pid)["your_turn_items"]
    briefing = BriefingService(rig.db, programs=lambda: rig.service)
    made = briefing.make(OWNER, [f"program:{pid}:{item['id']}"])
    _press(rig, pid, "retry")  # a newer failed line now holds the row
    try:
        briefing.answer(made["token"], f"program:{pid}:{item['id']}", "retry")
    except (program_module.ProgramRefused, BriefingRefused) as exc:
        assert exc.code == "answer_stale"
    else:
        raise AssertionError("an older page answered a newer delivery line")
    assert [row["choice"] for row in _delivery_lines(rig, pid)] == ["failed", "failed"]
    # A channel with no line (a direct call) is refused, never given the latest.
    try:
        briefing.decide_item(OWNER, f"program:{pid}:{item['id']}", "retry", via="call")
    except (program_module.ProgramRefused, BriefingRefused) as exc:
        assert exc.code == "answer_stale"
    else:
        raise AssertionError("a delivery press with no line was taken")


# ── HS-S32: continue a known delivery without making its PR again ─────

def test_a_failed_delivery_merge_keeps_its_pr_and_offers_check_not_retry(tmp_path, monkeypatch) -> None:
    """C32-04, C32-06, C32-13: the merge fails after the PR is open; the
    row offers Check (never Retry); Check reads the PR merged on GitHub and
    records the delivery, with no push, create, merge or dw command."""
    rig, pid = _done(tmp_path, merge_mode="fail")
    client = _client(rig, monkeypatch)
    [line] = _delivery_lines(rig, pid)
    number = max(rig.gh.prs)
    pr = rig.gh.prs[number]
    receipt = line["undo"]["receipt"]
    assert line["choice"] == "failed" and receipt["stage"] == "merge" and receipt["remote"] is True
    assert receipt["pr"] == {"url": pr["url"], "number": number, "branch": pr["branch"], "base": "main",
                             "head": pr["head_sha"]}
    assert receipt["merge_requested_at"] and receipt["merge_requested_by"] == "engine"
    assert line["undo"]["phase"] == {"project": "app", "phase": "1", "closed": True}  # kept through the failure
    wire = _fixture("program.delivery_check.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    [item] = wire["your_turn_items"]
    assert item["choices"] == ["check", "skip"] and item["delivery"]["state"] == "requested"
    assert item["brief"]["question"] == "Check the delivery pull request on GitHub, or skip the delivery?"
    assert item["brief"]["happened"] == f"A merge of the delivery PR #{number} is requested. GitHub has not confirmed it."
    # The merge went through on GitHub after all (someone pressed it there).
    pr["state"] = "merged"
    calls = len(rig.gh.calls)
    commands: list[list[str]] = []
    edge = rig.runner._run
    rig.runner._run = lambda argv, cwd=None, **kw: (commands.append(list(argv)), edge(argv, cwd=cwd, **kw))[1]
    _press(rig, pid, "check")
    assert commands == [["gh", "pr", "view", pr["url"], "--json",
                         "url,number,state,headRefOid,baseRefName,headRefName,isCrossRepository"]]
    assert rig.gh.calls[calls:] == commands
    checked = _delivery_lines(rig, pid)[0]
    assert checked["choice"] == "delivered" and checked["line"] == f"Delivered to dw app/1 (PR #{number}) · phase closed"
    assert checked["undo"]["receipt"]["reconciled"] is True and checked["undo"]["receipt"]["pr"]["number"] == number
    assert checked["undo"]["phase"] == line["undo"]["phase"]
    program = rig.program(pid)
    assert program["state"] == "done" and program["your_turn_items"] == []


def test_a_queued_merge_stays_not_confirmed_and_never_offers_merge_again(tmp_path, monkeypatch) -> None:
    """C32-05, C32-11, C32-17: GitHub answers yes and the PR stays open (a
    merge queue): not Delivered; the request stays; Check reads it again
    and never offers Merge."""
    rig, pid = _done(tmp_path, control="secure", merge_mode="queued")
    client = _client(rig, monkeypatch)
    number = max(rig.gh.prs)
    _press(rig, pid, "merge")
    merges = [call for call in rig.gh.calls if call[1:3] == ["pr", "merge"] and call[3].endswith(f"/{number}")]
    assert len(merges) == 1
    line = _delivery_lines(rig, pid)[0]
    assert line["choice"] == "pr_open" and line["line"] == (
        f"The delivery PR #{number} to dw app/1 is open on GitHub · a merge is requested, not confirmed")
    assert line["undo"]["receipt"]["merge_requested_at"]
    wire = _fixture("program.delivery_queued.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    [item] = wire["your_turn_items"]
    assert item["choices"] == ["check", "skip"] and item["delivery"]["words"] == f"PR #{number} · Not confirmed"
    for _ in range(2):  # Check again: read only, the request stays
        _press(rig, pid, "check")
        again = _delivery_lines(rig, pid)[0]
        assert again["choice"] == "pr_open" and again["undo"]["receipt"]["merge_requested_at"]
        assert rig.program(pid)["your_turn_items"][0]["choices"] == ["check", "skip"]
    assert len([call for call in rig.gh.calls if call[1:3] == ["pr", "merge"] and call[3].endswith(f"/{number}")]) == 1
    try:
        _press(rig, pid, "merge")
    except program_module.ProgramRefused as exc:
        assert exc.code == "choice_invalid"
    else:
        raise AssertionError("Merge was offered again over an unconfirmed request")


def test_check_of_an_open_secure_pr_offers_merge(tmp_path, monkeypatch) -> None:
    """C32-05: a matching open PR with no request: Check keeps Merge."""
    rig, pid = _done(tmp_path, control="secure")
    client = _client(rig, monkeypatch)
    number = max(rig.gh.prs)
    [item] = rig.program(pid)["your_turn_items"]
    # His Check, through the window's route; its answer is the window's next state.
    answer = client.post(f"/api/programs/{pid}/steps/program/decide", json={
        "kind": "delivery", "choice": "check", "expected_delivery_checkpoint_id": item["expected_delivery_checkpoint_id"]})
    assert answer.status_code == 200, answer.text
    wire = _fixture("program.delivery_checked_open.json", answer.json(), tmp_path)
    line = _delivery_lines(rig, pid)[0]
    assert line["choice"] == "pr_open" and line["line"] == f"The delivery PR #{number} to dw app/1 is open on GitHub"
    assert line["undo"]["receipt"]["observed"]["state"] == "OPEN"
    [after] = wire["program"]["your_turn_items"]
    assert after["choices"] == ["merge", "check", "skip"] and after["expected_delivery_checkpoint_id"] == line["id"]
    assert [call for call in rig.gh.calls if call[1:3] == ["pr", "merge"] and call[3].endswith(f"/{number}")] == []


def test_a_read_that_does_not_match_is_never_a_yes(tmp_path, monkeypatch) -> None:
    """C32-07, C32-08: a failed or unreadable read, a changed head, a fork,
    a closed PR: not confirmed, no merge, Check or Skip; Skip calls nothing
    and keeps the PR's identity and its uncertainty."""
    rig, pid = _done(tmp_path, control="secure")
    client = _client(rig, monkeypatch)
    number = max(rig.gh.prs)
    pr = rig.gh.prs[number]
    words = []
    for change in ("fail", "garbage", "head", "fork", "closed"):
        rig.gh.view_mode = change if change in ("fail", "garbage") else "live"
        saved = dict(pr)
        if change == "head":
            pr["head_sha"] = "0" * 40
        elif change == "fork":
            pr["fork"] = True
        elif change == "closed":
            pr["state"] = "closed"
        _press(rig, pid, "check")
        line = _delivery_lines(rig, pid)[0]
        assert line["choice"] == "failed" and line["undo"]["receipt"]["stage"] == "check", change
        assert line["undo"]["receipt"]["pr"]["number"] == number
        assert rig.program(pid)["your_turn_items"][0]["choices"] == ["check", "skip"], change
        words.append(line["undo"]["words"])
        if change != "closed":
            pr.clear()
            pr.update(saved)
    assert words == ["HoldSpeak could not read the PR on GitHub", "GitHub's answer was not readable",
                     "the PR on GitHub has commits HoldSpeak did not prepare",
                     "the PR on GitHub is not the delivery PR HoldSpeak opened",
                     "GitHub shows the PR closed, not merged"]
    assert [call for call in rig.gh.calls if call[1:3] == ["pr", "merge"] and call[3].endswith(f"/{number}")] == []
    wire = _fixture("program.delivery_unknown.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    [item] = wire["your_turn_items"]
    assert item["delivery"] == {"state": "unknown", "words": f"PR #{number} · Not confirmed",
                                "happened": f"HoldSpeak could not confirm the delivery PR #{number}: "
                                            "GitHub shows the PR closed, not merged"}
    assert item["brief"]["consequences"]["skip"] == "Skip it. The program stays Done. The delivery stays not confirmed."
    calls = len(rig.gh.calls)
    _press(rig, pid, "skip")
    assert rig.gh.calls[calls:] == []
    skipped = _delivery_lines(rig, pid)[0]
    assert skipped["line"] == f"Skipped the delivery: PR #{number} not confirmed"
    assert skipped["undo"]["receipt"]["pr"]["number"] == number and skipped["undo"]["pr_number"] == number
    assert rig.program(pid)["state"] == "done" and rig.program(pid)["your_turn_items"] == []


def _failing(stage: str):
    def edge(gh: Any, argv: list[str], cwd: Any = None, **kw: Any) -> Any:
        from types import SimpleNamespace

        if stage == "push" and argv[:2] == ["git", "-C"] and "push" in argv and argv[-1].endswith("/delivery"):
            return SimpleNamespace(returncode=1, stdout="", stderr="fatal: the remote end hung up unexpectedly")
        if stage == "pr" and argv[1:3] == ["pr", "create"] and "Delivery:" in " ".join(argv):
            gh.calls.append(list(argv))
            return SimpleNamespace(returncode=0, stdout="Creating pull request…\n", stderr="")
        return gh(argv, cwd=cwd, **kw)
    return edge


def test_a_push_or_create_with_no_answer_stays_not_confirmed(tmp_path) -> None:
    """C32-03: after a push or a create was attempted, no answer is not a
    safe repeat: no Retry, no adoption by branch; Skip only."""
    for stage in ("push", "pr"):
        rig, pid = _done(tmp_path / stage, edge=_failing(stage))
        [line] = _delivery_lines(rig, pid)
        receipt = line["undo"]["receipt"]
        assert line["choice"] == "failed" and receipt["stage"] == stage and receipt["remote"] is True, stage
        assert "url" not in receipt["pr"] and "number" not in receipt["pr"]
        [item] = rig.program(pid)["your_turn_items"]
        assert item["choices"] == ["skip"] and item["delivery"]["state"] == "blocked", stage
        assert item["brief"]["happened"] == "HoldSpeak cannot confirm what reached GitHub for this delivery."
        creates = len([call for call in rig.gh.calls if call[1:3] == ["pr", "create"]])
        try:
            _press(rig, pid, "retry")
        except program_module.ProgramRefused as exc:
            assert exc.code == "choice_invalid"
        else:
            raise AssertionError("Retry was taken after a remote write")
        assert len([call for call in rig.gh.calls if call[1:3] == ["pr", "create"]]) == creates
        _press(rig, pid, "skip")
        assert _delivery_lines(rig, pid)[0]["line"] == "Skipped the delivery: not confirmed"


def test_an_old_delivery_line_stays_visible_and_blocked(tmp_path, monkeypatch) -> None:
    """C32-09: a line written before HS-S32 (a PR number and a branch, no
    receipt) is never read as a fresh safe attempt: Skip only."""
    rig, pid = _done(tmp_path, control="secure")
    client = _client(rig, monkeypatch)
    rig.service.store.add_checkpoint(step_id="", program_id=pid, at=rig.service._clock(), by="engine",
                                     line="Could not deliver to dw app/1: GitHub did not merge the delivery PR",
                                     kind="delivery", choice="failed",
                                     undo={"words": "GitHub did not merge the delivery PR", "pr_number": 7,
                                           "branch": "program/the-hub-stops-stalling/delivery"})
    wire = _fixture("program.delivery_legacy_blocked.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    [item] = wire["your_turn_items"]
    assert item["choices"] == ["skip"] and item["delivery"]["state"] == "blocked"
    assert item["pr"] == {"number": 7, "url": None}
    assert item["brief"]["question"] == "Skip the delivery? HoldSpeak cannot confirm it."
    calls = len(rig.gh.calls)
    _press(rig, pid, "skip")
    assert rig.gh.calls[calls:] == [] and _delivery_lines(rig, pid)[0]["line"] == "Skipped the delivery: PR #7 not confirmed"


def test_retry_refuses_a_changed_target_and_check_keeps_the_recorded_one(tmp_path) -> None:
    """C32-14: a new target on a closed Program keeps the delivery line's id;
    Retry refuses, and the row names the recorded target."""
    rig, pid = _done(tmp_path, delivery="dw app/1/07")
    rig.service.update(OWNER, pid, delivery="dw app/1")
    [item] = rig.program(pid)["your_turn_items"]
    assert item["title"].startswith("Deliver “The hub stops stalling” to dw app/1/07:")
    try:
        _press(rig, pid, "retry")
    except program_module.ProgramRefused as exc:
        assert exc.code == "delivery_target_changed"
    else:
        raise AssertionError("Retry moved the delivery to a new target")
    assert len(_delivery_lines(rig, pid)) == 1


def test_his_merge_writes_the_request_before_any_merge_command(tmp_path, monkeypatch) -> None:
    """C32-16, C32-17: an append that fails sends nothing; a request line
    whose command never ran reads back as Check or Skip, never Merge."""
    from holdspeak.services import program_delivery

    rig, pid = _done(tmp_path, control="secure")
    number = max(rig.gh.prs)
    add = rig.service.store.add_checkpoint

    def refuse(**kw: Any) -> int:
        if ((kw.get("undo") or {}).get("receipt") or {}).get("merge_requested_at"):
            raise RuntimeError("database is locked")
        return add(**kw)

    rig.service.store.add_checkpoint = refuse
    calls = len(rig.gh.calls)
    try:
        _press(rig, pid, "merge")
    except RuntimeError:
        pass
    else:
        raise AssertionError("the merge ran without its request line")
    assert rig.gh.calls[calls:] == []
    rig.service.store.add_checkpoint = add
    # The request is written; the process stops before any command.
    monkeypatch.setattr(program_delivery, "_read", lambda *a, **kw: (_ for _ in ()).throw(SystemError("stopped")))
    try:
        _press(rig, pid, "merge")
    except SystemError:
        pass
    assert rig.gh.calls[calls:] == []
    line = _delivery_lines(rig, pid)[0]
    assert line["choice"] == "pr_open" and line["undo"]["receipt"]["merge_requested_at"]
    [item] = rig.program(pid)["your_turn_items"]
    assert item["choices"] == ["check", "skip"] and item["delivery"]["words"] == f"PR #{number} · Not confirmed"


def test_an_agent_cannot_press_the_delivery(tmp_path) -> None:
    """C32-10: the decision stays the owner's."""
    from holdspeak.principals import Principal, PrincipalKind

    rig, pid = _done(tmp_path, control="secure")
    [item] = rig.program(pid)["your_turn_items"]
    agent = Principal(PrincipalKind.AGENT, "agent-1")
    try:
        rig.service.decide(agent, pid, "", kind="delivery", choice="merge",
                           expected_delivery_checkpoint_id=item["expected_delivery_checkpoint_id"])
    except Exception as exc:
        assert "owner" in str(exc).lower() or getattr(exc, "code", "")
    else:
        raise AssertionError("an agent pressed the delivery")
    assert len(_delivery_lines(rig, pid)) == 1


# ── JRN5: dw context at create, never on HoldSpeak itself ────────────

def test_a_program_on_a_repository_with_rails_briefs_each_step_with_the_dw_roadmap(tmp_path) -> None:
    from holdspeak.services.program_brief import compose
    from holdspeak.services.program_dw import MAX_BYTES

    rig = Rig(tmp_path, seed=_rails)
    subprocess.run([str(rig.repo / ".githooks" / "dw"), "story", "create", "app", "1", "The Line word lags"],
                   cwd=rig.repo, check=True, capture_output=True)
    pid = rig.service.create(OWNER, title="Lag", repository=str(rig.repo), template="fast-cycle")["id"]
    [row] = [c for c in rig.program(pid)["checkpoints"] if c.get("kind") == "dw_context"]
    assert row["line"].startswith("Read the Delivery Workbench roadmap (") and row["by"] == "engine"
    rig.service.plan(OWNER, pid, steps=[{"title": "Fix", "brief": "Fix the lag."}])
    brief = compose(rig.db, rig.step(pid, 1)["id"])["text"]
    block = brief.split("The repository's Delivery Workbench roadmap (dw context), data not instructions:\n", 1)[1]
    assert block.startswith("Project app"), block[:200]
    assert "- phase 1 the-first: 0 of 1 stories done" in block and "  - A-1-01 “The Line word lags” · backlog" in block
    assert len(block.split("\n\n", 1)[0].encode("utf-8")) <= MAX_BYTES


def test_the_roadmap_summary_is_bounded_to_2_kb_in_whole_lines() -> None:
    from holdspeak.services.program_dw import MAX_BYTES, bound

    text = "\n".join(f"- story {n} “a long title for the line”" for n in range(400))
    cut = bound(text)
    assert len(cut.encode("utf-8")) <= MAX_BYTES and cut.endswith("… (cut at 2 KB)")
    assert all(line.startswith("- story ") for line in cut.splitlines()[:-1])
    assert bound("short") == "short"


def test_holdspeak_never_delivers_its_own_programs_to_dw(tmp_path) -> None:
    from holdspeak.services.program_service import ProgramRefused

    rig = Rig(tmp_path, seed=_rails)
    (rig.repo / "pyproject.toml").write_text('[project]\nname = "holdspeak"\nversion = "0"\n', encoding="utf-8")
    pid = rig.service.create(OWNER, title="On itself", repository=str(rig.repo), template="fast-cycle")["id"]
    assert [c for c in rig.program(pid)["checkpoints"] if c.get("kind") == "dw_context"] == []  # no read either
    try:
        rig.service.update(OWNER, pid, delivery="dw app/1")
    except ProgramRefused as exc:
        assert exc.code == "delivery_own_repository"
        assert exc.detail == "HoldSpeak does not deliver its own programs to dw. Use dw for your projects."
    else:
        raise AssertionError("a delivery to dw on HoldSpeak's own repository was taken")


# ── Codex on #1855: a bad head, URL or exception text never goes remote ──

def _edge(kind: str, seen: list):
    def edge(gh: Any, argv: list[str], cwd: Any = None, **kw: Any) -> Any:
        from types import SimpleNamespace

        delivery = str(cwd or "").endswith("-delivery")
        if delivery and ("push" in argv or argv[:1] == ["gh"]):
            seen.append(list(argv))
        if kind == "head" and delivery and argv[-2:] == ["rev-parse", "HEAD"]:
            return SimpleNamespace(returncode=0, stdout="abc\n", stderr="")
        if kind == "raise" and delivery and "push" in argv:
            raise OSError("[Errno 13] Permission denied: '/Users/karol/secret/app/.git' ghp_abcdef123456")
        if kind == "url" and argv[1:3] == ["pr", "create"] and "Delivery:" in " ".join(argv):
            gh.calls.append(list(argv))
            return SimpleNamespace(returncode=0, stdout="https://evil.example/acme/app/pull/5\n", stderr="")
        return gh(argv, cwd=cwd, **kw)
    return edge


def test_a_short_head_stops_before_any_remote_command_and_retries(tmp_path) -> None:
    seen: list = []
    rig, pid = _done(tmp_path, edge=_edge("head", seen))
    [line] = _delivery_lines(rig, pid)
    receipt = line["undo"]["receipt"]
    assert line["choice"] == "failed" and receipt["stage"] == "head" and receipt["remote"] is False
    assert "head" not in receipt["pr"]
    assert seen == []  # no push, no gh call from the delivery
    assert [call for call in rig.gh.calls if "Delivery:" in " ".join(call)] == []
    [item] = rig.program(pid)["your_turn_items"]
    assert item["choices"] == ["retry", "skip"] and item["delivery"]["state"] == "retry"


def test_a_malformed_pr_url_never_reaches_gh_again(tmp_path) -> None:
    seen: list = []
    rig, pid = _done(tmp_path, edge=_edge("url", seen))
    [line] = _delivery_lines(rig, pid)
    receipt = line["undo"]["receipt"]
    assert receipt["stage"] == "pr" and "url" not in receipt["pr"] and "number" not in receipt["pr"]
    assert [call for call in rig.gh.calls if "evil.example" in " ".join(call)] == []
    assert rig.program(pid)["your_turn_items"][0]["choices"] == ["skip"]


def test_a_thrown_push_leaves_no_path_or_token_in_the_ledger(tmp_path, monkeypatch) -> None:
    seen: list = []
    rig, pid = _done(tmp_path, edge=_edge("raise", seen))
    client = _client(rig, monkeypatch)
    [line] = _delivery_lines(rig, pid)
    assert line["undo"]["receipt"]["stage"] == "push" and line["undo"]["receipt"]["remote"] is True
    assert line["undo"]["detail"] == "OSError at the push stage: the command stopped before it answered."
    wire = json.dumps(client.get(f"/api/programs/{pid}").json())
    assert "/Users/karol/secret" not in wire and "ghp_abcdef" not in wire and "Permission denied" not in wire
