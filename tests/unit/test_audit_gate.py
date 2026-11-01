"""PG-LANG JRN8: an audit step's agent reads; the gate refuses its writes by rule.

The REAL hook verdict (``classify_tool_call``) and the REAL tool-gate policy
(``resolve_policy``), as the hub runs them for a call of an audit step
(``audit_step``, set by ``ToolCallCodec.authorize`` from the step's Program).
"""
from __future__ import annotations

from holdspeak.operation_policy import describe_operation, resolve_policy
from holdspeak.tool_gate_rules import classify_tool_call


def _outcome(tmp_path, tool: str, tool_input: dict, mode: str, *, audit: bool = True) -> tuple[str, str]:
    verdict = classify_tool_call(tool, tool_input, cwd=str(tmp_path), root=str(tmp_path)).to_dict()
    tool_call = {"launch_id": "L1", "scope": verdict["scope"], "rule": verdict["rule"],
                 "read_rule": verdict["read_rule"], "program_step": "1", **({"audit_step": "1"} if audit else {}),
                 **({"scratch_only": "1"} if verdict.get("scratch_only") else {})}
    operation = describe_operation(
        operation_id="op-1", family="tool_gate", effect_class="agent/tool_call_hold", actor="agent",
        destination=str(tmp_path), data_classes=("tool_arguments_redacted",), resource_scope=tool,
        fixed_destination=True, consequence="execute_on_approval")
    decision = resolve_policy(operation, mode=mode, source="config", tool_call=tool_call)
    return decision.outcome, decision.reason_code


def test_audit_reads_pass_and_writes_are_refused_by_rule(tmp_path) -> None:
    for mode in ("yolo", "neutral"):
        assert _outcome(tmp_path, "Bash", {"command": "git diff HEAD~1 && cat README.md"}, mode) == (
            "allowed", "audit_read_allowed")
        assert _outcome(tmp_path, "Read", {"file_path": str(tmp_path / "a.py")}, mode)[0] == "allowed"
        for tool, tool_input in (("Bash", {"command": "git commit -am x"}),
                                 ("Bash", {"command": "echo x > a.py"}),
                                 ("Edit", {"file_path": str(tmp_path / "a.py")}),
                                 ("Write", {"file_path": str(tmp_path / "b.py")})):
            assert _outcome(tmp_path, tool, tool_input, mode) == ("refused", "audit_reads_only"), (mode, tool_input)
    # A build step at YOLO still writes in its own worktree.
    assert _outcome(tmp_path, "Edit", {"file_path": str(tmp_path / "a.py")}, "yolo", audit=False)[0] == "allowed"
    # Secure holds every call, an audit's too.
    assert _outcome(tmp_path, "Bash", {"command": "git commit -am x"}, "safe")[0] == "authorization_required"


def test_audit_writes_into_its_own_scratch_pass(tmp_path, monkeypatch) -> None:
    """The agent's own scratch (its Claude Code session scratchpad) is not
    the repository: an audit step may write its notes there. Since the ruling
    of 2026-11-01 the rest of $TMPDIR is not its scratch: a write there is
    refused (Astra's post-merge check: a checkout can sit under $TMPDIR)."""
    import os

    from holdspeak.tool_gate_rules import agent_scratch_roots

    repo = tmp_path / "repo"
    repo.mkdir()
    tmp = tmp_path / "tmpdir"
    tmp.mkdir()
    monkeypatch.setenv("TMPDIR", str(tmp))
    pad = agent_scratch_roots(str(repo))[0]
    for mode in ("yolo", "neutral"):
        for tool, tool_input in (
            ("Bash", {"command": f"cat README.md > {pad}/scratchpad/notes.txt"}),
            ("Write", {"file_path": f"{pad}/scratchpad/report.md"}),
        ):
            assert _outcome(repo, tool, tool_input, mode) == ("allowed", "audit_read_allowed"), (mode, tool_input)
        for tool, tool_input in (
            ("Bash", {"command": f"git diff > {tmp}/audit.log"}),
            ("Write", {"file_path": f"{tmp}/shot-notes.md"}),
        ):
            assert _outcome(repo, tool, tool_input, mode) == ("refused", "audit_reads_only"), (mode, tool_input)
        # A write in the repository, or one that also writes there, is still refused.
        assert _outcome(repo, "Bash", {"command": f"git diff > {tmp}/a.log && echo x > a.py"}, mode)[0] == "refused"
        assert _outcome(repo, "Write", {"file_path": str(repo / "a.py")}, mode)[0] == "refused"
        assert _outcome(repo, "Write", {"file_path": os.path.expanduser("~/elsewhere.md")}, mode)[0] == "refused"
    # A build step's verdict on a plain read keeps its shape (no scratch_only key).
    from holdspeak.tool_gate_rules import classify_tool_call

    assert "scratch_only" not in classify_tool_call("Bash", {"command": "git status"}, cwd=str(repo), root=str(repo)).to_dict()
