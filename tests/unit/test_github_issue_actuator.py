"""HS-38-02 — GitHub issue write connector (`gh issue create`).

The first real write connector on the HS-38-01 framework. These tests prove the
actuator proposes faithfully (and never acts), the connector runs `gh issue
create` and *only* that through the `PermissionGate`, a non-allow-listed argv is
refused **before** egress (spy runner never invoked), and the full loop drives an
approved proposal to `executed` with the issue ref + an audit row — all with an
**injected runner**, so the default suite makes no real `gh` call.
"""

from __future__ import annotations

import subprocess
from datetime import datetime

import pytest

from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.actuator_executor import ActuatorExecutor
from holdspeak.plugins.actuators import ActuatorProposal
from holdspeak.plugins.builtin.github_issue_actuator import (
    GITHUB_ISSUE_MANIFEST,
    GithubIssueActuator,
    build_github_issue_connector,
    register_github_issue_actuator,
)
from holdspeak.plugins.contracts import PluginRun
from holdspeak.plugins.gated_connector import ConnectorOperationRefused, GatedOperation
from holdspeak.plugins.host import PluginHost
from holdspeak.plugins.persistence import record_actuator_proposal

ACTUATOR_ID = GithubIssueActuator.id

_CONTEXT = {
    "meeting_title": "Onboarding sync",
    "github_repo": "acme/app",
    "action_items": [
        {"task": "Define the welcome screen copy", "owner": "Ana", "due": "Fri"},
        {"task": "Wire the sample project content", "owner": None, "due": None},  # unowned
    ],
}


class _FakeGh:
    """A stand-in for `subprocess.run` that records argv and returns a CompletedProcess."""

    def __init__(self, *, returncode: int = 0, stdout: str = "", stderr: str = "", raises: bool = False):
        self.calls: list[list[str]] = []
        self._returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self._raises = raises

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        if self._raises:
            raise RuntimeError("gh exploded")
        return subprocess.CompletedProcess(
            argv, returncode=self._returncode, stdout=self._stdout, stderr=self._stderr
        )


# ──────────────────────── The proposal is faithful ────────────────────


def test_actuator_proposes_faithful_github_issue() -> None:
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_github_issue_actuator(host)
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h"
    )
    assert result.status == "proposed"
    out = result.output
    assert out["target"] == "github"
    assert out["action"] == "create_issue"
    assert out["payload"]["repo"] == "acme/app"
    assert "Wire the sample project content" in out["payload"]["title"]
    assert "Wire the sample project content" in out["payload"]["body"]
    assert "acme/app" in out["preview"]


def test_actuator_with_nothing_unowned_is_error() -> None:
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_github_issue_actuator(host)
    result = host.execute(
        ACTUATOR_ID,
        context={"github_repo": "acme/app", "action_items": [{"task": "owned", "owner": "Ana"}]},
        meeting_id="m1", window_id="w1", transcript_hash="h",
    )
    assert result.status == "error"  # run() raised → no proposal


def test_actuator_without_repo_is_error() -> None:
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_github_issue_actuator(host)
    result = host.execute(
        ACTUATOR_ID,
        context={"action_items": [{"task": "x", "owner": None}]},  # no github_repo
        meeting_id="m1", window_id="w1", transcript_hash="h",
    )
    assert result.status == "error"


def test_actuator_capability_off_blocks_proposing() -> None:
    host = PluginHost(default_timeout_seconds=1.0)  # no `actuator` capability
    register_github_issue_actuator(host)
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h"
    )
    assert result.status == "blocked"


# ──────────────────────── argv + allow-check ──────────────────────────


def _proposal(**payload) -> ActuatorProposal:
    return ActuatorProposal(
        target="github", action="create_issue", preview="x", payload=dict(payload)
    )


def test_connector_builds_gh_issue_create_argv() -> None:
    fake = _FakeGh(stdout="https://github.com/acme/app/issues/42")
    connector = build_github_issue_connector(runner=fake)

    result = connector(_proposal(repo="acme/app", title="Follow up: X", body="why"))

    assert fake.calls == [
        ["gh", "issue", "create", "--repo", "acme/app", "--title", "Follow up: X", "--body", "why"]
    ]
    assert result == {"url": "https://github.com/acme/app/issues/42", "issue": 42}


def test_manifest_allows_only_issue_create() -> None:
    assert GITHUB_ISSUE_MANIFEST.allows(GatedOperation.subprocess(["gh", "issue", "create", "--repo", "r"]))
    # Destructive / unrelated `gh` verbs are not declared → refused.
    assert not GITHUB_ISSUE_MANIFEST.allows(GatedOperation.subprocess(["gh", "repo", "delete", "acme/app"]))
    assert not GITHUB_ISSUE_MANIFEST.allows(GatedOperation.subprocess(["gh", "issue", "close", "1"]))


def test_payload_metacharacters_stay_arguments_not_injection() -> None:
    """A hostile payload value is still just an argument to `gh issue create` —
    it cannot change the subcommand or inject a second command (no shell, argv list)."""
    fake = _FakeGh(stdout="https://github.com/acme/app/issues/7")
    connector = build_github_issue_connector(runner=fake)

    connector(_proposal(repo="acme/app; rm -rf /", title="$(whoami)", body="`id`"))

    argv = fake.calls[0]
    assert argv[:3] == ["gh", "issue", "create"]
    # The metacharacters are inert argv tokens, never executed.
    assert "acme/app; rm -rf /" in argv
    assert "$(whoami)" in argv


# ──────────────────────── Refusal before egress ───────────────────────


def test_non_allow_listed_argv_refused_before_egress() -> None:
    """Even if a plan tried a different `gh` verb, the manifest refuses it before
    the runner is reached."""
    fake = _FakeGh()
    from holdspeak.plugins.gated_connector import build_gated_connector

    connector = build_gated_connector(
        GITHUB_ISSUE_MANIFEST,
        plan=lambda p: GatedOperation.subprocess(["gh", "repo", "delete", "acme/app"]),
        interpret=lambda raw, op: {"unreached": True},
        runner=fake,
    )
    with pytest.raises(ConnectorOperationRefused):
        connector(_proposal(repo="acme/app"))
    assert fake.calls == []  # never reached the runner → no egress


# ──────────────────────── Full loop (injected runner) ─────────────────


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "gh.db")
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="Onboarding sync", segments=[])
    )
    return db


def _propose(db: Database, host: PluginHost) -> str:
    result = host.execute(
        ACTUATOR_ID, context=dict(_CONTEXT), meeting_id="m1", window_id="w1", transcript_hash="h1"
    )
    assert result.status == "proposed", result
    run = PluginRun(
        plugin_id=result.plugin_id,
        plugin_version=result.plugin_version,
        window_id="w1",
        meeting_id="m1",
        profile="balanced",
        status="proposed",
        idempotency_key=result.idempotency_key,
        started_at=0.0,
        finished_at=0.1,
        duration_ms=result.duration_ms,
        output=result.output,
    )
    record_actuator_proposal(db, run)
    proposals = db.actuators.list_proposals("m1")
    assert len(proposals) == 1
    return proposals[0].id


def test_full_loop_approve_execute_audit(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_github_issue_actuator(host)
    fake = _FakeGh(stdout="https://github.com/acme/app/issues/9")
    connector = build_github_issue_connector(runner=fake)

    pid = _propose(db, host)
    executor = ActuatorExecutor(
        db, connector=connector, allow_actuators=True, allowed_actuator_ids=[ACTUATOR_ID]
    )

    # Negative — execute BEFORE approval: refused, no `gh` call.
    from holdspeak.plugins.actuator_executor import ActuatorExecutionError

    with pytest.raises(ActuatorExecutionError):
        executor.execute(pid)
    assert fake.calls == []

    db.actuators.transition_proposal(pid, to_status="approved", actor="karol")
    executed = executor.execute(pid)

    assert executed.status == "executed"
    assert executed.result == {"url": "https://github.com/acme/app/issues/9", "issue": 9}
    assert len(fake.calls) == 1
    assert fake.calls[0][:3] == ["gh", "issue", "create"]
    audit = db.actuators.list_audit(pid)
    assert [a.to_status for a in audit] == ["proposed", "approved", "executed"]


def test_nonzero_exit_marks_failed_and_audits(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_github_issue_actuator(host)
    fake = _FakeGh(returncode=1, stderr="HTTP 404: repo not found")
    connector = build_github_issue_connector(runner=fake)

    pid = _propose(db, host)
    db.actuators.transition_proposal(pid, to_status="approved")
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(pid)

    assert result.status == "failed"
    assert "gh issue create failed" in (result.error or "")
    assert "404" in (result.error or "")
    assert len(fake.calls) == 1  # it tried
    audit = db.actuators.list_audit(pid)
    assert audit[-1].to_status == "failed"


def test_runner_raising_marks_failed(tmp_path) -> None:
    db = _db(tmp_path)
    host = PluginHost(default_timeout_seconds=1.0, enabled_capabilities={"actuator"})
    register_github_issue_actuator(host)
    fake = _FakeGh(raises=True)
    connector = build_github_issue_connector(runner=fake)

    pid = _propose(db, host)
    db.actuators.transition_proposal(pid, to_status="approved")
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(pid)
    assert result.status == "failed"
    assert "gh exploded" in (result.error or "")


# ──────────────────────── Default set unaffected ──────────────────────


def test_github_actuator_not_in_default_builtins() -> None:
    from holdspeak.plugins.builtin import register_builtin_plugins

    host = PluginHost(default_timeout_seconds=1.0)
    registered = register_builtin_plugins(host)
    assert ACTUATOR_ID not in registered  # gated/opt-in, never in the default set
