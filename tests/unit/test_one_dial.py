"""HS-112-01 — one dial.

The `InferenceTarget` (profiles table) is the ONLY place an endpoint or
model lives. These tests pin: the one-time silent migration (idempotent,
honest on a fresh config), the pointer-only resolvers, the one sentinel,
the intel-queue resolver refactor, the read-only `/api/profiles` alias,
and the grep census over the dead legacy fields.
"""
from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import holdspeak.db as hsdb
from holdspeak.config import (
    Config,
    LEGACY_DICTATION_PROFILE_ID,
    LEGACY_INTEL_PROFILE_ID,
    LLMRuntimeConfig,
    MeetingConfig,
    RailsObserverConfig,
    migrate_legacy_endpoints,
)
from holdspeak.db import Database, reset_database
from holdspeak.db.models import ProfileRecord
from holdspeak.intel.providers import (
    effective_dictation_llm,
    effective_intel_cloud,
    profile_key_env,
)

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture
def db(tmp_path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


# ── the one-time migration ─────────────────────────────────────────────


def test_migration_mints_legacy_intel_target_once(tmp_path, db) -> None:
    cfg = Config()
    cfg.meeting.intel_cloud_base_url = "http://192.168.1.43:8080/v1"
    cfg.meeting.intel_cloud_model = "qwen"
    path = tmp_path / "config.json"

    assert migrate_legacy_endpoints(cfg, path, db=db) is True
    assert cfg.meeting.intel_profile_id == LEGACY_INTEL_PROFILE_ID
    row = db.profiles.get(LEGACY_INTEL_PROFILE_ID)
    assert row is not None
    assert row.kind == "openAICompatible"
    assert row.base_url == "http://192.168.1.43:8080/v1"
    assert row.model == "qwen"
    assert row.requires_key is False  # self-hosted endpoint

    # Idempotent: a second load-time run mints nothing new.
    assert migrate_legacy_endpoints(cfg, path, db=db) is False
    assert len([p for p in db.profiles.list() if not p.deleted]) == 1
    # The saved config carries the pointer, so a re-load skips too.
    reloaded = Config.load(path)
    assert reloaded.meeting.intel_profile_id == LEGACY_INTEL_PROFILE_ID


def test_migration_mints_dictation_target_for_endpoint_backend(tmp_path, db) -> None:
    cfg = Config()
    cfg.dictation.runtime.backend = "openai_compatible"
    cfg.dictation.runtime.openai_compatible_base_url = "http://10.0.0.9:8000/v1"
    cfg.dictation.runtime.openai_compatible_model = "small"
    path = tmp_path / "config.json"

    assert migrate_legacy_endpoints(cfg, path, db=db) is True
    assert cfg.dictation.runtime.profile_id == LEGACY_DICTATION_PROFILE_ID
    row = db.profiles.get(LEGACY_DICTATION_PROFILE_ID)
    assert row is not None
    assert row.base_url == "http://10.0.0.9:8000/v1"
    assert row.model == "small"

    assert migrate_legacy_endpoints(cfg, path, db=db) is False
    assert len([p for p in db.profiles.list() if not p.deleted]) == 1


def test_migration_covers_default_openai_cloud_provider(tmp_path, db) -> None:
    cfg = Config()
    cfg.meeting.intel_provider = "cloud"  # base_url unset = the default API
    assert migrate_legacy_endpoints(cfg, tmp_path / "c.json", db=db) is True
    row = db.profiles.get(LEGACY_INTEL_PROFILE_ID)
    assert row.base_url == "https://api.openai.com/v1"
    assert row.requires_key is True


def test_fresh_config_mints_nothing(tmp_path, db) -> None:
    cfg = Config()
    assert migrate_legacy_endpoints(cfg, tmp_path / "c.json", db=db) is False
    assert db.profiles.list() == []
    assert cfg.meeting.intel_profile_id is None
    assert cfg.dictation.runtime.profile_id is None


def test_migration_skips_when_pointer_already_set(tmp_path, db) -> None:
    cfg = Config()
    cfg.meeting.intel_cloud_base_url = "http://x:1/v1"
    cfg.meeting.intel_profile_id = "already-there"
    assert migrate_legacy_endpoints(cfg, tmp_path / "c.json", db=db) is False
    assert db.profiles.list() == []
    assert cfg.meeting.intel_profile_id == "already-there"


def test_migration_without_a_db_is_a_silent_no_op(tmp_path, monkeypatch) -> None:
    cfg = Config()
    cfg.meeting.intel_cloud_base_url = "http://x:1/v1"

    def boom(*a, **k):
        raise RuntimeError("no db")

    monkeypatch.setattr(hsdb, "get_database", boom)
    assert migrate_legacy_endpoints(cfg, tmp_path / "c.json") is False
    assert cfg.meeting.intel_profile_id is None


def test_explicit_path_load_never_migrates(tmp_path, monkeypatch) -> None:
    # A test/tool load (explicit path) must never touch the DB.
    def boom(*a, **k):  # pragma: no cover - would fail the test if called
        raise AssertionError("Config.load(path) must not open the DB")

    monkeypatch.setattr(hsdb, "get_database", boom)
    cfg = Config()
    cfg.meeting.intel_provider = "cloud"
    path = tmp_path / "config.json"
    cfg.save(path)
    loaded = Config.load(path)
    assert loaded.meeting.intel_profile_id is None


# ── one sentinel for the three pointers ────────────────────────────────


def test_pointer_sentinel_is_none_everywhere() -> None:
    assert MeetingConfig(intel_profile_id="").intel_profile_id is None
    assert MeetingConfig(intel_profile_id="  ").intel_profile_id is None
    assert MeetingConfig(intel_profile_id="p-1").intel_profile_id == "p-1"
    assert LLMRuntimeConfig(profile_id="").profile_id is None
    assert LLMRuntimeConfig(profile_id="p-2").profile_id == "p-2"
    assert RailsObserverConfig(profile_id="").profile_id is None
    assert RailsObserverConfig(profile_id=None).profile_id is None
    assert RailsObserverConfig(profile_id="p-3").profile_id == "p-3"


# ── the resolvers read ONLY the pointer ────────────────────────────────


def _profile(**overrides) -> ProfileRecord:
    fields = dict(
        id="p-43",
        name="LAN llama",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="Qwen3.5-9B-Q6_K",
    )
    fields.update(overrides)
    return ProfileRecord(**fields)


def test_effective_intel_cloud_ignores_legacy_fields() -> None:
    cfg = SimpleNamespace(
        intel_cloud_model="legacy-model",
        intel_cloud_api_key_env="LEGACY_ENV",
        intel_cloud_base_url="http://legacy:1/v1",
        intel_profile_id=None,
    )
    eff = effective_intel_cloud(cfg, get_profile=lambda pid: pytest.fail("no lookup"))
    assert eff.base_url is None
    assert eff.model == "gpt-5-mini"
    assert eff.api_key_env == "OPENAI_API_KEY"
    assert eff.profile_id is None


def test_effective_intel_cloud_resolves_through_the_pointer() -> None:
    cfg = SimpleNamespace(intel_profile_id="p-43")
    eff = effective_intel_cloud(cfg, get_profile=lambda pid: _profile(id=pid))
    assert eff.base_url == "http://192.168.1.43:8080/v1"
    assert eff.model == "Qwen3.5-9B-Q6_K"
    assert eff.api_key_env == profile_key_env("p-43")
    assert eff.profile_id == "p-43"


def test_effective_dictation_llm_ignores_legacy_fields() -> None:
    cfg = SimpleNamespace(
        openai_compatible_model="legacy-model",
        openai_compatible_api_key_env="LEGACY_ENV",
        openai_compatible_base_url="http://legacy:1/v1",
        profile_id=None,
    )
    eff = effective_dictation_llm(cfg, get_profile=lambda pid: pytest.fail("no lookup"))
    assert eff.base_url is None
    assert eff.model == ""
    assert eff.profile_id is None


def test_effective_dictation_llm_resolves_through_the_pointer() -> None:
    cfg = SimpleNamespace(profile_id="p-43")
    eff = effective_dictation_llm(cfg, get_profile=lambda pid: _profile(id=pid))
    assert eff.base_url == "http://192.168.1.43:8080/v1"
    assert eff.profile_id == "p-43"


def test_dangling_pointer_degrades_to_hub_default_with_reason() -> None:
    cfg = SimpleNamespace(intel_profile_id="gone")
    eff = effective_intel_cloud(cfg, get_profile=lambda pid: None)
    assert eff.base_url is None
    assert eff.reason and "gone" in eff.reason


# ── intel_queue reads the resolver, not threaded params ────────────────


def test_intel_queue_resolves_endpoint_through_the_resolver(monkeypatch) -> None:
    import holdspeak.intel_queue as iq

    cfg = Config()
    cfg.meeting.intel_profile_id = "p-43"
    monkeypatch.setattr(Config, "load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record",
        lambda pid: _profile(id=pid),
    )

    seen: dict = {}

    def fake_status(*args, **kwargs):
        seen.update(kwargs)
        return False, "paused for the test"

    monkeypatch.setattr(iq, "get_intel_runtime_status", fake_status)
    assert iq.process_next_intel_job(provider="cloud") is False
    assert seen["cloud_base_url"] == "http://192.168.1.43:8080/v1"
    assert seen["cloud_model"] == "Qwen3.5-9B-Q6_K"
    assert seen["cloud_api_key_env"] == profile_key_env("p-43")


def test_intel_queue_signatures_carry_no_endpoint_triple() -> None:
    import inspect

    import holdspeak.intel_queue as iq

    for fn in (iq.process_next_intel_job, iq.drain_intel_queue, iq.start_intel_queue_worker):
        params = set(inspect.signature(fn).parameters)
        assert not {"cloud_model", "cloud_api_key_env", "cloud_base_url"} & params, fn


# ── /api/profiles is a read-only alias ─────────────────────────────────


@pytest.fixture
def client(db, monkeypatch) -> TestClient:
    from holdspeak.web.context import WebContext
    from holdspeak.web.routes.primitives.profiles import build_profiles_router

    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    app = FastAPI()
    app.include_router(build_profiles_router(WebContext(get_state=lambda: {})))
    return TestClient(app)


def test_profiles_api_reads_but_refuses_writes(client, db) -> None:
    db.profiles.upsert(
        profile_id="p-1", name="A", kind="openAICompatible",
        base_url="http://h:1/v1", model="m",
    )
    assert client.get("/api/profiles").status_code == 200
    assert client.get("/api/profiles/p-1").status_code == 200

    for resp in (
        client.post("/api/profiles", json={"name": "B"}),
        client.put("/api/profiles/p-1", json={"name": "B"}),
        client.delete("/api/profiles/p-1"),
    ):
        assert resp.status_code == 405
        assert resp.json()["write_path"] == "/api/inference-targets"
    # Nothing changed.
    assert db.profiles.get("p-1").name == "A"


def test_inference_targets_stays_the_write_path(client, db) -> None:
    resp = client.post(
        "/api/inference-targets",
        json={"name": "LAN", "kind": "openAICompatible",
              "base_url": "http://192.168.1.43:8080/v1", "model": "q"},
    )
    assert resp.status_code == 201
    target = resp.json()["inference_target"]
    assert client.delete(f"/api/inference-targets/{target['id']}").status_code == 200


# ── the settings boundary never writes or returns the dead fields ──────


def test_redacted_settings_omits_legacy_endpoint_fields() -> None:
    from holdspeak.web.routes.system.settings_secrets import redacted_settings

    payload = redacted_settings(Config())
    assert "intel_cloud_base_url" not in payload["meeting"]
    assert "intel_cloud_model" not in payload["meeting"]
    assert "openai_compatible_base_url" not in payload["dictation"]["runtime"]
    assert "openai_compatible_model" not in payload["dictation"]["runtime"]
    # The pointers and the local-engine knobs stay.
    assert "intel_profile_id" in payload["meeting"]
    assert "profile_id" in payload["dictation"]["runtime"]
    assert "mlx_model" in payload["dictation"]["runtime"]


def test_settings_put_strips_legacy_endpoint_fields() -> None:
    from holdspeak.services.settings_service import _strip_legacy_endpoint_fields

    cleaned = _strip_legacy_endpoint_fields(
        {
            "meeting": {"intel_cloud_base_url": "http://x:1/v1", "mic_label": "Me"},
            "dictation": {"runtime": {"openai_compatible_base_url": "http://y:1/v1", "backend": "auto"}},
        }
    )
    assert "intel_cloud_base_url" not in cleaned["meeting"]
    assert cleaned["meeting"]["mic_label"] == "Me"
    assert "openai_compatible_base_url" not in cleaned["dictation"]["runtime"]
    assert cleaned["dictation"]["runtime"]["backend"] == "auto"


# ── every feature leg resolves through the one seam ────────────────────


def test_feature_legs_resolve_through_the_one_resolver() -> None:
    resolver_legs = {
        # HS-131-07: the admitted rails path captures an immutable revision
        # from the placement authority, rather than resolving a mutable target.
        "holdspeak/rails_observer.py": "resolve_placement",
        # HS-130-06: Ask resolves through the HS-130-01 placement authority
        # (resolve_placement composes the one resolve_inference_target seam),
        # so the id selects placement and Ask never model-name-hops.
        "holdspeak/services/ask_service.py": "resolve_placement",
        # HS-131-04: Sequence and Workflow now share the admitted service;
        # _target resolves placement for every eligible child.
        "holdspeak/services/sequence_workflow_service.py": "resolve_placement",
        "holdspeak/services/recipe_service.py": "resolve_inference_target",
        "holdspeak/plugins/dictation/assembly.py": "effective_dictation_llm",
        "holdspeak/runtime/meeting_glue.py": "effective_intel_cloud",
        "holdspeak/intel_queue.py": "effective_intel_cloud",
        "holdspeak/setup_runtime.py": "effective_dictation_llm",
    }
    for rel, seam in resolver_legs.items():
        text = (REPO / rel).read_text()
        assert seam in text, f"{rel} no longer resolves through {seam}"


# ── the grep census: the dead fields have no readers left ──────────────

_BANNED = re.compile(r"intel_cloud_base_url|openai_compatible_base_url")


def _files(root: Path, suffixes: tuple[str, ...]):
    for path in root.rglob("*"):
        if path.suffix in suffixes and path.is_file():
            yield path


def test_census_no_legacy_endpoint_fields_in_web_src() -> None:
    banned_web = re.compile(
        r"intel_cloud_base_url|intel_cloud_model|intel_cloud_api_key_env"
        r"|openai_compatible_base_url|openai_compatible_model"
        r"|openai_compatible_api_key_env"
    )
    offenders = [
        str(path)
        for path in _files(REPO / "web" / "src", (".ts", ".tsx"))
        if "node_modules" not in str(path) and banned_web.search(path.read_text())
    ]
    assert offenders == []


def test_census_no_feature_code_readers_outside_config() -> None:
    offenders = []
    for path in _files(REPO / "holdspeak", (".py",)):
        if path.name == "config.py" and path.parent.name == "holdspeak":
            continue  # declaration + the one migration shim
        # HS-117-12: config.py split into holdspeak/config/ package
        if "holdspeak/config/" in str(path):
            continue
        if _BANNED.search(path.read_text()):
            offenders.append(str(path))
    assert offenders == []
