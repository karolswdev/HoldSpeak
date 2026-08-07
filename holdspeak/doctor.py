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
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DEFAULT_URL = "http://127.0.0.1:8765"
_TIMEOUT_SECONDS = 3.0


@dataclass(frozen=True)
class DoctorResult:
    """One machine-readable diagnostic result."""

    status: str
    name: str
    detail: str

    def line(self) -> str:
        return f"{self.status:<5} {self.name:<17} {self.detail}"


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


def _get_json(url: str, path: str, token: str = "") -> tuple[int, object]:
    request = Request(f"{url}{path}", headers=_headers(token), method="GET")
    with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310 - operator-configured hub
        raw = response.read()
        return response.status, json.loads(raw.decode("utf-8"))


def _get_html(url: str) -> tuple[int, str]:
    request = Request(f"{url}/", method="GET")
    with urlopen(request, timeout=_TIMEOUT_SECONDS) as response:  # noqa: S310 - operator-configured hub
        return response.status, response.read().decode("utf-8", errors="replace")


def _failure(exc: Exception) -> str:
    if isinstance(exc, HTTPError):
        return f"HTTP {exc.code}"
    if isinstance(exc, URLError):
        return str(exc.reason)
    return str(exc) or type(exc).__name__


def _check_hub_health(url: str, token: str) -> DoctorResult:
    try:
        status, payload = _get_json(url, "/health", token)
        if status == 200 and payload == {"status": "ok"}:
            return DoctorResult("PASS", "hub-health", "/health → ok")
        return DoctorResult("FAIL", "hub-health", f"unexpected response: {payload!r}")
    except Exception as exc:  # each doctor check must remain independent
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
        with connect(
            ws_url,
            additional_headers=_headers(token),
            open_timeout=_TIMEOUT_SECONDS,
            close_timeout=_TIMEOUT_SECONDS,
        ) as websocket:
            websocket.send("ping")
            frame = websocket.recv(timeout=_TIMEOUT_SECONDS)
        elapsed_ms = int((time.monotonic() - start) * 1000)
        if frame == "pong":
            return DoctorResult("PASS", "websocket", f"frame received in {elapsed_ms}ms")
        return DoctorResult("FAIL", "websocket", f"unexpected frame: {frame!r}")
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
        return DoctorResult("PASS", "database", "primitives readable")
    except Exception as exc:
        return DoctorResult("FAIL", "database", _failure(exc))


def run_checks(url: str | None = None, token: str | None = None) -> list[DoctorResult]:
    """Run every desk diagnostic, collecting failures instead of raising them."""
    try:
        hub_url = _base_url(url or os.environ.get("HOLDSPEAK_URL", DEFAULT_URL))
    except ValueError as exc:
        return [DoctorResult("FAIL", name, str(exc)) for name in (
            "hub-health", "runtime-status", "websocket", "desk-bootstrap", "auth", "inference"
        )] + [_check_mcp_server(), _check_database()]

    credential = token if token is not None else os.environ.get("HOLDSPEAK_TOKEN", "")
    return [
        _check_hub_health(hub_url, credential),
        _check_runtime_status(hub_url, credential),
        _check_websocket(hub_url, credential),
        _check_desk_bootstrap(hub_url, credential),
        _check_auth(hub_url, credential),
        _check_mcp_server(),
        _check_inference(hub_url, credential),
        _check_database(),
    ]


def run_doctor(
    url: str | None = None,
    token: str | None = None,
    *,
    output: Callable[[str], None] = print,
) -> int:
    """Print diagnostics and return 0 unless a check failed."""
    results = run_checks(url, token)
    for result in results:
        output(result.line())
    counts = {status: sum(result.status == status for result in results) for status in ("PASS", "SKIP", "FAIL")}
    output(f"\n{counts['PASS']} PASS · {counts['SKIP']} SKIP · {counts['FAIL']} FAIL")
    return 1 if counts["FAIL"] else 0


def main() -> int:
    return run_doctor()


if __name__ == "__main__":
    raise SystemExit(main())
