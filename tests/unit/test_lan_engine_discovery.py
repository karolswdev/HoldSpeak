"""LAN engine discovery stays bounded, private, transient, and injectable."""
from __future__ import annotations

import ipaddress
import hashlib
import json
import threading
from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse
from urllib.error import HTTPError

import pytest

import holdspeak.db.core as db_core
import holdspeak.services.lan_engine_discovery as discovery
from holdspeak.db import Database
from holdspeak.kernel import runtime as kernel_runtime
from holdspeak.kernel.external_egress import EGRESS_EXECUTIONS, EgressOperationRefused, LOCAL_OWNER
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.services.lan_engine_discovery import (
    LanInterface,
    _parse_ifconfig,
    _parse_ip_json,
    _probe_endpoint,
    scan_lan_engines,
)


def _interface(address: str, network: str) -> LanInterface:
    return LanInterface(ipaddress.IPv4Address(address), ipaddress.IPv4Network(network))


def test_scan_returns_real_model_ids_and_excludes_self_and_broadcast() -> None:
    seen: list[str] = []

    def probe(url: str) -> dict[str, object]:
        seen.append(url)
        if url.startswith("http://192.168.1.43:8080/"):
            return {"ok": True, "models": ["qwen3.8-27b", "nomic-embed-text"]}
        return {"ok": False, "models": []}

    result = scan_lan_engines(
        interfaces=[_interface("192.168.1.10", "192.168.1.0/24")],
        ports=[(8080, "llama.cpp")],
        probe=probe,
        max_workers=8,
    )

    assert [row["name"] for row in result["engines"]] == ["qwen3.8-27b"]
    row = result["engines"][0]
    assert row == {
        "id": "lan:192.168.1.43:8080:qwen3.8-27b",
        "kind": "lan",
        "name": "qwen3.8-27b",
        "legacyLabel": "qwen3.8-27b",
        "host": "192.168.1.43",
        "state": "READY",
        "baseUrl": "http://192.168.1.43:8080/v1",
        "found": True,
    }
    assert "http://192.168.1.10:8080/v1" not in seen
    assert "http://192.168.1.0:8080/v1" not in seen
    assert "http://192.168.1.255:8080/v1" not in seen
    assert result["partial"] is False


def test_scan_reports_unavailable_without_interface_addresses() -> None:
    result = scan_lan_engines(interfaces=[])

    assert result["engines"] == []
    assert result["unavailable"] is True
    assert result["reason"] == "LAN interface addresses are unavailable."


def test_scan_reports_partial_when_a_large_network_is_capped() -> None:
    result = scan_lan_engines(
        interfaces=[_interface("192.168.1.10", "192.168.0.0/16")],
        ports=[(8080, "llama.cpp")],
        probe=lambda _url: {"ok": False, "models": []},
        deadline_seconds=1.0,
    )

    assert result["hostsChecked"] == 253  # the attached host is excluded
    assert result["partial"] is True


def test_scan_stays_inside_a_narrow_attached_network() -> None:
    seen: list[str] = []

    def probe(url: str) -> dict[str, object]:
        seen.append(url)
        return {"ok": False, "models": []}

    result = scan_lan_engines(
        interfaces=[_interface("192.168.1.10", "192.168.1.0/25")],
        ports=[(8080, "llama.cpp")],
        probe=probe,
        max_workers=8,
    )

    assert result["hostsChecked"] == 125  # 126 usable hosts minus the attached host
    assert result["partial"] is False
    assert all(
        urlparse(url).hostname is not None
        and urlparse(url).hostname.startswith("192.168.1.")
        and int(urlparse(url).hostname.rsplit(".", 1)[1]) < 128
        for url in seen
    )


def test_interface_parsers_keep_private_ipv4_only() -> None:
    assert [str(row.address) for row in _parse_ifconfig(
        """en0: flags=8863<UP>\n\tinet 192.168.1.10 netmask 0xffffff00 broadcast 192.168.1.255\n\tinet 8.8.8.8 netmask 0xffffff00\n"""
    )] == ["192.168.1.10"]
    assert [str(row.address) for row in _parse_ip_json(
        '[{"addr_info":[{"family":"inet","local":"10.0.0.5","prefixlen":24},{"family":"inet6","local":"::1","prefixlen":128}]}]'
    )] == ["10.0.0.5"]


def test_probe_does_tcp_preflight_then_models_get_without_credentials() -> None:
    connection = MagicMock()
    connection.__enter__.return_value = connection
    with patch("holdspeak.services.lan_engine_discovery.socket.create_connection", return_value=connection) as connect, \
         patch("holdspeak.services.lan_engine_discovery.discover_endpoint_models", return_value={"ok": True, "models": ["qwen"]}) as discover:
        result = _probe_endpoint("http://192.168.1.43:8080/v1", timeout=0.5)

    assert result == {"ok": True, "models": ["qwen"]}
    connect.assert_called_once_with(("192.168.1.43", 8080), timeout=0.15)
    discover.assert_called_once()
    assert "api_key" not in discover.call_args.kwargs
    assert discover.call_args.kwargs["http_get"] is not None


@pytest.fixture
def scan_runtime(tmp_path, monkeypatch):
    db = Database(tmp_path / "lan-kernel.db")
    monkeypatch.setattr(db_core, "_db", db)
    for name in ("_plans", "_operation_ids", "_results"):
        monkeypatch.setattr(EGRESS_EXECUTIONS, name, {})
    return db, kernel_runtime._configure(db)


def _scan_receipt(broker):
    result = list(EGRESS_EXECUTIONS._results.values())[-1]
    return broker.read(
        [f"operation:{result['operation_id']}"], "full", "committed", LOCAL_OWNER,
    )["objects"][0]


def test_interface_read_runner_refuses_other_commands() -> None:
    with patch.object(discovery.subprocess, "run") as run:
        for argv in (("ifconfig", "en0", "down"), ("ip", "link", "set", "en0", "down"), ("sh", "-c", "ip addr")):
            with pytest.raises(ValueError, match="fixed interface reads"):
                discovery._run(argv)
        run.assert_not_called()
        run.return_value.stdout = "interfaces"
        for argv in (("ifconfig",), ("ip", "-json", "-4", "addr", "show"), ("ip", "-4", "-o", "addr", "show")):
            assert discovery._run(argv) == "interfaces"
        assert run.call_count == 3
        assert all(call.kwargs["timeout"] == 1.0 for call in run.call_args_list)


def test_unavailable_interfaces_do_not_resolve_names_or_dispatch() -> None:
    with patch.object(discovery, "_run", return_value=""), \
         patch.object(discovery.socket, "getaddrinfo") as resolve, \
         patch.object(discovery.socket, "create_connection") as tcp, \
         patch.object(discovery._LAN_OPENER, "open") as http, \
         patch.object(discovery, "run_external_egress") as admit:
        result = scan_lan_engines()
    assert result["unavailable"] is True
    assert result["engines"] == []
    resolve.assert_not_called()
    tcp.assert_not_called()
    http.assert_not_called()
    admit.assert_not_called()


def test_refused_scan_never_dispatches_tcp_or_http(scan_runtime) -> None:
    _, broker = scan_runtime
    with patch.object(discovery.socket, "getaddrinfo") as resolve, \
         patch.object(discovery.socket, "create_connection") as tcp, \
         patch.object(discovery._LAN_OPENER, "open") as http:
        with pytest.raises(EgressOperationRefused) as caught:
            scan_lan_engines(
                interfaces=[_interface("192.168.1.1", "192.168.1.0/30")],
                ports=[(8080, "llama.cpp")], broker=broker,
                principal=Principal(PrincipalKind.AGENT, "no-lan-delegation"),
            )
    assert caught.value.receipt["state"] == "refused"
    assert caught.value.receipt["outcome"] == caught.value.reason
    resolve.assert_not_called()
    tcp.assert_not_called()
    http.assert_not_called()
    assert not EGRESS_EXECUTIONS._plans
    assert not EGRESS_EXECUTIONS._results


@pytest.mark.parametrize("principal", [
    LOCAL_OWNER, Principal(PrincipalKind.AGENT, "no-lan-delegation"),
])
def test_a_supplied_principal_still_admits_an_injected_probe(scan_runtime, principal) -> None:
    _, broker = scan_runtime
    probe = MagicMock(return_value={"ok": True, "models": ["qwen3.8-27b"]})
    kwargs = {
        "interfaces": [_interface("192.168.1.1", "192.168.1.0/30")],
        "ports": [(8080, "llama.cpp")], "probe": probe,
        "broker": broker, "principal": principal,
    }
    if principal.kind is PrincipalKind.OWNER:
        result = scan_lan_engines(**kwargs)
        assert result["engines"][0]["name"] == "qwen3.8-27b"
        probe.assert_called_once_with("http://192.168.1.2:8080/v1")
        assert _scan_receipt(broker)["receipt"]["outcome"] == "succeeded"
    else:
        with pytest.raises(EgressOperationRefused):
            scan_lan_engines(**kwargs)
        probe.assert_not_called()


def test_admitted_scan_freezes_manifest_and_receipts_success(scan_runtime, monkeypatch) -> None:
    _, broker = scan_runtime
    interfaces = [_interface("192.168.1.1", "192.168.1.0/30")]
    ports = [(8080, "llama.cpp")]
    captured = {}
    submit = broker.submit
    reads = MagicMock(return_value=interfaces)

    def submit_after_mutation(request, principal):
        envelope = EGRESS_EXECUTIONS.plan(request["arguments"]["egress_id"])
        assert envelope is not None
        plan = envelope.args[0]
        with pytest.raises(FrozenInstanceError):
            plan.targets = ()
        captured["manifest"] = plan.manifest()
        captured["digest"] = envelope.payload_digest
        captured["destination"] = envelope.destination
        assert envelope.allowed_destinations == (envelope.destination,)
        assert envelope.connector_id == "lan-engine-discovery"
        assert envelope.data_classes == ("engine-discovery",)
        assert principal is LOCAL_OWNER
        interfaces.append(_interface("10.0.0.1", "10.0.0.0/24"))
        ports.append((9000, "extra"))
        monkeypatch.setattr(discovery, "HTTP_PROBE_SECONDS", 900.0)
        monkeypatch.setattr(discovery, "TCP_PREFLIGHT_SECONDS", 900.0)
        return submit(request, principal)

    monkeypatch.setattr(broker, "submit", submit_after_mutation)
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"data":[{"id":"qwen3.8-27b"}]}'
    response.read1.side_effect = [response.read.return_value, b""]
    with patch.object(discovery.socket, "create_connection", return_value=MagicMock()) as tcp, \
         patch.object(discovery._LAN_OPENER, "open", return_value=response) as http:
        result = scan_lan_engines(interfaces=reads, ports=ports, broker=broker, principal=LOCAL_OWNER)

    reads.assert_called_once_with()
    assert result["engines"][0]["host"] == "192.168.1.2"
    assert result["portsChecked"] == 1
    assert result["partial"] is False
    tcp.assert_called_once_with(("192.168.1.2", 8080), timeout=0.15)
    http.assert_called_once()
    request = http.call_args.args[0]
    assert request.full_url == "http://192.168.1.2:8080/v1/models"
    assert request.get_method() == "GET"
    assert request.header_items() == [("Accept", "application/json")]
    assert 0 < http.call_args.kwargs["timeout"] <= 0.5
    manifest = captured["manifest"]
    assert manifest["interfaces"] == (("192.168.1.1", "192.168.1.0/30"),)
    assert manifest["ports"] == ((8080, "llama.cpp"),)
    assert manifest["targets"] == (("192.168.1.2", 8080),)
    assert manifest["method"] == "GET" and manifest["path"] == "/v1/models"
    expected = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert captured["destination"] == "lan-scan:" + expected
    assert captured["digest"] == "sha256:" + expected
    full = _scan_receipt(broker)
    assert full["receipt"]["outcome"] == "succeeded"
    assert full["native_receipts"][0]["destination"] == captured["destination"]
    assert full["native_receipts"][0]["data_classes"] == ["engine-discovery"]
    assert not EGRESS_EXECUTIONS._plans


@pytest.mark.parametrize("error,outcome", [
    (ConnectionRefusedError("closed port"), "succeeded"),
    (RuntimeError("unexpected sender failure"), "indeterminate"),
])
def test_scan_terminalizes_closed_ports_and_unexpected_failures(scan_runtime, error, outcome) -> None:
    _, broker = scan_runtime
    with patch.object(discovery.socket, "create_connection", side_effect=error), \
         patch.object(discovery._LAN_OPENER, "open") as http:
        if outcome == "indeterminate":
            with pytest.raises(RuntimeError, match="unexpected sender failure"):
                scan_lan_engines(
                    interfaces=[_interface("192.168.1.1", "192.168.1.0/30")],
                    ports=[(8080, "llama.cpp")], broker=broker, principal=LOCAL_OWNER,
                )
        else:
            result = scan_lan_engines(
                interfaces=[_interface("192.168.1.1", "192.168.1.0/30")],
                ports=[(8080, "llama.cpp")], broker=broker, principal=LOCAL_OWNER,
            )
            assert result["engines"] == [] and result["partial"] is False
    http.assert_not_called()
    full = _scan_receipt(broker)
    assert full["receipt"]["outcome"] == outcome
    assert full["native_receipts"][0]["outcome"] == outcome
    assert not EGRESS_EXECUTIONS._plans


def test_scan_expiry_is_frozen_before_admission(scan_runtime, monkeypatch) -> None:
    _, broker = scan_runtime
    now = [10.0]
    monkeypatch.setattr(discovery.time, "monotonic", lambda: now[0])
    submit = broker.submit

    def delay_admission(request, principal):
        now[0] = 20.0
        return submit(request, principal)

    monkeypatch.setattr(broker, "submit", delay_admission)
    with patch.object(discovery.socket, "create_connection") as tcp, \
         patch.object(discovery._LAN_OPENER, "open") as http:
        result = scan_lan_engines(
            interfaces=[_interface("192.168.1.1", "192.168.1.0/30")],
            ports=[(8080, "llama.cpp")], broker=broker, principal=LOCAL_OWNER,
        )
    assert result["partial"] is True
    tcp.assert_not_called()
    http.assert_not_called()
    assert _scan_receipt(broker)["receipt"]["outcome"] == "succeeded"


class _TimedModelsResponse:
    """Finite bytes and an injected clock: old read() succeeds too late.

    read1() consumes the same body in arriving chunks, without real sockets
    or sleeps. A single final chunk can also arrive after the deadline.
    """

    status = 200
    body = b'{"data":[{"id":"qwen3.8-27b"}]}'

    def __init__(self, clock, *, chunk_bytes=1, chunk_seconds=0.2):
        self.clock = clock
        self.chunk_bytes = chunk_bytes
        self.chunk_seconds = chunk_seconds
        self.remaining = self.body
        self.closed = False
        self.read_calls = 0
        self.read1_calls = 0
        self.workers = set()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.closed = True

    def read(self):
        self.workers.add(threading.current_thread())
        self.read_calls += 1
        chunks = (len(self.remaining) + self.chunk_bytes - 1) // self.chunk_bytes
        self.clock["now"] += chunks * self.chunk_seconds
        body, self.remaining = self.remaining, b""
        return body

    def read1(self, size):
        self.workers.add(threading.current_thread())
        self.read1_calls += 1
        if not self.remaining:
            return b""
        take = min(size, self.chunk_bytes)
        body, self.remaining = self.remaining[:take], self.remaining[take:]
        self.clock["now"] += self.chunk_seconds
        return body


@pytest.mark.parametrize("chunk_bytes,chunk_seconds", [
    (1, 0.2), (len(_TimedModelsResponse.body), 0.6),
], ids=["trickle", "late-complete-body"])
def test_probe_rejects_a_models_body_that_arrives_after_frozen_expiry(
    monkeypatch, chunk_bytes, chunk_seconds,
) -> None:
    clock = {"now": 100.0}
    expires_at = 100.5
    monkeypatch.setattr(discovery, "time", SimpleNamespace(monotonic=lambda: clock["now"]))
    response = _TimedModelsResponse(clock, chunk_bytes=chunk_bytes, chunk_seconds=chunk_seconds)
    with patch.object(discovery.socket, "create_connection", return_value=MagicMock()), \
         patch.object(discovery._LAN_OPENER, "open", return_value=response):
        answer = _probe_endpoint("http://192.168.1.43:8080/v1", timeout=0.5, expires_at=expires_at)
    # The original unbounded read returns this valid model list after expiry.
    assert answer["ok"] is False and answer["models"] == [], answer
    assert response.closed
    assert response.read_calls == 0
    assert 0 < response.read1_calls <= 3
    assert clock["now"] <= expires_at + discovery.HTTP_PROBE_SECONDS


def test_expired_models_body_unwinds_the_admitted_scan(scan_runtime, monkeypatch) -> None:
    _, broker = scan_runtime
    clock = {"now": 100.0}
    monkeypatch.setattr(discovery, "time", SimpleNamespace(monotonic=lambda: clock["now"]))
    response = _TimedModelsResponse(clock)
    with patch.object(discovery.socket, "create_connection", return_value=MagicMock()), \
         patch.object(discovery._LAN_OPENER, "open", return_value=response):
        result = scan_lan_engines(
            interfaces=[_interface("192.168.1.42", "192.168.1.42/31")],
            ports=[(8080, "llama.cpp")], max_workers=1, deadline_seconds=0.5,
            broker=broker, principal=LOCAL_OWNER,
        )
    assert result["engines"] == [] and result["partial"] is True, result
    assert response.closed and response.workers
    assert all(not worker.is_alive() for worker in response.workers)
    assert _scan_receipt(broker)["receipt"]["outcome"] == "succeeded"
    assert not EGRESS_EXECUTIONS._plans


@pytest.mark.parametrize("base_url", [
    "http://127.0.0.1:8080/v1", "http://169.254.1.1:8080/v1",
    "http://8.8.8.8:8080/v1", "http://engine.local:8080/v1",
    "https://192.168.1.43:8080/v1", "http://user:key@192.168.1.43:8080/v1",
    "http://192.168.1.43:8080/other", "http://192.168.1.43:8080/v1?more=1",
])
def test_probe_rejects_targets_outside_the_scan_contract_before_tcp(base_url) -> None:
    with patch.object(discovery.socket, "create_connection") as tcp, \
         patch.object(discovery._LAN_OPENER, "open") as http:
        assert _probe_endpoint(base_url, timeout=0.5)["ok"] is False
    tcp.assert_not_called()
    http.assert_not_called()


@pytest.mark.parametrize("url,headers", [
    ("http://127.0.0.1:8080/v1/models", {"Accept": "application/json"}),
    ("http://192.168.1.43:8080/other", {"Accept": "application/json"}),
    ("http://192.168.1.43:8080/v1/models", {"Authorization": "Bearer secret"}),
])
def test_models_get_refuses_changed_path_or_credentials_before_http(url, headers) -> None:
    with patch.object(discovery._LAN_OPENER, "open") as http:
        with pytest.raises(ValueError):
            discovery._lan_http_get(url, headers=headers, timeout=0.5)
    http.assert_not_called()


def test_models_get_has_no_proxy_or_redirect_transport() -> None:
    handlers = discovery._LAN_OPENER.handlers
    assert not any(
        isinstance(handler, discovery.ProxyHandler) and handler.proxies
        for handler in handlers
    )
    redirects = [handler for handler in handlers if isinstance(handler, discovery.HTTPRedirectHandler)]
    assert len(redirects) == 1
    with pytest.raises(HTTPError, match="redirect refused"):
        redirects[0].redirect_request(
            discovery.Request("http://192.168.1.43:8080/v1/models"),
            MagicMock(), 302, "Found", {}, "http://8.8.8.8/models",
        )
