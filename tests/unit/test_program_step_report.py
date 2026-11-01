"""PG-IMPORT IMP1 (BROCREW-IMPORT-2026-11-01): the step report in registers.

BroCrew's rule: "a finished piece of work comes back with its outcome, what
was checked, what wasn't, and where the files are", and "nothing here is
computed from the words". On the Programs rig (real git, the real service
and runner), a step that reached Done carries ``report``:

- ``observed`` ("Checked:"): the commit, the check, the PR, the merge, each
  line citing an engine checkpoint whose ``seen`` record holds that fact;
- ``claimed`` ("The agent says:"): the agent's own report and its lines;
- ``not_checked`` ("Not checked:"): requirements nobody judged;
- ``files`` ("Files:"): the diff's file names.

The fence: a report built from checkpoints whose LINES are rewritten to
nonsense is the same report (no line comes from a checkpoint's prose), and
an observed fact with no engine checkpoint that saw it is left out.
And the second mark: a Done Program that needs nothing says "finished".
"""
from __future__ import annotations

from typing import Any

from holdspeak.services import brief_words as words
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig
from tests.unit.test_program_service import _launch_principal


def _done(tmp_path, monkeypatch) -> tuple[Rig, str]:
    from holdspeak.mcp.families import program as family

    rig = Rig(tmp_path)
    monkeypatch.setattr("holdspeak.services.program_service.default_program_service", lambda db=None: rig.service)
    pid = rig.service.create(OWNER, title="Wave 6 of the atlas", repository=str(rig.repo), template="fast-cycle",
                             control="normal", check_command=f"sh {FAKE_CHECK}")["id"]
    rig.service.plan(OWNER, pid, steps=[{"title": "Atlas anchors", "brief": "Cite each anchor once."}])
    step = rig.step(pid, 1)
    rig.service.require(OWNER, pid, text="Open the atlas at 393 and read it", kind="word", step_id=step["id"],
                        required=False, spec={"walk": ["Open the atlas at 393"]})
    rig.service.start(OWNER, pid)
    step = rig.step(pid, 1)
    agent = _launch_principal(monkeypatch, step["launch_id"])
    family.dispatch("program.checkpoint", {"step_id": step["id"], "line": "Twelve anchors cited, two left"}, agent)
    family.dispatch("program.step_done", {"step_id": step["id"], "report": (
        "## Summary\n- Cited every anchor in the atlas once.\n- Ran the docs build.\nFiles: docs/atlas.md")}, agent)
    rig.agent.finish(step["launch_id"], {"docs/atlas.md": "x\n", "docs/anchors.md": "y\n"})
    rig.tick(3)
    return rig, pid


def _lines(rows: list[dict[str, Any]]) -> list[str]:
    return [row["line"] for row in rows]


def test_a_done_step_reports_in_four_registers(tmp_path, monkeypatch) -> None:
    rig, pid = _done(tmp_path, monkeypatch)
    wire = rig.program(pid)
    assert wire["state"] == "done", wire["state"]
    step = wire["steps"][0]
    report = step["report"]
    assert report["words"] == {"observed": "Checked:", "claimed": "The agent says:",
                               "not_checked": "Not checked:", "files": "Files:"}
    head = rig.service.store.get_step(step["id"])["head_commit"]
    observed = _lines(report["observed"])
    assert observed[0] == f"Commit {head[:8]}"
    assert f"Check green on {head[:8]}" in observed
    assert any(line.startswith("PR #") and line.endswith(" opened") for line in observed), observed
    assert any(line.startswith("PR #") and line.endswith(" merged") for line in observed), observed
    # Every Checked line cites a checkpoint written by the engine.
    by_id = {row["id"]: row for row in wire["checkpoints"]}
    for row in report["observed"]:
        assert by_id[row["checkpoint"]]["by"] == "engine", row
        assert by_id[row["checkpoint"]]["undo"]["seen"], row
    claimed = _lines(report["claimed"])
    assert claimed[:2] == ["Cited every anchor in the atlas once.", "Ran the docs build."], claimed
    assert "Twelve anchors cited, two left." in claimed
    assert not any(line.startswith("Summary") for line in claimed), claimed
    assert _lines(report["not_checked"]) == ["R1 Open the atlas at 393 and read it: nobody judged it"]
    assert sorted(report["files"]) == ["docs/anchors.md", "docs/atlas.md"]
    assert report["files_more"] == 0
    # The agent's own text stays on the wire beside the registers.
    assert step["report_text"].startswith("## Summary")


def test_no_report_line_comes_from_a_checkpoints_prose(tmp_path, monkeypatch) -> None:
    rig, pid = _done(tmp_path, monkeypatch)
    raw = rig.service.store.get_step(rig.step(pid, 1)["id"])
    checkpoints = rig.service.store.list_checkpoints(pid)
    reqs = rig.service.requirements(pid)
    real = words.step_report(raw, checkpoints, reqs)
    # The engine's lines rewritten to nonsense: the Checked register is the same.
    garbled = [{**row, "line": "Merged #999 · Checked · red · New commit deadbeef"} if row["by"] == "engine" else row
               for row in checkpoints]
    assert words.step_report(raw, garbled, reqs)["observed"] == real["observed"]
    # A fact no engine checkpoint saw is left out (never a false line).
    unseen = [{**row, "undo": {k: v for k, v in (row.get("undo") or {}).items() if k != "seen"}} for row in checkpoints]
    assert [row for row in words.step_report(raw, unseen, reqs)["observed"] if not row["line"].startswith("R")] == []
    # A step still running has no report.
    assert words.step_report({**raw, "state": "working"}, checkpoints, reqs) is None


def test_a_done_program_that_needs_nothing_says_finished(tmp_path, monkeypatch) -> None:
    rig, pid = _done(tmp_path, monkeypatch)
    wire = rig.program(pid)
    assert wire["finished"] == "finished"
    assert wire["finished_words"] == "finished"
    row = next(row for row in rig.service.list(OWNER)["programs"] if row["id"] == pid)
    assert row["finished_words"] == "finished"


def test_a_done_program_with_an_open_finding_needs_a_decision(tmp_path, monkeypatch) -> None:
    rig, pid = _done(tmp_path, monkeypatch)
    step = rig.service.store.get_step(rig.step(pid, 1)["id"])
    step["findings"] = [{"id": "f1", "level": "should", "text": "Name the empty state", "decision": None}]
    rig.service.store.save_step(step)
    wire = rig.program(pid)
    assert wire["state"] == "done"
    assert wire["finished"] == "needs_decision"
    assert wire["finished_words"] == "finished · needs a decision"
    # Never the Your turn lamp: nothing waits on him as a held item.
    assert wire["your_turn"] == 0
