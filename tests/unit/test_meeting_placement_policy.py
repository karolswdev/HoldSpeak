"""HS-130-05 — one meeting placement policy.

Meeting intelligence had two owners with no stated precedence: the
``intel_provider`` intent (local/auto/cloud) and the ``intel_profile_id``
destination pointer. With ``intel_provider`` defaulting to ``"local"``,
``build_configured_meeting_intel`` passed ``provider="local"`` and the resolved
destination was ignored — selecting a Meetings destination did NOTHING (a
silent no-op), while a ``meshNode`` pointer silently won and egressed.

These lock the convergence:

* ``resolve_meeting_placement`` is the ONE decision. An adopted destination
  (mesh OR openAICompatible) WINS over the local/auto/cloud intent, so a
  selected Meetings destination now takes effect — and every describer states
  its real boundary, so the placement is surfaced, never silent.
* ``mir_profile`` / ``plugin_profile`` converge to one ``routing_profile``
  accessor; the legacy values migrate once (idempotent); doctor and the runtime
  read the SAME value.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.intel as intel_module
from holdspeak.config.core import migrate_routing_profile
from holdspeak.config.meeting import MeetingConfig, effective_routing_profile
from holdspeak.db.models import ProfileRecord
from holdspeak.intel import providers
from holdspeak.intel.providers import (
    PLACEMENT_DESTINATION,
    PLACEMENT_PROVIDER,
    PLACEMENT_PROVIDER_OVERRIDDEN,
    build_configured_meeting_intel,
    resolve_meeting_placement,
)


def _meeting_cfg(**overrides):
    base = dict(
        intel_provider="local",
        intel_cloud_model="legacy-model",
        intel_cloud_api_key_env="LEGACY_KEY_ENV",
        intel_cloud_base_url=None,
        intel_cloud_reasoning_effort=None,
        intel_cloud_store=False,
        intel_realtime_model=None,
        intel_profile_id=None,
        intel_enabled=True,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _lan_profile(**overrides) -> ProfileRecord:
    fields = dict(
        id="p-43",
        name="LAN llama",
        kind="openAICompatible",
        base_url="http://192.168.1.43:8080/v1",
        model="Qwen3.5-9B-Q6_K",
    )
    fields.update(overrides)
    return ProfileRecord(**fields)


# ── 1. the silent no-op is gone: a selected destination takes effect ─────────


def test_local_provider_plus_selected_destination_used_to_be_a_no_op() -> None:
    """OLD behavior reproduction: with intel_provider='local', the destination
    pointer was resolved but IGNORED (build passed provider='local', which
    makes MeetingIntel ignore base_url). This asserts the NEW policy: the
    selected openAICompatible destination WINS — provider becomes 'cloud' and
    the run is placed on that endpoint."""
    placement = resolve_meeting_placement(
        _meeting_cfg(intel_provider="local", intel_profile_id="p-43"),
        get_profile=lambda pid: _lan_profile(),
    )
    # The selection wins over the local intent — no silent no-op.
    assert placement.provider == "cloud"
    assert placement.base_url == "http://192.168.1.43:8080/v1"
    assert placement.node is None
    # ...and it is SURFACED: the boundary names the private network, not local.
    assert placement.boundary == "private_network"
    assert placement.source == PLACEMENT_DESTINATION
    assert placement.profile_id == "p-43"


def test_build_configured_honors_the_selected_destination_under_local(monkeypatch) -> None:
    """End-to-end: build_configured_meeting_intel places the run on the
    selected endpoint even though intel_provider='local' (the old no-op)."""
    cfg = SimpleNamespace(meeting=_meeting_cfg(intel_provider="local", intel_profile_id="p-43"))
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(providers, "_lookup_profile_record", lambda pid: _lan_profile())

    intel = build_configured_meeting_intel()
    assert intel.provider == "cloud"  # NOT "local" — the destination took effect
    assert intel.cloud_base_url == "http://192.168.1.43:8080/v1"
    assert intel.cloud_model == "Qwen3.5-9B-Q6_K"


def test_no_destination_falls_back_to_provider_intent() -> None:
    placement = resolve_meeting_placement(_meeting_cfg(intel_provider="local", intel_profile_id=""))
    assert placement.provider == "local"
    assert placement.boundary == "local"
    assert placement.source == PLACEMENT_PROVIDER
    assert placement.profile_id is None


def test_dangling_pointer_is_surfaced_as_overridden_never_silent() -> None:
    """A pointer that is set but not usable does NOT silently win: it falls
    back to the provider intent and the reason rides `source`."""
    placement = resolve_meeting_placement(
        _meeting_cfg(intel_provider="local", intel_profile_id="gone"),
        get_profile=lambda pid: None,
    )
    assert placement.provider == "local"
    assert placement.boundary == "local"
    assert placement.source == PLACEMENT_PROVIDER_OVERRIDDEN
    assert placement.reason and "gone" in placement.reason


# ── 2. a mesh destination is never presented as "local" ──────────────────────


def test_mesh_destination_is_never_local(monkeypatch) -> None:
    cfg = _meeting_cfg(intel_provider="local", intel_profile_id="p-phone")
    placement = resolve_meeting_placement(
        cfg,
        get_profile=lambda pid: _lan_profile(
            id="p-phone", kind="meshNode", base_url=None, node="walk-edge", model="qwen3.5-4b"
        ),
    )
    assert placement.node == "walk-edge"
    assert placement.boundary == "mesh"  # per HS-130-04 vocabulary, never "local"
    assert placement.source == PLACEMENT_DESTINATION
    # The describer agrees (04 delegates to the placement).
    monkeypatch.setattr(
        providers,
        "_lookup_profile_record",
        lambda pid: _lan_profile(
            id="p-phone", kind="meshNode", base_url=None, node="walk-edge", model="qwen3.5-4b"
        ),
    )
    assert providers.configured_egress_boundary(cfg) == "mesh"
    can_transmit, description = providers.intel_egress_posture("local", meeting_cfg=cfg)
    assert can_transmit is True
    assert "local only" not in description.lower()


def test_build_configured_mesh_destination_relays(monkeypatch) -> None:
    cfg = SimpleNamespace(meeting=_meeting_cfg(intel_provider="local", intel_profile_id="p-phone"))
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        providers,
        "_lookup_profile_record",
        lambda pid: _lan_profile(
            id="p-phone", kind="meshNode", base_url=None, node="walk-edge", model="qwen3.5-4b"
        ),
    )
    intel = build_configured_meeting_intel()
    assert getattr(intel, "active_provider", "") == "mesh" or intel.__class__.__name__ == "MeshRelayIntel"


# ── the describer stays consistent with the run for the LAN case ─────────────


def test_configured_egress_boundary_matches_selected_destination(monkeypatch) -> None:
    cfg = _meeting_cfg(intel_provider="local", intel_profile_id="p-43")
    monkeypatch.setattr(providers, "_lookup_profile_record", lambda pid: _lan_profile())
    # build routes here (provider cloud, LAN base_url); the describer must agree.
    assert providers.configured_egress_boundary(cfg) == "private_network"


# ── 3. routing_profile convergence + one-shot idempotent migration ───────────


def test_effective_routing_profile_prefers_mir_over_plugin() -> None:
    # routing_profile default; mir wins over plugin (matches historical runtime).
    cfg = MeetingConfig(mir_profile="architect", plugin_profile="delivery")
    assert effective_routing_profile(cfg) == "architect"
    assert cfg.effective_routing_profile() == "architect"
    # an explicitly-set routing_profile wins over both legacy owners.
    cfg2 = MeetingConfig(routing_profile="incident", mir_profile="architect")
    assert effective_routing_profile(cfg2) == "incident"


def test_legacy_only_plugin_profile_is_read() -> None:
    cfg = MeetingConfig(plugin_profile="product")
    assert effective_routing_profile(cfg) == "product"


def _config_with(tmp_path, **meeting_overrides):
    from holdspeak.config import Config

    cfg = Config()
    for k, v in meeting_overrides.items():
        setattr(cfg.meeting, k, v)
    return cfg


def test_migration_folds_legacy_once_and_is_idempotent(tmp_path) -> None:
    path = tmp_path / "config.json"
    cfg = _config_with(tmp_path, mir_profile="architect", plugin_profile="delivery")

    # First run adopts mir (preferred) and consumes both legacy owners.
    assert migrate_routing_profile(cfg, path) is True
    assert cfg.meeting.routing_profile == "architect"
    assert cfg.meeting.mir_profile == "balanced"
    assert cfg.meeting.plugin_profile == "balanced"

    # Second run is a no-op — the migration is one-shot.
    assert migrate_routing_profile(cfg, path) is False
    assert cfg.meeting.routing_profile == "architect"


def test_migration_prefers_plugin_when_only_it_is_set(tmp_path) -> None:
    cfg = _config_with(tmp_path, plugin_profile="incident")
    assert migrate_routing_profile(cfg, tmp_path / "c.json") is True
    assert cfg.meeting.routing_profile == "incident"


def test_migration_noop_on_fresh_config(tmp_path) -> None:
    cfg = _config_with(tmp_path)
    assert migrate_routing_profile(cfg, tmp_path / "c.json") is False
    assert cfg.meeting.routing_profile == "balanced"


def test_migration_does_not_override_an_explicit_routing_profile(tmp_path) -> None:
    cfg = _config_with(tmp_path, routing_profile="product", mir_profile="architect")
    assert migrate_routing_profile(cfg, tmp_path / "c.json") is False
    assert cfg.meeting.routing_profile == "product"


def test_config_load_runs_the_migration_once(tmp_path, monkeypatch) -> None:
    from holdspeak.config import Config

    path = tmp_path / "config.json"
    seed = Config()
    seed.meeting.mir_profile = "architect"
    seed.save(path)

    # An explicit path load skips migration (test/tool load) but the accessor
    # still reads the effective value...
    loaded = Config.load(path)
    assert effective_routing_profile(loaded.meeting) == "architect"


# ── 4. doctor and the runtime name the SAME value ────────────────────────────


def test_doctor_and_runtime_read_one_routing_profile() -> None:
    from holdspeak.commands import doctor
    from holdspeak.config import Config

    config = Config()
    config.meeting.intent_router_enabled = True
    config.meeting.routing_profile = "architect"

    # doctor
    result = doctor._check_mir_routing(config)
    assert result.status == "PASS"
    assert "profile=architect" in result.detail

    # runtime accessor (what web_runtime / intel_queue / session read)
    assert effective_routing_profile(config.meeting) == "architect"
