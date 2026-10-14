"""Bounded, owner-initiated discovery of OpenAI-compatible engines on the LAN.

The scan is deliberately separate from Concierge detection.  Detection is a
cheap read that may happen while a face opens; this operation is an explicit
owner press and therefore has a small, honest network budget.  It only sends
GET requests to private IPv4 addresses and never reads a saved key or writes a
profile.
"""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from http.client import HTTPResponse
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from ..setup_runtime import discover_endpoint_models
from .inference_default_service import LOOPBACK_ENGINE_PORTS, is_chat_model

# The same four common engine ports the local scanner knows.  The LAN scan
# never imports or changes the local scanner's loopback-only behavior.
LAN_ENGINE_PORTS: tuple[tuple[int, str], ...] = LOOPBACK_ENGINE_PORTS
MAX_NETWORK_WINDOWS = 2
MAX_WORKERS = 64
SCAN_DEADLINE_SECONDS = 8.0
TCP_PREFLIGHT_SECONDS = 0.15
HTTP_PROBE_SECONDS = 0.5


@dataclass(frozen=True)
class LanInterface:
    address: ipaddress.IPv4Address
    network: ipaddress.IPv4Network


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: HTTPResponse,
        code: int,
        msg: str,
        headers: Mapping[str, str],
        newurl: str,
    ) -> None:
        raise HTTPError(req.full_url, code, "redirect refused", headers, fp)


_LAN_OPENER = build_opener(ProxyHandler({}), _NoRedirect())
_INET_RE = re.compile(r"\binet\s+(\d+\.\d+\.\d+\.\d+)(?:/(\d+))?")
_IFCONFIG_RE = re.compile(
    r"\binet\s+(\d+\.\d+\.\d+\.\d+)\s+netmask\s+(0x[0-9a-fA-F]+|\d+\.\d+\.\d+\.\d+)"
)


def _valid_interface(address: str, prefix: int | None) -> LanInterface | None:
    try:
        ip = ipaddress.IPv4Address(address)
        if not ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast:
            return None
        if prefix is None:
            prefix = 24
        interface = ipaddress.IPv4Interface(f"{ip}/{int(prefix)}")
        return LanInterface(ip, interface.network)
    except (ValueError, TypeError):
        return None


def _mask_prefix(mask: str) -> int | None:
    try:
        if mask.lower().startswith("0x"):
            value = int(mask, 16)
            return value.bit_count() if 0 <= value <= 0xFFFFFFFF else None
        return ipaddress.IPv4Network(f"0.0.0.0/{mask}").prefixlen
    except ValueError:
        return None


def _run(argv: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            list(argv), capture_output=True, text=True, timeout=1.0, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout or ""


def _parse_ifconfig(output: str) -> list[LanInterface]:
    found: list[LanInterface] = []
    for line in output.splitlines():
        match = _IFCONFIG_RE.search(line)
        if not match:
            continue
        row = _valid_interface(match.group(1), _mask_prefix(match.group(2)))
        if row is not None:
            found.append(row)
    return found


def _parse_ip_json(output: str) -> list[LanInterface]:
    try:
        rows = json.loads(output)
    except (TypeError, json.JSONDecodeError):
        return []
    found: list[LanInterface] = []
    for interface in rows if isinstance(rows, list) else []:
        for address in interface.get("addr_info", []) if isinstance(interface, dict) else []:
            if not isinstance(address, dict) or address.get("family") not in ("inet", 2):
                continue
            row = _valid_interface(str(address.get("local") or ""), int(address["prefixlen"]) if address.get("prefixlen") is not None else None)
            if row is not None:
                found.append(row)
    return found


def _parse_ip_text(output: str) -> list[LanInterface]:
    found: list[LanInterface] = []
    for line in output.splitlines():
        match = _INET_RE.search(line)
        if not match:
            continue
        row = _valid_interface(match.group(1), int(match.group(2)) if match.group(2) else None)
        if row is not None:
            found.append(row)
    return found


def _interface_snapshot() -> tuple[tuple[LanInterface, ...], str]:
    """Read private IPv4 addresses and name the source for honest reporting."""
    found = _parse_ip_json(_run(("ip", "-json", "-4", "addr", "show")))
    source = "ip-json"
    if not found:
        found = _parse_ip_text(_run(("ip", "-4", "-o", "addr", "show")))
        source = "ip"
    if not found:
        found = _parse_ifconfig(_run(("ifconfig",)))
        source = "ifconfig"
    if not found:
        # A stdlib-only fallback has no portable netmask API.  Its bounded /24
        # result is marked partial by the caller, never reported as complete.
        source = "stdlib-fallback"
        try:
            names = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        except OSError:
            names = []
        for item in names:
            address = str(item[4][0]) if item and item[4] else ""
            row = _valid_interface(address, 24)
            if row is not None:
                found.append(row)
    unique = {(str(row.address), str(row.network)): row for row in found}
    return tuple(unique[key] for key in sorted(unique)), source


def attached_private_ipv4_interfaces() -> tuple[LanInterface, ...]:
    """Read private IPv4 addresses from the host's interfaces, without sockets."""
    return _interface_snapshot()[0]


def _window_for_interface(interface: LanInterface) -> ipaddress.IPv4Network:
    """The bounded window for one interface, never outside a narrow network."""
    if interface.network.prefixlen < 24:
        return ipaddress.IPv4Network(f"{interface.address}/24", strict=False)
    return interface.network


def _candidate_windows(interfaces: Iterable[LanInterface]) -> tuple[ipaddress.IPv4Network, ...]:
    windows: dict[str, ipaddress.IPv4Network] = {}
    for interface in interfaces:
        address = interface.address
        if not address.is_private:
            continue
        window = _window_for_interface(interface)
        if not window.overlaps(interface.network):
            continue
        windows[str(window)] = window
    return tuple(windows[key] for key in sorted(windows)[:MAX_NETWORK_WINDOWS])


def _hosts(interfaces: Sequence[LanInterface]) -> tuple[str, ...]:
    self_addresses = {interface.address for interface in interfaces}
    candidates: set[ipaddress.IPv4Address] = set()
    for network in _candidate_windows(interfaces):
        candidates.update(network.hosts())
    candidates.difference_update(self_addresses)
    return tuple(str(address) for address in sorted(candidates))


def _lan_http_get(url: str, *, headers: dict[str, str], timeout: float) -> tuple[int, bytes]:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("LAN discovery requires an IPv4 address") from exc
    if not isinstance(address, ipaddress.IPv4Address) or not address.is_private:
        raise ValueError("LAN discovery only permits private IPv4 addresses")
    request = Request(url, headers=headers, method="GET")
    with _LAN_OPENER.open(request, timeout=max(0.01, timeout)) as response:  # noqa: S310
        return int(getattr(response, "status", 200) or 200), response.read()


def _probe_endpoint(base_url: str, *, timeout: float) -> dict[str, Any]:
    """TCP preflight, then one keyless GET /v1/models."""
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    port = int(parsed.port or 80)
    if not host or not ipaddress.ip_address(host).is_private:
        return {"ok": False, "models": []}
    with socket.create_connection((host, port), timeout=min(timeout, TCP_PREFLIGHT_SECONDS)):
        pass
    return discover_endpoint_models(
        base_url,
        timeout_seconds=min(timeout, HTTP_PROBE_SECONDS),
        http_get=_lan_http_get,
    )


def _row(host: str, port: int, model: str) -> dict[str, Any]:
    base_url = f"http://{host}:{port}/v1"
    return {
        "id": f"lan:{host}:{port}:{model}",
        "kind": "lan",
        "name": model,
        "legacyLabel": model,
        "host": host,
        "state": "READY",
        "baseUrl": base_url,
        "found": True,
    }


def scan_lan_engines(
    *,
    interfaces: Sequence[LanInterface] | Callable[[], Sequence[LanInterface]] | None = None,
    ports: Sequence[tuple[int, str]] = LAN_ENGINE_PORTS,
    probe: Callable[[str], dict[str, Any]] | None = None,
    deadline_seconds: float = SCAN_DEADLINE_SECONDS,
    max_workers: int = MAX_WORKERS,
) -> dict[str, Any]:
    """Return transient Found rows from at most two private /24 windows."""
    interface_source = "injected"
    if interfaces is None:
        selected, interface_source = _interface_snapshot()
    else:
        raw_interfaces = interfaces() if callable(interfaces) else interfaces
        selected = tuple(raw_interfaces)
    normalized = tuple(
        row if isinstance(row, LanInterface) else _valid_interface(str(row), 24)
        for row in selected
    )
    usable = tuple(row for row in normalized if row is not None)
    hosts = _hosts(usable)
    targets = [(host, int(port)) for host in hosts for port, _engine in ports]
    all_windows = {str(_window_for_interface(row)) for row in usable}
    bounded = (
        bool(usable)
        and interface_source != "stdlib-fallback"
        and all(interface.network.prefixlen >= 24 for interface in usable)
        and len(all_windows) <= MAX_NETWORK_WINDOWS
    )
    if not usable:
        return {
            "engines": [],
            "partial": False,
            "unavailable": True,
            "reason": "LAN interface addresses are unavailable.",
            "hostsChecked": 0,
            "portsChecked": 0,
        }
    started = time.monotonic()
    probe_fn = probe or (lambda base_url: _probe_endpoint(base_url, timeout=HTTP_PROBE_SECONDS))
    results: list[dict[str, Any]] = []
    futures: dict[Any, tuple[str, int]] = {}
    completed_hosts: set[str] = set()
    workers = max(1, min(int(max_workers), MAX_WORKERS))
    timed_out = False
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="holdspeak-lan-scan") as pool:
        for host, port in targets:
            if time.monotonic() - started >= deadline_seconds:
                break
            futures[pool.submit(probe_fn, f"http://{host}:{port}/v1")] = (host, port)
        remaining = max(0.0, deadline_seconds - (time.monotonic() - started))
        try:
            completed = as_completed(futures, timeout=remaining)
            for future in completed:
                host, port = futures[future]
                completed_hosts.add(host)
                try:
                    answer = future.result()
                except Exception:
                    continue
                if not isinstance(answer, dict) or not answer.get("ok"):
                    continue
                for model in answer.get("models") or []:
                    model_name = str(model or "").strip()
                    if model_name and is_chat_model(model_name):
                        results.append(_row(host, port, model_name))
        except TimeoutError:
            timed_out = True
            for future in futures:
                future.cancel()
    unique = {(row["host"], row["baseUrl"], row["name"]): row for row in results}
    partial = (
        not bounded
        or timed_out
        or len(futures) < len(targets)
        or time.monotonic() - started >= deadline_seconds
    )
    return {
        "engines": [unique[key] for key in sorted(unique)],
        "partial": partial,
        "unavailable": False,
        "interfaceSource": interface_source,
        "hostsChecked": len(completed_hosts),
        "portsChecked": len(ports),
    }


def checked_at() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "LAN_ENGINE_PORTS",
    "LanInterface",
    "attached_private_ipv4_interfaces",
    "checked_at",
    "scan_lan_engines",
]
