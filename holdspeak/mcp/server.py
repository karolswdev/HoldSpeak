"""Newline-delimited JSON-RPC stdio server for HoldSpeak MCP tools.

**The sidecar is a CLIENT of the running hub, not a second writer
(HS-200-45 R2).** It used to be its own composition root: ``uv run
holdspeak-mcp`` inherits ``$HOME`` from whatever launched it, opened
``~/.local/share/holdspeak/holdspeak.db`` -- the file a running hub owns --
ran ``reconcile_schema`` (a write transaction) on every start, and never
touched the owner lock. ``runtime_lock.py``'s own docstring says C10 "forbids
introducing a multi-writer SQLite arrangement at all"; ``grep -rn
"runtime_lock" holdspeak/mcp/`` found zero hits.

So :func:`serve` no longer composes anything. For each message it discovers
the hub through the owner lock beside the default database path (pid liveness
confirmed, host and port read from the lock body) and forwards the JSON-RPC
message **verbatim** to ``POST http://127.0.0.1:<port>/api/mcp`` with the
owner's token, returning the hub's response verbatim. Discovery is per message
and never cached, so a hub started *after* the editor launched this sidecar
just starts working.

With no live hub, everything but ``initialize`` and ``ping`` answers a
JSON-RPC error naming the situation and the remedy -- and the database is not
opened at all: no ``reconcile_schema``, no ``get_database()``, no
``holdspeak.db`` created.

**The rejected option: a read-only second builder.** Letting the sidecar open
the file read-only and serve just the read tools was considered and refused,
for the reason ``runtime_lock.py``'s docstring already gives about a read-only
second hub: it is still a second builder of the same service layer, so every
write tool would either have to be hidden (changing the tool catalogue
depending on who is running, which the palettes deliberately do not do) or
silently refuse; and a reader that walks around the owner lock still holds an
open handle on a file another process is checkpointing. Proxying keeps ONE
writer, ONE composition root, and a tool catalogue that means the same thing
wherever it is called from.

**Proxy only (PHILO-5-01, the owner's D2).** The standalone hatch
(``HOLDSPEAK_MCP_STANDALONE=1``), which composed the service layer in this
process and claimed the owner lock, is retired. The variable is ignored: with
or without it, this process composes nothing and opens no database.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional, TextIO

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


#: Methods the sidecar answers itself when no hub is reachable, so a client's
#: handshake completes and it can report the real problem on the first tool call
#: instead of failing to connect at all.
_LOCAL_WHEN_NO_HUB = frozenset({"initialize", "ping", "notifications/initialized"})

#: How long to wait on the hub's loopback HTTP response. Generous: a steward run
#: or a model-invoking tool is slow by design, and MCP-003's long-running
#: contract already returns a run id promptly for the slowest of them.
_HUB_TIMEOUT_SECONDS = 300.0


def _default_db_path() -> Path:
    """The database path the hub would own. Reading this opens nothing."""
    from holdspeak.db.core import DEFAULT_DB_PATH

    return Path(DEFAULT_DB_PATH).expanduser()


def discover_hub(db_path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """The live hub that owns the database, or ``None``.

    Reads the owner lock's JSON body beside the database FILE -- never the
    database itself -- and trusts it only as far as ``pid_alive`` confirms.
    Called on every message: a hub that starts later is found without
    restarting this process, and a hub that dies is not proxied to twice.
    """
    from holdspeak.runtime_lock import read_owner

    path = db_path or _default_db_path()
    owner = read_owner(path)
    if not owner or not owner.get("alive"):
        return None
    try:
        port = int(owner.get("port") or 0)
    except (TypeError, ValueError):
        return None
    if port <= 0:
        return None
    host = str(owner.get("host") or "127.0.0.1")
    # Always speak to loopback: a hub bound to 0.0.0.0 is still reachable on
    # 127.0.0.1, and POST /api/mcp refuses an OWNER token off-loopback (C5).
    from holdspeak.web_auth import is_loopback_host

    bound_host = host
    if not is_loopback_host(host):
        host = "127.0.0.1"
    return {
        "host": host, "port": port, "pid": owner.get("pid"),
        "db_path": str(path), "bound_host": bound_host,
        "label": owner.get("label") or "holdspeak web",
    }


def _owner_token() -> str:
    """The hub's web auth token, read straight out of the config FILE.

    Not ``Config.load``: with no file present that SAVES a default config,
    so the sidecar was creating ``~/.config/holdspeak/config.json`` on a
    machine that had never run the hub (counsel P1-2). And its legacy
    migration calls ``get_database()``. This process writes nothing and opens
    nothing: a missing or unreadable file is simply "no token".
    """
    import holdspeak.config as config_facade

    path = Path(getattr(config_facade, "CONFIG_FILE"))
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    meeting = data.get("meeting") if isinstance(data, dict) else None
    token = meeting.get("web_auth_token") if isinstance(meeting, dict) else ""
    return str(token or "")


def no_hub_message(db_path: Optional[Path] = None) -> str:
    """One sentence: the situation, and the remedy."""
    path = db_path or _default_db_path()
    return (
        f"No running HoldSpeak hub owns {path}; start `holdspeak web`, then retry. "
        "The MCP sidecar is a client of the hub and never opens the database "
        "itself."
    )


def forward_to_hub(
    request: dict[str, Any], hub: dict[str, Any]
) -> dict[str, Any] | None:
    """POST *request* to the hub's ``/api/mcp`` and return its response.

    Verbatim in both directions: the hub owns every protocol decision -- the
    tool catalogue, the palette refusals, the error codes. ``204`` means the
    hub treated the message as a notification, so there is no response.
    """
    body = json.dumps(request).encode("utf-8")
    url = f"http://{hub['host']}:{hub['port']}/api/mcp"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    token = _owner_token()
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=_HUB_TIMEOUT_SECONDS) as resp:
        if resp.status == 204:
            return None
        raw = resp.read()
    if not raw:
        return None
    return json.loads(raw.decode("utf-8"))


def handle_message_via_hub(request: dict[str, Any]) -> dict[str, Any] | None:
    """One message, answered by the running hub -- or refused honestly."""
    request_id = request.get("id")
    method = request.get("method")
    hub = discover_hub()
    if hub is None:
        if method in _LOCAL_WHEN_NO_HUB or (
            isinstance(method, str) and method.startswith("notifications/")
        ):
            return handle_message_locally(request)
        return _error(request_id, -32002, no_hub_message())
    try:
        return forward_to_hub(request, hub)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        if not _owner_token():
            import holdspeak.config as config_facade

            return _error(
                request_id,
                -32002,
                f"The hub at 127.0.0.1:{hub['port']} (pid {hub['pid']}) refused "
                f"this MCP call with HTTP {exc.code}, and no owner token is "
                f"configured in {getattr(config_facade, 'CONFIG_FILE')}; the "
                "sidecar sends the hub's own token, so run `holdspeak web` on "
                "this machine once so it writes one, then retry.",
            )
        return _error(
            request_id,
            -32002,
            f"The hub at 127.0.0.1:{hub['port']} (pid {hub['pid']}) refused this "
            f"MCP call with HTTP {exc.code}; check that its owner token matches "
            f"this machine's config. {detail}".strip(),
        )
    except (urllib.error.URLError, OSError, ValueError) as exc:
        bound = hub.get("bound_host") or "127.0.0.1"
        if bound != hub["host"]:
            # The lock says the hub is bound off-loopback. The sidecar dials
            # loopback only (an OWNER token is refused off-loopback, C5), so
            # "restart" would be the wrong remedy (counsel P2-ii).
            return _error(
                request_id,
                -32002,
                f"The hub (pid {hub['pid']}) is bound to {bound}:{hub['port']}; "
                "the sidecar reaches it on loopback only, and 127.0.0.1 did not "
                f"answer ({exc}). Set HOLDSPEAK_WEB_HOST so the hub also listens "
                "on loopback, then retry.",
            )
        return _error(
            request_id,
            -32002,
            f"The owner lock names pid {hub['pid']} on port {hub['port']}, but "
            f"that hub did not answer POST /api/mcp ({exc}); restart "
            f"`holdspeak web`, then retry.",
        )


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


#: The in-process handler, kept under an explicit name. It composes against
#: whatever composition root this process holds, so it is reached only from
#: :func:`handle_message_via_hub`'s local handshake answers and from the tests
#: that drive dispatch directly.
handle_message_locally = handle_message


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
            # PHILO-7-02 class 4: a named tool of an ADMITTED operation leaves a
            # refusal receipt; the answer is unchanged.
            from holdspeak.mcp.tools import refuse_before_invoke

            kernel = refuse_before_invoke(name, arguments, principal, "invalid_arguments") or {}
            return _response(request_id, _tool_result({"error": "Tool arguments must be an object", **kernel}, is_error=True))
        try:
            if palette is not None:
                value = dispatch_for_palette(name, arguments, principal, palette)
            else:
                value = dispatch(name, arguments, principal)
        except ToolError as exc:
            # HS-174: palette refusal carries MCP-005. PHILO-7-02: a refusal of
            # an ADMITTED operation carries its operation_id and receipt.
            msg = str(exc)
            kernel = getattr(exc, "kernel", None) or {}
            if "not in the configured palette" in msg:
                return _error(
                    request_id, _MCP_005_CODE, msg,
                    data={"code": "MCP-005", "tool": name, **kernel},
                )
            return _response(request_id, _tool_result({"error": msg, **kernel}, is_error=True))
        except ServiceError as exc:
            return _response(
                request_id,
                _tool_result(
                    {"error": exc.detail, "code": exc.code, **exc.context},
                    is_error=True,
                ),
            )
        except (ValueError, KeyError, TypeError) as exc:
            return _response(request_id, _tool_result({"error": str(exc), **(getattr(exc, "kernel", None) or {})}, is_error=True))
        except Exception as exc:
            return _response(request_id, _tool_result({"error": str(exc) or type(exc).__name__}, is_error=True))
        return _response(request_id, _tool_result(value))
    if method.startswith("notifications/"):
        return None
    return _error(request_id, -32601, f"Method not found: {method}")


def _pump(
    stdin: TextIO, stdout: TextIO, handler: Any
) -> int:
    """Read newline-delimited JSON-RPC from *stdin*, answer on *stdout*."""
    for line in stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("request must be an object")
        except (json.JSONDecodeError, ValueError) as exc:
            stdout.write(json.dumps(_error(None, -32700, f"Parse error: {exc}")) + "\n")
            stdout.flush()
            continue
        response = handler(request)
        if response is not None:
            stdout.write(json.dumps(response, default=str) + "\n")
            stdout.flush()
    return 0


def serve(stdin: TextIO = sys.stdin, stdout: TextIO = sys.stdout) -> int:
    """Run the stdio proxy until the client closes its input pipe.

    The only mode: nothing is composed here and the database is never opened;
    every message goes to the hub that owns the database.
    """
    return _pump(stdin, stdout, handle_message_via_hub)


def main() -> int:
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
