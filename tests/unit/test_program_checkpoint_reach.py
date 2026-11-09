"""HS-S35 (earlier D04): a checkpoint's recoverability is visible without
falsifying history.

The Program read carries, beside each stored ref, whether that ref names
its stored commit now (``reach``). The stored ref is never rewritten; a
later pin is a new row; a pin failure is logged and the line is written.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from types import SimpleNamespace

from holdspeak.services.program_checkpoint_reach import project
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig, git


def _started(tmp_path: Path) -> tuple[Rig, str, dict]:
    rig = Rig(tmp_path, real_git=True)  # the reach is read from real refs
    pid = rig.service.create(OWNER, title="P", repository=str(rig.repo), check_command=f"sh {FAKE_CHECK}",
                             control="yolo")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Pin it"}])
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    assert step["launch_id"]
    return rig, pid, step


def _pinned(rig: Rig, pid: str) -> list[dict]:
    """His pinned lines (the engine pins its own lines too), oldest first."""
    return sorted((row for row in rig.program(pid)["checkpoints"] if row.get("ref") and row["line"].endswith(" pin")),
                  key=lambda row: row["id"])


def _n(row: dict) -> int:
    return int(row["ref"].rsplit("/", 1)[1])


def test_a_later_pin_is_a_new_row_and_a_gone_ref_reads_not_found_beside_its_stored_ref(tmp_path) -> None:
    rig, pid, step = _started(tmp_path)
    worktree = Path(rig.ledger.get(step["launch_id"])["worktree_path"])
    rig.service.checkpoint(OWNER, pid, step["id"], "First pin")
    (worktree / "more.txt").write_text("more\n", encoding="utf-8")
    rig.service.checkpoint(OWNER, pid, step["id"], "Second pin")
    first, second = _pinned(rig, pid)
    assert _n(second) == _n(first) + 1
    assert first["ref_commit"] != second["ref_commit"] and len(first["ref_commit"]) == 40
    assert [row["reach"] for row in (first, second)] == ["reachable", "reachable"]
    assert first["reach_words"] == f"checkpoint {first['ref_commit']} · reachable"
    stored = {key: first[key] for key in ("id", "ref", "ref_commit", "line", "at")}

    # The ref is gone (a prune): the row says so; its stored ref and commit stay as written.
    git(rig.repo, "update-ref", "-d", first["ref"])
    first_now, second_now = _pinned(rig, pid)
    assert (first_now["reach"], first_now["reach_words"]) == ("not_found", "stored, not found in the repository")
    assert {key: first_now[key] for key in stored} == stored
    assert second_now["reach"] == "reachable"
    raw = next(row for row in rig.service.store.list_checkpoints(pid) if row["id"] == first["id"])
    assert (raw["ref"], raw["ref_commit"]) == (first["ref"], first["ref_commit"])

    # A ref that now names another commit is "moved", never re-stored.
    git(rig.repo, "update-ref", second["ref"], first["ref_commit"])
    second_moved = _pinned(rig, pid)[1]
    assert (second_moved["reach"], second_moved["ref_commit"]) == ("moved", second["ref_commit"])

    # A third pin is a third row; the two before keep their ids, refs and commits.
    rig.service.checkpoint(OWNER, pid, step["id"], "Third pin")
    rows = _pinned(rig, pid)
    assert [_n(row) for row in rows] == [_n(first), _n(first) + 1, _n(first) + 2]
    assert [(row["id"], row["ref_commit"]) for row in rows[:2]] == [(first["id"], first["ref_commit"]),
                                                                      (second["id"], second["ref_commit"])]


def test_a_pin_failure_is_logged_and_the_line_is_still_written(tmp_path, caplog) -> None:
    rig, pid, step = _started(tmp_path)
    worktree = Path(rig.ledger.get(step["launch_id"])["worktree_path"])
    shutil.rmtree(worktree)
    with caplog.at_level(logging.INFO):
        answer = rig.service.checkpoint(OWNER, pid, step["id"], "Pin with no worktree")
    assert answer["checkpoint"]["ref"] is None
    row = next(row for row in rig.program(pid)["checkpoints"] if row["id"] == answer["checkpoint"]["id"])
    assert row["line"] == "Pin with no worktree" and row["pin_note"] and "reach" not in row
    assert any("not pinned" in record.getMessage() for record in caplog.records)


def test_no_pinned_row_runs_no_git_and_an_unreadable_repository_is_not_read(tmp_path) -> None:
    calls: list[list[str]] = []

    def spy(argv, **_kwargs):
        calls.append(list(argv))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    rows = [{"id": 1, "line": "A line", "ref": None}]
    assert project(rows, str(tmp_path), spy) is rows and calls == []
    pinned = [{"id": 2, "ref": "refs/holdspeak/checkpoints/s/1", "ref_commit": "a" * 40}]
    [row] = project(pinned, str(tmp_path / "gone"), spy)
    assert (row["reach"], row["reach_words"], row["ref"]) == ("not_read", "stored, not read", pinned[0]["ref"])
    assert calls == []
