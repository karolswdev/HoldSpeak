"""Phase 133 cadence family tests: dispatch, error paths, resource read."""
from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest

from holdspeak.mcp import resources as resources_mod
from holdspeak.mcp import server
from holdspeak.mcp import tools as mcp_tools
from holdspeak.mcp.families import cadence as cadence_mod
from holdspeak.mcp.server import handle_message
from holdspeak.principals import Principal, PrincipalKind

OWNER = Principal(PrincipalKind.OWNER, "cadence-test")


# ---------------------------------------------------------------------------
# Fake CadenceService for monkeypatching
# ---------------------------------------------------------------------------

class FakeCadenceService:
    """Stub that records calls and returns canned data."""

    def __init__(self, db: Any = None, config: Any = None, kernel: Any = None, *, observer: Any = None) -> None:
        self._db = db
        self._config = config
        self._calls: list[tuple[str, tuple, dict]] = []

    def _record(self, name: str, *args: Any, **kwargs: Any) -> None:
        self._calls[:]  # keep list accessible
        self._calls.append((name, args, kwargs))

    def status(self, principal: Any) -> dict[str, Any]:
        self._record("status", principal)
        return {"enabled": True, "pressure": "normal", "counts": {"open": 3}, "egress": {"cloud": False}}

    def list_loops(self, principal: Any, *, include_terminal: bool = False) -> dict[str, Any]:
        self._record("list_loops", principal, include_terminal=include_terminal)
        return {"loops": [{"id": "loop-1", "status": "open"}], "egress": {"cloud": False}}

    async def get_loop(self, principal: Any, loop_id: str) -> dict[str, Any]:
        self._record("get_loop", principal, loop_id)
        return {"id": loop_id, "status": "open", "next_action": {"kind": "nudge"}}

    def brief(self, principal: Any) -> dict[str, Any]:
        self._record("brief", principal)
        return {"date": "2026-08-16", "headline": "All quiet", "items": []}

    def closeout(self, principal: Any) -> dict[str, Any]:
        self._record("closeout", principal)
        return {"date": "2026-08-16", "recs": []}

    def history(self, principal: Any, *, limit: int = 50) -> dict[str, Any]:
        self._record("history", principal, limit=limit)
        return {"nudges": [], "egress": {"cloud": False}}

    def audit(self, principal: Any) -> dict[str, Any]:
        self._record("audit", principal)
        return {"loops": [], "policies": []}

    def snooze(self, principal: Any, loop_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._record("snooze", principal, loop_id, payload)
        return {"id": loop_id, "status": "open", "snoozed_until": "2026-08-17T00:00:00"}

    def set_status(self, principal: Any, loop_id: str, status: str) -> dict[str, Any]:
        self._record("set_status", principal, loop_id, status)
        return {"id": loop_id, "status": status}

    def run_now(self, principal: Any) -> dict[str, Any]:
        self._record("run_now", principal)
        return {"at": "2026-08-16T12:00:00", "projected": 0, "open_loops": 3, "due": []}

    def apply_closeout(self, principal: Any, payload: dict[str, Any]) -> dict[str, Any]:
        self._record("apply_closeout", principal, payload)
        return {"applied": 1, "skipped": 0, "egress": {"cloud": False}}


@pytest.fixture()
def _patch_cadence(monkeypatch: pytest.MonkeyPatch) -> FakeCadenceService:
    """Monkeypatch cadence family dispatch to use FakeCadenceService."""
    fake = FakeCadenceService()

    def _fake_service() -> FakeCadenceService:
        return fake

    monkeypatch.setattr(cadence_mod, "_service", _fake_service)
    monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))
    return fake


def _call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Call a tool through the MCP protocol and return the parsed payload."""
    response = handle_message({
        "jsonrpc": "2.0",
        "id": name,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    })
    assert response is not None
    return response["result"]


def _call_ok(name: str, arguments: dict[str, Any]) -> Any:
    """Call a tool and assert success; return the parsed JSON payload."""
    result = _call(name, arguments)
    assert result["isError"] is False, f"Unexpected error: {result}"
    return json.loads(result["content"][0]["text"])


def _call_err(name: str, arguments: dict[str, Any]) -> str:
    """Call a tool and assert isError:true; return the error text."""
    result = _call(name, arguments)
    assert result["isError"] is True, f"Expected isError:true, got: {result}"
    return result["content"][0]["text"]


# ---------------------------------------------------------------------------
# Dispatch tests — each tool
# ---------------------------------------------------------------------------

class TestCadenceGetLoop:

    def test_missing_loop_id(self, _patch_cadence: FakeCadenceService) -> None:
        err = _call_err("cadence.get_loop", {})
        assert "loop_id" in err


class TestCadenceSnooze:

    def test_missing_loop_id(self, _patch_cadence: FakeCadenceService) -> None:
        err = _call_err("cadence.snooze", {})
        assert "loop_id" in err

    def test_unknown_loop_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Snooze on an unknown loop must return isError:true."""
        from holdspeak.services.errors import NotFound

        class RaisingService:
            def snooze(self, principal: Any, loop_id: str, payload: dict[str, Any]) -> Any:
                raise NotFound("loop", loop_id)

        monkeypatch.setattr(cadence_mod, "_service", lambda: RaisingService())
        monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

        err = _call_err("cadence.snooze", {"loop_id": "no-such-loop"})
        assert "no-such-loop" in err or "not found" in err.lower() or "loop" in err.lower()


class TestCadenceSetStatus:

    def test_invalid_status_returns_error(self, _patch_cadence: FakeCadenceService) -> None:
        """Status outside the enum must return isError:true."""
        err = _call_err("cadence.set_status", {"loop_id": "loop-1", "status": "invalid"})
        assert "status" in err.lower()

    def test_missing_status(self, _patch_cadence: FakeCadenceService) -> None:
        err = _call_err("cadence.set_status", {"loop_id": "loop-1"})
        assert "status" in err.lower()

    def test_missing_loop_id(self, _patch_cadence: FakeCadenceService) -> None:
        err = _call_err("cadence.set_status", {"status": "open"})
        assert "loop_id" in err


class TestCadenceApplyCloseout:

    def test_missing_decisions(self, _patch_cadence: FakeCadenceService) -> None:
        err = _call_err("cadence.apply_closeout", {})
        assert "decisions" in err.lower()


# ---------------------------------------------------------------------------
# Resource test — holdspeak://cadence/status through handle_message
# ---------------------------------------------------------------------------

class TestCadenceStatusResource:
    def test_resource_read(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """holdspeak://cadence/status answers resources/read through handle_message."""
        canned_status = {"enabled": True, "pressure": "normal", "counts": {"open": 2},
                         "egress": {"cloud": False}}

        class StubCadenceService:
            def __init__(self, *args: Any, **kwargs: Any) -> None:
                pass

            def status(self, principal: Any) -> dict[str, Any]:
                return canned_status

        monkeypatch.setattr(resources_mod, "CadenceService", StubCadenceService)
        monkeypatch.setattr(server, "resolve_auth", lambda: SimpleNamespace(principal=OWNER))

        response = handle_message({
            "jsonrpc": "2.0",
            "id": "res-cadence",
            "method": "resources/read",
            "params": {"uri": "holdspeak://cadence/status"},
        })
        assert response is not None
        contents = response["result"]["contents"]
        assert len(contents) == 1
        assert contents[0]["uri"] == "holdspeak://cadence/status"
        assert contents[0]["mimeType"] == "application/json"
        data = json.loads(contents[0]["text"])
        assert data["enabled"] is True
        assert data["pressure"] == "normal"

    def test_resource_listed(self) -> None:
        """holdspeak://cadence/status appears in resources/list."""
        response = handle_message({
            "jsonrpc": "2.0",
            "id": "res-list",
            "method": "resources/list",
        })
        assert response is not None
        uris = {r["uri"] for r in response["result"]["resources"]}
        assert "holdspeak://cadence/status" in uris


# ---------------------------------------------------------------------------
# Catalogue presence test
# ---------------------------------------------------------------------------

class TestCadenceToolsCatalogue:
    CADENCE_TOOLS = {
        "cadence.status", "cadence.loops", "cadence.get_loop",
        "cadence.brief", "cadence.closeout", "cadence.history",
        "cadence.audit", "cadence.snooze", "cadence.set_status",
        "cadence.run_now", "cadence.apply_closeout",
    }

    def test_all_eleven_tools_in_catalogue(self) -> None:
        """All eleven cadence tools appear in the tools/list catalogue."""
        response = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response is not None
        names = {t["name"] for t in response["result"]["tools"]}
        missing = self.CADENCE_TOOLS - names
        assert not missing, f"Missing from catalogue: {missing}"

    def test_closed_schemas(self) -> None:
        """Every cadence tool has additionalProperties: false."""
        response = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        assert response is not None
        for tool in response["result"]["tools"]:
            if tool["name"] in self.CADENCE_TOOLS:
                assert tool["inputSchema"]["additionalProperties"] is False, (
                    f"{tool['name']} missing additionalProperties: false"
                )
