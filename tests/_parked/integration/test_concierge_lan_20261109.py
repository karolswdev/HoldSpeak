# Parked: the Concierge LAN route was replaced by Setup; live scan coverage uses /api/setup/lan.
from tests.integration.test_concierge_readiness import *

def test_find_on_lan_returns_transient_found_rows_without_writing(cold, monkeypatch) -> None:
    from holdspeak.kernel.external_egress import run_external_egress
    from holdspeak.principals import PrincipalKind
    from holdspeak.services import lan_engine_discovery as discovery

    monkeypatch.setattr(discovery, "_interface_snapshot", lambda: ((
        discovery.LanInterface(ipaddress.IPv4Address("192.168.1.42"), ipaddress.IPv4Network("192.168.1.42/31")),
    ), "ip-json"))
    admitted = []

    def admit(**kwargs):
        admitted.append(kwargs)
        return run_external_egress(**kwargs)

    monkeypatch.setattr(discovery, "run_external_egress", admit)

    def connect(address, **_kwargs):
        if address[1] != 8080:
            raise ConnectionRefusedError("closed port")
        return MagicMock()

    tcp = MagicMock(side_effect=connect)
    response = MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"data":[{"id":"qwen3.8-27b"}]}'
    response.read1.side_effect = [response.read.return_value, b""]
    http = MagicMock(return_value=response)
    monkeypatch.setattr(discovery.socket, "create_connection", tcp)
    monkeypatch.setattr(discovery._LAN_OPENER, "open", http)
    client = _client()
    before = cold.profiles.list()
    settings_path = config_module.CONFIG_FILE
    settings_before = settings_path.read_bytes() if settings_path.exists() else None
    denied = client.post("/api/concierge/discover-lan", headers={"X-HoldSpeak-Token": "not-the-owner"})
    assert denied.status_code in {401, 403}
    assert admitted == []
    tcp.assert_not_called()
    http.assert_not_called()
    response = client.post("/api/concierge/discover-lan")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["engines"][0]["name"] == "qwen3.8-27b"
    assert payload["engines"][0]["found"] is True
    assert payload["engines"][0]["host"] == "192.168.1.43"
    assert payload["partial"] is False
    assert len(admitted) == 1
    assert admitted[0]["principal"].kind is PrincipalKind.OWNER
    assert admitted[0]["principal"].identity == "owner-session"
    assert admitted[0]["connector_id"] == "lan-engine-discovery"
    http.assert_called_once()
    assert cold.profiles.list() == before
    assert (settings_path.read_bytes() if settings_path.exists() else None) == settings_before

def test_find_on_lan_returns_a_named_egress_refusal(cold, monkeypatch) -> None:
    from holdspeak.kernel.external_egress import EgressOperationRefused
    from holdspeak.principals import PrincipalKind

    def refused(*, principal):
        assert principal.kind is PrincipalKind.OWNER
        raise EgressOperationRefused("lan-scan:manifest", "external_egress_warrant_refused")

    monkeypatch.setattr(
        "holdspeak.services.lan_engine_discovery.scan_lan_engines",
        refused,
    )
    response = _client().post("/api/concierge/discover-lan")
    assert response.status_code == 403, response.text
    assert response.json() == {
        "code": "concierge_lan_refused", "message": "external_egress_warrant_refused",
    }
