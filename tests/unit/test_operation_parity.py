"""The census separates missing ports from shells and declared HTTP callbacks."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

spec = importlib.util.spec_from_file_location("operation_parity", Path(__file__).parents[2] / "scripts/operation_parity.py")
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)


def shell() -> HTMLResponse:
    return HTMLResponse("<html></html>")


def test_route_kind_reads_the_response_and_protocol_not_path_names() -> None:
    app = FastAPI(openapi_url="/reference/schema", docs_url="/reference/ui", redoc_url=None)

    @app.get("/api/looks-like-a-capability")
    def page():
        return shell()

    @app.get("/docs/looks-like-a-page")
    def data():
        return {"ok": True}

    @app.websocket("/anything")
    async def socket(websocket):
        await websocket.accept()

    kinds = {route.path: parity.route_kind(route, app) for route in app.routes}
    assert kinds["/api/looks-like-a-capability"] == "page"
    assert kinds["/docs/looks-like-a-page"] == "API"
    assert kinds["/anything"] == "socket"
    assert kinds["/reference/schema"] == kinds["/reference/ui"] == "docs"


def test_http_only_rows_are_derived_from_the_registered_descriptors() -> None:
    from holdspeak.operations import DESCRIPTORS

    parity._load_descriptors()
    assert parity.DESCRIPTORS == {d.name: (parity._norm(d.service) or d.service, d.method) for d in DESCRIPTORS}
    assert ("setup_service", "scan_lan") not in parity.HTTP_ONLY  # its tool is produced
    for operation in (("system_service", "runtime_status"), ("onboarding_service", "agents_use"),
                      ("walk_service", "known")):
        assert all(name in parity.DESCRIPTORS and reason for name, reason in parity.HTTP_ONLY[operation])


def test_head_separates_api_bypasses_undeclared_calls_and_http_only(monkeypatch, capsys) -> None:
    monkeypatch.setattr(parity, "_load_descriptors", lambda: None)
    monkeypatch.setattr(parity, "HTTP_ONLY", {("callback_service", "read"): [("callback.read", "Device callback.")]})
    monkeypatch.setattr(parity, "RESOURCE_OPS", set())
    rows = [("GET", "/api/raw", set()), ("GET", "/a-page", set()), ("WS", "/socket", set()),
            ("GET", "/schema", set()), ("GET", "/api/callback", {("callback_service", "read")}),
            ("POST", "/api/missing", {("missing_service", "run")})]
    monkeypatch.setattr(parity, "ROUTE_KINDS", {
        (m, p): k for (m, p, _o), k in zip(rows, ["API", "page", "socket", "docs", "API", "API"])})
    monkeypatch.setattr(parity, "web_routes", lambda: rows)
    monkeypatch.setattr(parity, "mcp_tools", dict)
    monkeypatch.setattr(parity, "cli_ops", lambda _routes: set())
    assert parity.main() == 0
    output = capsys.readouterr().out
    assert "API routes that bypass a service: 1" in output
    assert "web-only operations NOT declared HTTP-only: 1" in output
    assert "operations declared HTTP-only by their row: 1" in output
    assert "pages, docs and sockets (not capabilities): 3" in output
    assert "`callback.read`: Device callback." in output
    undeclared = output.split("## Web-only operations without an HTTP-only declaration")[1].split("## Declared")[0]
    assert "missing_service" in undeclared and "callback_service" not in undeclared
