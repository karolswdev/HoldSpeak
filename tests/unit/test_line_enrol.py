"""The Line on another machine (LINE-3): enrolment with a one-time code, a
node credential scoped to the Line's three wire routes, the readiness word
from the last hello (stale after 2 minutes), and the node's own credential.

The hub app is the real one (``MeetingWebServer._create_app``: the edge
middleware, the route-right table, the node token store); nothing listens.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

TOKEN = "owner-token-line3"


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    import holdspeak.config as config_module
    import holdspeak.db.core as db_core
    from holdspeak.calls import service as calls_service
    from holdspeak.db import reset_database
    from holdspeak.delivery import node_link
    from holdspeak.line import adapter, enrol
    from holdspeak.line import hub as line_hub
    import holdspeak.web.routes.calls as calls_routes
    from holdspeak.web_server import MeetingWebServer, WebRuntimeCallbacks

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("HOLDSPEAK_CALLS", "off")
    monkeypatch.delenv("HOLDSPEAK_LINE", raising=False)
    monkeypatch.setenv("HOLDSPEAK_CHANNEL_KEYSTORE_FILE", str(home / "keys.json"))
    monkeypatch.setattr(config_module, "CONFIG_FILE", home / ".holdspeak" / "config.json")
    monkeypatch.setattr(db_core, "DEFAULT_DB_PATH", tmp_path / "holdspeak.db")
    monkeypatch.setattr(node_link, "DEFAULT_TOKEN_STORE_PATH", home / ".holdspeak" / "node_auth_tokens.json")
    reset_database()
    fresh = line_hub.LineHub()
    for module in (line_hub, calls_routes, adapter):
        monkeypatch.setattr(module, "LINE_HUB", fresh)
    monkeypatch.setattr(calls_service, "_LINES", {})
    codes = enrol.EnrolCodes()
    monkeypatch.setattr(calls_routes, "CODES", codes)
    server = MeetingWebServer(
        WebRuntimeCallbacks(on_bookmark=lambda *_: None, on_stop=lambda: None, get_state=lambda: {}),
        auth_token=TOKEN,
    )
    app = server._create_app()
    with TestClient(app) as client:
        # tests/conftest.py gives every TestClient the owner's token; a node's
        # request here carries only its own credential, so the owner's goes per call.
        client.headers.pop("X-HoldSpeak-Token", None)
        client.line_hub = fresh  # type: ignore[attr-defined]
        client.store = app.state.node_token_store  # type: ignore[attr-defined]
        yield client
    reset_database()


OWNER = {"X-HoldSpeak-Token": TOKEN}


def _enrol(client: Any, node: str = "karol") -> str:
    minted = client.post("/api/calls/line/codes", json={"node": node}, headers=OWNER)
    assert minted.status_code == 200, minted.text
    body = minted.json()
    assert body["expires_in"] == 600 and body["node"] == node
    assert body["command"].startswith("holdspeak line enrol --hub ") and body["code"] in body["command"]
    answer = client.post("/api/calls/line/enrol", json={"code": body["code"]})
    assert answer.status_code == 200, answer.text
    assert answer.json()["node"] == node
    return answer.json()["token"]


def test_a_code_works_once_and_needs_the_owner_to_mint_it(hub) -> None:
    assert hub.post("/api/calls/line/codes", json={"node": "karol"}).status_code == 401
    code = hub.post("/api/calls/line/codes", json={"node": "karol"}, headers=OWNER).json()["code"]
    first = hub.post("/api/calls/line/enrol", json={"code": code.lower().replace("-", "")})
    assert first.status_code == 200 and first.json()["token"]
    again = hub.post("/api/calls/line/enrol", json={"code": code})
    assert again.status_code == 401 and again.json()["reason"] == "code_unknown"
    assert hub.post("/api/calls/line/enrol", json={"code": "AAAA-BBBB"}).json()["reason"] == "code_unknown"
    assert hub.post("/api/calls/line/codes", json={"node": "this-mac"}, headers=OWNER).status_code == 400
    assert hub.post("/api/calls/line/codes", json={"node": "Bad Name!"}, headers=OWNER).status_code == 400


def test_a_code_is_ten_minutes_old_at_most() -> None:
    from holdspeak.line.enrol import EnrolCodes, EnrolError

    now = [1000.0]
    codes = EnrolCodes(clock=lambda: now[0])
    fresh = codes.mint("karol")["code"]
    late = codes.mint("box2")["code"]
    now[0] += 599.0
    assert codes.take(fresh) == "karol"
    now[0] += 2.0
    with pytest.raises(EnrolError) as refused:
        codes.take(late)
    assert refused.value.reason == "code_expired"
    # A new code for a machine ends the one before it.
    one = codes.mint("karol")["code"]
    two = codes.mint("karol")["code"]
    with pytest.raises(EnrolError):
        codes.take(one)
    assert codes.take(two) == "karol"


def test_the_line_credential_reaches_the_three_wire_routes_and_nothing_else(hub) -> None:
    token = _enrol(hub)
    node = {"X-HoldSpeak-Node-Token": token}
    hello = hub.post("/api/calls/line/hello", headers=node, json={
        "version": "line-3", "lines": [{"id": "main", "kind": "sip", "address": "sip:holdspeak@100.118.33.80:5060",
                                        "state": "listening"}],
        "machine": {"name": "karol", "platform": "Linux x86_64", "baresip": "4.12.0",
                    "models": [{"id": "line-stt", "name": "Phone speech in (Parakeet)", "state": "ready"}]}})
    assert hello.status_code == 200, hello.text
    assert hub.post("/api/calls/line/next", headers=node, json={"after": 0, "wait_s": 0}).json() == {"commands": []}
    assert hub.post("/api/calls/line/events", headers=node, json={"events": []}).json() == {"acked": 0}
    # It speaks only for its own node: another node's name in the body is refused.
    assert hub.post("/api/calls/line/hello", headers=node, json={"node": "this-mac", "lines": []}).status_code == 400
    # Nothing else: not an owner read, not the node link, not the mesh, not a face's route.
    for method, path in (("GET", "/api/calls/status"), ("GET", "/api/calls/line/status"),
                         ("POST", "/api/calls/line/test"), ("POST", "/api/calls/line/codes"),
                         ("POST", "/api/delivery/node/hello"), ("POST", "/api/mesh/relay/claim"),
                         ("GET", "/api/settings")):
        refused = hub.request(method, path, headers=node, json={})
        assert refused.status_code == 403, (path, refused.status_code)
    # The hello is the node's: name, platform, baresip, models.
    snap = hub.line_hub.snapshot("karol")
    assert snap["machine"] == {"name": "karol", "platform": "Linux x86_64", "baresip": "4.12.0",
                               "models": [{"id": "line-stt", "name": "Phone speech in (Parakeet)", "state": "ready"}]}
    rows = hub.get("/api/calls/line/nodes", headers=OWNER).json()["nodes"]
    assert [(r["node"], r["state"], r["words"]) for r in rows] == [("karol", "ready", "Ready")]
    # Revoked from Settings: the credential is dead at once.
    assert hub.delete("/api/calls/line/nodes/karol", headers=OWNER).json() == {"node": "karol", "revoked": True}
    assert hub.post("/api/calls/line/hello", headers=node, json={"lines": []}).status_code == 401
    assert hub.get("/api/calls/line/nodes", headers=OWNER).json() == {"nodes": []}
    assert hub.delete("/api/calls/line/nodes/karol", headers=OWNER).status_code == 404


def test_a_link_node_credential_does_not_reach_the_line(hub) -> None:
    _node_id, token, _snap = hub.store.pair("karol")  # a delivery/mesh node of the same machine
    linked = {"X-HoldSpeak-Node-Token": token}
    assert hub.post("/api/calls/line/hello", headers=linked, json={"node": "karol", "lines": []}).status_code == 403
    # Enrolling the Line never touches that pairing (the Line's key is line:karol).
    _enrol(hub)
    assert hub.store.pairing("karol") is not None
    # Enrolling again replaces the Line's own credential only.
    old = _enrol(hub, "box2")
    new = _enrol(hub, "box2")
    assert hub.post("/api/calls/line/hello", headers={"X-HoldSpeak-Node-Token": old}, json={"lines": []}).status_code == 401
    assert hub.post("/api/calls/line/hello", headers={"X-HoldSpeak-Node-Token": new}, json={"lines": []}).status_code == 200


def test_the_owner_token_still_runs_the_local_node(hub) -> None:
    assert hub.post("/api/calls/line/hello", headers=OWNER, json={"node": "this-mac", "lines": []}).status_code == 200


def test_the_word_comes_from_the_last_hello_and_is_stale_after_two_minutes(monkeypatch) -> None:
    from holdspeak.calls.service import line_status
    from holdspeak.config.calls import CallsConfig
    from holdspeak.line import hub as line_hub
    from holdspeak.line.adapter import Line

    now = [5000.0]
    monkeypatch.setattr(line_hub.time, "monotonic", lambda: now[0])
    hub = line_hub.LineHub()
    line = Line("karol", hub=hub)
    cfg = CallsConfig(line={"where": "node:karol"})
    assert line_status(line, cfg)["words"] == "Not running"  # never said hello
    hub.hello("karol", lines=[{"id": "main", "kind": "sip", "address": "sip:holdspeak@100.118.33.80:5060",
                               "state": "listening"}], machine={"name": "karol", "baresip": "4.12.0"})
    assert line_status(line, cfg)["words"] == "Ready"
    now[0] += 119.0  # past the link's 30 s offline, inside the hello's 2 minutes
    status = line_status(line, cfg)
    assert (status["state"], status["words"]) == ("ready", "Ready")
    assert status["machine"]["baresip"] == "4.12.0"
    now[0] += 2.0
    assert (line_status(line, cfg)["state"], line_status(line, cfg)["words"]) == ("not_running", "Not running")


def test_the_node_keeps_its_credential_owner_only_and_uses_the_node_header(tmp_path, monkeypatch) -> None:
    from holdspeak.line import install, node

    monkeypatch.setenv("HOLDSPEAK_LINE_HOME", str(tmp_path / "line"))
    assert install.load_credential() is None
    path = install.save_credential("https://hub.example.ts.net/", "karol", "tok-1")
    assert path == tmp_path / "line" / "credential.json"
    assert oct(os.stat(path).st_mode & 0o777) == "0o600"
    assert install.load_credential() == {"hub": "https://hub.example.ts.net", "node": "karol", "node_token": "tok-1"}
    args = node.argparse.Namespace(hub="", node="")
    link = node._link_for(args)
    assert link is not None and link.hub == "https://hub.example.ts.net" and args.node == "karol"
    assert link._header == "X-HoldSpeak-Node-Token"
    os.chmod(path, 0o644)  # custody refuses a loose file rather than reading it
    with pytest.raises(Exception):
        install.load_credential()
    os.chmod(path, 0o600)
    assert install.forget_credential() and install.load_credential() is None


def test_run_with_no_credential_and_no_token_exits_clean(tmp_path, monkeypatch, capsys) -> None:
    from holdspeak.line import node

    monkeypatch.setenv("HOLDSPEAK_LINE_HOME", str(tmp_path / "line"))
    monkeypatch.setenv("HOLDSPEAK_BARESIP", "/bin/sh")
    monkeypatch.setattr(node, "_hub_token", lambda: "")
    assert node.main(["run"]) == 0  # a clean exit: the service does not loop
    assert "Not enrolled" in capsys.readouterr().out
