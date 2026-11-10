"""HS-174-02: Streamable HTTP transport for MCP (POST /api/mcp).

JSON-RPC in -> handle_message_for_principal -> JSON-RPC out.

**How the composition actually works (HS-200-45).** This docstring used to
claim the route composed "on the web runtime's LIVE services (never the
sidecar's bare serve() instances)". That was false: the route received
``ctx: WebContext``, handed the message to ``handle_message_for_principal``,
and ``tools.dispatch`` rebuilt every service from ``get_database()`` -- bare,
with no broadcast. The context was received and unused for dispatch.

It is true now, and by a different mechanism than "the route passes ctx
along". ``MeetingWebServer._create_app`` installs its composed services as the
process's ONE composition root
(``holdspeak/runtime/composition.py``); ``tools.dispatch`` and every MCP family
read that root. So this route needs to pass nothing: the dispatch it calls
resolves the same ``PrimitiveService`` (with ``on_changed`` bound to the bus),
the same ``MeetingService`` (with its lifecycle callbacks), and the same
``Database`` handle that the hub's HTTP routes use. A ``desk.create`` over this
route therefore puts a ``desk_changed`` frame on ``/ws``, exactly as the
equivalent ``POST /api/notes`` does.

Principal derivation per D3:
- Loopback + owner token -> OWNER (unrestricted).
- Loopback + agent credential -> AGENT (palette from credential).
- Non-loopback + owner token -> 403 (Article XI:4, per-route guard C5).
- Non-loopback + agent credential -> AGENT (palette from credential).
- No match -> 401.
- Conductor K6: loopback + a LAUNCH-BOUND agent credential (one a launch
  issued, ``AgentCredential.launch_id``) passes with the Reach switch off,
  as AGENT with its CONDUCTOR palette. A hand-issued agent credential, and
  any agent credential from elsewhere, still needs the switch on.

**The enable flag governs the REMOTE listener, not the local transport
(HS-200-45 R3).** ``remote.streamable_http_enabled`` is the owner's switch for
letting *agent credentials from elsewhere* in. A loopback request bearing the
owner's own token is not remote access -- it is the hub's own local transport,
the one the stdio sidecar proxies into so that the sidecar never has to open
the database itself. Refusing that with 404 while the flag is off would leave
the sidecar no lawful path and push it straight back to being a second writer.
So: a loopback OWNER is admitted with the flag off; everything else still needs
the flag on.

Settings routes:
- GET  /api/settings/remote        -> current remote config + credential list
- PUT  /api/settings/remote        -> update enabled/bind_host
- POST /api/settings/remote/credentials -> issue a new credential
- DELETE /api/settings/remote/credentials/{id} -> revoke (the credential's
  LIVE desk grant first, durably, with its own receipt; PHILO-7-02)
- PUT    /api/settings/remote/delegations/{identity} -> delegation.grant
- DELETE /api/settings/remote/delegations/{identity} -> delegation.revoke
- PUT    /api/settings/remote/delegations/{identity}/projects/{project_id} -> project.delegation.grant
- DELETE /api/settings/remote/delegations/{identity}/projects/{project_id} -> project.delegation.revoke

PHILO-7-02 (R1): the owner's desk delegation grant rides the credential ledger.
``GET /api/settings/remote`` carries, per credential, ``delegation``: the
grant's EFFECTIVE state ``{state, grant_id, expires_at}`` (``state`` LIVE,
EXPIRED or REVOKED; ``null`` = never granted), computed with the kernel's own
time-aware rule, never the stored state alone; and ``delegations``: the same
projection, with ``identity``, for every identity that has a grant row (LIVE or
historical) and NO credential row. Both are read whatever the remote switch
says: the switch governs transport, not authority.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from ...config import Config
from ...logging_config import get_logger
from ...principals import (
    AgentCredentialStore,
    PrincipalKind,
    UNAUTHENTICATED,
)
from ...services.observer import _origin, _caller, _caller_identity
from ...web_auth import is_loopback_host
from ..context import WebContext

log = get_logger("web.routes.mcp_http")

# HS-174 C5: the per-route loopback guard applies ONLY to POST /api/mcp.
# The owner's browser over the tailnet keeps its session through the
# existing _web_auth_gate middleware on all other routes.


def build_mcp_http_router(ctx: WebContext) -> APIRouter:
    router = APIRouter(tags=["mcp-http"])

    def _get_credential_store(request: Request) -> AgentCredentialStore:
        return getattr(request.app.state, "agent_credentials", AgentCredentialStore())

    def _remote_enabled(request: Request) -> bool:
        return bool(Config.load().remote.streamable_http_enabled)

    # ── POST /api/mcp ──────────────────────────────────────────────
    def _blocking_io_tools() -> frozenset[str]:
        """The tools that run beside the ordered queue: declared blocking I/O, and the long tools."""
        from ... import operations as _operations
        from ...mcp.long_tools import LONG_TOOLS

        return frozenset(d.name for d in _operations.DESCRIPTORS if d.blocking_io) | frozenset(LONG_TOOLS)

    _worker: list[Any] = []

    import threading as _threading

    _key_guard = _threading.Lock()
    _key_locks: dict[str, Any] = {}

    def _locks_for(keys: list[str]) -> list[Any]:
        """One lock per key (``holdspeak/mcp/long_tools.py:lock_keys``), made once."""
        with _key_guard:
            return [_key_locks.setdefault(key, _threading.Lock()) for key in keys]

    def _tool_worker() -> Any:
        """The one thread that runs MCP tool calls, first in, first out."""
        if not _worker:
            from concurrent.futures import ThreadPoolExecutor

            _worker.append(ThreadPoolExecutor(max_workers=1, thread_name_prefix="holdspeak-mcp-tools"))
        return _worker[0]

    @router.post("/api/mcp")
    async def mcp_http_endpoint(request: Request) -> JSONResponse:
        """Streamable HTTP transport for MCP JSON-RPC.

        Long-running contract (MCP-003): project.run_steward returns
        run_id promptly; the client polls project.get_steward_run(run_id).
        Terminal states: completed, failed, cancelled.  A credential
        expiring mid-run returns 403 on the poll; the run continues on
        the hub.
        """
        principal_probe = getattr(request.state, "principal", UNAUTHENTICATED)
        probe_host = request.client.host if request.client else "unknown"
        loopback_owner = (
            principal_probe.kind is PrincipalKind.OWNER
            and is_loopback_host(probe_host)
        )
        # The credential behind an AGENT principal (palette, launch binding).
        from ...web_auth import extract_request_token

        credential_store = _get_credential_store(request)
        token = extract_request_token(
            authorization=request.headers.get("authorization"),
            header_token=request.headers.get("x-holdspeak-token"),
            query_token=None,
        )
        cred = (
            credential_store.derive_credential(token)
            if token and principal_probe.kind is PrincipalKind.AGENT
            else None
        )
        # Conductor K6: an agent HoldSpeak launched on this machine is local
        # work, not Reach. Its launch-bound credential, from loopback, passes
        # with the Reach switch off. A hand-issued credential still needs it.
        loopback_launch_agent = (
            cred is not None
            and cred.launch_id is not None
            and is_loopback_host(probe_host)
        )
        # Betterment M1: an agent CLI run is a call INSIDE another call (a
        # model call the queue or a long tool is waiting on). Its calls never
        # wait behind that parent: no object lock, and not the one queue.
        from ...services.conductor_launch import RUN_IDENTITY_PREFIX

        run_agent = (
            cred is not None
            and cred.launch_id is not None
            and str(cred.principal.identity).startswith(RUN_IDENTITY_PREFIX)
        )

        # Gate: return 404 when the REMOTE transport is not enabled. A loopback
        # OWNER is the hub's own local transport (HS-200-45 R3) and passes with
        # the flag off -- the stdio sidecar proxies through here rather than
        # opening the database as a second writer.
        if not _remote_enabled(request) and not (loopback_owner or loopback_launch_agent):
            return JSONResponse(
                {"error": "streamable_http_not_enabled"},
                status_code=404,
            )

        # Counsel-on-built 174, condition 1: a credential never rides the
        # URL on this route (query strings land in access, proxy and
        # history logs), whatever principal the middleware derived from
        # it.  The runner sends ``Authorization: Bearer``.
        if request.query_params.get("token"):
            return JSONResponse(
                {"error": "token_in_query_refused",
                 "detail": "send the credential as Authorization: Bearer"},
                status_code=401,
            )

        principal = getattr(request.state, "principal", UNAUTHENTICATED)

        # HS-174 C5: per-route loopback guard -- OWNER from non-loopback
        # is refused on this route only.
        client_host = request.client.host if request.client else "unknown"
        if principal.kind is PrincipalKind.OWNER and not is_loopback_host(client_host):
            return JSONResponse(
                {
                    "error": "owner_refused_remote",
                    "detail": "OWNER principal is not accepted on the remote MCP path (XI:4).",
                },
                status_code=403,
            )

        # Unauthenticated -> 401.
        if principal.kind is PrincipalKind.NONE:
            return JSONResponse(
                {"error": "unauthenticated"},
                status_code=401,
            )

        # An AGENT whose credential died between the edge and here is refused,
        # never served without its palette.
        if principal.kind is PrincipalKind.AGENT and cred is None:
            return JSONResponse({"error": "unauthenticated"}, status_code=401)

        # Derive palette from the credential (if AGENT), derived above.
        palette: frozenset[str] | None = None
        call_gate: Any = None
        resource_gate: Any = None
        if cred and cred.palette is not None:
            palette = cred.palette
        if cred and cred.palette_name == "CONDUCTOR":
            # The palette is re-resolved per request, so a tool added since
            # the launch classifies itself; mixed tools are classed per call.
            from ...mcp.palettes import (
                conductor_call_allowed,
                conductor_resource_allowed,
                resolve_palette,
            )

            palette = resolve_palette("CONDUCTOR")
            # AG12: advertise the same immutable read-only posture enforced
            # again at dispatch. The second fence matters for callers that
            # send a tool name without first reading this list.
            from ...services.conductor_launch import reviewer_credential, reviewer_tool_allowed

            if reviewer_credential(principal) is not None:
                palette = frozenset(name for name in palette if reviewer_tool_allowed(name))
            call_gate = conductor_call_allowed
            resource_gate = conductor_resource_allowed

        # Parse JSON-RPC request body.
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
                status_code=200,
            )
        if not isinstance(body, dict):
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid Request"}},
                status_code=200,
            )

        # HS-174-04: tag origin BEFORE dispatch (H3: before returning, not after).
        from ...mcp.server import handle_message_for_principal

        is_remote = not is_loopback_host(client_host)
        origin_value = "remote" if is_remote else "local"
        identity_label = cred.principal.identity if cred else principal.identity

        def handle() -> Any:
            # Per-key locks (Astra on #867): calls on one object run one at a
            # time, whichever path they take; calls on different objects run
            # in parallel. Taken in sorted order, so no two calls deadlock.
            held: list[Any] = []
            call: dict[str, Any] = {}
            if body.get("method") == "tools/call":
                call = body.get("params") if isinstance(body.get("params"), dict) else {}
                arguments = call.get("arguments") if isinstance(call.get("arguments"), dict) else {}
                from ...mcp.long_tools import lock_keys, run_lock_keys

                keys = run_lock_keys if run_agent else lock_keys
                held = _locks_for(keys(str(call.get("name") or ""), arguments))
            for lock in held:
                lock.acquire()
            origin_token = _origin.set(origin_value)
            caller_token = _caller.set(client_host)
            identity_token = _caller_identity.set(identity_label)
            try:
                gates = (
                    {"call_gate": call_gate, "resource_gate": resource_gate}
                    if call_gate is not None or resource_gate is not None
                    else {}
                )
                response = handle_message_for_principal(body, principal, palette=palette, **gates)
                if run_agent and body.get("method") == "tools/call":
                    # Betterment M2: the run's call, against its run (Looked
                    # at / Wrote / Prepared on the automation's result).
                    from ...services import run_trace

                    run_trace.record_call(
                        run_trace.run_id_of(cred.principal.identity),
                        str(call.get("name") or ""), call.get("arguments"), response,
                    )
                elif cred is not None and body.get("method") == "tools/call":
                    # Betterment AG10: a launched agent's call, against its
                    # launch (Looked at / Wrote / Prepared on its Result).
                    from ...services import run_trace

                    launch_key = run_trace.launch_key_of(cred.principal.identity)
                    if launch_key:
                        run_trace.record_call(
                            launch_key, str(call.get("name") or ""), call.get("arguments"), response,
                        )
                return response
            finally:
                _origin.reset(origin_token)
                _caller.reset(caller_token)
                _caller_identity.reset(identity_token)
                for lock in reversed(held):
                    lock.release()

        # A tool call never runs on the event loop. A tool body is synchronous;
        # one that calls an async service hands the coroutine back to this loop
        # (``holdspeak/mcp/aio.py``) and waits for it, and on the loop that wait
        # is impossible (before 2026-10-03 every async tool refused here).
        #
        # Order (PHILO-10-02 GATE 2, kept): tool calls run ONE AT A TIME, in
        # arrival order, on the one MCP worker thread. The services are not
        # safe for two writers (two ``desk.update`` calls on one Note lose a
        # change). Two exceptions run on the thread pool beside that queue: an
        # operation that DECLARES blocking I/O
        # (``OperationDescriptor.blocking_io``) and a tool named in
        # ``holdspeak/mcp/long_tools.py`` (a model call, gh, acli). Every call
        # takes its per-key locks first (``handle`` above), so a slow tool
        # holds only the calls on its own objects. A third: every call of an
        # agent CLI run (``run_agent`` above), whose parent may be the very
        # call the queue is running.
        # The flag decides ordering only; no tool needs it to work.
        params = body.get("params") if isinstance(body.get("params"), dict) else {}
        if body.get("method") != "tools/call":
            response = handle()
        elif run_agent or params.get("name") in _blocking_io_tools():
            from starlette.concurrency import run_in_threadpool

            response = await run_in_threadpool(handle)
        else:
            import asyncio

            response = await asyncio.get_running_loop().run_in_executor(_tool_worker(), handle)

        if response is None:
            # Notification (no response expected). A bare Response: a
            # JSONResponse(None) serialises the literal ``null`` into a 204,
            # and uvicorn raises "Response content longer than Content-Length"
            # on every sidecar handshake (HS-200-45 counsel P1-1).
            return Response(status_code=204)
        return JSONResponse(content=response, status_code=200)

    # All remote settings verbs are produced from owner-only declarations.
    from fastapi import Depends
    from ...access_operations import REMOTE_ACCESS_OPERATIONS
    from ...services.remote_access_service import credential_store_context
    from ... import operations
    from ..operation_routes import operation_router

    async def credentials(request: Request):
        token = credential_store_context.set(_get_credential_store(request))
        try:
            yield
        finally:
            credential_store_context.reset(token)

    def registry() -> Any:
        return operations.for_context(ctx, remote_access_service=lambda: _remote_service(ctx))

    def issue(descriptor: Any) -> Any:
        async def endpoint(request: Request) -> Any:
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            try:
                registry().authorize(principal, descriptor.name)
            except operations.OperationOwnerRequired as exc:
                return JSONResponse({"error": exc.code}, status_code=403)
            try:
                body = await request.json()
            except ValueError:
                body = None
            if not isinstance(body, dict):
                return JSONResponse({"error": "invalid_arguments"}, status_code=400)
            args = {k: v for k, v in body.items() if k != "identity"}
            args["agent_identity"] = body.get("identity")
            return await _remote_answer(lambda: registry().invoke(principal, descriptor.name, args, shape="web"))
        endpoint.__name__ = descriptor.handler
        return endpoint

    def grant(descriptor: Any) -> Any:
        # Grant codecs receipt malformed bodies. The generic producer treats a
        # non-object as {}, which would grant instead of refusing that attempt.
        async def call(request: Request, agent_identity: str, project_id: str | None = None) -> Any:
            import json
            raw = await request.body()
            try:
                body = json.loads(raw) if raw.strip() else {}
            except ValueError:
                body = None
            principal = getattr(request.state, "principal", UNAUTHENTICATED)
            args = {"agent_identity": agent_identity, "body": body}
            if project_id is not None:
                args["project_id"] = project_id
            return await _remote_answer(lambda: registry().invoke(principal, descriptor.name, args, shape="web"))

        if "{project_id}" in descriptor.http[1]:
            async def endpoint(agent_identity: str, project_id: str, request: Request) -> Any:
                return await call(request, agent_identity, project_id)
        else:
            async def endpoint(agent_identity: str, request: Request) -> Any:
                return await call(request, agent_identity)
        endpoint.__name__ = descriptor.handler
        return endpoint

    router.include_router(operation_router(
        REMOTE_ACCESS_OPERATIONS, registry, _remote_answer, module=__name__,
        hand_written={"settings.remote.credential.create": issue,
                      **{row.name: grant for row in REMOTE_ACCESS_OPERATIONS if "delegation" in row.method}},
    ), dependencies=[Depends(credentials)])
    return router


def _remote_service(ctx: WebContext) -> Any:
    from ...services.remote_access_service import RemoteAccessService
    return RemoteAccessService(ctx.settings_service)


async def _remote_answer(fn: Any, *, status: int = 200) -> JSONResponse:
    from starlette.concurrency import run_in_threadpool
    from ...operations import OperationRefused
    from ...services.errors import ServiceError

    try:
        return JSONResponse(await run_in_threadpool(fn), status_code=status)
    except OperationRefused as exc:
        return JSONResponse({"error": exc.code}, status_code=403 if exc.code == "owner_required" else 400)
    except ServiceError as exc:
        return JSONResponse(exc.context.get("response") or {"error": exc.code, "detail": exc.detail, **exc.context},
                            status_code=int(exc.context.get("status") or 409))
    except (TypeError, ValueError):
        return JSONResponse({"error": "invalid_arguments"}, status_code=400)
