"""HS-38-01 — gated write-connector framework + permission manifest.

The manifest is the *narrowest* gate: it declares exactly which concrete
operations a write connector may perform, and `build_gated_connector` refuses
anything else **before** any egress. These tests assert that contract with a
fake gate / fake runner / fake opener (the default suite makes no real outbound
call), then drive a gated connector through the real `ActuatorExecutor` to prove
the integration: `executed` on a permitted op, `failed` (no egress) on a refused
one.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.connector_runtime import PermissionDenied, PermissionGate
from holdspeak.connector_sdk import ConnectorManifest
from holdspeak.db import Database
from holdspeak.meeting_session import MeetingState
from holdspeak.plugins.actuator_executor import ActuatorExecutor
from holdspeak.plugins.actuators import ActuatorProposal
from holdspeak.plugins.gated_connector import (
    ConnectorOperationRefused,
    GatedOperation,
    WriteConnectorManifest,
    build_gated_connector,
)

# ──────────────────────────── Fakes ───────────────────────────────────


class _SpyGate:
    """A stand-in for `PermissionGate` that records whether egress was reached.

    Used to prove a refused op never touches the gate. On the permitted path it
    delegates to the injected runner / opener so the result still flows through.
    """

    def __init__(self) -> None:
        self.subprocess_calls: list[tuple[str, ...]] = []
        self.socket_calls: list[tuple[str, int]] = []

    def run_subprocess(self, command, *, runner=None, **kwargs):
        self.subprocess_calls.append(tuple(command))
        return runner(list(command), **kwargs) if runner else None

    def open_outbound_socket(self, address, *, opener=None):
        self.socket_calls.append(address)
        return opener(address) if opener else None


class _FakeRunner:
    """Records argv and returns a canned 'completed process' stand-in."""

    def __init__(self, *, returncode: int = 0, stdout: str = "ok") -> None:
        self.calls: list[list[str]] = []
        self._returncode = returncode
        self._stdout = stdout

    def __call__(self, argv, **kwargs):
        self.calls.append(list(argv))
        return {"returncode": self._returncode, "stdout": self._stdout}


# A CLI manifest: may only run `gh issue create …`.
_CLI_MANIFEST = WriteConnectorManifest(
    connector_id="gh_writer",
    permission="shell:exec",
    allowed_argv_prefixes=(("gh", "issue", "create"),),
)

# A webhook manifest: may only POST to hooks.example.test.
_WEBHOOK_MANIFEST = WriteConnectorManifest(
    connector_id="hook_writer",
    permission="network:outbound",
    allowed_hosts=("hooks.example.test",),
)


def _proposal(**payload) -> ActuatorProposal:
    return ActuatorProposal(
        target="github",
        action="create_issue",
        preview="Open a follow-up issue",
        payload=dict(payload),
    )


# ──────────────────────── Manifest validation ─────────────────────────


def test_manifest_rejects_non_write_permission() -> None:
    with pytest.raises(ValueError, match="permission must be one of"):
        WriteConnectorManifest(connector_id="x", permission="fs:read")


def test_manifest_operation_maps_permission_to_gate_op() -> None:
    assert _CLI_MANIFEST.operation == "run_subprocess"
    assert _WEBHOOK_MANIFEST.operation == "open_outbound_socket"


# ──────────────────────── Allow-check (manifest) ──────────────────────


def test_cli_manifest_allows_declared_prefix_only() -> None:
    assert _CLI_MANIFEST.allows(
        GatedOperation.subprocess(["gh", "issue", "create", "--title", "T"])
    )
    # A mutating sibling verb is not declared → refused.
    assert not _CLI_MANIFEST.allows(GatedOperation.subprocess(["gh", "issue", "close", "1"]))
    # A different binary entirely → refused.
    assert not _CLI_MANIFEST.allows(GatedOperation.subprocess(["rm", "-rf", "/"]))
    # An outbound op against a shell:exec manifest → refused (kind mismatch).
    assert not _CLI_MANIFEST.allows(GatedOperation.outbound("hooks.example.test", 443))


def test_webhook_manifest_allows_listed_host_only() -> None:
    assert _WEBHOOK_MANIFEST.allows(GatedOperation.outbound("hooks.example.test", 443))
    # Case-insensitive host match (DNS is case-insensitive).
    assert _WEBHOOK_MANIFEST.allows(GatedOperation.outbound("Hooks.Example.Test", 443))
    # An off-list host → refused.
    assert not _WEBHOOK_MANIFEST.allows(GatedOperation.outbound("evil.example.test", 443))
    # A subprocess op against a network:outbound manifest → refused.
    assert not _WEBHOOK_MANIFEST.allows(GatedOperation.subprocess(["gh", "issue", "create"]))


def test_empty_allow_list_admits_nothing() -> None:
    empty = WriteConnectorManifest(connector_id="noop", permission="shell:exec")
    assert not empty.allows(GatedOperation.subprocess(["gh", "issue", "create"]))


# ──────────────────────── build_gated_connector: permit ───────────────


def test_permitted_subprocess_routes_through_gate() -> None:
    runner = _FakeRunner(stdout="created #7")
    gate = _CLI_MANIFEST.build_gate()  # a real gate admitting shell:exec

    def plan(proposal):
        title = proposal.payload["title"]
        return GatedOperation.subprocess(["gh", "issue", "create", "--title", title])

    def interpret(raw, op):
        return {"stdout": raw["stdout"], "argv": list(op.argv)}

    connector = build_gated_connector(
        _CLI_MANIFEST, plan=plan, interpret=interpret, gate=gate, runner=runner
    )

    result = connector(_proposal(title="Ship it"))

    assert result == {
        "stdout": "created #7",
        "argv": ["gh", "issue", "create", "--title", "Ship it"],
    }
    assert runner.calls == [["gh", "issue", "create", "--title", "Ship it"]]


def test_permitted_outbound_routes_through_gate_with_request() -> None:
    sent: list[GatedOperation] = []

    def opener(op):  # the injected HTTP client — receives the full op
        sent.append(op)
        return {"status": 200}

    def plan(proposal):
        return GatedOperation.outbound(
            "hooks.example.test", 443, request={"text": proposal.payload["text"]}
        )

    def interpret(raw, op):
        return {"status": raw["status"], "host": op.host}

    connector = build_gated_connector(
        _WEBHOOK_MANIFEST, plan=plan, interpret=interpret, opener=opener
    )

    result = connector(_proposal(text="hello"))

    assert result == {"status": 200, "host": "hooks.example.test"}
    assert len(sent) == 1
    assert sent[0].request == {"text": "hello"}


# ──────────────────────── build_gated_connector: refuse ───────────────


def test_refused_op_raises_before_gate_is_touched() -> None:
    spy = _SpyGate()
    runner = _FakeRunner()

    def plan(proposal):
        # A verb the manifest does not declare.
        return GatedOperation.subprocess(["gh", "issue", "close", "1"])

    connector = build_gated_connector(
        _CLI_MANIFEST,
        plan=plan,
        interpret=lambda raw, op: {"unreached": True},
        gate=spy,
        runner=runner,
    )

    with pytest.raises(ConnectorOperationRefused) as exc:
        connector(_proposal())

    assert exc.value.connector_id == "gh_writer"
    assert "gh issue close" in str(exc.value)
    # The gate was never reached → no egress, no runner call.
    assert spy.subprocess_calls == []
    assert runner.calls == []


def test_refused_outbound_host_raises_before_socket() -> None:
    spy = _SpyGate()
    opened: list[GatedOperation] = []

    def plan(proposal):
        return GatedOperation.outbound("evil.example.test", 443, request={"x": 1})

    connector = build_gated_connector(
        _WEBHOOK_MANIFEST,
        plan=plan,
        interpret=lambda raw, op: {"unreached": True},
        gate=spy,
        opener=lambda op: opened.append(op),
    )

    with pytest.raises(ConnectorOperationRefused):
        connector(_proposal())

    assert spy.socket_calls == []
    assert opened == []


# ──────────────────────── Gate layer is real ──────────────────────────


def test_gate_permission_is_enforced_under_the_manifest() -> None:
    """The synthesized gate genuinely enforces the permission — inject a gate
    built from a manifest WITHOUT shell:exec and the permitted-looking op still
    raises PermissionDenied at the gate."""
    wrong = ConnectorManifest(
        id="gh_writer",
        label="gh",
        version="0.0.0",
        kind="cli_enrichment",
        capabilities=("commands",),
        permissions=(),  # no shell:exec
    )
    connector = build_gated_connector(
        _CLI_MANIFEST,
        plan=lambda p: GatedOperation.subprocess(["gh", "issue", "create", "--title", "T"]),
        interpret=lambda raw, op: {"ok": True},
        gate=PermissionGate(wrong),
        runner=_FakeRunner(),
    )
    with pytest.raises(PermissionDenied):
        connector(_proposal(title="T"))


# ──────────────────────── ActuatorExecutor integration ────────────────


def _db(tmp_path) -> Database:
    db = Database(tmp_path / "gated.db")
    db.meetings.save_meeting(
        MeetingState(id="m1", started_at=datetime.now(), title="t", segments=[])
    )
    return db


def _approved(db: Database, *, payload):
    p = db.actuators.record_proposal(
        meeting_id="m1",
        window_id="w1",
        plugin_id="gh_writer",
        plugin_version="1.0.0",
        idempotency_key="k1",
        target="github",
        action="create_issue",
        preview="Open a follow-up issue",
        payload=payload,
        reversible=True,
        required_capabilities=["actuator"],
    )
    return db.actuators.transition_proposal(p.id, to_status="approved", actor="karol")


def test_executor_executes_permitted_gated_connector(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db, payload={"title": "Follow up"})
    runner = _FakeRunner(stdout="https://github.test/acme/app/issues/9")

    connector = build_gated_connector(
        _CLI_MANIFEST,
        plan=lambda p: GatedOperation.subprocess(
            ["gh", "issue", "create", "--title", p.payload["title"]]
        ),
        interpret=lambda raw, op: {"url": raw["stdout"]},
        gate=_CLI_MANIFEST.build_gate(),
        runner=runner,
    )
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(proposal.id)

    assert result.status == "executed"
    assert result.result == {"url": "https://github.test/acme/app/issues/9"}
    assert runner.calls == [["gh", "issue", "create", "--title", "Follow up"]]
    audit = db.actuators.list_audit(proposal.id)
    assert audit[-1].to_status == "executed"


def test_executor_marks_failed_on_refused_op_no_egress(tmp_path) -> None:
    db = _db(tmp_path)
    proposal = _approved(db, payload={"title": "Follow up"})
    spy = _SpyGate()
    runner = _FakeRunner()

    connector = build_gated_connector(
        _CLI_MANIFEST,
        # Plan an op the manifest does not admit.
        plan=lambda p: GatedOperation.subprocess(["gh", "issue", "delete", "1"]),
        interpret=lambda raw, op: {"unreached": True},
        gate=spy,
        runner=runner,
    )
    executor = ActuatorExecutor(db, connector=connector, allow_actuators=True)

    result = executor.execute(proposal.id)

    assert result.status == "failed"  # refusal surfaced as a connector failure
    assert "ConnectorOperationRefused" in (result.error or "")
    assert spy.subprocess_calls == []  # no egress
    assert runner.calls == []
    audit = db.actuators.list_audit(proposal.id)
    assert audit[-1].to_status == "failed"
    # Retryable: failed -> approved is still a legal transition.
    assert db.actuators.transition_proposal(proposal.id, to_status="approved").status == "approved"
