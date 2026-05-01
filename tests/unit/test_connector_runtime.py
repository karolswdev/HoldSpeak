"""HS-13-02 — connector runtime permission gate tests.

`PermissionGate` is the in-process check that turns manifest
permissions from documentation into enforced contracts. Each
test here pins one (operation, permission) pair: a pack
declaring the right permission gets through; a pack that does
not gets a `PermissionDenied` with a reportable message.
"""

from __future__ import annotations

import subprocess

import pytest

from holdspeak.connector_runtime import (
    PermissionDenied,
    PermissionGate,
)
from holdspeak.connector_sdk import ConnectorManifest, validate_manifest


def _manifest(permissions: list[str], **overrides) -> ConnectorManifest:
    base = {
        "id": "evil_pack",
        "label": "Evil pack (test fixture)",
        "version": "0.1.0",
        "kind": "candidate_inference",
        "capabilities": ["candidates"],
        "permissions": permissions,
        "requires_network": any(p in {"network:outbound", "loopback:http"} for p in permissions),
    }
    base.update(overrides)
    return validate_manifest(base)


# ──────────────────────── shell:exec ────────────────────────


def test_run_subprocess_requires_shell_exec_permission():
    """A pack with no `shell:exec` permission must not be able
    to launch a subprocess via the gate, even if it provides a
    fake runner. The gate's check happens before the runner is
    consulted."""
    gate = PermissionGate(_manifest(["read:activity_records"]))

    called = False

    def fake_runner(*_args, **_kwargs):
        nonlocal called
        called = True
        return subprocess.CompletedProcess([], 0, stdout="", stderr="")

    with pytest.raises(PermissionDenied) as exc_info:
        gate.run_subprocess(["gh", "pr", "view"], runner=fake_runner)

    assert called is False
    assert exc_info.value.connector_id == "evil_pack"
    assert exc_info.value.operation == "run_subprocess"
    assert exc_info.value.required_permission == "shell:exec"
    # The message names the connector + missing permission so
    # operators reading `last_error` know exactly what failed.
    message = str(exc_info.value)
    assert "evil_pack" in message
    assert "shell:exec" in message


def test_run_subprocess_succeeds_when_permission_declared():
    """A pack declaring `shell:exec` (e.g. the gh / jira
    first-party packs) gets through to the underlying runner."""
    gate = PermissionGate(
        _manifest(
            ["shell:exec"],
            kind="cli_enrichment",
            requires_cli="echo",
            capabilities=["annotations", "commands"],
        )
    )

    received: list[list[str]] = []

    def fake_runner(command, **_kwargs):
        received.append(list(command))
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    completed = gate.run_subprocess(
        ["gh", "pr", "view", "1"],
        runner=fake_runner,
        check=False,
    )

    assert completed.returncode == 0
    assert received == [["gh", "pr", "view", "1"]]


# ─────────────────────── network:outbound ───────────────────


def test_open_outbound_socket_requires_network_outbound():
    gate = PermissionGate(_manifest(["read:activity_records"]))

    def fake_opener(_address):
        raise AssertionError("opener must not run when permission is missing")

    with pytest.raises(PermissionDenied) as exc_info:
        gate.open_outbound_socket(("example.com", 443), opener=fake_opener)

    assert exc_info.value.required_permission == "network:outbound"


def test_open_outbound_socket_succeeds_when_permission_declared():
    gate = PermissionGate(
        _manifest(
            ["network:outbound"],
            kind="cli_enrichment",
            requires_cli="curl",
            capabilities=["annotations"],
        )
    )

    sentinel = object()

    def fake_opener(_address):
        return sentinel

    assert gate.open_outbound_socket(("example.com", 443), opener=fake_opener) is sentinel


# ─────────────────────── loopback:http ──────────────────────


def test_accept_loopback_event_requires_loopback_http():
    gate = PermissionGate(_manifest(["read:activity_records"]))
    with pytest.raises(PermissionDenied) as exc_info:
        gate.accept_loopback_event()
    assert exc_info.value.required_permission == "loopback:http"


def test_accept_loopback_event_succeeds_when_permission_declared():
    """The first-party firefox_ext pack declares loopback:http.
    Running this gate against its real manifest must not raise
    — that's the contract the web endpoint relies on."""
    from holdspeak.connector_packs import firefox_ext

    gate = PermissionGate(firefox_ext.MANIFEST)
    gate.accept_loopback_event()  # no exception


# ────────────────────────── fs:read ─────────────────────────


def test_read_file_requires_fs_read():
    gate = PermissionGate(_manifest(["read:activity_records"]))

    def fake_opener(_path):
        raise AssertionError("opener must not run when permission is missing")

    with pytest.raises(PermissionDenied) as exc_info:
        gate.read_file("/tmp/anywhere", opener=fake_opener)

    assert exc_info.value.required_permission == "fs:read"


def test_read_file_succeeds_when_permission_declared(tmp_path):
    gate = PermissionGate(_manifest(["fs:read"]))

    target = tmp_path / "ok.txt"
    target.write_text("contents")

    received: list = []

    def fake_opener(path):
        received.append(path)
        return "contents"

    assert gate.read_file(target, opener=fake_opener) == "contents"
    assert received == [target]


# ───────────────────── error reportability ──────────────────


def test_permission_denied_is_persistable_as_last_error():
    """The exception's `str(...)` must be operator-readable so
    runners can write it directly into `connector.last_error`.
    The message names the connector, the operation, and the
    missing permission."""
    gate = PermissionGate(_manifest(["read:activity_records"]))
    with pytest.raises(PermissionDenied) as exc_info:
        gate.run_subprocess(["x"], runner=lambda *a, **k: None)

    rendered = str(exc_info.value)
    assert "'evil_pack'" in rendered
    assert "'run_subprocess'" in rendered
    assert "'shell:exec'" in rendered
    assert "read:activity_records" in rendered  # declared set is shown


# ───────────────── first-party honest packs ────────────────


def test_first_party_cli_packs_pass_run_subprocess_gate():
    """gh + jira packs already declare `shell:exec` in their
    manifests. The gate must let them through so the existing
    runner integration stays unchanged."""
    from holdspeak.connector_packs import github_cli, jira_cli

    captured: list[list[str]] = []

    def fake_runner(command, **_kwargs):
        captured.append(list(command))
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    PermissionGate(github_cli.MANIFEST).run_subprocess(
        ["gh", "pr", "view", "1"], runner=fake_runner
    )
    PermissionGate(jira_cli.MANIFEST).run_subprocess(
        ["jira", "issue", "view", "K"], runner=fake_runner
    )

    assert len(captured) == 2


def test_calendar_pack_has_no_shell_exec():
    """The calendar pack is pure inference — it must not
    declare `shell:exec`, and the gate must reject any
    subprocess attempt on its behalf."""
    from holdspeak.connector_packs import calendar_activity

    gate = PermissionGate(calendar_activity.MANIFEST)
    with pytest.raises(PermissionDenied):
        gate.run_subprocess(["echo", "x"], runner=lambda *a, **k: None)
