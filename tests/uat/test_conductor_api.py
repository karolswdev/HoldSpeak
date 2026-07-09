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


def test_list_decks(client):
    r = client.get("/api/decks")
    assert r.status_code == 200
    names = {d["name"] for d in r.json()["decks"]}
    assert {"golden-local", "golden-43", "bad-endpoint", "no-model", "mesh-node"} <= names


def test_list_recipes(client):
    r = client.get("/api/recipes")
    assert r.status_code == 200
    names = {d["name"] for d in r.json()["recipes"]}
    assert {"fresh-desk", "seeded-desk", "intel-endpoint-dead"} <= names


def test_apply_recipe_unknown_run_404(client):
    assert client.post("/api/runs/nope/recipes/fresh-desk", json={}).status_code == 404


def test_features_route(client):
    r = client.get("/api/features")
    assert r.status_code == 200
    body = r.json()
    assert body["feature_count"] > 200
    assert body["phases_total"] == 88


def test_packs_and_pack_detail(client):
    r = client.get("/api/packs")
    assert r.status_code == 200
    packs = {p["pack"]: p for p in r.json()["packs"]}
    assert "smoke" in packs
    assert packs["smoke"]["scenario_count"] >= 6

    d = client.get("/api/packs/smoke")
    assert d.status_code == 200
    detail = d.json()
    assert detail["validation_errors"] == []
    assert len(detail["scenarios"]) >= 6
    assert detail["coverage"]["overall"]["total"] > 0


def test_unknown_pack_404(client):
    assert client.get("/api/packs/nope").status_code == 404
