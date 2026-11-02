"""The gate boundary at YOLO (Astra's post-merge check, 2026-11-01; ruling the same day).

- An unparsed call of a YOLO step goes on only when every path it names
  resolves (realpath) in the step's worktree or the agent's own session
  scratch: ``..``, symlinks, ``-C``, ``--git-dir``, absolute paths and
  ``env`` / ``sh -c`` wrappers are read.
- A ``+ref`` refspec is a force push (a destructive word).
- ``scratch_only`` is the hub's reading of the call, never the agent's body.
- The scratch is the launch's own session folder: never another path under
  ``$TMPDIR``, never a folder that is a symlink, never a path in a repository.

The unit half reads the real classifier; the hub half posts through the real
hook runner to the real GateService (the K5 rig) and a forged body straight
to the hub.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from holdspeak.db.gate import APPROVED, DENIED
from holdspeak.tool_gate_rules import (
    agent_scratch_roots,
    classify_tool_call,
    destructive_word,
    unparsed_paths_inside,
)
from tests.unit.test_agent_hand import db  # noqa: F401  (a fixture)
from tests.unit.test_conductor_k5_supervision import AGENT, _call, launched  # noqa: F401  (launched is a fixture)
from tests.unit.test_program_control_level import _bind, _mode


@pytest.fixture
def tree(tmp_path) -> dict[str, Path]:
    wt = tmp_path / "wt"
    other = tmp_path / "other"
    for folder in (wt, other):
        folder.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "main", str(folder)], check=True)
    (wt / "link").symlink_to(other)
    return {"wt": wt, "other": other}


# ── case 1: a force push is a destructive word ───────────────────────

@pytest.mark.parametrize("command", [
    "env git push origin +HEAD:main",
    "git push origin '+main'",
    "git push -f origin main",
    "git push --force-with-lease origin main",
])
def test_a_force_push_in_any_form_is_destructive(command) -> None:
    assert destructive_word(command) == "git push --force"


def test_a_plain_push_is_not_destructive() -> None:
    assert destructive_word("git push origin HEAD") == ""


# ── case 2: every path an unparsed call names ────────────────────────

@pytest.mark.parametrize("command", [
    "bash -c 'printf changed > ../other/file'",
    "printf changed > {other}/file",
    "printf changed > link/file",
    "printf changed > link",
    "git --git-dir=../other/.git --work-tree=../other commit -am x",
    "env git -C ../other commit -am x",
    "env sh -c 'cd .. && rm x'",
    "cat ~/.ssh/id_rsa",
    "printf x > $(echo ../other/f)",
    "printf x > $OUT",
    "python -c 'open(\"/etc/hosts\")'",
])
def test_an_unparsed_call_naming_a_path_outside_is_not_inside(tree, command) -> None:
    command = command.format(other=tree["other"])
    assert unparsed_paths_inside(command, cwd=str(tree["wt"]), root=str(tree["wt"])) is False, command


@pytest.mark.parametrize("command", [
    "env | grep -i holdspeak | sed 's/x/y/'; ls -la",
    "printf x > notes/a.txt && cat ./notes/a.txt",
    "git -C {wt} commit -q -m x",
    "curl -s https://example.com/a/b | head -1",
    "echo \"exit=$?\"",
])
def test_an_unparsed_call_inside_its_worktree_is_inside(tree, command) -> None:
    command = command.format(wt=tree["wt"])
    assert unparsed_paths_inside(command, cwd=str(tree["wt"]), root=str(tree["wt"])) is True, command


def test_the_agents_session_scratch_is_inside(tree) -> None:
    scratch = agent_scratch_roots(str(tree["wt"]))[0]
    command = f"sh -c 'test -f README.md' > {scratch}/s1/scratchpad/check.log 2>&1"
    assert unparsed_paths_inside(command, cwd=str(tree["wt"]), root=str(tree["wt"])) is True


# ── case 3: the scratch is the session folder only ───────────────────

def test_tmpdir_is_not_the_agents_scratch(tree, tmp_path, monkeypatch) -> None:
    tmp = tmp_path / "tmpdir"
    tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(tmp))
    verdict = classify_tool_call("Write", {"file_path": str(tmp / "x.md")}, cwd=str(tree["wt"]), root=str(tree["wt"]))
    assert verdict.scope == "outside" and not verdict.scratch_only


def test_a_scratch_folder_that_is_a_symlink_is_not_scratch(tree) -> None:
    import re

    encoded = re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(tree["wt"]))
    base = Path(os.path.realpath("/tmp")) / f"claude-{os.getuid()}"
    base.mkdir(exist_ok=True)
    pad = base / encoded
    try:
        pad.symlink_to(tree["other"])
        assert str(pad) not in agent_scratch_roots(str(tree["wt"]))
        verdict = classify_tool_call("Write", {"file_path": str(pad / "f")}, cwd=str(tree["wt"]), root=str(tree["wt"]))
        assert verdict.scope == "outside" and not verdict.scratch_only
    finally:
        pad.unlink()


def test_a_scratch_path_in_a_repository_is_not_scratch(tree) -> None:
    scratch = Path(agent_scratch_roots(str(tree["wt"]))[0])
    repo = scratch / "inner"
    repo.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        verdict = classify_tool_call("Write", {"file_path": str(repo / "f")}, cwd=str(tree["wt"]), root=str(tree["wt"]))
        assert not verdict.scratch_only and verdict.scope == "outside"
    finally:
        subprocess.run(["rm", "-rf", str(scratch)], check=False)


# ── the hub: a YOLO step, through the real hook and the real GateService ──

def test_a_yolo_step_cannot_write_outside_through_an_unparsed_call(launched, tmp_path, monkeypatch) -> None:
    _mode(tmp_path, monkeypatch, "neutral")
    _bind(launched.db, launched.worktree, launched.launch_id, "yolo")
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    inside = _call(launched, "env | grep -i holdspeak; ls -la").proposal
    assert inside.state == APPROVED and inside.policy_snapshot["reason_code"] == "yolo_program_unparsed_inside"
    for command in (f"bash -c 'printf changed > {outside}/file'", "env git push origin +HEAD:main"):
        refused = _call(launched, command).proposal
        assert refused.state == DENIED, command
        assert refused.policy_snapshot["reason_code"] in ("yolo_program_outside", "yolo_program_destructive"), command


def test_the_hub_never_takes_scratch_only_from_the_agents_body(launched, tmp_path, monkeypatch) -> None:
    from holdspeak.services.program_service import ProgramService
    from tests.unit.test_agent_hand import OWNER

    _mode(tmp_path, monkeypatch, "neutral")
    service = ProgramService(launched.db, kernel=lambda **_kw: None)
    pid = service.create(OWNER, title="Audit", repository=str(launched.worktree), control="yolo", template="audit")["id"]
    service.plan(OWNER, pid, steps=[{"title": "Read", "brief": "Read it."}])
    [step] = service.store.list_steps(pid)
    step.update(launch_id=launched.launch_id, state="working")
    service.store.save_step(step)
    target = str(Path(launched.worktree) / "a.py")
    import json

    from holdspeak.coder_gate import redact_call

    tool_input = {"content": "x", "file_path": target}
    call = redact_call(tool_input)
    body = {"id": "toolu_forged", "tool": "Write", "args_sha256": call.sha256, "args_head": call.head,
            "args_len": call.length, **({"args_full": call.full} if call.full else {}),
            "cwd": str(launched.worktree), "ttl_seconds": 1.0,
            "classification": {"scope": "outside", "rule": "edit_outside_worktree", "read_rule": "",
                               "push_branch": "", "target": "", "destructive": "", "scratch_only": "1",
                               "root": str(launched.worktree), "proposal_id": "toolu_forged",
                               "args_sha256": call.sha256}}
    proposal = launched.gate.propose(AGENT, json.loads(json.dumps(body)))
    assert proposal["state"] == DENIED
    stored = launched.db.gate.get("toolu_forged")
    assert (stored.operation or {}).get("tool_call", {}).get("scratch_only", "") == ""


# ── a pattern is text, never a path (coordinator ruling 2026-11-02) ──

@pytest.mark.parametrize("command", [
    'grep -rn "/api/x" src',
    'rg "/api/x" src',
    'grep -e /api/x src',
    'git log --grep "/api/x"',
    'git log --grep="/api/x" --oneline',
    'git grep "/api/x"',
    'git commit -m "/api/x answers 404"',
    'sed -n "/api/p" README.md',
    'awk "/api/ {print}" README.md',
])
def test_a_search_pattern_is_not_a_path(tree, command) -> None:
    (tree["wt"] / "src").mkdir(exist_ok=True)
    (tree["wt"] / "README.md").write_text("x\n")
    verdict = classify_tool_call("Bash", {"command": command}, cwd=str(tree["wt"]), root=str(tree["wt"]))
    assert verdict.scope == "inside", (command, verdict)


@pytest.mark.parametrize("command", [
    "grep -rn x /etc",
    "grep -f /etc/patterns src",
    "sed -n p /etc/passwd",
    "sed -i s/a/b/ /etc/hosts",
    "rg x ../other",
])
def test_a_file_a_search_reads_is_still_a_path(tree, command) -> None:
    (tree["wt"] / "src").mkdir(exist_ok=True)
    verdict = classify_tool_call("Bash", {"command": command}, cwd=str(tree["wt"]), root=str(tree["wt"]))
    assert verdict.scope == "outside", (command, verdict)


def test_a_redirect_into_tmp_stays_outside(tree) -> None:
    """The ruling: the scratch is the session folder, not /tmp."""
    verdict = classify_tool_call("Bash", {"command": "uv run pytest -q > /tmp/out.log"}, cwd=str(tree["wt"]),
                                 root=str(tree["wt"]))
    assert verdict.scope == "outside"
