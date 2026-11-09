"""The gate, the principals and the kernel on the declared contract (2026-11-09).

A produced route with no principal is UNAUTHENTICATED (#2057), so every row in
``holdspeak/gate_operations.py`` carries its edge right and refuses a caller
without it before the service runs. These are properties over every row, not
a list of names.
"""
from __future__ import annotations

import re
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import operations
from holdspeak.gate_operations import GATE_OPERATIONS, KERNEL_OPERATIONS, RIGHTS, holders
from holdspeak.principals import UNAUTHENTICATED, Principal, PrincipalKind, required_right
from holdspeak.services.errors import ServiceError

ROWS = GATE_OPERATIONS + KERNEL_OPERATIONS
#: Arguments that pass each call's own checks before the service (the kernel decide's body rule).
ARGS: dict[str, dict[str, Any]] = {"kernel.decide": {"decision": "approve", "expected_revision": 1}}


def _path(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "x", path)


class _Recorder:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def __getattr__(self, name: str) -> Any:
        def run(*_a: Any, **_k: Any) -> Any:
            self.calls.append(name)
            return {}
        return run


def _registry(target: Any) -> operations.OperationRegistry:
    return operations.bind({"gate_service": target, "kernel_service": target}, ROWS)


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_every_row_carries_its_edge_right(row: Any) -> None:
    right = required_right(row.http[0], _path(row.http[1]))
    assert right is not None and RIGHTS[row.name] is right, (row.name, right)
    assert right.value in row.principal and "UNAUTHENTICATED" in row.principal
    assert row.owner_only is (holders(right) == ("owner",)), row.name
    assert ("owner_required" in row.refusals) is row.owner_only


@pytest.mark.parametrize("row", ROWS, ids=lambda row: row.name)
def test_a_caller_without_the_right_never_reaches_the_service(row: Any) -> None:
    target = _Recorder()
    registry = _registry(target)
    right = RIGHTS[row.name]
    refused = [None, UNAUTHENTICATED] + [Principal(kind, "k") for kind in PrincipalKind
                                          if not Principal(kind, "k").permits(right)]
    for principal in refused:
        with pytest.raises(ServiceError) as caught:
            registry.invoke(principal, row.name, dict(ARGS.get(row.name, {})))
        assert caught.value.code in {"owner_required", "principal_right_required"}, (row.name, principal)
    assert target.calls == []
    for kind in (kind for kind in PrincipalKind if Principal(kind, "k").permits(right)):
        registry.invoke(Principal(kind, "k"), row.name, dict(ARGS.get(row.name, {})))
    assert target.calls and set(target.calls) == {row.method}, (row.name, target.calls)


def test_threads_never_offer_a_write_and_a_decide_is_the_owners_word() -> None:
    from holdspeak.mcp.tool_authority import THREAD_EXCLUDED

    for row in ROWS:
        if row.tool_schema is not None and row.effect == "write":
            assert row.tool_name in THREAD_EXCLUDED, row.name
    for name in ("gate.decide", "kernel.decide", "principals.agent.revoke", "principals.agent.issue"):
        row = next(r for r in ROWS if r.name == name)
        assert row.owner_only and row.owner_press, name
    # The whole held call, a credential and the node link never reach a model.
    no_tool = {r.name for r in ROWS if r.tool_schema is None}
    assert no_tool == {"gate.full_call", "principals.agent.issue", "kernel.executor.claim",
                       "kernel.executor.receipt", "kernel.executor.reconcile"}


def test_the_issued_credential_is_not_in_the_pipeline_log() -> None:
    from holdspeak.services.observer import WITHHELD, _summarize_result

    assert WITHHELD in _summarize_result("GateService", "issue_agent", {"credential": "secret-token"})


def test_a_produced_route_with_no_principal_is_refused(tmp_path) -> None:
    from holdspeak.db import Database
    from holdspeak.services.gate_service import GateService
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.system.gate_routes import build_gate_router
    from holdspeak.web.routes.system.kernel_routes import build_kernel_router

    app = FastAPI()  # no edge: no request.state.principal
    app.include_router(build_gate_router(WebContext(get_state=lambda: {}, gate_service=GateService(
        Database(tmp_path / "gate.db")))))
    app.include_router(build_kernel_router())
    client = TestClient(app)
    for method, path in [r.http for r in ROWS]:
        response = client.request(method, _path(path), json={"identity": "a"} if path == "/api/principals/agents" else {})
        assert response.status_code == 403, (method, path, response.text)
        assert response.json()["error"] in {"owner_required", "principal_right_required"}, (path, response.text)
