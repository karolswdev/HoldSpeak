"""Newline-delimited JSON-RPC stdio server for HoldSpeak MCP tools."""
from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from .auth import resolve_auth
from .resources import ResourceError, list_resources, read_resource
from .tools import TOOLS, ToolError, dispatch
from holdspeak.services.errors import ServiceError

JSONRPC_VERSION = "2.0"
MCP_PROTOCOL_VERSION = "2024-11-05"


def _response(request_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def _error(
    request_id: Any,
    code: int,
    message: str,
    *,
    data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    response = {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": code, "message": message},
    }
    if data is not None:
        response["error"]["data"] = data
    return response


def _tool_result(value: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(value, sort_keys=True, default=str)}],
        "isError": is_error,
    }


def handle_message(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle one MCP JSON-RPC request without allowing service errors to escape."""
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}
    if not isinstance(method, str):
        return _error(request_id, -32600, "Invalid Request: method is required")
    if not isinstance(params, dict):
        return _error(request_id, -32602, "Invalid params")

    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return _response(request_id, {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": False},
                "resources": {"listChanged": False, "subscribe": False},
            },
            "serverInfo": {"name": "holdspeak-mcp", "version": "0.4.0"},
        })
    if method == "ping":
        return _response(request_id, {})
    if method == "tools/list":
        return _response(request_id, {"tools": TOOLS})
    if method == "resources/list":
        return _response(request_id, list_resources(resolve_auth().principal))
    if method == "resources/read":
        uri = params.get("uri")
        if not isinstance(uri, str):
            return _error(request_id, -32602, "Invalid params: uri is required")
        try:
            return _response(request_id, read_resource(uri, resolve_auth().principal))
        except ServiceError as exc:
            return _error(
                request_id,
                -32002,
                exc.detail,
                data={"code": exc.code, **exc.context},
            )
        except (ResourceError, ValueError, KeyError, TypeError) as exc:
            return _error(request_id, -32002, str(exc))
        except Exception as exc:  # Resources must not crash the stdio sidecar.
            return _error(request_id, -32000, str(exc) or type(exc).__name__)
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str):
            return _response(request_id, _tool_result({"error": "Tool name is required"}, is_error=True))
        if not isinstance(arguments, dict):
            return _response(request_id, _tool_result({"error": "Tool arguments must be an object"}, is_error=True))
        try:
            value = dispatch(name, arguments, resolve_auth().principal)
        except ServiceError as exc:
            return _response(
                request_id,
                _tool_result(
                    {"error": exc.detail, "code": exc.code, **exc.context},
                    is_error=True,
                ),
            )
        except (ToolError, ValueError, KeyError, TypeError) as exc:
            return _response(request_id, _tool_result({"error": str(exc)}, is_error=True))
        except Exception as exc:  # Service errors are tool results, never sidecar crashes.
            return _response(request_id, _tool_result({"error": str(exc) or type(exc).__name__}, is_error=True))
        return _response(request_id, _tool_result(value))
    if method.startswith("notifications/"):
        return None
    return _error(request_id, -32601, f"Method not found: {method}")


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    """Run the stdio server until the client closes its input pipe."""
    from .families import thought
    from .refinement_runtime import SidecarRefinementRuntime

    runtime = SidecarRefinementRuntime()
    runtime.start()
    thought.configure_runtime(runtime)
    try:
        for line in stdin:
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError("request must be an object")
            except (json.JSONDecodeError, ValueError) as exc:
                stdout.write(json.dumps(_error(None, -32700, f"Parse error: {exc}")) + "\n")
                stdout.flush()
                continue
            response = handle_message(request)
            if response is not None:
                stdout.write(json.dumps(response, default=str) + "\n")
                stdout.flush()
        return 0
    finally:
        thought.configure_runtime(None)
        runtime.close()


def main() -> int:
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
