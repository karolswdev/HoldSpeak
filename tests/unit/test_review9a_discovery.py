"""Credential origin binding, redirect refusal and reply filtering for Check."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from contextlib import contextmanager
from urllib.error import HTTPError

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from holdspeak import setup_runtime
from holdspeak.db import Database
from holdspeak.intel.providers import profile_key_env
from holdspeak.principals import Principal, PrincipalKind
from holdspeak.profile_key_store import ProfileKeyStore
from holdspeak.services.setup_service import SetupService
from holdspeak.services.sqlite_observer import SQLiteObserver
from holdspeak.web.context import WebContext
from holdspeak.web.routes.setup import build_setup_router

OWNER = Principal(PrincipalKind.OWNER, "check-owner")
SECRET = "review9a-synthetic-profile-key"
OWN_URL = "https://engine.example:8443/v1"


@pytest.fixture
def check(tmp_path, monkeypatch):
    import holdspeak.profile_key_store as custody
    db = Database(tmp_path / "hub.db")
    store = ProfileKeyStore(tmp_path / "custody" / "keys.json")
    monkeypatch.setattr(custody, "_default_profile_key_store", lambda: store)
    db.profiles.upsert(profile_id="saved", name="Owner engine", kind="openAICompatible", base_url=OWN_URL)
    service = SetupService(db, observer=SQLiteObserver(db._connection))
    app = FastAPI()

    @app.middleware("http")
    async def owner(request: Request, call_next):
        request.state.principal = OWNER
        return await call_next(request)

    app.include_router(build_setup_router(WebContext(get_state=lambda: {}, setup_service=service)))
    calls = []

    def get(url, *, headers, timeout):
        calls.append((url, dict(headers)))
        if url.endswith("/props"):
            return 200, b'{"chat_template_caps":{"supports_tools":true}}'
        return 200, b'{"data":[{"id":"model-safe","context_length":4096}]}'

    monkeypatch.setattr(setup_runtime, "_default_http_json", get)
    return TestClient(app), db, store, calls


def bind_key(store, monkeypatch, mode):
    slot = profile_key_env("saved")
    if mode == "stored":
        store.set(slot, SECRET)
    else:
        monkeypatch.setenv(slot, SECRET)


@pytest.mark.parametrize("mode", ["stored", "environment"])
@pytest.mark.parametrize("url", ["http://engine.example:8443/v1", "https://other.example:8443/v1", "https://engine.example:9443/v1"])
def test_saved_profile_key_never_leaves_its_origin(check, monkeypatch, mode, url):
    client, db, store, calls = check
    bind_key(store, monkeypatch, mode)
    response = client.post("/api/setup/discover-models", json={"profile_id": "saved", "base_url": url})
    assert response.status_code == 400
    assert response.json()["reason"] == "profile_origin_mismatch"
    assert response.json()["models"] == []
    assert not calls
    assert SECRET not in response.text


@pytest.mark.parametrize("mode", ["stored", "environment"])
def test_settings_check_keeps_its_profile_and_own_address_contract(check, monkeypatch, mode):
    client, db, store, calls = check
    bind_key(store, monkeypatch, mode)
    response = client.post("/api/setup/discover-models", json={
        "profile_id": "saved", "base_url": OWN_URL, "check_tools": True})
    assert response.status_code == 200
    assert response.json()["models"] == ["model-safe"]
    assert response.json()["contexts"] == {"model-safe": 4096}
    assert response.json()["tools"] == "yes"
    assert calls and all(headers["Authorization"] == f"Bearer {SECRET}" for _, headers in calls)


def test_saved_engine_probe_uses_the_saved_address_and_key(check, monkeypatch):
    from holdspeak.services.profile_service import ProfileService

    _, db, store, calls = check
    bind_key(store, monkeypatch, "stored")
    answer = ProfileService(db).probe_inference_target(OWNER, "saved")
    assert answer["reachable"] and answer["models"] == ["model-safe"]
    assert calls == [(OWN_URL + "/models", {
        "Accept": "application/json", "Authorization": f"Bearer {SECRET}",
    })]


def test_origin_uses_effective_default_port_and_ignores_path(check, monkeypatch):
    client, db, store, calls = check
    db.profiles.upsert(profile_id="saved", kind="openAICompatible", base_url="https://ENGINE.example:443/v1")
    bind_key(store, monkeypatch, "stored")
    response = client.post("/api/setup/discover-models", json={"profile_id": "saved", "base_url": "https://engine.example/another"})
    assert response.status_code == 200
    assert calls[0][1]["Authorization"] == f"Bearer {SECRET}"


def test_a_typed_key_is_for_the_typed_address_even_when_a_profile_is_named(check, monkeypatch):
    client, db, store, calls = check
    bind_key(store, monkeypatch, "stored")
    response = client.post("/api/setup/discover-models", json={
        "profile_id": "saved", "base_url": "https://other.example/v1", "api_key": "typed-for-this-address"})
    assert response.status_code == 200
    assert calls[0][1]["Authorization"] == "Bearer typed-for-this-address"


@pytest.mark.parametrize("mode", ["typed", "stored", "environment"])
def test_discovery_drops_echoed_key_values_and_context_keys(check, monkeypatch, mode):
    client, db, store, calls = check
    if mode != "typed":
        bind_key(store, monkeypatch, mode)
    payload = {"data": [{"id": "model-safe", "context_length": 4096},
                        {"id": SECRET, "context_length": 8192},
                        {"id": f"prefix-{SECRET}-suffix", "context_length": 16384}]}
    monkeypatch.setattr(setup_runtime, "_default_http_json", lambda *a, **k: (200, json.dumps(payload).encode()))
    body = {"base_url": OWN_URL, **({"api_key": SECRET} if mode == "typed" else {"profile_id": "saved"})}
    response = client.post("/api/setup/discover-models", json=body)
    assert response.status_code == 200
    assert response.json()["models"] == ["model-safe"]
    assert response.json()["contexts"] == {"model-safe": 4096}
    assert response.json()["detail"] == "Found 1 model."
    assert SECRET not in response.text
    with db._connection() as conn:
        events = list(conn.execute("SELECT args_summary, result_summary FROM pipeline_events"))
    assert events and SECRET not in str([tuple(e) for e in events])


@contextmanager
def server(handler):
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}"
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()


@pytest.mark.parametrize("transport", ["get", "json", "post"])
def test_remote_discovery_transport_never_forwards_credentials_on_redirect(monkeypatch, transport):
    import holdspeak.loopback_http as loopback
    received = []

    class Receiver(BaseHTTPRequestHandler):
        def do_GET(self):
            self.rfile.read(int(self.headers.get("Content-Length", "0")))
            received.append(dict(self.headers))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{}')
        do_POST = do_GET
        def log_message(self, *args): pass

    with server(Receiver) as destination:
        class Redirect(BaseHTTPRequestHandler):
            def do_GET(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                assert self.headers["Authorization"] == f"Bearer {SECRET}"
                self.send_response(302)
                self.send_header("Location", destination + "/stolen")
                self.end_headers()
            do_POST = do_GET
            def log_message(self, *args): pass

        with server(Redirect) as source:
            # Exercise the remote transport branch against two authorized local
            # fixtures; normal loopback transport already refuses redirects.
            monkeypatch.setattr(loopback, "is_loopback_url", lambda _: False)
            headers = {"Authorization": f"Bearer {SECRET}", "x-api-key": SECRET}
            if transport == "post":
                code, _ = setup_runtime._default_http_post_json(source, headers=headers, body=b'{}', timeout=2)
                assert code == 302
            else:
                method = setup_runtime._default_http_json if transport == "json" else setup_runtime._default_http_get
                with pytest.raises(HTTPError) as refused:
                    method(source, headers=headers, timeout=2)
                assert refused.value.code == 302
    assert received == []
