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
from holdspeak.delivery.node_link import NodeTokenStore
from holdspeak.deployment_revisions import DeploymentRevision
from holdspeak.inference_targets import DeploymentIdentity
from holdspeak.intel.mesh_relay import MeshRelayIntel
from holdspeak.intel.models import MeetingIntelError
from holdspeak.intel.providers import configured_meeting_intel
from tests.unit.admitted_context import admitted_context
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


@pytest.fixture
def paired(tmp_path):
    """A REAL pairing for ``walk-edge``, in this test's own custody file.

    HS-131-16 repair R2.5 deleted the name-only liveness fallback: a mesh
    destination is an exact ``(node_id, credential_generation)`` or it is not a
    destination at all. These tests therefore pair the node the way the product
    does — ``holdspeak node token create`` — instead of relying on a bare
    ``touch_worker`` name stamp that any generation could satisfy.
    """
    store = NodeTokenStore(tmp_path / "nodes.json")
    node_id, _token, snapshot = store.pair("walk-edge")
    return SimpleNamespace(
        store=store, node_id=node_id, generation=snapshot.generation
    )


def _live(db, paired, *, now=T0) -> None:
    """Stamp the EXACT paired credential's poll — the only liveness there is."""
    db.mesh_relay.touch_worker(
        "walk-edge", node_id=paired.node_id, generation=paired.generation, now=now
    )


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


def _revision() -> DeploymentRevision:
    return DeploymentRevision.from_identity(DeploymentIdentity(
        destination_id="p-phone", kind="mesh_node", engine="cloud", model="qwen3.5-4b",
        node="walk-edge", boundary="mesh", endpoint="http://edge.example/v1",
        model_path=None, secret_slot="HOLDSPEAK_PROFILE_P_PHONE_KEY",
    ))


def _provider(db, clock, paired=None, **kw) -> MeshRelayIntel:
    if paired is not None:
        kw.setdefault("token_store", paired.store)
    return MeshRelayIntel(
        node="walk-edge", model_hint="qwen3.5-4b", deployment_revision=_revision(),
        warrant={"signed": "warrant"}, relay=db.mesh_relay, sleep=clock.sleep,
        now=clock.now, **kw,
    )


def _configured_intel():
    """The ONE configured-construction entrance (HS-131-14).

    The old public uncontextual factory is gone: the body is private and reachable
    only through ``configured_meeting_intel``, which refuses without the dispatch
    context an admitted child carries. The placement assertions below are unchanged
    — what changed is that reaching the constructor now requires admission.
    """
    revision = SimpleNamespace(id="dep_configured", destination_id="configured")
    return configured_meeting_intel(
        context=admitted_context(revision=revision), revision=revision
    )

def test_offline_node_refuses_immediately_by_name(db, tmp_path, paired) -> None:
    """Every unusable destination refuses IMMEDIATELY, by a FIXED name (R2.5).

    The old fallback answered from a name-only ``mesh_workers`` timestamp, so an
    unpaired node looked merely "offline" and ANY generation's poll counted as
    this destination being alive. There is no fallback now: absence, unreadable
    custody, a silent credential, and a stale generation each have their own
    fixed class, and none of them queues a row.
    """
    clock = _Clock(T0)

    # 1. No pairing at all — not "offline", UNPAIRED.
    unpaired = NodeTokenStore(tmp_path / "empty-nodes.json")
    with pytest.raises(MeetingIntelError, match="mesh_node_unpaired"):
        _provider(db, clock, token_store=unpaired).run_prompt(user_prompt="hi")

    # 2. Unreadable custody is refused, never guessed at.
    class _Unreadable:
        def pairing(self, _name):
            raise ValueError("node_custody_schema_unknown")

    with pytest.raises(MeetingIntelError, match="mesh_node_custody_unreadable"):
        _provider(db, clock, token_store=_Unreadable()).run_prompt(user_prompt="hi")

    # 3. Paired, but no worker has ever polled under that credential.
    with pytest.raises(MeetingIntelError, match="mesh_node_offline"):
        _provider(db, clock, paired).run_prompt(user_prompt="hi")

    # 4. Paired and polling, but 60 seconds ago — outside the window.
    _live(db, paired, now=T0 - timedelta(seconds=60))
    with pytest.raises(MeetingIntelError, match="mesh_node_offline"):
        _provider(db, clock, paired).run_prompt(user_prompt="hi")

    # 5. A live poll under the PREVIOUS generation is not this destination.
    db.mesh_relay.touch_worker(
        "walk-edge", node_id=paired.node_id,
        generation=paired.generation - 1 or 99, now=T0,
    )
    with pytest.raises(MeetingIntelError, match="mesh_node_offline"):
        _provider(db, clock, paired).run_prompt(user_prompt="hi")

    # nothing was ever queued — refusal is immediate, not queue-then-timeout
    assert db.mesh_relay.claim_next("walk-edge", now=T0) is None


def test_custody_is_held_across_the_pairing_liveness_and_enqueue(db, paired) -> None:
    """Repair R2.5: one held lock spans all three, so nothing splits them.

    Reading the pairing, then checking liveness, then queueing gave a rotate or
    re-pair three places to land — and a row addressed to a credential nothing
    is polling under sits until its deadline. The lock is taken once, before the
    pairing read, and released after the row exists.
    """
    from contextlib import contextmanager

    clock = _Clock(T0)
    _live(db, paired)
    order: list[str] = []
    original_lock = paired.store.custody_lock
    original_pairing = paired.store.pairing
    original_live = db.mesh_relay.node_live
    original_enqueue = db.mesh_relay.enqueue

    @contextmanager
    def watching_lock():
        order.append("lock")
        with original_lock():
            yield
        order.append("unlock")

    def watching_pairing(name):
        order.append("pairing")
        return original_pairing(name)

    def watching_live(*a, **kw):
        order.append("live")
        return original_live(*a, **kw)

    def watching_enqueue(**kw):
        order.append("enqueue")
        return original_enqueue(**kw)

    paired.store.custody_lock = watching_lock
    paired.store.pairing = watching_pairing
    db.mesh_relay.node_live = watching_live
    db.mesh_relay.enqueue = watching_enqueue

    def sleep_and_work(seconds: float) -> None:
        clock.t += timedelta(seconds=seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            db.mesh_relay.complete(job.id, result="ok", now=clock.now())

    try:
        provider = MeshRelayIntel(
            node="walk-edge", model_hint="qwen3.5-4b", deployment_revision=_revision(),
            warrant={"signed": "warrant"}, relay=db.mesh_relay,
            sleep=sleep_and_work, now=clock.now, token_store=paired.store,
        )
        assert provider.run_prompt(user_prompt="hi") == "ok"
    finally:
        db.mesh_relay.node_live = original_live
        db.mesh_relay.enqueue = original_enqueue

    assert order == ["lock", "pairing", "live", "enqueue", "unlock"], order


def test_run_round_trips_through_the_queue(db, paired) -> None:
    clock = _Clock(T0)
    _live(db, paired)

    # a fake worker: completes the job on the first poll tick
    original_sleep = clock.sleep
    claimed: dict = {}

    def sleep_and_work(seconds: float) -> None:
        original_sleep(seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            claimed["job"] = job
            assert job.system_prompt == "Be brief."
            assert job.user_prompt == "What is dictation?"
            assert job.model_hint == "qwen3.5-4b"
            assert job.envelope == {
                "deployment_revision": _revision().to_dict(), "warrant": {"signed": "warrant"},
            }
            db.mesh_relay.complete(job.id, result="Speaking words.", now=clock.now())

    provider = MeshRelayIntel(
        node="walk-edge", model_hint="qwen3.5-4b", deployment_revision=_revision(),
        warrant={"signed": "warrant"}, relay=db.mesh_relay,
        sleep=sleep_and_work, now=clock.now, token_store=paired.store,
    )
    out = provider.run_prompt(system_prompt="Be brief.", user_prompt="What is dictation?")
    assert out == "Speaking words."
    # The row is bound to the EXACT credential it was addressed to (R2.5).
    assert claimed["job"].destination_node_id == paired.node_id
    assert claimed["job"].destination_generation == paired.generation


def test_chat_seam_folds_messages_onto_the_relay(db, paired) -> None:
    """The HS-85-05 walk find: built-in plugins speak `_chat_completion_text`
    (the engine's de-facto second seam), and without it every LLM plugin
    failed softly while the reroute still said executed=True."""
    clock = _Clock(T0)
    _live(db, paired)
    original_sleep = clock.sleep

    def sleep_and_work(seconds: float) -> None:
        original_sleep(seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            assert job.system_prompt == "Plan milestones."
            assert job.user_prompt == "The transcript.\n\nThe tail."
            db.mesh_relay.complete(job.id, result="{}", now=clock.now())

    provider = MeshRelayIntel(
        node="walk-edge", deployment_revision=_revision(), warrant={"signed": "warrant"},
        relay=db.mesh_relay, sleep=sleep_and_work, now=clock.now,
        token_store=paired.store,
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


def test_node_side_failure_surfaces_verbatim(db, paired) -> None:
    clock = _Clock(T0)
    _live(db, paired)

    def sleep_and_fail(seconds: float) -> None:
        clock.t += timedelta(seconds=seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            db.mesh_relay.fail(job.id, error="no model loaded", now=clock.now())

    provider = MeshRelayIntel(
        node="walk-edge", deployment_revision=_revision(), warrant={"signed": "warrant"},
        relay=db.mesh_relay, sleep=sleep_and_fail, now=clock.now,
        token_store=paired.store,
    )
    with pytest.raises(MeetingIntelError, match="walk-edge.*no model loaded"):
        provider.run_prompt(user_prompt="hi")


def test_deadline_expiry_surfaces_the_queue_reason(db, paired) -> None:
    clock = _Clock(T0)
    _live(db, paired)
    provider = _provider(db, clock, paired, deadline_seconds=10, poll_interval_seconds=2.0)
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
    assert eff.base_url is None
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


def test_assembly_builds_the_mesh_runtime_from_the_frozen_admission() -> None:
    from holdspeak.config import DictationConfig
    from holdspeak.plugins.dictation.assembly import _try_build_runtime

    revision = SimpleNamespace(
        engine="mesh_relay",
        node="walk-edge",
        model="qwen3.5-4b",
    )
    admission = SimpleNamespace(
        declares=lambda _capability: True,
        revision=lambda _capability: "dep_mesh_relay",
        plan=SimpleNamespace(deployment=lambda _revision_id: revision),
    )
    cfg = DictationConfig()
    cfg.runtime.backend = "mlx"
    cfg.runtime.profile_id = "ambient-profile-must-not-win"

    runtime, status, detail = _try_build_runtime(cfg, None, admission=admission)

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
    from types import SimpleNamespace

    from tests.unit.admitted_context import admitted_context

    # HS-131-10: the profile builder is a context-requiring adapter factory, and
    # the context is minted from the frozen revision the child was admitted for.
    frozen = SimpleNamespace(id="dep_relay", destination_id="p-phone")
    intel = build_meeting_intel_for_profile(
        kind="meshNode", base_url=None, model="qwen3.5-4b",
        profile_id="p-phone", node="walk-edge", deployment_revision=frozen,
        context=admitted_context(revision=frozen),
    )
    assert isinstance(intel, MeshRelayIntel)
    assert intel.node == "walk-edge" and intel.model_hint == "qwen3.5-4b"


def test_configured_builder_returns_the_relay_provider(monkeypatch) -> None:
    cfg = SimpleNamespace(meeting=_meeting_cfg(intel_profile_id="p-phone"))
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        "holdspeak.intel.providers._lookup_profile_record", lambda pid: _mesh_profile()
    )
    intel = _configured_intel()
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
    from holdspeak.services.support import _run_egress

    egress, model = _run_egress(_mesh_profile(), SimpleNamespace(active_provider="cloud"), default_model="")
    assert egress == {"scope": "mesh", "host": "walk-edge"} and model == "qwen3.5-4b"

    relay = MeshRelayIntel(node="walk-edge", model_hint="qwen3.5-4b", relay=object())
    egress, model = _run_egress(None, relay, default_model="")
    assert egress == {"scope": "mesh", "host": "walk-edge"} and model == "qwen3.5-4b"


# ── HS-131-10 round 2: the relay cannot ride a stale warrant ─────────────────


def test_a_relay_reused_across_children_refuses_its_stale_warrant(db) -> None:
    """Terra blocker 6, mesh half: the envelope must be THIS child's.

    The revision and the warrant are CONSTRUCTOR state. A relay engine that
    outlived one admitted child therefore carried that child's warrant into the
    next one's request: the mesh node would have been handed an envelope whose
    authority belonged to a different operation, while the receipt named this
    one. Nothing on the wire would have looked wrong.

    The runner now refuses to rebind a foreign context onto an engine at all, so
    the reuse cannot happen; this is the same fact checked from the relay's own
    side, at the last possible moment, and named rather than relayed.
    """
    from holdspeak.kernel.dispatch_context import bind_dispatch_context
    from tests.unit.admitted_context import admitted_context

    clock = _Clock(T0)
    frozen = _revision()
    warrant = {"signature": "the-warrant-this-engine-was-built-with"}
    provider = MeshRelayIntel(
        node="walk-edge", model_hint="qwen3.5-4b", deployment_revision=frozen,
        warrant=warrant, relay=db.mesh_relay, sleep=clock.sleep, now=clock.now,
    )

    # A LATER child's context, bound onto the engine an earlier child built.
    later = admitted_context(
        revision=SimpleNamespace(id=frozen.id, destination_id=frozen.destination_id)
    )
    bind_dispatch_context(provider, later)

    with pytest.raises(MeetingIntelError, match="mesh_envelope_stale_warrant"):
        provider.run_prompt(user_prompt="hi")
    # Refused BEFORE the queue: no job carries the wrong authority.
    assert db.mesh_relay.claim_next("walk-edge", now=T0) is None


def test_a_relay_whose_context_agrees_still_relays(db, paired) -> None:
    """The guard is about disagreement, not about carrying a context at all."""
    from holdspeak.kernel.dispatch_context import bind_dispatch_context
    from tests.unit.admitted_context import admitted_context

    clock = _Clock(T0)
    _live(db, paired)
    frozen = _revision()
    context = admitted_context(
        revision=SimpleNamespace(id=frozen.id, destination_id=frozen.destination_id)
    )
    # The warrant the claim actually verified is the one the envelope carries.
    warrant = {"signature": context.warrant_basis}

    original_sleep = clock.sleep

    def sleep_and_work(seconds: float) -> None:
        original_sleep(seconds)
        job = db.mesh_relay.claim_next("walk-edge", now=clock.now())
        if job is not None:
            assert job.envelope["warrant"] == warrant
            db.mesh_relay.complete(job.id, result="relayed", now=clock.now())

    provider = MeshRelayIntel(
        node="walk-edge", model_hint="qwen3.5-4b", deployment_revision=frozen,
        warrant=warrant, relay=db.mesh_relay, sleep=sleep_and_work, now=clock.now,
        token_store=paired.store,
    )
    bind_dispatch_context(provider, context)

    assert provider.run_prompt(user_prompt="hi") == "relayed"
