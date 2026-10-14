"""LAN engine discovery stays bounded, private, transient, and injectable."""
from __future__ import annotations

import ipaddress
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

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
