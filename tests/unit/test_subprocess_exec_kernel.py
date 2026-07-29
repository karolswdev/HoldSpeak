from __future__ import annotations

import inspect
import subprocess

import pytest

import holdspeak.db.core as db_core
from holdspeak.connector_runtime import PermissionGate, ReadSubprocessDenied
from holdspeak.connector_sdk import ConnectorManifest
from holdspeak.db import Database
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.kernel.subprocess_exec import (
    EXECUTIONS,
    LOCAL_OWNER,
    SubprocessOutcomeIndeterminate,
    run_subprocess_operation,
)
from holdspeak.plugins import gated_connector
from holdspeak.principals import Principal, PrincipalKind


def _manifest() -> ConnectorManifest:
    return ConnectorManifest(
        id="proof_connector",
        label="Proof connector",
        version="1.0.0",
        kind="cli_enrichment",
        capabilities=("commands",),
        permissions=("shell:exec",),
    )


@pytest.fixture
def broker(tmp_path, monkeypatch):
    db = Database(tmp_path / "subprocess-kernel.db")
    monkeypatch.setattr(db_core, "_db", db)
    EXECUTIONS._plans.clear()
    EXECUTIONS._operation_ids.clear()
    EXECUTIONS._results.clear()
    return kernel_runtime._configure(db)


def _latest_full(broker):
    result = list(EXECUTIONS._results.values())[-1]
    return broker.read(
        [f"operation:{result['operation_id']}"], "full", "committed", LOCAL_OWNER
    )["objects"][0]


def test_success_and_nonzero_are_distinct_process_outcomes(broker) -> None:
    zero = subprocess.CompletedProcess(["printf", "ok"], 0, stdout="ok", stderr="")
    run_subprocess_operation(
        zero.args,
        connector_id="proof_connector",
        declared_permissions=("shell:exec",),
        runner=lambda *_a, **_k: zero,
        broker=broker,
        capture_output=True,
        text=True,
    )
    success = _latest_full(broker)
    assert success["receipt"]["outcome"] == "succeeded"
    assert success["native_receipts"] == [
        {
            "receipt_ref": success["receipt"]["result_ref"],
            "native_id": success["canonical"]["native_id"],
            "binary": "printf",
            "argv": ["printf", "ok"],
            "cwd": success["canonical"]["cwd"],
            "operation_outcome": "succeeded",
            "process_outcome": "exited_zero",
            "returncode": 0,
        }
    ]

    nonzero = subprocess.CompletedProcess(["sh", "-c", "exit 7"], 7, stdout="", stderr="")
    run_subprocess_operation(
        nonzero.args,
        connector_id="proof_connector",
        declared_permissions=("shell:exec",),
        runner=lambda *_a, **_k: nonzero,
        broker=broker,
    )
    failed_child = _latest_full(broker)
    assert failed_child["receipt"]["outcome"] == "succeeded"
    assert failed_child["native_receipts"][0]["process_outcome"] == "nonzero_exit"
    assert failed_child["native_receipts"][0]["returncode"] == 7


def test_indeterminate_is_receipted_once_and_never_retried(broker) -> None:
    calls = 0

    def killed(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise subprocess.TimeoutExpired(["sleep", "30"], 0.01)

    with pytest.raises(SubprocessOutcomeIndeterminate) as caught:
        run_subprocess_operation(
            ["sleep", "30"],
            connector_id="proof_connector",
            declared_permissions=("shell:exec",),
            runner=killed,
            broker=broker,
        )
    full = broker.read(
        [f"operation:{caught.value.operation_id}"], "full", "committed", LOCAL_OWNER
    )["objects"][0]
    assert calls == 1
    assert full["receipt"]["outcome"] == "indeterminate"
    assert full["native_receipts"][0]["process_outcome"] == "indeterminate"


def test_argv_and_cwd_cannot_change_at_decision(broker, tmp_path) -> None:
    source = ["printf", "owner-approved"]
    seen: list[tuple[list[str], str]] = []

    class MutatingDecisionBroker:
        def submit(self, *args, **kwargs):
            return broker.submit(*args, **kwargs)

        def decide(self, *args, **kwargs):
            source[:] = ["rm", "-rf", "/"]
            return broker.decide(*args, **kwargs)

        def claim(self, *args, **kwargs):
            return broker.claim(*args, **kwargs)

        def receipt(self, *args, **kwargs):
            return broker.receipt(*args, **kwargs)

    def runner(argv, **kwargs):
        seen.append((list(argv), kwargs["cwd"]))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    run_subprocess_operation(
        source,
        connector_id="proof_connector",
        declared_permissions=("shell:exec",),
        runner=runner,
        broker=MutatingDecisionBroker(),
        cwd=tmp_path,
    )
    full = _latest_full(broker)
    assert source == ["rm", "-rf", "/"]
    assert seen == [(["printf", "owner-approved"], str(tmp_path.resolve()))]
    assert full["canonical"]["argv"] == ["printf", "owner-approved"]
    assert full["canonical"]["cwd"] == str(tmp_path.resolve())


def test_agent_is_refused_named_gh_read_authority() -> None:
    called = False

    def runner(*_args, **_kwargs):
        nonlocal called
        called = True

    agent = Principal(PrincipalKind.AGENT, "agent:untrusted")
    with pytest.raises(ReadSubprocessDenied) as caught:
        PermissionGate(_manifest()).run_read_subprocess(
            ["gh", "pr", "view", "1"], principal=agent, runner=runner
        )
    assert caught.value.command_name == "gh"
    assert "read authority for 'gh'" in str(caught.value)
    assert not called


def test_mixed_sites_have_one_kernel_decision_and_no_legacy_policy_call(broker) -> None:
    decisions = 0

    class CountingBroker:
        def submit(self, *args, **kwargs):
            return broker.submit(*args, **kwargs)

        def decide(self, *args, **kwargs):
            nonlocal decisions
            decisions += 1
            return broker.decide(*args, **kwargs)

        def claim(self, *args, **kwargs):
            return broker.claim(*args, **kwargs)

        def receipt(self, *args, **kwargs):
            return broker.receipt(*args, **kwargs)

    completed = subprocess.CompletedProcess(["true"], 0, stdout="", stderr="")
    run_subprocess_operation(
        ["true"],
        connector_id="proof_connector",
        declared_permissions=("shell:exec",),
        allowed_argv_prefixes=(("true",),),
        runner=lambda *_a, **_k: completed,
        broker=CountingBroker(),
    )
    assert decisions == 1

    permission_source = inspect.getsource(PermissionGate.execute_subprocess)
    route_source = inspect.getsource(gated_connector._route)
    connector_source = inspect.getsource(gated_connector.build_gated_connector)
    assert "_require(" not in permission_source
    assert permission_source.count("run_subprocess_operation(") == 1
    assert route_source.count("execute_subprocess(") == 1
    assert "manifest.allows(op)" not in connector_source
