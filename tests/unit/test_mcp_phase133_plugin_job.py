"""Phase 133 plugin_job family tests: dispatch + refusal paths."""
from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.mcp import server, tools as mcp_tools
from holdspeak.mcp.server import handle_message
from holdspeak.mcp.families import plugin_job as pj_mod
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.errors import ConflictError, NotFound

OWNER = Principal(PrincipalKind.OWNER, "pj-test")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _stub_service(monkeypatch: pytest.MonkeyPatch) -> dict[str, list]:
    """Install a monkeypatched PluginJobService and return call records."""
    calls: dict[str, list] = {"list": [], "summary": [], "retry": [], "cancel": []}

    class StubPluginJobService:
        def __init__(self, db: Any = None, *, observer: Any = None) -> None:
            pass

        def list(self, principal: Any, status: str = "all",
                 meeting_id: str | None = None, limit: int = 200) -> dict[str, Any]:
            calls["list"].append({"status": status, "meeting_id": meeting_id, "limit": limit})
            return {"jobs": [{"id": 1, "status": status}]}

        def summary(self, principal: Any) -> dict[str, Any]:
            calls["summary"].append({})
            return {
                "total_jobs": 10, "queued_jobs": 3, "running_jobs": 1,
                "failed_jobs": 2, "queued_due_jobs": 1,
                "scheduled_retry_jobs": 0, "next_retry_at": None,
            }

        def retry(self, principal: Any, job_id: int) -> dict[str, Any]:
            calls["retry"].append({"job_id": job_id})
            return {"success": True, "job": {"id": job_id, "status": "queued"}}

        def cancel(self, principal: Any, job_id: int) -> dict[str, Any]:
            calls["cancel"].append({"job_id": job_id})
            return {"success": True}

    monkeypatch.setattr(pj_mod, "PluginJobService", StubPluginJobService)
    monkeypatch.setattr(pj_mod, "get_database", lambda: object())
    monkeypatch.setattr(pj_mod, "get_observer", lambda: None)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    return calls


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Send a tools/call message and return the result dict."""
    response = handle_message({
        "jsonrpc": "2.0", "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert response is not None
    return response["result"]


# ---------------------------------------------------------------------------
# Catalogue: all four tools appear with closed schemas
# ---------------------------------------------------------------------------

def test_plugin_job_tools_in_catalogue() -> None:
    """All four plugin_job.* tools appear in the catalogue with closed schemas."""
    response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response is not None
    tools = response["result"]["tools"]
    names = {t["name"] for t in tools}
    expected = {"plugin_job.list", "plugin_job.summary", "plugin_job.retry", "plugin_job.cancel"}
    assert expected <= names, f"Missing: {expected - names}"

    for t in tools:
        if t["name"] in expected:
            assert t["inputSchema"]["type"] == "object"
            assert t["inputSchema"]["additionalProperties"] is False


# ---------------------------------------------------------------------------
# Happy-path dispatch per tool
# ---------------------------------------------------------------------------

def test_plugin_job_list_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_service(monkeypatch)
    result = _call("plugin_job.list", {"status": "failed", "meeting_id": "m1", "limit": 50})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["jobs"] == [{"id": 1, "status": "failed"}]
    assert calls["list"] == [{"status": "failed", "meeting_id": "m1", "limit": 50}]


def test_plugin_job_list_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_service(monkeypatch)
    result = _call("plugin_job.list", {})
    assert result["isError"] is False
    assert calls["list"] == [{"status": "all", "meeting_id": None, "limit": 200}]


def test_plugin_job_summary_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_service(monkeypatch)
    result = _call("plugin_job.summary", {})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["total_jobs"] == 10
    assert calls["summary"] == [{}]


def test_plugin_job_retry_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_service(monkeypatch)
    result = _call("plugin_job.retry", {"job_id": 42})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["success"] is True
    assert payload["job"]["id"] == 42
    assert calls["retry"] == [{"job_id": 42}]


def test_plugin_job_cancel_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _stub_service(monkeypatch)
    result = _call("plugin_job.cancel", {"job_id": 7})
    assert result["isError"] is False
    payload = json.loads(result["content"][0]["text"])
    assert payload["success"] is True
    assert calls["cancel"] == [{"job_id": 7}]


# ---------------------------------------------------------------------------
# Refusal paths: retry/cancel against a running job => isError:true
# ---------------------------------------------------------------------------

def _stub_refusing_service(monkeypatch: pytest.MonkeyPatch, verb: str) -> None:
    """Install a service that raises ConflictError for the given verb."""

    class RefusingPluginJobService:
        def __init__(self, db: Any = None, *, observer: Any = None) -> None:
            pass

        def list(self, principal: Any, **kw: Any) -> dict[str, Any]:
            return {"jobs": []}

        def summary(self, principal: Any) -> dict[str, Any]:
            return {"total_jobs": 0, "queued_jobs": 0, "running_jobs": 0,
                    "failed_jobs": 0, "queued_due_jobs": 0,
                    "scheduled_retry_jobs": 0, "next_retry_at": None}

        def retry(self, principal: Any, job_id: int) -> dict[str, Any]:
            if verb == "retry":
                raise ConflictError("Cannot retry a running plugin job")
            return {"success": True, "job": {"id": job_id, "status": "queued"}}

        def cancel(self, principal: Any, job_id: int) -> dict[str, Any]:
            if verb == "cancel":
                raise ConflictError("Cannot cancel a running plugin job")
            return {"success": True}

    monkeypatch.setattr(pj_mod, "PluginJobService", RefusingPluginJobService)
    monkeypatch.setattr(pj_mod, "get_database", lambda: object())
    monkeypatch.setattr(pj_mod, "get_observer", lambda: None)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))


def test_retry_running_job_surfaces_isError(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_refusing_service(monkeypatch, "retry")
    result = _call("plugin_job.retry", {"job_id": 99})
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "running" in payload["error"].lower()


def test_cancel_running_job_surfaces_isError(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_refusing_service(monkeypatch, "cancel")
    result = _call("plugin_job.cancel", {"job_id": 99})
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "running" in payload["error"].lower()


# ---------------------------------------------------------------------------
# Refusal path: retry unknown job_id => isError:true
# ---------------------------------------------------------------------------

def test_retry_unknown_job_id_surfaces_isError(monkeypatch: pytest.MonkeyPatch) -> None:
    """Retry against a non-existent job_id surfaces NotFound as isError:true."""

    class NotFoundPluginJobService:
        def __init__(self, db: Any = None, *, observer: Any = None) -> None:
            pass

        def retry(self, principal: Any, job_id: int) -> dict[str, Any]:
            raise NotFound("plugin job", str(job_id))

    monkeypatch.setattr(pj_mod, "PluginJobService", NotFoundPluginJobService)
    monkeypatch.setattr(pj_mod, "get_database", lambda: object())
    monkeypatch.setattr(pj_mod, "get_observer", lambda: None)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

    result = _call("plugin_job.retry", {"job_id": 9999})
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "9999" in payload["error"]


# ---------------------------------------------------------------------------
# Validation: job_id must be an integer
# ---------------------------------------------------------------------------

def test_retry_missing_job_id_isError(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_service(monkeypatch)
    result = _call("plugin_job.retry", {})
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "integer" in payload["error"].lower()


def test_cancel_missing_job_id_isError(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_service(monkeypatch)
    result = _call("plugin_job.cancel", {})
    assert result["isError"] is True
    payload = json.loads(result["content"][0]["text"])
    assert "integer" in payload["error"].lower()
