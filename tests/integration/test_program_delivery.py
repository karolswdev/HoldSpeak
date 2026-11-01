"""Programs LANG13: the delivery at Done (PG-LANG §8, default 9 approved).

A scratch repository with the real Delivery Workbench rails (this
repository's ``.githooks/dw`` and ``dw_pmo``, copied) and a bare origin. A
Program with ``delivery dw app/1`` runs to Done; the engine writes ONE PR
whose roadmap diff is one story and its evidence, marked done, never in the
working tree. A dw refusal is a Your turn row in words; Retry writes it
again; Skip leaves the Program Done.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git

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


def _done(tmp_path: Path, *, control: str = "yolo", delivery: str = "dw app/1") -> tuple[Rig, str]:
    rig = Rig(tmp_path)
    _rails(rig.repo)
    pid = rig.service.create(OWNER, title="The hub stops stalling", goal="Stop the stalls.", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}", template="fast-cycle", control=control)["id"]
    rig.service.update(OWNER, pid, delivery=delivery)
    rig.service.plan(OWNER, pid, steps=[{"title": "Indexes", "brief": "Add the indexes."}])
    rig.service.start(OWNER, pid)
    rig.agent.finish(rig.step(pid, 1)["launch_id"], {"a.py": "1\n"})
    rig.tick(3)
    if control == "secure":
        rig.service.decide(OWNER, pid, rig.step(pid, 1)["id"], kind="merge", choice="merge")
        rig.tick(2)
        rig.service.close(OWNER, pid)
    return rig, pid


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
    assert line["line"] == f"Delivered to dw app/1 (PR #{number})" and line["choice"] == "delivered"
    assert delivery[delivery.index("--title") + 1] == "Delivery: The hub stops stalling done"
    branch = delivery[delivery.index("--head") + 1]
    assert branch == "program/the-hub-stops-stalling/delivery"
    assert ["gh", "pr", "merge", str(number), "--squash"] in rig.gh.calls
    # The PR's diff is one story and its evidence, marked done.
    files = git(rig.repo, "diff", "--name-only", "origin/main", f"origin/{branch}").splitlines()
    assert sorted(files) == ["pm/roadmap/app/phase-1-the-first/current-phase-status.md",
                             "pm/roadmap/app/phase-1-the-first/evidence-story-01.md",
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


def test_a_dw_refusal_is_his_row_in_words_and_retry_or_skip_answers_it(tmp_path) -> None:
    rig, pid = _done(tmp_path, delivery="dw app/1/07")  # story 07 is not there
    [line] = _delivery_lines(rig, pid)
    assert line["choice"] == "failed"
    assert line["line"] == "Could not deliver to dw app/1/07: Delivery Workbench did not take the evidence"
    assert line["undo"]["detail"]  # dw's own words, for the evidence fold
    [item] = rig.program(pid)["your_turn_items"]
    assert item["kind"] == "delivery" and item["choices"] == ["retry", "skip"]
    assert item["title"] == ("Deliver “The hub stops stalling” to dw app/1/07: "
                             "it Delivery Workbench did not take the evidence")
    rig.service.decide(OWNER, pid, "", kind="delivery", choice="retry")
    assert [row["choice"] for row in _delivery_lines(rig, pid)] == ["failed", "failed"]
    rig.service.decide(OWNER, pid, "", kind="delivery", choice="skip")
    assert _delivery_lines(rig, pid)[0]["line"] == "Skipped the delivery"
    assert rig.program(pid)["your_turn_items"] == [] and rig.program(pid)["state"] == "done"


def test_at_secure_the_delivery_pr_waits_for_his_merge(tmp_path) -> None:
    rig, pid = _done(tmp_path, control="secure")
    [line] = _delivery_lines(rig, pid)
    number = max(rig.gh.prs)
    assert line["choice"] == "pr_open" and line["line"] == f"The delivery PR #{number} to dw app/1 waits for your merge"
    assert ["gh", "pr", "merge", str(number), "--squash"] not in rig.gh.calls
    [item] = rig.program(pid)["your_turn_items"]
    assert item["kind"] == "delivery" and item["choices"] == ["merge", "skip"] and item["pr"]["number"] == number
    rig.service.decide(OWNER, pid, "", kind="delivery", choice="merge")
    assert ["gh", "pr", "merge", str(number), "--squash"] in rig.gh.calls
    assert _delivery_lines(rig, pid)[0]["line"] == f"Delivered to dw app/1 (PR #{number})"
    assert rig.program(pid)["your_turn_items"] == []
