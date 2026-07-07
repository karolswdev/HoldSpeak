"""HS-85-04 — liveness on every surface + the honest doctor.

A mesh model's availability is soft: `/api/models` rows carry `live` +
last-seen; an offline meshNode target refuses the ask IMMEDIATELY with a
400 naming the node (never queue-then-timeout); the profiles list carries
liveness as an ENVELOPE sidecar (the synced shape stays pure); doctor lists
every edge with its age and the Runtime-profiles line names the node.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.commands import doctor
from holdspeak.db import Database, reset_database
from holdspeak.web.context import WebContext
from holdspeak.web.routes import build_primitives_router


@pytest.fixture
def env(tmp_path, monkeypatch):
    reset_database()
    db = Database(tmp_path / "holdspeak.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_primitives_router(WebContext(get_state=lambda: {})))
    yield db, TestClient(app)
    reset_database()


def _mesh_profile(db, **overrides):
    fields = dict(
        profile_id="p-phone", name="Pocket 4B", kind="meshNode",
        node="walk-edge", model="qwen3.5-4b",
    )
    fields.update(overrides)
    return db.profiles.upsert(**fields)


# ── /api/models: liveness, not existence ─────────────────────────────────


def test_models_rows_carry_mesh_liveness(env) -> None:
    db, client = env
    _mesh_profile(db)

    rows = client.get("/api/models").json()["models"]
    row = next(r for r in rows if r["name"] == "qwen3.5-4b")
    assert row["node"] == "walk-edge"
    assert row["live"] is False and row["last_seen_seconds"] is None

    db.mesh_relay.touch_worker("walk-edge")
    rows = client.get("/api/models").json()["models"]
    row = next(r for r in rows if r["name"] == "qwen3.5-4b")
    assert row["live"] is True and row["last_seen_seconds"] == 0


def test_stale_worker_reads_offline_with_age(env) -> None:
    db, client = env
    _mesh_profile(db)
    db.mesh_relay.touch_worker("walk-edge", now=datetime.now() - timedelta(seconds=120))
    row = next(
        r for r in client.get("/api/models").json()["models"] if r["name"] == "qwen3.5-4b"
    )
    assert row["live"] is False and row["last_seen_seconds"] >= 119


def test_non_mesh_rows_are_untouched(env) -> None:
    db, client = env
    db.profiles.upsert(
        profile_id="p-lan", name="LAN", kind="openAICompatible",
        base_url="http://x.example/v1", model="lan-model",
    )
    row = next(
        r for r in client.get("/api/models").json()["models"] if r["name"] == "lan-model"
    )
    assert "live" not in row and "node" not in row


# ── the ask refuses an offline node fast, by name ────────────────────────


def test_ask_against_offline_mesh_node_is_an_immediate_400(env) -> None:
    db, client = env
    prof = _mesh_profile(db)
    resp = client.post("/api/ask", json={"prompt": "Go", "profile_id": prof.id})
    assert resp.status_code == 400
    assert "mesh node 'walk-edge' is offline (no worker has ever polled)" in resp.json()["error"]
    # NOTHING was queued — refusal, not queue-then-timeout
    assert db.mesh_relay.claim_next("walk-edge") is None

    db.mesh_relay.touch_worker("walk-edge", now=datetime.now() - timedelta(seconds=60))
    resp = client.post("/api/ask", json={"prompt": "Go", "model": "qwen3.5-4b"})
    assert resp.status_code == 400
    assert "last seen" in resp.json()["error"]


def test_ask_against_live_mesh_node_proceeds(env, monkeypatch) -> None:
    db, client = env
    _mesh_profile(db)
    db.mesh_relay.touch_worker("walk-edge")

    class _FakeRelay:
        active_provider = "mesh"
        node = "walk-edge"
        model_hint = "qwen3.5-4b"

        def run_prompt(self, **kwargs):
            return "FROM THE EDGE"

    monkeypatch.setattr(
        "holdspeak.intel.providers.build_meeting_intel_for_profile",
        lambda **kw: _FakeRelay(),
    )
    resp = client.post("/api/ask", json={"prompt": "Go", "model": "qwen3.5-4b"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["output"] == "FROM THE EDGE"
    assert body["egress"] == {"scope": "mesh", "host": "walk-edge"}


# ── the profiles list: liveness rides the envelope ───────────────────────


def test_profiles_list_carries_the_liveness_sidecar(env) -> None:
    db, client = env
    _mesh_profile(db)
    db.mesh_relay.touch_worker("walk-edge")

    data = client.get("/api/profiles").json()
    assert data["mesh_liveness"]["walk-edge"]["live"] is True
    # the synced shape stays pure — no liveness key on the profile object
    served = next(p for p in data["profiles"] if p["id"] == "p-phone")
    assert "live" not in served and "mesh_liveness" not in served


# ── doctor ───────────────────────────────────────────────────────────────


def test_doctor_mesh_edges_states(env, monkeypatch) -> None:
    db, _ = env
    check = doctor._check_mesh_edges(SimpleNamespace())
    assert check.status == "PASS" and "no node has ever served" in check.detail

    db.mesh_relay.touch_worker("walk-edge")
    db.mesh_relay.touch_worker("attic-mac", now=datetime.now() - timedelta(seconds=300))
    check = doctor._check_mesh_edges(SimpleNamespace())
    assert "walk-edge: live (0s ago)" in check.detail
    assert "attic-mac: offline (300s ago)" in check.detail


def test_doctor_runtime_profiles_names_the_mesh_node(env, monkeypatch) -> None:
    db, _ = env
    prof = _mesh_profile(db)
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: prof
    )
    cfg = SimpleNamespace(
        meeting=SimpleNamespace(
            intel_enabled=True, intel_provider="cloud",
            intel_cloud_model="m", intel_cloud_api_key_env="E",
            intel_cloud_base_url=None, intel_profile_id="p-phone",
        ),
        dictation=SimpleNamespace(
            pipeline=SimpleNamespace(enabled=False),
            runtime=SimpleNamespace(profile_id=None),
        ),
    )
    check = doctor._check_runtime_profiles(cfg)
    assert check.status == "PASS"
    assert "meeting intel: profile 'Pocket 4B' (mesh node 'walk-edge')" in check.detail
