"""Bounded, owner-initiated discovery of OpenAI-compatible engines on the LAN.

The scan is deliberately separate from Concierge detection.  Detection is a
cheap read that may happen while a face opens; this operation is an explicit
owner press and therefore has a small, honest network budget.  It only sends
GET requests to private IPv4 addresses and never reads a saved key or writes a
profile.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import partial
from http.client import HTTPResponse
from typing import Any, Callable, Iterable, Mapping, Sequence
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from ..setup_runtime import discover_endpoint_models
from ..principals import Principal, UNAUTHENTICATED
from ..kernel.external_egress import run_external_egress
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


@dataclass(frozen=True)
class LanScanPlan:
    interfaces: tuple[LanInterface, ...]
    ports: tuple[tuple[int, str], ...]
    targets: tuple[tuple[str, int], ...]
    interface_source: str
    bounded: bool
    expires_at: float
    tcp_seconds: float
    http_seconds: float
    workers: int
    probe: Callable[[str], dict[str, Any]] | None = field(compare=False, repr=False)

    def manifest(self) -> dict[str, Any]:
        return {
            "interfaces": tuple((str(row.address), str(row.network)) for row in self.interfaces),
            "ports": self.ports,
            "targets": self.targets,
            "method": "GET", "path": "/v1/models",
            "expiresAtMonotonic": self.expires_at,
            "tcpSeconds": self.tcp_seconds, "httpSeconds": self.http_seconds,
            "workers": self.workers,
        }


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
    # These fixed interface reads cannot be expanded into a process effect.
    command = tuple(argv)
    if command not in {
        ("ip", "-json", "-4", "addr", "show"),
        ("ip", "-4", "-o", "addr", "show"),
        ("ifconfig",),
    }:
        raise ValueError("LAN discovery only permits fixed interface reads")
    try:
        result = subprocess.run(
            list(command), capture_output=True, text=True, timeout=1.0, check=False,
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
    # Hostname resolution is not an interface read: it can send DNS before
    # admission. If the fixed local commands have no address, report unavailable.
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


def _lan_http_get(
    url: str, *, headers: dict[str, str], timeout: float,
    expires_at: float | None = None,
) -> tuple[int, bytes]:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("LAN discovery requires an IPv4 address") from exc
    if not isinstance(address, ipaddress.IPv4Address) or _valid_interface(host, 24) is None:
        raise ValueError("LAN discovery only permits private IPv4 addresses")
    if parsed.scheme != "http" or parsed.path != "/v1/models" or parsed.query or parsed.fragment:
        raise ValueError("LAN discovery only permits GET /v1/models")
    if parsed.username or parsed.password or headers != {"Accept": "application/json"}:
        raise ValueError("LAN discovery does not send credentials")
    deadline = time.monotonic() + timeout
    if expires_at is not None:
        deadline = min(deadline, expires_at)
    if time.monotonic() >= deadline:
        raise TimeoutError("LAN models body deadline expired")
    request = Request(url, headers=headers, method="GET")
    with _LAN_OPENER.open(request, timeout=timeout) as response:  # noqa: S310
        # read() can wait forever while body bytes keep trickling. read1()
        # yields ordinary body chunks so the frozen expiry is checked after
        # each arrival, including a complete body that arrived too late.
        # A blocked ordinary read can exceed expiry by one socket timeout
        # (at most HTTP_PROBE_SECONDS). urllib's header/chunk-framing reads
        # remain outside this body check; this is not a hard wall-clock bound.
        body = bytearray()
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError("LAN models body deadline expired")
            chunk = response.read1(16 * 1024)
            if time.monotonic() >= deadline:
                raise TimeoutError("LAN models body deadline expired")
            if not chunk:
                return int(getattr(response, "status", 200) or 200), bytes(body)
            body.extend(chunk)


def _probe_endpoint(
    base_url: str, *, timeout: float, expires_at: float | None = None,
    tcp_seconds: float = TCP_PREFLIGHT_SECONDS,
) -> dict[str, Any]:
    """TCP preflight, then one keyless GET /v1/models."""
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    port = int(parsed.port or 80)
    if (
        _valid_interface(host, 24) is None
        or parsed.scheme != "http" or parsed.path != "/v1"
        or parsed.username or parsed.password or parsed.query or parsed.fragment
    ):
        return {"ok": False, "models": []}
    remaining = timeout if expires_at is None else expires_at - time.monotonic()
    if remaining <= 0:
        return {"ok": False, "models": []}
    with socket.create_connection((host, port), timeout=min(remaining, tcp_seconds)):
        pass
    remaining = timeout if expires_at is None else expires_at - time.monotonic()
    if remaining <= 0:
        return {"ok": False, "models": []}
    return discover_endpoint_models(
        base_url,
        timeout_seconds=min(remaining, timeout),
        http_get=partial(_lan_http_get, expires_at=expires_at),
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
    principal: Principal = UNAUTHENTICATED,
    broker: Any = None,
) -> dict[str, Any]:
    """Freeze one finite scan, then admit all real transports before dispatch.

    A test that injects interfaces and a pure probe without a principal or
    broker can exercise the computation alone. Authenticated scans still admit.
    """
    interface_source = "injected"
    if interfaces is None:
        selected, interface_source = _interface_snapshot()
    else:
        raw_interfaces = interfaces() if callable(interfaces) else interfaces
        selected = tuple(raw_interfaces)
    normalized = tuple(
        _valid_interface(str(row.address), row.network.prefixlen)
        if isinstance(row, LanInterface) and row.address in row.network
        else _valid_interface(str(row), 24)
        for row in selected
    )
    usable = tuple(row for row in normalized if row is not None)
    hosts = _hosts(usable)
    frozen_ports = tuple((int(port), str(engine)) for port, engine in ports)
    if any(not 1 <= port <= 65535 for port, _engine in frozen_ports):
        raise ValueError("LAN discovery requires valid TCP ports")
    targets = tuple((host, port) for host in hosts for port, _engine in frozen_ports)
    all_windows = {str(_window_for_interface(row)) for row in usable}
    bounded = (
        bool(usable)
        and all(interface.network.prefixlen >= 24 for interface in usable)
        and len(all_windows) <= MAX_NETWORK_WINDOWS
    )
    plan = LanScanPlan(
        usable, frozen_ports, targets, interface_source, bounded,
        time.monotonic() + max(0.0, min(float(deadline_seconds), SCAN_DEADLINE_SECONDS)),
        TCP_PREFLIGHT_SECONDS, HTTP_PROBE_SECONDS,
        max(1, min(int(max_workers), MAX_WORKERS)), probe,
    )
    pure_test = (
        probe is not None and interfaces is not None
        and principal is UNAUTHENTICATED and broker is None
    )
    if not usable or pure_test:
        return _execute_scan(plan)
    manifest = plan.manifest()
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    destination = "lan-scan:" + digest
    return run_external_egress(
        connector_id="lan-engine-discovery", destination=destination,
        data_classes=("engine-discovery",), payload_material=manifest,
        allowed_destinations=(destination,), principal=principal, broker=broker,
        sender=_execute_scan, args=(plan,),
    )


def _execute_scan(plan: LanScanPlan) -> dict[str, Any]:
    """The admitted sender: only the frozen target list can reach transports."""
    if not plan.interfaces:
        return {
            "engines": [],
            "partial": False,
            "unavailable": True,
            "reason": "LAN interface addresses are unavailable.",
            "hostsChecked": 0,
            "portsChecked": 0,
        }

    def probe_fn(base_url: str) -> dict[str, Any]:
        if time.monotonic() >= plan.expires_at:
            return {"ok": False, "models": []}
        if plan.probe is not None:
            return plan.probe(base_url)
        return _probe_endpoint(
            base_url, timeout=plan.http_seconds,
            expires_at=plan.expires_at, tcp_seconds=plan.tcp_seconds,
        )

    results: list[dict[str, Any]] = []
    futures: dict[Any, tuple[str, int]] = {}
    completed_hosts: set[str] = set()
    timed_out = False
    with ThreadPoolExecutor(max_workers=plan.workers, thread_name_prefix="holdspeak-lan-scan") as pool:
        for host, port in plan.targets:
            if time.monotonic() >= plan.expires_at:
                break
            futures[pool.submit(probe_fn, f"http://{host}:{port}/v1")] = (host, port)
        remaining = max(0.0, plan.expires_at - time.monotonic())
        try:
            completed = as_completed(futures, timeout=remaining)
            for future in completed:
                host, port = futures[future]
                completed_hosts.add(host)
                try:
                    answer = future.result()
                except OSError:
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
        not plan.bounded
        or timed_out
        or len(futures) < len(plan.targets)
        or time.monotonic() >= plan.expires_at
    )
    return {
        "engines": [unique[key] for key in sorted(unique)],
        "partial": partial,
        "unavailable": False,
        "interfaceSource": plan.interface_source,
        "hostsChecked": len(completed_hosts),
        "portsChecked": len(plan.ports),
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
