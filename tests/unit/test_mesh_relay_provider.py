"""HS-85-02 — the meshNode profile kind + the relay provider.

`MeshRelayIntel` speaks the standard provider interface by enqueueing on the
HS-85-01 queue and waiting bounded; a non-live node refuses IMMEDIATELY by
name; node-side failures and deadline expiries surface the queue's own named
errors. The resolver adopts meshNode profiles for chat/intel and honestly
refuses them for the DIR dictation runtime. Egress badges say `mesh` + node.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from holdspeak.db import Database, reset_database
from holdspeak.db.models import ProfileRecord
from holdspeak.intel.mesh_relay import MeshRelayIntel
from holdspeak.intel.models import MeetingIntelError
from holdspeak.intel.providers import (
    build_meeting_intel_for_profile,
    effective_dictation_llm,
    effective_intel_cloud,
    endpoint_egress,
)

T0 = datetime(2026, 7, 7, 12, 0, 0)


@pytest.fixture
def db(tmp_path) -> Database:
    reset_database()
    database = Database(tmp_path / "holdspeak.db")
    yield database
    reset_database()


def _mesh_profile(**overrides) -> ProfileRecord:
    fields = dict(
        id="p-phone", name="Pocket 4B", kind="meshNode",
        node="walk-edge", model="qwen3.5-4b",
    )
    fields.update(overrides)
    return ProfileRecord(**fields)


class _Clock:
    def __init__(self, start: datetime) -> None:
        self.t = start

    def now(self) -> datetime:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += timedelta(seconds=seconds)


# ── the provider ─────────────────────────────────────────────────────────


def _provider(db, clock, **kw) -> MeshRelayIntel:
    return MeshRelayIntel(
        node="walk-edge", model_hint="qwen3.5-4b",
        relay=db.mesh_relay, sleep=clock.sleep, now=clock.now, **kw,
    )


def test_offline_node_refuses_immediately_by_name(db) -> None:
    clock = _Clock(T0)
    with pytest.raises(MeetingIntelError, match="walk-edge.*offline.*no worker has ever polled"):
        _provider(db, clock).run_prompt(user_prompt="hi")

    db.mesh_relay.touch_worker("walk-edge", now=T0 - timedelta(seconds=60))
    with pytest.raises(MeetingIntelError, match="offline .last seen 60s ago"):
        _provider(db, clock).run_prompt(user_prompt="hi")
    # nothing was ever queued — refusal is immediate, not queue-then-timeout
    assert db.mesh_relay.claim_next("walk-edge", now=T0) is None


def test_run_round_trips_through_the_queue(db) -> None:
    clock = _Clock(T0)
    db.mesh_relay.touch_worker("walk-edge", now=T0)

    # a fake worker: completes the job on the first poll tick
    original_sleep = clock.sleep

    def sleep_and_work(seconds: float) -> None:
        original_sleep(seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            assert job.system_prompt == "Be brief."
            assert job.user_prompt == "What is dictation?"
            assert job.model_hint == "qwen3.5-4b"
            db.mesh_relay.complete(job.id, result="Speaking words.", now=clock.now())

    provider = MeshRelayIntel(
        node="walk-edge", model_hint="qwen3.5-4b",
        relay=db.mesh_relay, sleep=sleep_and_work, now=clock.now,
    )
    out = provider.run_prompt(system_prompt="Be brief.", user_prompt="What is dictation?")
    assert out == "Speaking words."


def test_chat_seam_folds_messages_onto_the_relay(db) -> None:
    """The HS-85-05 walk find: built-in plugins speak `_chat_completion_text`
    (the engine's de-facto second seam), and without it every LLM plugin
    failed softly while the reroute still said executed=True."""
    clock = _Clock(T0)
    db.mesh_relay.touch_worker("walk-edge", now=T0)
    original_sleep = clock.sleep

    def sleep_and_work(seconds: float) -> None:
        original_sleep(seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            assert job.system_prompt == "Plan milestones."
            assert job.user_prompt == "The transcript.\n\nThe tail."
            db.mesh_relay.complete(job.id, result="{}", now=clock.now())

    provider = MeshRelayIntel(
        node="walk-edge", relay=db.mesh_relay, sleep=sleep_and_work, now=clock.now,
    )
    out = provider._chat_completion_text(
        [
            {"role": "system", "content": "Plan milestones."},
            {"role": "user", "content": "The transcript."},
            {"role": "user", "content": "The tail."},
        ],
        temperature=0.2,
        max_tokens=1000,
    )
    assert out == "{}"


def test_node_side_failure_surfaces_verbatim(db) -> None:
    clock = _Clock(T0)
    db.mesh_relay.touch_worker("walk-edge", now=T0)

    def sleep_and_fail(seconds: float) -> None:
        clock.t += timedelta(seconds=seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            db.mesh_relay.fail(job.id, error="no model loaded", now=clock.now())

    provider = MeshRelayIntel(
        node="walk-edge", relay=db.mesh_relay, sleep=sleep_and_fail, now=clock.now,
    )
    with pytest.raises(MeetingIntelError, match="walk-edge.*no model loaded"):
        provider.run_prompt(user_prompt="hi")


def test_deadline_expiry_surfaces_the_queue_reason(db) -> None:
    clock = _Clock(T0)
    db.mesh_relay.touch_worker("walk-edge", now=T0)
    provider = _provider(db, clock, deadline_seconds=10, poll_interval_seconds=2.0)
    with pytest.raises(MeetingIntelError, match="never claimed the run before its deadline"):
        provider.run_prompt(user_prompt="hi")


# ── the resolver adopts meshNode ─────────────────────────────────────────


def _meeting_cfg(**overrides):
    base = dict(
        intel_provider="cloud", intel_cloud_model="legacy-model",
        intel_cloud_api_key_env="LEGACY_KEY_ENV",
        intel_cloud_base_url="http://legacy.example:8000/v1",
        intel_profile_id=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_effective_intel_adopts_mesh_node() -> None:
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="p-phone"), get_profile=lambda pid: _mesh_profile()
    )
    assert eff.node == "walk-edge" and eff.base_url is None
    assert eff.model == "qwen3.5-4b" and eff.profile_name == "Pocket 4B"
    assert eff.reason is None


def test_mesh_profile_without_node_falls_back_with_reason() -> None:
    eff = effective_intel_cloud(
        _meeting_cfg(intel_profile_id="p-phone"),
        get_profile=lambda pid: _mesh_profile(node=""),
    )
    assert eff.node is None
    assert eff.base_url == "http://legacy.example:8000/v1"
    assert "names no node" in (eff.reason or "")


def test_dictation_adopts_mesh_nodes_too() -> None:
    # owner call (2026-07-07): DIR's endpoint leg is already advisory-
    # constrained, so the relay rides the same posture
    runtime = SimpleNamespace(
        openai_compatible_model="dict-model",
        openai_compatible_api_key_env="OPENAI_API_KEY",
        openai_compatible_base_url="http://127.0.0.1:8000/v1",
        profile_id="p-phone",
    )
    eff = effective_dictation_llm(runtime, get_profile=lambda pid: _mesh_profile())
    assert eff.node == "walk-edge" and eff.reason is None
    assert eff.model == "qwen3.5-4b"


class _FakeRelayIntel:
    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.reply = '{"matched": true, "block_id": "b1", "confidence": 0.9, "extras": {}}'

    def run_prompt(self, **kwargs):
        self.calls.append(kwargs)
        return self.reply


def test_dictation_mesh_runtime_classifies_via_the_relay() -> None:
    from holdspeak.plugins.dictation.grammars import StructuredOutputSchema
    from holdspeak.plugins.dictation.runtime_mesh_relay import MeshRelayRuntime

    fake = _FakeRelayIntel()
    rt = MeshRelayRuntime(node="walk-edge", model_hint="qwen3.5-4b", intel=fake)
    schema = StructuredOutputSchema(block_ids=("b1",), extras_per_block={"b1": {}})
    out = rt.classify("route this", schema)
    assert out["matched"] is True and out["block_id"] == "b1"
    assert "Allowed output schema" in fake.calls[0]["user_prompt"]

    fake.reply = "rewritten text"
    assert rt.rewrite("rewrite this") == "rewritten text"
    assert fake.calls[-1]["user_prompt"] == "rewrite this"


def test_dictation_mesh_runtime_maps_relay_errors_to_the_pipeline_contract() -> None:
    from holdspeak.plugins.dictation.runtime_mesh_relay import MeshRelayRuntime

    class _Offline:
        def run_prompt(self, **kwargs):
            raise MeetingIntelError("mesh node 'walk-edge' is offline (last seen 60s ago)")

    rt = MeshRelayRuntime(node="walk-edge", intel=_Offline())
    with pytest.raises(RuntimeError, match="walk-edge.*offline"):
        rt.rewrite("x")


def test_assembly_builds_the_mesh_runtime_on_adoption(monkeypatch) -> None:
    from holdspeak.config import DictationConfig
    from holdspeak.plugins.dictation.assembly import _try_build_runtime

    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _mesh_profile()
    )
    cfg = DictationConfig()
    cfg.runtime.backend = "mlx"
    cfg.runtime.profile_id = "p-phone"
    runtime, status, detail = _try_build_runtime(cfg, None)
    assert status == "loaded"
    assert "backend=mesh_relay node=walk-edge" in detail
    assert runtime.info()["backend"] == "mesh_relay"


def test_probe_runtime_reports_mesh_node_liveness(monkeypatch, tmp_path) -> None:
    from holdspeak.config import DictationConfig
    from holdspeak.db import Database, reset_database
    import holdspeak.db as hsdb
    from holdspeak.setup_runtime import probe_runtime

    reset_database()
    db = Database(tmp_path / "probe.db")
    monkeypatch.setattr(hsdb, "get_database", lambda *a, **k: db)
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _mesh_profile()
    )
    cfg = DictationConfig()
    cfg.pipeline.enabled = True
    cfg.runtime.profile_id = "p-phone"

    offline = probe_runtime(cfg)
    assert offline["ok"] is False and offline["backend"] == "mesh_relay"
    assert "walk-edge" in offline["detail"]

    db.mesh_relay.touch_worker("walk-edge")
    live = probe_runtime(cfg)
    assert live["ok"] is True and "is live" in live["detail"]
    reset_database()


def test_per_run_profile_builder_returns_the_relay_provider() -> None:
    intel = build_meeting_intel_for_profile(
        kind="meshNode", base_url=None, model="qwen3.5-4b",
        profile_id="p-phone", node="walk-edge",
    )
    assert isinstance(intel, MeshRelayIntel)
    assert intel.node == "walk-edge" and intel.model_hint == "qwen3.5-4b"


def test_configured_builder_returns_the_relay_provider(monkeypatch) -> None:
    from holdspeak.intel.providers import build_configured_meeting_intel

    cfg = SimpleNamespace(meeting=_meeting_cfg(intel_profile_id="p-phone"))
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _mesh_profile()
    )
    intel = build_configured_meeting_intel()
    assert isinstance(intel, MeshRelayIntel) and intel.node == "walk-edge"


# ── egress says what happened ────────────────────────────────────────────


def test_endpoint_egress_mesh_shape() -> None:
    assert endpoint_egress(node="walk-edge") == {"scope": "mesh", "host": "walk-edge"}
    # existing shapes byte-identical
    assert endpoint_egress(cloud=False) == {"scope": "local"}
    assert endpoint_egress(cloud=True, base_url="http://x.example/v1") == {
        "scope": "cloud", "host": "x.example",
    }


def test_run_egress_reports_mesh_for_profile_and_default(monkeypatch) -> None:
    from holdspeak.web.routes.primitives.ask import _run_egress

    egress, model = _run_egress(ctx=None, prof=_mesh_profile(), intel=SimpleNamespace(active_provider="cloud"))
    assert egress == {"scope": "mesh", "host": "walk-edge"} and model == "qwen3.5-4b"

    relay = MeshRelayIntel(node="walk-edge", model_hint="qwen3.5-4b", relay=object())
    egress, model = _run_egress(ctx=None, prof=None, intel=relay)
    assert egress == {"scope": "mesh", "host": "walk-edge"} and model == "qwen3.5-4b"
