"""The conductor's HTTP API, over a fake-product RunManager."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from uat.conductor.app import create_app
from uat.conductor.db import Database
from uat.conductor.runs import RunManager


@pytest.fixture
def client(fake_products):
    mgr = RunManager(Database(), boot_timeout=1.0, link_caches=False)
    app = create_app(mgr)
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["service"] == "uat-conductor"


def test_create_get_logs_delete_run(client):
    r = client.post("/api/runs", json={"config": {"model": {"warm_on_start": False}}})
    assert r.status_code == 201, r.text
    run = r.json()
    rid = run["id"]
    assert run["status"] == "up"
    assert run["pairing"]["url"]

    g = client.get(f"/api/runs/{rid}")
    assert g.status_code == 200
    assert g.json()["status"] == "up"

    logs = client.get(f"/api/runs/{rid}/logs")
    assert logs.status_code == 200
    assert "stdout" in logs.json()

    d = client.delete(f"/api/runs/{rid}")
    assert d.status_code == 200
    assert d.json()["status"] == "down"


def test_restart_run(client):
    rid = client.post("/api/runs", json={}).json()["id"]
    r = client.post(f"/api/runs/{rid}/restart", json={"config": {"meeting": {"intel_enabled": False}}})
    assert r.status_code == 200
    assert r.json()["status"] == "up"


def test_failed_boot_surfaces_as_status_failed(client, fake_products):
    fake_products.boot_ok = False
    r = client.post("/api/runs", json={})
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "failed"
    assert body["error"]


def test_unknown_run_404(client):
    assert client.get("/api/runs/nope").status_code == 404
    assert client.delete("/api/runs/nope").status_code == 404
    assert client.post("/api/runs/nope/restart", json={}).status_code == 404
