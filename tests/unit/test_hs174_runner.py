"""HS-174-08/09 tests: the .43 runner and the desk.notification mesh event.

Proves the reach runner's main loop against a stub HTTP server speaking the
JSON-RPC shapes, and the story-09 mesh event publish in heartbeat_notify.
"""
from __future__ import annotations

import http.server
import io
import json
import re
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Stub JSON-RPC server
# ---------------------------------------------------------------------------

class _StubHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP handler that speaks the MCP JSON-RPC shapes."""

    # Shared across requests via the server instance
    @property
    def _behaviour(self) -> dict[str, Any]:
        return self.server._behaviour  # type: ignore[attr-defined]

    def log_message(self, *args: Any, **kwargs: Any) -> None:
        pass  # silence request logs

    def do_POST(self) -> None:
        # Read the request body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        auth = self.headers.get("Authorization", "")

        # Auth checks
        if self._behaviour.get("reject_auth"):
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "jsonrpc": "2.0", "id": None,
                "error": {"code": -32001, "message": "Unauthorized"},
            }).encode())
            return

        if self._behaviour.get("reject_palette"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "jsonrpc": "2.0", "id": 1,
                "error": {"code": -32005, "message": "Palette refused",
                           "data": {"code": "palette_refused"}},
            }).encode())
            return

        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        method = request.get("method", "")
        request_id = request.get("id")
        params = request.get("params", {})

        response = self._dispatch(method, request_id, params)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if response is not None:
            self.wfile.write(json.dumps(response, default=str).encode())

    def _dispatch(self, method: str, request_id: Any, params: dict[str, Any]) -> dict[str, Any] | None:
        if method == "initialize":
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "holdspeak-mcp", "version": "0.4.0"},
                },
            }

        if method == "notifications/initialized":
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            return self._dispatch_tool(request_id, tool_name, arguments)

        return {
            "jsonrpc": "2.0", "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    def _dispatch_tool(self, request_id: Any, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        def _ok(value: Any) -> dict[str, Any]:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(value, default=str)}],
                    "isError": False,
                },
            }

        def _err(msg: str, code: str = "") -> dict[str, Any]:
            return {
                "jsonrpc": "2.0", "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": msg, "code": code})}],
                    "isError": True,
                },
            }

        if name in ("cadence.run_now", "heartbeat.run_now"):
            if self._behaviour.get("sweep_fail"):
                return _err("sweep failed", "internal")
            return _ok({"evaluated": 5, "due": 2})

        if name == "project.list":
            projects = self._behaviour.get("projects", [
                {"id": "proj-a", "name": "Alpha", "archived": False},
                {"id": "proj-b", "name": "Beta", "archived": False},
            ])
            return _ok({"projects": projects})

        if name == "project.run_steward":
            project_id = arguments.get("project_id", "")
            if self._behaviour.get("steward_fail_project") == project_id:
                return _err("steward run failed", "internal")
            run_id = f"run_{project_id}"
            return _ok({"success": True, "run_id": run_id})

        if name == "project.get_steward_run":
            run_id = arguments.get("run_id", "")
            status = self._behaviour.get("steward_status", "completed")
            return _ok({
                "run": {"run_id": run_id, "status": status},
                "steps": [],
            })

        return _err(f"Unknown tool: {name}", "not_found")


@contextmanager
def _stub_server(behaviour: dict[str, Any] | None = None) -> Generator[tuple[str, int], None, None]:
    """Start a stub JSON-RPC server in a thread and yield (host, port)."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _StubHandler)
    server._behaviour = behaviour or {}  # type: ignore[attr-defined]
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield ("127.0.0.1", port)
    finally:
        server.shutdown()


def _run_runner(hub: str, token: str, rooms: str = "all", poll: int = 1, timeout: int = 10) -> tuple[int, str]:
    """Import and run the runner, capturing stdout.  Returns (exit_code, stdout)."""
    # Import the runner module
    runner_path = Path(__file__).resolve().parents[2] / "scripts" / "reach_runner.py"
    assert runner_path.is_file(), f"Runner not found at {runner_path}"

    import importlib.util
    spec = importlib.util.spec_from_file_location("reach_runner", runner_path)
    mod = importlib.util.module_from_spec(spec)

    # Reset global message id for deterministic tests
    buf = io.StringIO()
    with patch.object(sys, "stdout", buf):
        spec.loader.exec_module(mod)
        mod._MSG_ID = 0
        code = mod.run(hub=hub, token=token, rooms=rooms, poll_interval=poll, timeout=timeout)

    return code, buf.getvalue()


# ---------------------------------------------------------------------------
# Tests: happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    """The full transcript: CONNECT, sweep, steward for each room, DISCONNECT."""

    def test_happy_path_transcript(self):
        with _stub_server() as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token="test-token-abc")

        assert code == 0, f"Expected exit 0, got {code}.\nOutput:\n{out}"

        lines = out.strip().splitlines()
        assert len(lines) >= 4, f"Expected at least 4 lines, got {len(lines)}"

        # Every line starts with a timestamp
        ts_pattern = re.compile(r"^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\]")
        for line in lines:
            assert ts_pattern.match(line), f"Missing timestamp: {line}"

        # Check the transcript steps
        assert "CONNECT" in lines[0]
        assert "hub=" in lines[0]
        assert "protocol=" in lines[0]

        # Find the CALL cadence_run_now and its OK
        call_lines = [l for l in lines if "CALL cadence_run_now" in l]
        assert len(call_lines) >= 1, "Missing CALL cadence_run_now"

        ok_sweep = [l for l in lines if "OK sweep" in l]
        assert len(ok_sweep) >= 1, "Missing OK sweep line"

        # Steward calls for projects
        steward_calls = [l for l in lines if "CALL project_run_steward" in l]
        assert len(steward_calls) == 2, f"Expected 2 steward calls, got {len(steward_calls)}"

        steward_ok = [l for l in lines if "OK steward_run completed" in l]
        assert len(steward_ok) == 2, f"Expected 2 steward OKs, got {len(steward_ok)}"

        # DISCONNECT
        assert "DISCONNECT" in lines[-1]


# ---------------------------------------------------------------------------
# Tests: connection refused -> exit 2
# ---------------------------------------------------------------------------


class TestConnectionRefused:
    def test_unreachable_hub(self):
        # Connect to a port nobody listens on
        code, out = _run_runner("http://127.0.0.1:1", token="x")
        assert code == 2
        assert "HUB ASLEEP OR OFF" in out


# ---------------------------------------------------------------------------
# Tests: credential refused -> exit 3
# ---------------------------------------------------------------------------


class TestCredentialRefused:
    def test_401_response(self):
        with _stub_server({"reject_auth": True}) as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token="bad-token")

        assert code == 3
        assert "CREDENTIAL REFUSED" in out


# ---------------------------------------------------------------------------
# Tests: palette refused -> exit 4
# ---------------------------------------------------------------------------


class TestPaletteRefused:
    def test_palette_error(self):
        with _stub_server({"reject_palette": True}) as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token="token")

        assert code == 4
        assert "PALETTE REFUSED" in out


# ---------------------------------------------------------------------------
# Tests: steward fails -> exit 1
# ---------------------------------------------------------------------------


class TestStewardFailed:
    def test_steward_run_fails(self):
        with _stub_server({"steward_status": "failed"}) as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token="token")

        assert code == 1
        assert "FAILED steward_run" in out


# ---------------------------------------------------------------------------
# Tests: steward timeout -> exit 1
# ---------------------------------------------------------------------------


class TestStewardTimeout:
    def test_steward_timeout(self):
        with _stub_server({"steward_status": "running"}) as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token="token", timeout=2, poll=1)

        assert code == 1
        assert "TIMEOUT" in out


# ---------------------------------------------------------------------------
# Tests: token never in output
# ---------------------------------------------------------------------------


class TestTokenNeverLeaked:
    def test_token_not_in_stdout(self):
        secret = "super-secret-token-that-must-never-appear"
        with _stub_server() as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token=secret)

        assert secret not in out, "Token leaked to stdout"

    def test_token_not_in_stderr(self):
        """The token must never appear in stderr either."""
        secret = "another-secret-token-12345"
        err_buf = io.StringIO()
        with _stub_server() as (host, port):
            hub = f"http://{host}:{port}"
            with patch.object(sys, "stderr", err_buf):
                code, out = _run_runner(hub, token=secret)

        assert secret not in err_buf.getvalue(), "Token leaked to stderr"


# ---------------------------------------------------------------------------
# Tests: specific room IDs
# ---------------------------------------------------------------------------


class TestSpecificRooms:
    def test_specific_rooms(self):
        with _stub_server() as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token="token", rooms="proj-x,proj-y")

        assert code == 0
        steward_calls = [l for l in out.strip().splitlines() if "CALL project_run_steward" in l]
        assert len(steward_calls) == 2
        assert "project=proj-x" in steward_calls[0]
        assert "project=proj-y" in steward_calls[1]


# ---------------------------------------------------------------------------
# Tests: sweep fails -> exit 1 but steward still runs
# ---------------------------------------------------------------------------


class TestSweepFails:
    def test_sweep_failure_continues_to_steward(self):
        with _stub_server({"sweep_fail": True}) as (host, port):
            hub = f"http://{host}:{port}"
            code, out = _run_runner(hub, token="token")

        assert code == 1  # sweep failed
        assert "FAILED cadence_run_now" in out
        # Steward still ran
        assert "CALL project_run_steward" in out


# ---------------------------------------------------------------------------
# Tests: HS-174-09 desk.notification mesh event
# ---------------------------------------------------------------------------


class TestDeskNotificationMeshEvent:
    """Story 09: heartbeat_notify publishes desk.notification on the mesh bus."""

    def test_mesh_event_fires_on_notification(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        events: list[dict[str, Any]] = []

        result = heartbeat_notify(
            3, 2,
            edge=edge,
            quiet_hours_start=0,
            quiet_hours_end=0,
            mesh_event_writer=events.append,
            _notifier=lambda *a, **kw: True,
        )

        assert result["fired"] is True
        assert len(events) == 1
        ev = events[0]
        assert ev["kind"] == "desk.notification"
        assert ev["count"] == 3
        assert ev["projects"] == 2
        assert ev["origin"] == "heartbeat"

    def test_mesh_event_not_fired_when_no_edge(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        edge.mark_fired(5)  # last notified at 5
        events: list[dict[str, Any]] = []

        result = heartbeat_notify(
            3, 1,
            edge=edge,
            quiet_hours_start=0,
            quiet_hours_end=0,
            mesh_event_writer=events.append,
            _notifier=lambda *a, **kw: True,
        )

        assert result["fired"] is False
        assert len(events) == 0

    def test_mesh_event_not_fired_when_quiet_hours(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()
        events: list[dict[str, Any]] = []

        result = heartbeat_notify(
            3, 1,
            edge=edge,
            quiet_hours_start=0,
            quiet_hours_end=23,  # always quiet
            mesh_event_writer=events.append,
            _notifier=lambda *a, **kw: True,
        )

        assert result["held"] is True
        assert len(events) == 0

    def test_mesh_event_not_fired_when_writer_absent(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()

        # No mesh_event_writer -- should not crash
        result = heartbeat_notify(
            3, 1,
            edge=edge,
            quiet_hours_start=0,
            quiet_hours_end=0,
            _notifier=lambda *a, **kw: True,
        )

        assert result["fired"] is True

    def test_mesh_event_writer_exception_swallowed(self):
        from holdspeak.desktop_notify import EdgeDetector, heartbeat_notify

        edge = EdgeDetector()

        def _bad_writer(ev: dict[str, Any]) -> None:
            raise RuntimeError("boom")

        # Should not crash
        result = heartbeat_notify(
            3, 1,
            edge=edge,
            quiet_hours_start=0,
            quiet_hours_end=0,
            mesh_event_writer=_bad_writer,
            _notifier=lambda *a, **kw: True,
        )

        assert result["fired"] is True


# ---------------------------------------------------------------------------
# Tests: main() CLI argument parsing
# ---------------------------------------------------------------------------


class TestCLITokenFile:
    def test_missing_token_file_exits_3(self, tmp_path):
        runner_path = Path(__file__).resolve().parents[2] / "scripts" / "reach_runner.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location("reach_runner_cli", runner_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        err_buf = io.StringIO()
        with patch.object(sys, "stderr", err_buf):
            with patch.object(sys, "argv", [
                "reach_runner.py",
                "--hub", "http://127.0.0.1:9999",
                "--token-file", str(tmp_path / "nonexistent"),
            ]):
                code = mod.main()

        assert code == 3
        assert "not found" in err_buf.getvalue().lower()

    def test_empty_token_file_exits_3(self, tmp_path):
        token_file = tmp_path / "empty-token"
        token_file.write_text("")

        runner_path = Path(__file__).resolve().parents[2] / "scripts" / "reach_runner.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location("reach_runner_cli2", runner_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        err_buf = io.StringIO()
        with patch.object(sys, "stderr", err_buf):
            with patch.object(sys, "argv", [
                "reach_runner.py",
                "--hub", "http://127.0.0.1:9999",
                "--token-file", str(token_file),
            ]):
                code = mod.main()

        assert code == 3


# ---------------------------------------------------------------------------
# Integration: see tests/integration/test_hs174_runner_loopback.py
# (moved there now that the transport lane has landed)
# ---------------------------------------------------------------------------
