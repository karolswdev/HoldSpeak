"""Cross-machine steering relay (HS-89-03).

Fake opener (no real HTTP): what's pinned — the node's own route is called
with the pane key percent-encoded and the bearer token attached; the node's
typed refusal (a 409) rides through as DATA; an unreachable node refuses BY
NAME (node_offline); an unconfigured node is unknown_node; the HTTP-code
mapping (502 gateway / 409 node-refusal / 200 delivered).
"""

from __future__ import annotations

import urllib.error

import pytest

from holdspeak import coder_steering_relay as relay_mod
from holdspeak.coder_steering_relay import load_nodes, relay, relay_http_code

NODES = {"beta": {"base_url": "http://beta.tailnet:8000/", "token": "sekret"}}


def _opener(record: dict, *, status: int = 200, payload=None, boom: Exception | None = None):
    def send(method, url, headers, body, timeout):
        record.update(method=method, url=url, headers=headers, body=body, timeout=timeout)
        if boom is not None:
            raise boom
        return {"status": status, "json": payload if payload is not None else {"status": "delivered", "pane_id": "%5"}}
    return send


def test_load_nodes_from_env_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOLDSPEAK_STEER_NODES", '{"beta": {"base_url": "http://b:8000", "token": "t"}}')
    nodes = load_nodes()
    assert nodes["beta"]["base_url"] == "http://b:8000"
    monkeypatch.setenv("HOLDSPEAK_STEER_NODES", "not json")
    assert load_nodes() == {}


def test_relay_calls_the_nodes_own_route_with_encoded_key_and_token() -> None:
    rec: dict = {}
    res = relay("beta", "keys", "pane:%5", body={"keys": ["C-c"]},
                nodes=NODES, opener=_opener(rec))
    # the pane key is percent-encoded so pane:%5 survives the URL
    assert rec["url"] == "http://beta.tailnet:8000/api/coders/pane%3A%255/keys"
    assert rec["headers"]["Authorization"] == "Bearer sekret"
    assert rec["body"] == {"keys": ["C-c"]}
    assert res["status"] == "delivered" and res["node"] == "beta"  # stamped WHERE it landed


def test_unknown_node_refuses_by_name() -> None:
    res = relay("ghost", "keys", "pane:%5", nodes=NODES, opener=_opener({}))
    assert res["status"] == "unknown_node" and res["node"] == "ghost"
    assert relay_http_code(res) == 502


def test_offline_node_refuses_by_name_never_hangs() -> None:
    res = relay("beta", "steer", "claude:x", body={"text": "hi"}, nodes=NODES,
                opener=_opener({}, boom=urllib.error.URLError("connection refused")))
    assert res["status"] == "node_offline" and res["node"] == "beta"
    assert "did not answer" in res["detail"]
    assert relay_http_code(res) == 502


def test_node_typed_refusal_rides_through_as_data() -> None:
    # The node answered 409 with its own consent refusal — that is DATA, and
    # the hub surfaces it as 409, not a gateway error.
    res = relay("beta", "steer", "claude:x", body={"text": "hi"}, nodes=NODES,
                opener=_opener({}, status=409, payload={"status": "unarmed"}))
    assert res["status"] == "unarmed" and res["node"] == "beta"
    assert relay_http_code(res) == 409


def test_delivered_maps_to_200() -> None:
    res = relay("beta", "keys", "pane:%5", nodes=NODES, opener=_opener({}))
    assert relay_http_code(res) == 200


def test_no_configured_nodes_means_every_relay_refuses() -> None:
    res = relay("beta", "keys", "pane:%5", nodes={}, opener=_opener({}))
    assert res["status"] == "unknown_node"
