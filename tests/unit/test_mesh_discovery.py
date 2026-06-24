"""HSM-15-10: desktop LAN discovery — the advertiser + the identify endpoint.

Two halves, both testable without a live network:

1. The advertiser's *decision* + *ServiceInfo construction*: it advertises only
   off-loopback, builds `_holdspeak._tcp` with the right name/port/TXT, and the
   registration is best-effort (a zeroconf failure never propagates).
2. `GET /api/mesh/info` returns `{name, version, requiresToken}` and is reachable
   WITHOUT a token (it is the pre-pairing identify endpoint).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from holdspeak import mesh
from holdspeak.mesh import (
    MESH_SERVICE_TYPE,
    MeshAdvertiser,
    build_service_info,
    resolve_device_name,
    should_advertise,
)
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_mesh_router


# --------------------------------------------------------------------------- #
# The advertise decision (off-loopback only)
# --------------------------------------------------------------------------- #


def test_should_advertise_off_loopback_only():
    # Loopback binds advertise NOTHING (privacy + no one to discover them).
    assert should_advertise("127.0.0.1") is False
    assert should_advertise("localhost") is False
    assert should_advertise("::1") is False
    assert should_advertise("") is False
    # An off-loopback / wildcard bind is on the LAN and should advertise.
    assert should_advertise("0.0.0.0") is True
    assert should_advertise("192.168.1.50") is True


def test_resolve_device_name_prefers_config_then_hostname():
    assert resolve_device_name("Karol's Mac") == "Karol's Mac"
    assert resolve_device_name("  spaced  ") == "spaced"
    with patch("holdspeak.mesh.socket.gethostname", return_value="studio.local"):
        # falls back to the hostname, stripped of a trailing ".local"
        assert resolve_device_name("") == "studio"
    with patch("holdspeak.mesh.socket.gethostname", return_value=""):
        assert resolve_device_name("") == "HoldSpeak"


# --------------------------------------------------------------------------- #
# ServiceInfo construction (name / port / TXT)
# --------------------------------------------------------------------------- #


def test_build_service_info_name_port_and_txt():
    info = build_service_info(
        device_name="Studio",
        host="192.168.1.50",
        port=8723,
        version="9.9.9",
        requires_token=True,
    )
    assert info.type == MESH_SERVICE_TYPE
    assert info.name == f"Studio.{MESH_SERVICE_TYPE}"
    assert info.port == 8723
    # zeroconf stores TXT properties as bytes -> bytes.
    props = info.properties
    assert props[b"name"] == b"Studio"
    assert props[b"version"] == b"9.9.9"
    assert props[b"requiresToken"] == b"1"


def test_build_service_info_requires_token_flag_false():
    info = build_service_info(
        device_name="Mac",
        host="0.0.0.0",
        port=9000,
        version="1.0.0",
        requires_token=False,
    )
    assert info.properties[b"requiresToken"] == b"0"


# --------------------------------------------------------------------------- #
# Advertiser lifecycle (best-effort; registers off-loopback, unregisters clean)
# --------------------------------------------------------------------------- #


def test_advertiser_does_not_register_on_loopback():
    adv = MeshAdvertiser(
        device_name="Mac",
        host="127.0.0.1",
        port=8000,
        version="1.0.0",
        requires_token=False,
    )
    # No zeroconf import/registration should even be attempted on loopback.
    with patch("holdspeak.mesh.Zeroconf", create=True) as zc_cls:
        assert adv.start() is False
        zc_cls.assert_not_called()
    assert adv.active is False


def test_advertiser_registers_and_unregisters_off_loopback():
    fake_zc = MagicMock()
    with patch("zeroconf.Zeroconf", return_value=fake_zc):
        adv = MeshAdvertiser(
            device_name="Studio",
            host="192.168.1.50",
            port=8723,
            version="2.0.0",
            requires_token=True,
        )
        assert adv.start() is True
        assert adv.active is True
        # registered the _holdspeak._tcp service with our port + TXT
        fake_zc.register_service.assert_called_once()
        info = fake_zc.register_service.call_args.args[0]
        assert info.port == 8723
        assert info.properties[b"name"] == b"Studio"

        adv.stop()
        fake_zc.unregister_service.assert_called_once()
        fake_zc.close.assert_called_once()
        assert adv.active is False


def test_advertiser_is_best_effort_when_zeroconf_missing():
    # Simulate the zeroconf package being unavailable: start() must NOT raise.
    def _raise(*_a, **_k):
        raise ImportError("No module named 'zeroconf'")

    adv = MeshAdvertiser(
        device_name="Mac",
        host="192.168.1.50",
        port=8723,
        version="1.0.0",
        requires_token=True,
    )
    with patch("builtins.__import__", side_effect=_raise):
        # Defensive: even if the import machinery blows up, no exception escapes.
        try:
            result = adv.start()
        except Exception as exc:  # pragma: no cover - this is the failure we guard
            raise AssertionError(f"advertiser.start() raised: {exc!r}")
    assert result is False
    assert adv.active is False


def test_advertiser_is_best_effort_when_registration_fails():
    fake_zc = MagicMock()
    fake_zc.register_service.side_effect = OSError("network down")
    with patch("zeroconf.Zeroconf", return_value=fake_zc):
        adv = MeshAdvertiser(
            device_name="Studio",
            host="192.168.1.50",
            port=8723,
            version="1.0.0",
            requires_token=True,
        )
        # A registration failure is swallowed; the server keeps running.
        assert adv.start() is False
    assert adv.active is False
    # We tidied up the half-built Zeroconf rather than leaking its socket.
    fake_zc.close.assert_called_once()


# --------------------------------------------------------------------------- #
# GET /api/mesh/info — unauthenticated identify endpoint
# --------------------------------------------------------------------------- #


def _mesh_client(*, requires_token: bool) -> TestClient:
    app = FastAPI()
    ctx = WebContext(get_state=lambda: {}, mesh_requires_token=requires_token)
    app.include_router(build_mesh_router(ctx))
    return TestClient(app)


def test_mesh_info_shape_and_reachable_without_token():
    from holdspeak import __version__

    client = _mesh_client(requires_token=True)
    # No Authorization / X-HoldSpeak-Token header at all.
    resp = client.get("/api/mesh/info")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"name", "version", "requiresToken"}
    assert isinstance(body["name"], str) and body["name"]
    assert body["version"] == __version__
    assert body["requiresToken"] is True
    # Nothing sensitive leaks.
    assert "token" not in {k.lower() for k in body} - {"requirestoken"}
    assert "auth_token" not in body
    assert "psk" not in body


def test_mesh_info_requires_token_false_on_loopback_context():
    client = _mesh_client(requires_token=False)
    body = client.get("/api/mesh/info").json()
    assert body["requiresToken"] is False


def test_mesh_info_uses_configured_device_name():
    client = _mesh_client(requires_token=True)
    fake_cfg = MagicMock()
    fake_cfg.mesh.device_name = "The Coder Mac"
    with patch("holdspeak.config.Config.load", return_value=fake_cfg):
        body = client.get("/api/mesh/info").json()
    assert body["name"] == "The Coder Mac"


def test_mesh_module_constant_is_holdspeak_tcp():
    # The Bonjour service type the iPad's NWBrowser browses for.
    assert mesh.MESH_SERVICE_TYPE == "_holdspeak._tcp.local."
