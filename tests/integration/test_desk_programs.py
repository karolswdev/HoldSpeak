"""PG16 on the Programs rig: decisions from a Program (design §9b).

His Skip, a rule's Skip above NOTE, and a merge by rule each become ONE
proposed decision record: the reason, the rule and the level in its
context, linked to the Program and to the step's PR, filed to the Project.
The Room's decisions section carries it under ``proposed`` with its Program
and PR; the Program's checkpoint and Decided for you rows carry its id;
``decision_record.list`` filters by program. The NOTE rule's Skip (the
noise filter) proposes nothing. A withdrawn record comes back as the same
record (one per checkpoint).
No auto-confirm: the record stays proposed.

The face half replays the answers recorded here
(``web/src/desk/programs/__fixtures__/program.skip_decision.json`` and
``room.decisions.proposed.json``; ``HOLDSPEAK_WIRE_WRITE=1`` rewrites them,
else this test fences their shape).
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak.services import program_service as program_module
from holdspeak.services.decision_record_service import DecisionRecordService
from holdspeak.services.project_service import ProjectService
from holdspeak.web.routes.programs import build_programs_router
from tests.integration.program_rig import FAKE_CHECK, OWNER, Rig

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
    app = FastAPI()
    app.include_router(build_programs_router(None))  # type: ignore[arg-type]
    return TestClient(app)


def _rig(tmp_path: Path, control: str) -> tuple[Rig, str]:
    rig = Rig(tmp_path)
    with rig.db._connection() as conn:
        conn.execute("INSERT INTO projects (id, name) VALUES ('proj-holdspeak', 'HoldSpeak')")
    pid = rig.service.create(
        OWNER, title="The words wave", goal="Plain words.", repository=str(rig.repo),
        check_command=f"sh {FAKE_CHECK}", template="build-and-review", control=control,
        reviewer_profile="codex-default", project_id="proj-holdspeak",
    )["id"]
    rig.service.plan(OWNER, pid, steps=[
        {"title": "Dock words", "brief": "Plain words on the Dock.", "owns": ["web/src/desk/dock/words.ts"]},
    ])
    rig.service.start(OWNER, pid)
    return rig, pid


def _review(rig: Rig, pid: str, words: str) -> None:
    one = rig.step(pid, 1)
    rig.agent.finish(one["launch_id"], {"web/src/desk/dock/words.ts": "export {};\n"})
    rig.tick(2)  # the check, then the reviewer starts
    for record in rig.ledger.list():
        if record.get("helper_of"):
            rig.words[record["launch_id"]] = words
            rig.states[record["launch_id"]] = {"state": "done", "turn_id": "r"}
    rig.tick(2)


def _record(rig: Rig, record_id: str) -> dict[str, Any]:
    record = DecisionRecordService(rig.db).get(OWNER, record_id)
    assert record is not None, record_id
    return record


def test_a_skip_is_a_proposed_decision_in_the_room_with_its_program_and_pr(tmp_path, monkeypatch) -> None:
    rig, pid = _rig(tmp_path, "secure")
    client = _client(rig, monkeypatch)
    _review(rig, pid, "MUST: none\nSHOULD: sentence case the title\nNOTE: the old name stays in a comment")
    step = rig.step(pid, 1)
    assert step["state"] == "findings", step["state"]
    should = next(f for f in step["findings"] if f["level"] == "SHOULD")
    note = next(f for f in step["findings"] if f["level"] == "NOTE")

    # The NOTE rule skipped the note (every level): the noise filter, no record.
    assert note["decision"] == "skip" and not note.get("decision_record_id")
    decided = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "finding_note")
    assert decided["decision_record_id"] is None
    assert not ProjectService(rig.db).room(OWNER, "proj-holdspeak")["decisions"]["proposed"]
    from holdspeak.mcp import tools as mcp_tools

    monkeypatch.setattr(mcp_tools, "get_database", lambda: rig.db)
    assert mcp_tools.dispatch("decision_record.list", {"program_id": pid}, OWNER) == []

    # His Overturn: the finding is his again (nothing to withdraw).
    rig.service.overturn(OWNER, pid, decided["id"])

    # His Skip of the note: a proposed record, his reason.
    answer = client.post(f"/api/programs/{pid}/steps/{step['id']}/decide", json={
        "kind": "finding", "choice": "skip", "finding_id": note["id"], "reason": "The comment helps a reader"})
    assert answer.status_code == 200, answer.text
    note_record = answer.json()["decision_record_id"]
    assert note_record
    again = _record(rig, note_record)
    assert "Reason: The comment helps a reader" in again["rationale"] and "Decided by: you" in again["rationale"]
    assert "Control: Secure" in again["rationale"] and "Rule:" not in again["rationale"]
    assert again["status"] == "proposed" and again["lifecycle"] == "active"

    # His Skip of the SHOULD: a second record; every finding is decided, so the PR opens.
    answer = client.post(f"/api/programs/{pid}/steps/{step['id']}/decide", json={
        "kind": "finding", "choice": "skip", "finding_id": should["id"], "reason": "The title is a proper name"})
    assert answer.status_code == 200, answer.text
    should_record = answer.json()["decision_record_id"]
    assert should_record and should_record != note_record
    step = rig.step(pid, 1)
    assert step["state"] in ("pr_open", "merge_ask") and step["pr"]["url"], step["state"]

    record = _record(rig, should_record)
    assert record["decision_text"] == "Skip this should finding on step 1: sentence case the title"
    assert record["title"] == "Skip: sentence case the title"
    assert {(w["work_type"], w["work_ref"]) for w in record["work"]} == {
        ("program", pid), ("pr", step["pr"]["url"])}
    assert {(s["source_type"], s["source_ref"]) for s in record["sources"]} == {("project", "proj-holdspeak")}

    # The checkpoint row of his Skip names the record.
    lines = {c["line"]: c for c in rig.program(pid)["checkpoints"]}
    assert lines["Skip: sentence case the title"]["decision_record_id"] == should_record

    # The Room: both proposed, with the Program and the PR; not in the decided items.
    decisions = ProjectService(rig.db).room(OWNER, "proj-holdspeak")["decisions"]
    assert decisions["state"] == "ok"
    assert not decisions["items"]
    rows = {row["id"]: row for row in decisions["proposed"]}
    assert set(rows) == {should_record, note_record}
    assert rows[should_record]["text"] == "Skip: sentence case the title"
    assert rows[should_record]["program"] == {"id": pid, "title": "The words wave"}
    assert rows[should_record]["prs"] == [{"number": step["pr"]["number"], "url": step["pr"]["url"]}]

    # MCP: decision_record.list by program.
    listed = mcp_tools.dispatch("decision_record.list", {"program_id": pid}, OWNER)
    assert {row["id"] for row in listed} == set(rows)
    assert all(row["status"] == "proposed" for row in listed)

    _fixture("program.skip_decision.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    _fixture("room.decisions.proposed.json", decisions, tmp_path)


def test_a_merge_by_rule_is_a_proposed_decision_with_its_rule(tmp_path, monkeypatch) -> None:
    rig, pid = _rig(tmp_path, "normal")
    _review(rig, pid, "MUST: none")
    rig.tick()
    step = rig.step(pid, 1)
    assert step["state"] in ("merged", "done"), step["state"]
    merge = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "merge")
    assert merge["decision_record_id"]
    record = _record(rig, merge["decision_record_id"])
    assert record["status"] == "proposed"
    assert record["title"] == f"Merge PR #{step['pr']['number']}: Dock words"
    assert "Rule: Normal merges on a green check and a passed review" in record["rationale"]
    assert "Reason: Check green, review passed" in record["rationale"]
    assert ("pr", step["pr"]["url"]) in {(w["work_type"], w["work_ref"]) for w in record["work"]}
    # One record per merge: another tick writes nothing new.
    rig.tick(2)
    # The id is the checkpoint's: proposing again is the same record; a
    # withdrawn record comes back as the same record.
    from types import SimpleNamespace

    from holdspeak.services import program_decisions

    program = rig.service.store.get_program(pid)
    stored = rig.service.store.get_step(step["id"])
    outcome = SimpleNamespace(rule="Normal merges on a green check and a passed review")
    assert rig.service.propose_merge(program, stored, outcome) == merge["decision_record_id"]
    program_decisions.withdraw(rig.db, merge["decision_record_id"])
    assert DecisionRecordService(rig.db).get(OWNER, merge["decision_record_id"]) is None
    assert rig.service.propose_merge(program, stored, outcome) == merge["decision_record_id"]
    assert _record(rig, merge["decision_record_id"])["status"] == "proposed"
    from holdspeak.mcp import tools as mcp_tools

    monkeypatch.setattr(mcp_tools, "get_database", lambda: rig.db)
    assert [row["id"] for row in mcp_tools.dispatch("decision_record.list", {"program_id": pid}, OWNER)] == [
        merge["decision_record_id"]]


# ── PG20: hidden-ref checkpoints on the rig's real git ───────────────


def _tree_of_worktree(path: Path) -> str:
    """The worktree's tree as git sees it now, read through a scratch index
    (the worktree's own index is not touched)."""
    import shutil
    import subprocess
    import tempfile

    from tests.integration.program_rig import git

    index = git(path, "rev-parse", "--path-format=absolute", "--git-path", "index")
    with tempfile.TemporaryDirectory() as scratch:
        temp = Path(scratch) / "index"
        shutil.copyfile(index, temp)
        env = {**os.environ, "GIT_INDEX_FILE": str(temp)}
        subprocess.run(["git", "-C", str(path), "add", "-A"], env=env, check=True, capture_output=True)
        return subprocess.run(["git", "-C", str(path), "write-tree"], env=env, check=True, capture_output=True,
                              text=True).stdout.strip()


def _pinned_rig(tmp_path: Path, control: str) -> tuple[Rig, str, dict[str, Any], Path, dict[str, Any]]:
    """Step 1 is handed; it has a commit and a change it did not commit; his
    checkpoint pins it."""
    from tests.integration.program_rig import git

    rig, pid = _rig(tmp_path, control)
    one = rig.step(pid, 1)
    tree = Path(rig.ledger.get(one["launch_id"])["worktree_path"])
    (tree / "web" / "src" / "desk" / "dock").mkdir(parents=True, exist_ok=True)
    (tree / "web" / "src" / "desk" / "dock" / "words.ts").write_text("export const one = 1;\n", encoding="utf-8")
    git(tree, "add", "-A")
    git(tree, "commit", "-m", "first words")
    (tree / "web" / "src" / "desk" / "dock" / "words.ts").write_text("export const one = 'one';\n", encoding="utf-8")
    (tree / "notes.md").write_text("half way\n", encoding="utf-8")
    row = rig.service.checkpoint(OWNER, pid, one["id"], "Half way: the words are plain")["checkpoint"]
    return rig, pid, rig.step(pid, 1), tree, row


def test_a_checkpoint_pins_a_hidden_ref_whose_tree_is_the_worktree(tmp_path, monkeypatch) -> None:
    from tests.integration.program_rig import git

    rig, pid, one, tree, row = _pinned_rig(tmp_path, "normal")
    head, branch = git(tree, "rev-parse", "HEAD"), git(tree, "rev-parse", "--abbrev-ref", "HEAD")
    status = git(tree, "status", "--porcelain")
    ref = row["ref"]
    assert re.fullmatch(rf"refs/holdspeak/checkpoints/{one['id']}/\d+", ref), ref
    # The ref's tree is the worktree at that moment, the change it did not commit and the new file included.
    assert git(tree, "rev-parse", f"{ref}^{{tree}}") == _tree_of_worktree(tree)
    assert git(tree, "show", f"{ref}:web/src/desk/dock/words.ts") == "export const one = 'one';"
    assert git(tree, "show", f"{ref}:notes.md") == "half way"
    # Its parent is the step's HEAD; its message names the checkpoint.
    assert git(tree, "rev-parse", f"{ref}^") == head
    assert "Half way: the words are plain" in git(tree, "log", "-1", "--format=%s", ref)
    # The working tree, its index and its branch did not change.
    assert git(tree, "rev-parse", "HEAD") == head and git(tree, "rev-parse", "--abbrev-ref", "HEAD") == branch
    assert git(tree, "status", "--porcelain") == status and "?? notes.md" in status
    assert ref not in git(tree, "branch", "--all")
    # Each checkpoint has its own number; the engine's own lines pin too.
    rows = [c for c in rig.program(pid)["checkpoints"] if c["step_id"] == one["id"] and c.get("ref")]
    assert len({c["ref"] for c in rows}) == len(rows) >= 2
    # program.get over MCP carries the refs.
    from holdspeak.mcp import tools as mcp_tools

    monkeypatch.setattr(program_module, "default_program_service", lambda db=None: rig.service)
    got = mcp_tools.dispatch("program.get", {"program_id": pid}, OWNER)
    pinned = next(c for c in got["checkpoints"] if c["id"] == row["id"])
    assert pinned["ref"] == ref and pinned["ref_commit"] == git(tree, "rev-parse", ref)
    # A Program-wide line pins nothing; a step with no worktree yet keeps a note.
    started = next(c for c in got["checkpoints"] if c["line"] == "Started the program")
    assert started["ref"] is None and started["pin_note"] is None


def test_a_checkpoint_without_git_is_a_note_never_a_stop(tmp_path) -> None:
    import shutil

    rig, pid, one, tree, _row = _pinned_rig(tmp_path, "normal")
    shutil.rmtree(tree)
    row = rig.service.checkpoint(OWNER, pid, one["id"], "The worktree went away")["checkpoint"]
    assert row["ref"] is None
    pinned = next(c for c in rig.program(pid)["checkpoints"] if c["id"] == row["id"])
    assert pinned["pin_note"] == "No worktree to pin yet" and pinned["ref"] is None


def test_a_handoff_names_the_ref_it_continues_from(tmp_path, monkeypatch) -> None:
    from tests.integration.program_rig import git

    rig, pid, one, tree, row = _pinned_rig(tmp_path, "normal")
    # View brief before the move: the preview names the last pinned checkpoint.
    preview = rig.service.handoff(OWNER, pid, one["id"], "codex", preview=True)
    last = next(c for c in rig.program(pid)["checkpoints"] if c["step_id"] == one["id"] and c.get("ref"))
    assert f"- Continues from: `{last['ref']}`" in preview["brief"]
    (tree / "notes.md").write_text("more\n", encoding="utf-8")
    answer = rig.service.handoff(OWNER, pid, one["id"], "codex")
    entry = answer["handoff"]
    ref = entry["continues_from"]
    assert ref and ref != row["ref"] and ref.startswith(f"refs/holdspeak/checkpoints/{one['id']}/")
    # The brief the next agent got names the ref; the ref's tree is the worktree it continues in.
    step = rig.step(pid, 1)
    brief = step["handoffs"][-1]["brief"]
    assert f"- Continues from: `{ref}` (commit {entry['continues_commit'][:12]})" in brief
    assert rig.ledger.get(entry["launch_to"])["worktree_path"] == str(tree)
    assert git(tree, "rev-parse", f"{ref}^{{tree}}") == _tree_of_worktree(tree)
    assert git(tree, "show", f"{ref}:notes.md") == "more"
    # The handoff's checkpoint row carries the ref (the Checkpoints fold's divider).
    divider = next(c for c in rig.program(pid)["checkpoints"] if c.get("kind") == "handoff")
    assert divider["ref"] == ref


def test_start_from_here_makes_a_worktree_at_that_tree(tmp_path, monkeypatch) -> None:
    from tests.integration.program_rig import git

    rig, pid, one, tree, row = _pinned_rig(tmp_path, "normal")
    client = _client(rig, monkeypatch)
    pinned_tree = git(tree, "rev-parse", f"{row['ref']}^{{tree}}")
    # The worktree moves on; the checkpoint stays what it was.
    (tree / "notes.md").write_text("a wrong turn\n", encoding="utf-8")
    answer = client.post(f"/api/programs/{pid}/checkpoints/{row['id']}/start-from")
    assert answer.status_code == 200, answer.text
    body = answer.json()
    assert body["ref"] == row["ref"] and body["step_id"]
    new = next(s for s in body["program"]["steps"] if s["id"] == body["step_id"])
    assert new["title"].startswith("Dock words (from checkpoint ") and new["ordinal"] == 2
    # The tick hands it; its worktree starts at the ref's tree, on its own branch.
    rig.tick()
    new = rig.step(pid, 2)
    assert new["launch_id"], new["state"]
    fresh = Path(rig.ledger.get(new["launch_id"])["worktree_path"])
    assert fresh != tree
    assert git(fresh, "rev-parse", "HEAD") == git(tree, "rev-parse", row["ref"])
    assert git(fresh, "rev-parse", "HEAD^{tree}") == pinned_tree
    assert (fresh / "notes.md").read_text(encoding="utf-8") == "half way\n"
    assert git(fresh, "rev-parse", "--abbrev-ref", "HEAD") == new["branch"]
    lines = [c["line"] for c in rig.program(pid)["checkpoints"]]
    assert f"Started step 2 from {row['ref']}" in lines
    # Refused: an unknown checkpoint, and one that pinned nothing.
    assert client.post(f"/api/programs/{pid}/checkpoints/999999/start-from").status_code == 404
    started = next(c for c in rig.program(pid)["checkpoints"] if c["line"] == "Started the program")
    assert client.post(f"/api/programs/{pid}/checkpoints/{started['id']}/start-from").status_code == 400
    _fixture("program.start_from.json", client.get(f"/api/programs/{pid}").json(), tmp_path)


def test_an_agent_asks_to_start_from_a_checkpoint_and_the_ladder_decides(tmp_path, monkeypatch) -> None:
    from tests.unit.test_program_service import _launch_principal

    # Normal: the agent's ask is his to add.
    rig, pid, one, _tree, row = _pinned_rig(tmp_path / "normal", "normal")
    agent = _launch_principal(monkeypatch, one["launch_id"])
    answer = rig.service.start_from(agent, pid, row["id"])
    assert answer["step_id"] is None
    turn = next(item for item in rig.program(pid)["your_turn_items"] if item["kind"] == "add_step")
    assert turn["title"] == f"Start a step from checkpoint {row['ref'].rsplit('/', 1)[-1]} of step 1 \u201cDock words\u201d"
    rig.service.decide(OWNER, pid, one["id"], kind="add_step", choice="add", finding_id=turn["proposal"])
    added = rig.step(pid, 2)
    assert added["title"].startswith("Dock words (from checkpoint ")

    # YOLO: the engine adds it and says so (Decided for you, overturnable).
    rig, pid, one, _tree, row = _pinned_rig(tmp_path / "yolo", "yolo")
    agent = _launch_principal(monkeypatch, one["launch_id"])
    rig.service.start_from(agent, pid, row["id"])
    decided = next(r for r in rig.program(pid)["decided_for_you"] if r["kind"] == "add_step")
    assert f"from {row['ref']} (asked by step 1)" in decided["line"] and decided["overturnable"]

    # Another launch may not ask on this step.
    stranger = _launch_principal(monkeypatch, "L-stranger")
    import pytest

    with pytest.raises(program_module.ProgramRefused):
        rig.service.start_from(stranger, pid, row["id"])


# ── PG17: the first Program is the engine's own history ─────────────

GH_HISTORY = Path(__file__).resolve().parents[1] / "fixtures" / "gh" / "pr_view_history.json"


def _importer() -> Any:
    import importlib.util

    path = Path(__file__).resolve().parents[2] / "scripts" / "program_import_history.py"
    spec = importlib.util.spec_from_file_location("program_import_history", path)
    module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _recorded_prs() -> list[dict[str, Any]]:
    """``gh pr view --json number,title,url,state,mergedAt,mergeCommit``
    for #1584, #1585, #1596 (closed, not merged) and #1598, recorded."""
    return json.loads(GH_HISTORY.read_text(encoding="utf-8"))


def test_the_importer_builds_one_history_step_per_merged_pr_from_recorded_gh(tmp_path) -> None:
    importer = _importer()
    assert importer.pr_numbers(["1584-1586", "1590,#1591", "1585"]) == [1584, 1585, 1586, 1590, 1591]
    payload = importer.build_payload(_recorded_prs(), title="The hub stops stalling", goal="Off the loop.",
                                     repository="/repo")
    assert payload["create"] == {"title": "The hub stops stalling", "goal": "Off the loop.", "repository": "/repo"}
    steps = payload["plan"]["steps"]
    assert [step["history"]["pr_number"] for step in steps] == [1584, 1585, 1598]
    assert payload["skipped"] == [{"number": 1596, "state": "CLOSED"}]
    first = steps[0]
    assert first["history"] == {
        "pr_number": 1584, "pr_url": "https://github.com/karolswdev/HoldSpeak/pull/1584",
        "merged_at": "2026-10-28T15:36:11Z", "head_commit": "82067a48929f1ba7d77abf6bc793f96a8d68f493",
    }
    assert first["title"].startswith("The dock and the chair never force") and len(first["title"]) <= 200

    # --dry-run prints the payload and posts nothing; a run posts create, then plan.
    import io

    recorded = {int(pr["number"]): pr for pr in _recorded_prs()}
    posts: list[tuple[str, Any]] = []

    def post(hub: str, path: str, body: Any, token: str) -> dict[str, Any]:
        posts.append((path, body))
        return {"id": "program-x"} if path == "/api/programs" else {"title": "T", "state_word": "Done",
                                                                       "history": {"words": "Merged 3 PRs · 28 Oct"}}

    out, err = io.StringIO(), io.StringIO()
    argv = ["--title", "T", "--repository", "/repo", "--pr", "1584,1585,1596,1598", "--token", "t"]
    assert importer.run([*argv, "--dry-run"], view=lambda n, **_kw: recorded[n], post=post, out=out, err=err) == 0
    assert json.loads(out.getvalue())["plan"]["steps"][2]["history"]["pr_number"] == 1598 and posts == []
    assert "PR #1596 did not merge (closed); left out" in err.getvalue()
    assert importer.run(argv, view=lambda n, **_kw: recorded[n], post=post, out=out, err=err) == 0
    assert [path for path, _ in posts] == ["/api/programs", "/api/programs/program-x/plan"]
    assert len(posts[1][1]["steps"]) == 3


def test_a_plan_of_merged_prs_is_a_done_program_the_runner_never_moves(tmp_path, monkeypatch) -> None:
    from datetime import datetime

    rig = Rig(tmp_path)
    client = _client(rig, monkeypatch)
    importer = _importer()
    payload = importer.build_payload(_recorded_prs(), title="The hub stops stalling",
                                     goal="The hub answers at once.", repository=str(rig.repo))
    made = client.post("/api/programs", json=payload["create"])
    assert made.status_code == 201, made.text
    pid = made.json()["id"]
    answer = client.post(f"/api/programs/{pid}/plan", json=payload["plan"])
    assert answer.status_code == 200, answer.text
    program = answer.json()

    # Every step is written Merged and closes with the Program: Done at plan
    # time, closed at the last merge.
    assert program["state"] == "done" and program["state_word"] == "Done"
    assert program["closed_at"] == "2026-10-28T18:14:50Z"
    assert program["done"] == program["total"] == 3
    assert program["history"]["prs"] == 3 and program["history"]["words"].startswith("Merged 3 PRs · ")
    assert program["done_in"]  # first merge to last merge, never negative
    rows = program["steps"]
    assert [row["pr"]["number"] for row in rows] == [1584, 1585, 1598]
    assert all(row["state"] == "done" and row["station"] == 5 for row in rows)
    assert rows[0]["ended_at"] == "2026-10-28T15:36:11Z" and rows[0]["history"]["pr_number"] == 1584
    assert all(row["worktree"] is None and row["launch_id"] is None and row["last_checkpoint"] is None for row in rows)
    assert not program["your_turn_items"]

    # The runner's tick moves nothing and hands nothing.
    before = [(row["id"], row["state"], row["updated_at"]) for row in rig.program(pid)["steps"]]
    rig.tick(3)
    assert [(row["id"], row["state"], row["updated_at"]) for row in rig.program(pid)["steps"]] == before
    assert rig.ledger.list() == []

    # Today's Since this morning: an old merge is not today's work.
    now = datetime(2026, 10, 30, 12, 0).astimezone()
    assert rig.service.since_morning(OWNER, now=now) == {"moved": 0, "running": 0, "waiting": 0, "done": 0, "merged": 0}
    merge_day = datetime(2026, 10, 28, 20, 0).astimezone()
    assert rig.service.since_morning(OWNER, now=merge_day)["merged"] == 3

    # The Programs window lists it under Done with what merged.
    listed = client.get("/api/programs").json()
    row = next(item for item in listed["programs"] if item["id"] == pid)
    assert row["state"] == "done" and row["history"]["words"] == program["history"]["words"]
    _fixture("program.history.json", client.get(f"/api/programs/{pid}").json(), tmp_path)
    _fixture("programs.history.list.json", listed, tmp_path)


def test_history_mixes_with_live_steps_and_is_validated(tmp_path, monkeypatch) -> None:
    rig = Rig(tmp_path)
    client = _client(rig, monkeypatch)
    pid = rig.service.create(OWNER, title="After the refactor", repository=str(rig.repo),
                             check_command=f"sh {FAKE_CHECK}")["id"]

    # A history step needs its PR number and its merge time.
    bad = client.post(f"/api/programs/{pid}/plan", json={"steps": [{"title": "Old", "history": {"pr_number": 1584}}]})
    assert bad.status_code == 400 and "merged_at" in bad.text
    bad = client.post(f"/api/programs/{pid}/plan", json={"steps": [{"title": "Old", "history": {"merged_at": "2026-10-28T15:36:11Z"}}]})
    assert bad.status_code == 400 and "pr_number" in bad.text

    # MCP program.plan passes history through (its schema names it).
    from holdspeak.mcp.families import program as program_family

    schema = next(tool for tool in program_family.TOOLS if tool["name"] == "program.plan")["inputSchema"]
    assert schema["properties"]["steps"]["items"]["properties"]["history"]["required"] == ["pr_number", "merged_at"]
    planned = program_family.dispatch("program.plan", {"program_id": pid, "steps": [
        {"title": "The hub stops stalling", "history": {"pr_number": 1585, "merged_at": "2026-10-28T16:05:42Z"}},
        {"title": "Dock words", "brief": "Plain words on the Dock.", "owns": ["web/src/desk/dock/words.ts"], "after": [1]},
    ]}, OWNER)
    assert [row["state"] for row in planned["steps"]] == ["merged", "planned"]
    assert planned["state"] == "drafting"

    # The live step runs as usual; `after` a history step counts as done.
    rig.service.start(OWNER, pid)
    rig.tick()
    one, two = rig.step(pid, 1), rig.step(pid, 2)
    assert one["state"] == "merged" and one["history"]["pr_number"] == 1585
    assert two["state"] not in ("planned", "ready"), two["state"]
    assert two["launch_id"]
