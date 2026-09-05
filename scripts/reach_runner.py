#!/usr/bin/env python3
"""HoldSpeak Reach Runner (HS-174-08).

A dependency-light MCP client that connects to a HoldSpeak hub's
Streamable HTTP endpoint, triggers the sweep and the steward's drafter
for each active Room, and disconnects.  Designed to run on the .43 box
with plain python3 (stdlib only: urllib, json, argparse).

Exit codes:
    0  all ok
    1  any tool call failed or steward run timed out
    2  connect refused (hub asleep or off)
    3  credential refused (401/403)
    4  palette refused (MCP-005)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# -- helpers ----------------------------------------------------------------

_MSG_ID = 0


def _next_id() -> int:
    global _MSG_ID
    _MSG_ID += 1
    return _MSG_ID


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("[%Y-%m-%d %H:%M:%S]")


def _log(line: str) -> None:
    print(f"{_ts()} {line}", flush=True)


def _jsonrpc(method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    msg: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": _next_id(),
        "method": method,
    }
    if params is not None:
        msg["params"] = params
    return msg


# -- transport --------------------------------------------------------------


class _AuthError(Exception):
    """Raised when the hub returns 401 or 403."""

    def __init__(self, code: int, message: str = "") -> None:
        super().__init__(message)
        self.code = code


def _post(
    hub: str,
    payload: dict[str, Any],
    token: str,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """POST one JSON-RPC message to the hub and return the parsed response.

    Raises _AuthError on 401/403, urllib.error.URLError on connection
    failure, ValueError on unexpected responses.
    """
    data = json.dumps(payload).encode("utf-8")
    url = hub.rstrip("/") + "/api/mcp"
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise _AuthError(exc.code, f"HTTP {exc.code}") from exc
        raise
    if not body.strip():
        # 204 No Content (notification acknowledged, no body)
        return {"jsonrpc": "2.0", "id": payload.get("id"), "result": {}}
    return json.loads(body)


def _call_tool(
    hub: str,
    token: str,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Call one MCP tool and return the parsed result content.

    Returns the deserialized content text from the tool result.
    Raises RuntimeError on tool-level errors.
    """
    msg = _jsonrpc("tools/call", {
        "name": tool_name,
        "arguments": arguments or {},
    })
    resp = _post(hub, msg, token, timeout=timeout)

    # JSON-RPC error (transport-level)
    if "error" in resp:
        err = resp["error"]
        code = err.get("code", 0)
        message = err.get("message", "")
        raise RuntimeError(f"RPC error {code}: {message}")

    result = resp.get("result", {})
    is_error = result.get("isError", False)

    # Parse the content text
    content_list = result.get("content", [])
    if content_list:
        text = content_list[0].get("text", "{}")
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = {"raw": text}
    else:
        parsed = {}

    if is_error:
        error_detail = parsed.get("error", "unknown tool error")
        error_code = parsed.get("code", "")
        raise RuntimeError(f"tool error: {error_detail} (code={error_code})")

    return parsed


# -- main loop --------------------------------------------------------------


def run(
    hub: str,
    token: str,
    rooms: str,
    poll_interval: int,
    timeout: int,
) -> int:
    """Execute the reach runner transcript.  Returns the exit code."""
    failed = False

    # -- CONNECT -----------------------------------------------------------
    try:
        init_msg = _jsonrpc("initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "reach-runner", "version": "1.0.0"},
        })
        resp = _post(hub, init_msg, token)
    except _AuthError:
        _log("CONNECT FAILED CREDENTIAL REFUSED")
        return 3
    except urllib.error.URLError:
        _log("CONNECT FAILED HUB ASLEEP OR OFF")
        return 2
    except Exception:
        _log("CONNECT FAILED HUB ASLEEP OR OFF")
        return 2

    # Check for auth errors in the response
    if "error" in resp:
        err = resp["error"]
        code = err.get("code", 0)
        message = err.get("message", "")
        if code in (-32001,) or "unauthorized" in message.lower() or "forbidden" in message.lower():
            _log(f"CONNECT FAILED CREDENTIAL REFUSED")
            return 3
        # MCP-005 palette error
        data = err.get("data", {})
        if data.get("code") == "palette_refused" or code == -32005:
            _log(f"CONNECT FAILED PALETTE REFUSED")
            return 4
        _log(f"CONNECT FAILED RPC error {code}: {message}")
        return 2

    result = resp.get("result", {})
    server_info = result.get("serverInfo", {})
    protocol_version = result.get("protocolVersion", "unknown")
    identity = server_info.get("name", "unknown")
    # The palette is carried in the credential, not echoed by initialize;
    # we print what we know from the client side.
    _log(f"CONNECT hub={hub} protocol={protocol_version} identity={identity}")

    # Send initialized notification (no response expected, but send anyway)
    try:
        notif = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        _post(hub, notif, token, timeout=5)
    except Exception:
        pass  # notifications may not return a body

    # -- CALL heartbeat.run_now (the sweep) ----------------------------------
    _log("CALL cadence_run_now")
    try:
        sweep = _call_tool(hub, token, "heartbeat.run_now")
        summary_parts = []
        # heartbeat.run_now returns the sweep receipt with watches/rooms/held
        for key in ("watches", "rooms", "evaluated", "due"):
            if key in sweep:
                summary_parts.append(f"{key}={sweep[key]}")
        summary = " ".join(summary_parts) if summary_parts else "completed"
        _log(f"OK sweep {summary}")
    except RuntimeError as exc:
        err_str = str(exc)
        if "palette" in err_str.lower() or "-32005" in err_str:
            _log(f"FAILED cadence_run_now PALETTE REFUSED")
            return 4
        if "unauthorized" in err_str.lower() or "forbidden" in err_str.lower():
            _log(f"FAILED cadence_run_now CREDENTIAL REFUSED")
            return 3
        _log(f"FAILED cadence_run_now {exc}")
        failed = True

    # -- Discover active rooms ---------------------------------------------
    project_ids: list[str] = []
    if rooms == "all":
        try:
            projects = _call_tool(hub, token, "project.list")
            for p in projects.get("projects", []):
                pid = p.get("id", "")
                if pid and not p.get("archived", False):
                    project_ids.append(pid)
        except RuntimeError as exc:
            _log(f"FAILED project.list {exc}")
            failed = True
    else:
        project_ids = [r.strip() for r in rooms.split(",") if r.strip()]

    # -- CALL project_run_steward for each room ----------------------------
    for project_id in project_ids:
        _log(f"CALL project_run_steward project={project_id}")
        try:
            run_result = _call_tool(hub, token, "project.run_steward", {
                "project_id": project_id,
            })
            run_id = run_result.get("run_id")
            if not run_id:
                _log(f"OK steward project={project_id} no_run_id (steward may be disabled)")
                continue

            # Poll for terminal state
            deadline = time.monotonic() + timeout
            status = "pending"
            while time.monotonic() < deadline:
                time.sleep(poll_interval)
                try:
                    poll = _call_tool(hub, token, "project.get_steward_run", {
                        "run_id": run_id,
                    })
                    run_data = poll.get("run", {})
                    status = run_data.get("status", "unknown")
                    if status in ("completed", "failed", "cancelled"):
                        break
                except RuntimeError:
                    # Transient poll failure -- keep trying until deadline
                    pass

            if status == "completed":
                _log(f"OK steward_run completed run_id={run_id} project={project_id}")
            elif status in ("failed", "cancelled"):
                _log(f"FAILED steward_run {status} run_id={run_id} project={project_id}")
                failed = True
            else:
                _log(f"TIMEOUT steward_run run_id={run_id} project={project_id} status={status}")
                failed = True

        except RuntimeError as exc:
            err_str = str(exc)
            # Typed refusals that are not failures
            if "steward_disabled" in err_str:
                _log(f"OK steward project={project_id} disabled")
                continue
            if "cooldown_active" in err_str:
                _log(f"OK steward project={project_id} cooldown")
                continue
            if "active_run_exists" in err_str:
                _log(f"OK steward project={project_id} active_run_exists")
                continue
            _log(f"FAILED project_run_steward project={project_id} {exc}")
            failed = True

    # -- DISCONNECT --------------------------------------------------------
    _log("DISCONNECT")

    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HoldSpeak Reach Runner -- overnight MCP client",
    )
    parser.add_argument(
        "--hub",
        required=True,
        help="Hub URL (e.g. http://100.64.0.2:8765)",
    )
    parser.add_argument(
        "--token-file",
        required=True,
        help="Path to a file containing the bearer token (one line, no newline arts).",
    )
    parser.add_argument(
        "--rooms",
        default="all",
        help="Comma-separated project IDs or 'all' (default: all).",
    )
    parser.add_argument(
        "--poll",
        type=int,
        default=5,
        help="Steward run poll interval in seconds (default: 5).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Steward run timeout in seconds (default: 900).",
    )
    args = parser.parse_args()

    # Read token from file (never from argv)
    token_path = Path(args.token_file)
    if not token_path.is_file():
        print(f"Token file not found: {args.token_file}", file=sys.stderr)
        return 3
    token = token_path.read_text().strip()
    if not token:
        print("Token file is empty", file=sys.stderr)
        return 3

    return run(
        hub=args.hub,
        token=token,
        rooms=args.rooms,
        poll_interval=args.poll,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    raise SystemExit(main())
