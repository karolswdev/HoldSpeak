"""Phase 133 sequence/workflow family tests: dispatch, _run wrapping, cancel routing, error paths."""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.mcp import server
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.families import sequence as seq_mod
from holdspeak.mcp.server import handle_message
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ServiceError

OWNER = Principal(PrincipalKind.OWNER, "sequence-test")


def _call(monkeypatch: pytest.MonkeyPatch, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Send a tools/call through handle_message and return the full result dict."""
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    response = handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert response is not None
    return response["result"]


def _patch_runtime(monkeypatch: pytest.MonkeyPatch, broker: Any) -> None:
    """Patch get_database, get_observer, and _configure at their source modules."""
    monkeypatch.setattr(seq_mod, "get_database", lambda: object())
    monkeypatch.setattr(seq_mod, "get_observer", lambda: None)
    # _configure is imported inside dispatch from holdspeak.kernel.runtime
    monkeypatch.setattr("holdspeak.kernel.runtime._configure", lambda db: broker)


# ---------- sequence.run: _run wrapping + service dispatch ----------

class _FakeSequenceService:
    """Stub that records run_sequence calls and returns a canned result."""
    def __init__(self, db: Any, broker: Any) -> None:
        self.db = db
        self.broker = broker

    async def run_sequence(self, principal: Any, chain_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {
            "parent_operation_id": "op-seq-1",
            "chain_id": chain_id,
            "output": "seq-result",
            "receipt_id": "r-1",
            "steps": [{"recipe_id": "agent-a", "output": "seq-result"}],
            "sources": [{"source_type": "chain", "source_ref": chain_id}],
        }


def test_sequence_run_dispatches_through_run_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    """sequence.run wraps the async coroutine in _run() and returns the service result."""
    fake_broker = object()
    _patch_runtime(monkeypatch, fake_broker)
    # Patch SequenceWorkflowService at its source so the local import grabs the stub.
    monkeypatch.setattr(
        "holdspeak.services.sequence_workflow_service.SequenceWorkflowService",
        _FakeSequenceService,
    )

    result = _call(monkeypatch, "sequence.run", {"chain_id": "chain-abc", "input": "hello"})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["chain_id"] == "chain-abc"
    assert payload["output"] == "seq-result"
    assert payload["steps"][0]["recipe_id"] == "agent-a"


# ---------- workflow.run: _run wrapping + service dispatch ----------

class _FakeWorkflowService:
    """Stub that records run_workflow calls and returns a canned result."""
    def __init__(self, db: Any, broker: Any) -> None:
        self.db = db
        self.broker = broker

    async def run_workflow(self, principal: Any, workflow_id: str, body: dict[str, Any]) -> dict[str, Any]:
        return {
            "parent_operation_id": "op-wf-1",
            "workflow_id": workflow_id,
            "output": "wf-result",
            "receipt_id": "r-2",
            "steps": [{"node_id": "n1", "output": "wf-result"}],
            "sources": [{"source_type": "workflow", "source_ref": workflow_id}],
        }


def test_workflow_run_dispatches_through_run_wrapper(monkeypatch: pytest.MonkeyPatch) -> None:
    """workflow.run wraps the async coroutine in _run() and returns the service result."""
    fake_broker = object()
    _patch_runtime(monkeypatch, fake_broker)
    monkeypatch.setattr(
        "holdspeak.services.sequence_workflow_service.SequenceWorkflowService",
        _FakeWorkflowService,
    )

    result = _call(monkeypatch, "workflow.run", {"workflow_id": "wf-xyz", "input": "go"})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["workflow_id"] == "wf-xyz"
    assert payload["output"] == "wf-result"
    assert payload["steps"][0]["node_id"] == "n1"


# ---------- sequence.cancel: broker routing ----------

def test_sequence_cancel_routes_through_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    """sequence.cancel dispatches to broker.parent_run_controller.cancel_by_operation_id."""
    cancel_calls: list[tuple[Any, str]] = []

    def _fake_cancel(principal: Any, op_id: str) -> str:
        cancel_calls.append((principal, op_id))
        return "cancelled"

    fake_controller = SimpleNamespace(cancel_by_operation_id=_fake_cancel)
    fake_broker = SimpleNamespace(parent_run_controller=fake_controller)
    _patch_runtime(monkeypatch, fake_broker)

    result = _call(monkeypatch, "sequence.cancel", {"parent_operation_id": "op-seq-99"})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["parent_operation_id"] == "op-seq-99"
    assert payload["disposition"] == "cancelled"
    assert len(cancel_calls) == 1
    assert cancel_calls[0][1] == "op-seq-99"


# ---------- workflow.cancel: broker routing ----------

def test_workflow_cancel_routes_through_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    """workflow.cancel dispatches to broker.parent_run_controller.cancel_by_operation_id."""
    cancel_calls: list[tuple[Any, str]] = []

    def _fake_cancel(principal: Any, op_id: str) -> str:
        cancel_calls.append((principal, op_id))
        return "cancelled"

    fake_controller = SimpleNamespace(cancel_by_operation_id=_fake_cancel)
    fake_broker = SimpleNamespace(parent_run_controller=fake_controller)
    _patch_runtime(monkeypatch, fake_broker)

    result = _call(monkeypatch, "workflow.cancel", {"parent_operation_id": "op-wf-77"})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["parent_operation_id"] == "op-wf-77"
    assert payload["disposition"] == "cancelled"
    assert len(cancel_calls) == 1
    assert cancel_calls[0][1] == "op-wf-77"


# ---------- Error paths: unknown IDs -> isError:true through handle_message ----------

def test_sequence_run_unknown_chain_id_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """sequence.run with a chain_id the service does not know surfaces isError:true."""
    class _NotFoundService:
        def __init__(self, db: Any, broker: Any) -> None:
            pass
        async def run_sequence(self, principal: Any, chain_id: str, body: dict[str, Any]) -> dict[str, Any]:
            raise ServiceError("not_found", f"Unknown Sequence: {chain_id}", context={"status": 404})

    fake_broker = object()
    _patch_runtime(monkeypatch, fake_broker)
    monkeypatch.setattr(
        "holdspeak.services.sequence_workflow_service.SequenceWorkflowService",
        _NotFoundService,
    )

    result = _call(monkeypatch, "sequence.run", {"chain_id": "no-such-chain"})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "Unknown Sequence" in error_text


def test_workflow_run_unknown_workflow_id_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """workflow.run with a workflow_id the service does not know surfaces isError:true."""
    class _NotFoundService:
        def __init__(self, db: Any, broker: Any) -> None:
            pass
        async def run_workflow(self, principal: Any, workflow_id: str, body: dict[str, Any]) -> dict[str, Any]:
            raise ServiceError("not_found", f"Unknown workflow: {workflow_id}", context={"status": 404})

    fake_broker = object()
    _patch_runtime(monkeypatch, fake_broker)
    monkeypatch.setattr(
        "holdspeak.services.sequence_workflow_service.SequenceWorkflowService",
        _NotFoundService,
    )

    result = _call(monkeypatch, "workflow.run", {"workflow_id": "no-such-wf"})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "Unknown workflow" in error_text


def test_sequence_cancel_unknown_parent_op_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """sequence.cancel with unknown parent_operation_id surfaces isError:true."""
    def _fail_cancel(principal: Any, op_id: str) -> str:
        raise ValueError(f"Unknown parent operation: {op_id}")

    fake_controller = SimpleNamespace(cancel_by_operation_id=_fail_cancel)
    fake_broker = SimpleNamespace(parent_run_controller=fake_controller)
    _patch_runtime(monkeypatch, fake_broker)

    result = _call(monkeypatch, "sequence.cancel", {"parent_operation_id": "op-nope"})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "Unknown parent operation" in error_text


def test_workflow_cancel_unknown_parent_op_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """workflow.cancel with unknown parent_operation_id surfaces isError:true."""
    def _fail_cancel(principal: Any, op_id: str) -> str:
        raise ValueError(f"Unknown parent operation: {op_id}")

    fake_controller = SimpleNamespace(cancel_by_operation_id=_fail_cancel)
    fake_broker = SimpleNamespace(parent_run_controller=fake_controller)
    _patch_runtime(monkeypatch, fake_broker)

    result = _call(monkeypatch, "workflow.cancel", {"parent_operation_id": "op-nope"})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "Unknown parent operation" in error_text


# ---------- Validation: missing required fields ----------

def test_sequence_run_missing_chain_id_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """sequence.run without chain_id raises ValueError -> isError:true."""
    result = _call(monkeypatch, "sequence.run", {})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "chain_id" in error_text


def test_workflow_run_missing_workflow_id_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """workflow.run without workflow_id raises ValueError -> isError:true."""
    result = _call(monkeypatch, "workflow.run", {})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "workflow_id" in error_text


def test_sequence_cancel_missing_parent_op_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """sequence.cancel without parent_operation_id raises ValueError -> isError:true."""
    result = _call(monkeypatch, "sequence.cancel", {})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "parent_operation_id" in error_text


def test_workflow_cancel_missing_parent_op_returns_is_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """workflow.cancel without parent_operation_id raises ValueError -> isError:true."""
    result = _call(monkeypatch, "workflow.cancel", {})
    assert result["isError"] is True
    error_text = json.loads(result["content"][0]["text"])["error"]
    assert "parent_operation_id" in error_text
