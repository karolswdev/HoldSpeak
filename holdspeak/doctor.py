"""Deterministic health checks for a running HoldSpeak desk hub.

This module deliberately checks the hub's public seams rather than starting a
browser or loading an audio backend.  It is safe to run against a remote hub.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener, urlopen

DEFAULT_URL = "http://127.0.0.1:8765"
_TIMEOUT_SECONDS = 3.0

#: PHILO-15 11 (B08): the hub-health detail when nothing listens at the hub
#: address.  ``run_doctor`` prints one plain line for it, not one connection
#: error per network check.
HUB_NOT_RUNNING = "not running"

#: PHILO-15 11 (B08): the words a person reads for each check.  ``name`` stays
#: the machine id (tests and scripts key on it); the printed row uses the label.
ROW_LABELS = {
    "hub-health": "Hub",
    "runtime-status": "Hub status",
    "runtime-preflight": "AI model test",
    "websocket": "Live link",
    "desk-bootstrap": "Desk page",
    "auth": "Hub token",
    "mcp-server": "Agent server",
    "inference": "AI places",
    "database": "Database",
    "observer": "Event log",
}

def is_starter_model(path: str) -> bool:
    """True only for the starter model that Set up local AI downloads.

    The identity is the content-addressed artifact folder plus the file name
    of ``DEFAULT_INTEL_MODEL_PATH`` (the signed starter preset), never a path
    substring: a custom model under ``models/artifacts`` is not the starter
    (Astra r1 on #986).
    """
    from pathlib import PurePosixPath

    from .intel.models import DEFAULT_INTEL_MODEL_PATH

    starter = PurePosixPath(DEFAULT_INTEL_MODEL_PATH)
    given = PurePosixPath(str(path).strip().rstrip("."))
    return given.name == starter.name and given.parent.name == starter.parent.name


#: PHILO-15 11 (Astra r1 on #986): engine ids as a person reads them, on
#: the printed line only (the check data keeps the wire ids).
PLAIN_WORDS = (
    ("openai_compatible", "OpenAI-compatible server"),
    ("llama_cpp", "llama.cpp"),
)


def plain(text: str) -> str:
    """The printed words for one doctor detail or fix line."""
    for wire, words in PLAIN_WORDS:
        text = text.replace(wire, words)
    return text


#: The local AI card on the first-run page downloads the product's model.
SET_UP_LOCAL_AI = "Start HoldSpeak (`holdspeak`) and push Set up local AI on the Local AI card."


@dataclass(frozen=True)
class DoctorResult:
    """One machine-readable diagnostic result."""

    status: str
    name: str
    detail: str

    @property
    def label(self) -> str:
        return ROW_LABELS.get(self.name, self.name)

    def line(self) -> str:
        return f"{self.status:<5} {self.label:<14} {plain(self.detail)}"


def _base_url(url: str) -> str:
    cleaned = url.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("HOLDSPEAK_URL must be an http:// or https:// URL")
    return cleaned


def _headers(token: str) -> dict[str, str]:
    if not token:
        return {}
    # Send both supported forms. The explicit HoldSpeak header avoids relying
    # on a proxy preserving Authorization, while the bearer form works with
    # clients that only recognize the conventional header.
    return {"Authorization": f"Bearer {token}", "X-HoldSpeak-Token": token}


class _NoRedirect(HTTPRedirectHandler):
    """A request that carries the hub token never follows a redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        raise HTTPError(req.full_url, code, "redirect refused: the request carries a token", headers, fp)


#: A token-bearing request to a named hub: no redirect (proxies as configured).
_TOKEN_OPENER = build_opener(_NoRedirect())
#: A token-bearing request to a loopback hub: no redirect and no proxy, so the
#: token reaches 127.0.0.1 and nothing else (holdspeak/loopback_http.py rules).
_LOOPBACK_TOKEN_OPENER = build_opener(ProxyHandler({}), _NoRedirect())


def _open(request: Request) -> Any:
    """Open one doctor request.  With a token: never a redirect; loopback: no proxy."""
    if not request.has_header("Authorization"):
        return urlopen(request, timeout=_TIMEOUT_SECONDS)  # noqa: S310 - operator-configured hub
    from .loopback_http import is_loopback_url

    opener = _LOOPBACK_TOKEN_OPENER if is_loopback_url(request.full_url) else _TOKEN_OPENER
    return opener.open(request, timeout=_TIMEOUT_SECONDS)  # noqa: S310 - operator-configured hub


def _get_json(url: str, path: str, token: str = "") -> tuple[int, object]:
    request = Request(f"{url}{path}", headers=_headers(token), method="GET")
    with _open(request) as response:
        raw = response.read()
        return response.status, json.loads(raw.decode("utf-8"))


def _get_html(url: str) -> tuple[int, str]:
    request = Request(f"{url}/", method="GET")
    with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310 - operator-configured hub
        return response.status, response.read().decode("utf-8", errors="replace")


def _post_json(url: str, path: str, token: str = "") -> tuple[int, object]:
    request = Request(
        f"{url}{path}", headers=_headers(token), data=b"{}", method="POST"
    )
    request.add_header("Content-Type", "application/json")
    with _open(request) as response:
        raw = response.read()
        return response.status, json.loads(raw.decode("utf-8"))


def _failure(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, URLError):
        return str(exc.reason)
    return str(exc) or type(exc).__name__


def _refused(exc: Exception) -> bool:
    """True when nothing listens at the hub address (the hub is not running)."""
    reason = exc.reason if isinstance(exc, URLError) and not isinstance(exc, HTTPError) else exc
    return isinstance(reason, ConnectionRefusedError)


def _check_hub_health(url: str, token: str) -> DoctorResult:
    try:
        status, payload = _get_json(url, "/health", token)
        if status == 200 and payload == {"status": "ok"}:
            return DoctorResult("PASS", "hub-health", "running")
        return DoctorResult("FAIL", "hub-health", f"unexpected response: {payload!r}")
    except Exception as exc:  # each doctor check must remain independent
        if _refused(exc):
            return DoctorResult("FAIL", "hub-health", HUB_NOT_RUNNING)
        return DoctorResult("FAIL", "hub-health", _failure(exc))


def _check_runtime_status(url: str, token: str) -> DoctorResult:
    try:
        status, payload = _get_json(url, "/api/runtime/status", token)
        ready = isinstance(payload, dict) and (
            payload.get("status") in {"ok", "ready"}
            or payload.get("runtime_status") == "ready"
        )
        if status == 200 and ready:
            return DoctorResult("PASS", "runtime-status", "ready")
        return DoctorResult("FAIL", "runtime-status", f"unexpected response: {payload!r}")
    except Exception as exc:
        return DoctorResult("FAIL", "runtime-status", _failure(exc))


def _check_runtime_preflight(url: str, token: str) -> DoctorResult:
    """Report the configured inference endpoint's actual reachability."""
    try:
        status, payload = _post_json(url, "/api/setup/runtime-test", token)
        if not isinstance(payload, dict):
            return DoctorResult("FAIL", "runtime-preflight", f"unexpected response: {payload!r}")
        detail = str(payload.get("detail") or payload.get("error") or "no detail")
        if status == 200 and payload.get("ok") is True:
            return DoctorResult("PASS", "runtime-preflight", detail)
        if detail.startswith("Model not found at"):
            path = detail.removeprefix("Model not found at").strip().rstrip(".")
            name = path.rsplit("/", 1)[-1]
            if is_starter_model(path):
                # PHILO-15 11 (B08): the starter model, not downloaded yet.
                # That is a step still to do, not a failure.
                return DoctorResult(
                    "SKIP", "runtime-preflight", f"the local AI model {name} is not downloaded yet. {SET_UP_LOCAL_AI}"
                )
            # A model the owner chose, and its file is gone: a real fault.
            return DoctorResult("FAIL", "runtime-preflight", f"model file missing: {name} ({path})")
        return DoctorResult("FAIL", "runtime-preflight", detail)
    except Exception as exc:
        return DoctorResult("FAIL", "runtime-preflight", _failure(exc))


def _check_websocket(url: str, token: str) -> DoctorResult:
    if not token:
        return DoctorResult("SKIP", "websocket", "no token configured")
    try:
        from websockets.sync.client import connect
    except ImportError:
        return DoctorResult("FAIL", "websocket", "websockets package unavailable")

    parsed = urlparse(url)
    scheme = "wss" if parsed.scheme == "https" else "ws"
    ws_url = f"{scheme}://{parsed.netloc}{parsed.path.rstrip('/')}/ws"
    start = time.monotonic()
    try:
        from .loopback_http import is_loopback_url

        with connect(
            ws_url,
            additional_headers=_headers(token),
            # A loopback hub is reached directly, never through a proxy (the
            # sync client follows no redirect).
            **({"proxy": None} if is_loopback_url(url) else {}),
            open_timeout=_TIMEOUT_SECONDS,
            close_timeout=_TIMEOUT_SECONDS,
        ) as websocket:
            websocket.send("ping")
            # The hub also pushes its own frames (the first is "duration"), so
            # read until the pong, bounded by the timeout and a frame count.
            deadline = start + _TIMEOUT_SECONDS
            frame: object = None
            for _ in range(50):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                frame = websocket.recv(timeout=remaining)
                if frame == "pong":
                    break
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if frame == "pong":
            return DoctorResult("PASS", "websocket", f"pong received in {elapsed_ms}ms")
        return DoctorResult("FAIL", "websocket", f"no pong; last frame: {frame!r}")
    except Exception as exc:
        return DoctorResult("FAIL", "websocket", _failure(exc))


def _check_desk_bootstrap(url: str, token: str) -> DoctorResult:
    try:
        status, body = _get_html(url)
        if status == 200 and "<html" in body.lower():
            return DoctorResult("PASS", "desk-bootstrap", "/ → 200")
        return DoctorResult("FAIL", "desk-bootstrap", "response is not HTML")
    except Exception as exc:
        return DoctorResult("FAIL", "desk-bootstrap", _failure(exc))


def _check_auth(url: str, token: str) -> DoctorResult:
    if not token:
        return DoctorResult("SKIP", "auth", "no token configured")
    try:
        status, payload = _get_json(url, "/api/runtime/status", token)
        if status == 200 and isinstance(payload, dict):
            return DoctorResult("PASS", "auth", "principal: authenticated")
        return DoctorResult("FAIL", "auth", f"unexpected response: {payload!r}")
    except Exception as exc:
        return DoctorResult("FAIL", "auth", _failure(exc))


def _check_mcp_server() -> DoctorResult:
    executable = shutil.which("holdspeak-mcp")
    if executable is None:
        return DoctorResult("SKIP", "mcp-server", "not available")

    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            [executable],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        assert process.stdin is not None and process.stdout is not None
        process.stdin.write(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "holdspeak-doctor", "version": "1"},
                    },
                }
            )
            + "\n"
        )
        process.stdin.flush()
        executor = ThreadPoolExecutor(max_workers=1)
        try:
            line = executor.submit(process.stdout.readline).result(timeout=_TIMEOUT_SECONDS)
        finally:
            # Do not wait for readline before terminating the sidecar below:
            # an unavailable sidecar must make doctor fail promptly.
            executor.shutdown(wait=False, cancel_futures=True)
        response = json.loads(line)
        if response.get("id") == 1 and "result" in response:
            return DoctorResult("PASS", "mcp-server", "initialization received")
        return DoctorResult("FAIL", "mcp-server", f"unexpected response: {response!r}")
    except Exception as exc:
        return DoctorResult("FAIL", "mcp-server", _failure(exc))
    finally:
        if process is not None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def _check_inference(url: str, token: str) -> DoctorResult:
    if not token:
        return DoctorResult("SKIP", "inference", "no token configured")
    try:
        status, payload = _get_json(url, "/api/inference-targets", token)
        targets = payload.get("targets", []) if isinstance(payload, dict) else []
        ready = [target for target in targets if target.get("readiness", {}).get("available")]
        if status == 200 and ready:
            return DoctorResult("PASS", "inference", f"target: {ready[0].get('id', 'ready')}")
        if status == 200:
            return DoctorResult("SKIP", "inference", "no targets configured")
        return DoctorResult("FAIL", "inference", f"unexpected response: {payload!r}")
    except Exception as exc:
        return DoctorResult("FAIL", "inference", _failure(exc))


def _check_database() -> DoctorResult:
    try:
        from .db import get_database
        from .principals import Principal, PrincipalKind
        from .services.primitive_service import PrimitiveService

        PrimitiveService(get_database()).list_notes(Principal(PrincipalKind.OWNER, "doctor"))
        return DoctorResult("PASS", "database", "notes readable")
    except Exception as exc:
        return DoctorResult("FAIL", "database", _failure(exc))


def check_observer() -> DoctorResult:
    """Verify the pipeline observer's event table can round-trip an event."""
    try:
        from .db import get_database

        database = get_database()
        with database._connection() as conn:
            table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                ("pipeline_events",),
            ).fetchone()
            if table is None:
                return DoctorResult(
                    "FAIL", "observer", "unhealthy: pipeline_events table missing; 24h events: unavailable"
                )

            recent_events = conn.execute(
                "SELECT COUNT(*) FROM pipeline_events WHERE timestamp >= ?",
                (time.time() - 86_400,),
            ).fetchone()[0]
            event_id = f"doctor-probe-{uuid.uuid4()}"
            try:
                conn.execute(
                    """
                    INSERT INTO pipeline_events (
                        event_id, timestamp, service, method, principal_kind
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (event_id, time.time(), "doctor", "check_observer", "system"),
                )
                event = conn.execute(
                    "SELECT event_id FROM pipeline_events WHERE event_id = ?", (event_id,)
                ).fetchone()
                if event is None:
                    raise RuntimeError("probe event was not readable")
            finally:
                conn.execute("DELETE FROM pipeline_events WHERE event_id = ?", (event_id,))

        return DoctorResult("PASS", "observer", f"healthy: 24h events: {recent_events}")
    except Exception as exc:
        return DoctorResult("FAIL", "observer", f"degraded: {_failure(exc)}; 24h events: unavailable")


def discovered_hub_url() -> str | None:
    """The running hub's real URL, from its owner lock beside the database.

    The hub binds port 8765 (``web_server.DEFAULT_WEB_PORT``), or a free
    port when another process holds 8765, and writes the port it took into
    its owner lock.  ``holdspeak-mcp`` finds the hub
    the same way (``holdspeak.mcp.server.discover_hub``).  Reading the lock
    opens no database and makes no network request.
    """
    try:
        from .mcp.server import discover_hub

        hub = discover_hub()
    except Exception:
        return None
    if not hub:
        return None
    return f"http://{hub['host']}:{int(hub['port'])}"


def _local_owner_token() -> str:
    try:
        from .mcp.server import _owner_token

        return _owner_token()
    except Exception:
        return ""


def resolve_hub_url(url: str | None = None) -> str:
    """The hub to check: the argument, then HOLDSPEAK_URL, then the running
    hub's real port, then the fixed fallback."""
    return url or os.environ.get("HOLDSPEAK_URL", "") or discovered_hub_url() or DEFAULT_URL


def run_checks(url: str | None = None, token: str | None = None) -> list[DoctorResult]:
    """Run every desk diagnostic, collecting failures instead of raising them."""
    try:
        hub_url = _base_url(resolve_hub_url(url))
    except ValueError as exc:
        return [DoctorResult("FAIL", name, str(exc)) for name in (
            "hub-health", "runtime-status", "websocket", "desk-bootstrap", "auth", "inference"
        )] + [_check_mcp_server(), _check_database(), check_observer()]

    credential = token if token is not None else os.environ.get("HOLDSPEAK_TOKEN", "")
    if not credential and not url and not os.environ.get("HOLDSPEAK_URL", ""):
        from .loopback_http import is_loopback_url, pin_loopback_url

        # The hub on THIS machine (its owner lock, or 127.0.0.1:8765): its
        # owner token is in the config file, as holdspeak-mcp reads it.  It
        # goes only to a loopback literal (pinned 127.0.0.1), never through a
        # proxy and never across a redirect (_open), and never to a URL the
        # caller named.
        if is_loopback_url(hub_url):
            hub_url = pin_loopback_url(hub_url)
            credential = _local_owner_token()
    hub = _check_hub_health(hub_url, credential)
    if getattr(hub, "detail", None) == HUB_NOT_RUNNING:
        # PHILO-15 11 (B08): no hub, so every other hub check can only say
        # "connection refused".  One line says it.
        return [hub]
    return [
        hub,
        _check_runtime_status(hub_url, credential),
        _check_runtime_preflight(hub_url, credential),
        _check_websocket(hub_url, credential),
        _check_desk_bootstrap(hub_url, credential),
        _check_auth(hub_url, credential),
        _check_mcp_server(),
        _check_inference(hub_url, credential),
        _check_database(),
        check_observer(),
    ]


def run_doctor(
    url: str | None = None,
    token: str | None = None,
    *,
    output: Callable[[str], None] = print,
) -> int:
    """Print diagnostics and return 0 unless a check failed.

    A hub that is not running is not a failure (before the first launch it is
    the normal state): one line says so and how to start it.
    """
    results = run_checks(url, token)
    if len(results) == 1 and results[0].name == "hub-health" and results[0].detail == HUB_NOT_RUNNING:
        output(hub_not_running_line(url))
        return 0
    for result in results:
        output(result.line())
    counts = {status: sum(result.status == status for result in results) for status in ("PASS", "SKIP", "FAIL")}
    output(f"\n{counts['PASS']} PASS · {counts['SKIP']} SKIP · {counts['FAIL']} FAIL")
    return 1 if counts["FAIL"] else 0


def hub_not_running_line(url: str | None = None) -> str:
    """The one line ``holdspeak doctor`` prints when the hub is not running."""
    if url or os.environ.get("HOLDSPEAK_URL", ""):
        return f"HUB · NOT RUNNING · nothing answers at {resolve_hub_url(url)}"
    return "HUB · NOT RUNNING · start it with `holdspeak`"


def main() -> int:
    return run_doctor()


if __name__ == "__main__":
    raise SystemExit(main())
