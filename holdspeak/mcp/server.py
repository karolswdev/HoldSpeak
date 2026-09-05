"""Newline-delimited JSON-RPC stdio server for HoldSpeak MCP tools."""
from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from .auth import resolve_auth
from .resources import ResourceError, list_resources, read_resource
from .tools import TOOLS, ToolError, dispatch, dispatch_for_palette, tools_for_palette
from holdspeak.principals import Principal
from holdspeak.services.errors import ServiceError

JSONRPC_VERSION = "2.0"
# HS-174: bumped to Streamable HTTP revision; both stdio and HTTP announce
# the same version.
MCP_PROTOCOL_VERSION = "2025-03-26"


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


# HS-174: MCP-005 error code for palette refusal.
_MCP_005_CODE = -32005


def handle_message_for_principal(
    request: dict[str, Any],
    principal: Principal,
    *,
    palette: frozenset[str] | None = None,
) -> dict[str, Any] | None:
    """Handle one MCP JSON-RPC request with an externally-derived principal.

    Used by the Streamable HTTP transport (POST /api/mcp) where the principal
    comes from the web-auth middleware, not the stdio environment.  When
    *palette* is non-None, tools outside it are refused with MCP-005.
    """
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
        available_tools = tools_for_palette(palette) if palette else TOOLS
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
        available_tools = tools_for_palette(palette) if palette else TOOLS
        return _response(request_id, {"tools": available_tools})
    if method == "resources/list":
        return _response(request_id, list_resources(principal))
    if method == "resources/read":
        uri = params.get("uri")
        if not isinstance(uri, str):
            return _error(request_id, -32602, "Invalid params: uri is required")
        try:
            return _response(request_id, read_resource(uri, principal))
        except ServiceError as exc:
            return _error(
                request_id, -32002, exc.detail,
                data={"code": exc.code, **exc.context},
            )
        except (ResourceError, ValueError, KeyError, TypeError) as exc:
            return _error(request_id, -32002, str(exc))
        except Exception as exc:
            return _error(request_id, -32000, str(exc) or type(exc).__name__)
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments", {})
        if not isinstance(name, str):
            return _response(request_id, _tool_result({"error": "Tool name is required"}, is_error=True))
        if not isinstance(arguments, dict):
            return _response(request_id, _tool_result({"error": "Tool arguments must be an object"}, is_error=True))
        try:
            if palette is not None:
                value = dispatch_for_palette(name, arguments, principal, palette)
            else:
                value = dispatch(name, arguments, principal)
        except ToolError as exc:
            # HS-174: palette refusal carries MCP-005.
            msg = str(exc)
            if "not in the configured palette" in msg:
                return _error(
                    request_id, _MCP_005_CODE, msg,
                    data={"code": "MCP-005", "tool": name},
                )
            return _response(request_id, _tool_result({"error": msg}, is_error=True))
        except ServiceError as exc:
            return _response(
                request_id,
                _tool_result(
                    {"error": exc.detail, "code": exc.code, **exc.context},
                    is_error=True,
                ),
            )
        except (ValueError, KeyError, TypeError) as exc:
            return _response(request_id, _tool_result({"error": str(exc)}, is_error=True))
        except Exception as exc:
            return _response(request_id, _tool_result({"error": str(exc) or type(exc).__name__}, is_error=True))
        return _response(request_id, _tool_result(value))
    if method.startswith("notifications/"):
        return None
    return _error(request_id, -32601, f"Method not found: {method}")


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    """Run the stdio server until the client closes its input pipe."""
    # Compose the immutable semantic registry before the sidecar announces any
    # capability. A bad census/plugin/schema is a process-start failure, not
    # a lazy resource-read error after MCP initialization.
    from holdspeak.inference_capabilities import process_inference_capability_registry
    from .families import thought
    from .refinement_runtime import SidecarRefinementRuntime

    process_inference_capability_registry()
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
