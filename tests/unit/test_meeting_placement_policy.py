"""HS-130-05 — one meeting placement policy.

Meeting intelligence had two owners with no stated precedence: the
``intel_provider`` intent (local/auto/cloud) and the ``intel_profile_id``
destination pointer. With ``intel_provider`` defaulting to ``"local"``,
the configured construction passed ``provider="local"`` and the resolved
destination was ignored — selecting a Meetings destination did NOTHING (a
silent no-op), while a ``meshNode`` pointer silently won and egressed.

These lock the convergence:

* ``resolve_meeting_placement`` is the ONE decision. An adopted destination
  (mesh OR openAICompatible) WINS over the local/auto/cloud intent, so a
  selected Meetings destination now takes effect — and every describer states
  its real boundary, so the placement is surfaced, never silent.
* ``routing_profile`` is the ONE routing profile field (HS-134-08 deleted the
  legacy ``mir_profile`` / ``plugin_profile`` pair); doctor and the runtime
  read the SAME value via ``effective_routing_profile``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import holdspeak.intel as intel_module
from holdspeak.config.meeting import MeetingConfig, effective_routing_profile
from holdspeak.db.models import ProfileRecord
from holdspeak.intel import providers
from holdspeak.intel.providers import (
    PLACEMENT_DESTINATION,
    PLACEMENT_PROVIDER,
    PLACEMENT_PROVIDER_OVERRIDDEN,
    configured_meeting_intel,
    resolve_meeting_placement,
)

from tests.unit.admitted_context import admitted_context



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


def test_configured_intel_honors_the_selected_destination_under_local(monkeypatch) -> None:
    """End-to-end: the configured entrance places the run on the
    selected endpoint even though intel_provider='local' (the old no-op)."""
    cfg = SimpleNamespace(meeting=_meeting_cfg(intel_provider="local", intel_profile_id="p-43"))
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(providers, "_lookup_profile_record", lambda pid: _lan_profile())

    intel = _configured_intel()
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


def test_configured_intel_mesh_destination_relays(monkeypatch) -> None:
    cfg = SimpleNamespace(meeting=_meeting_cfg(intel_provider="local", intel_profile_id="p-phone"))
    monkeypatch.setattr("holdspeak.config.Config.load", classmethod(lambda cls, path=None: cfg))
    monkeypatch.setattr(
        providers,
        "_lookup_profile_record",
        lambda pid: _lan_profile(
            id="p-phone", kind="meshNode", base_url=None, node="walk-edge", model="qwen3.5-4b"
        ),
    )
    intel = _configured_intel()
    assert getattr(intel, "active_provider", "") == "mesh" or intel.__class__.__name__ == "MeshRelayIntel"


# ── the describer stays consistent with the run for the LAN case ─────────────


def test_configured_egress_boundary_matches_selected_destination(monkeypatch) -> None:
    cfg = _meeting_cfg(intel_provider="local", intel_profile_id="p-43")
    monkeypatch.setattr(providers, "_lookup_profile_record", lambda pid: _lan_profile())
    # build routes here (provider cloud, LAN base_url); the describer must agree.
    assert providers.configured_egress_boundary(cfg) == "private_network"


# ── 3. routing_profile is the ONE field (HS-134-08) ─────────────────────────


def test_effective_routing_profile_reads_routing_profile() -> None:
    cfg = MeetingConfig(routing_profile="architect")
    assert effective_routing_profile(cfg) == "architect"
    assert cfg.effective_routing_profile() == "architect"


def test_effective_routing_profile_defaults_to_balanced() -> None:
    cfg = MeetingConfig()
    assert effective_routing_profile(cfg) == "balanced"


def test_effective_routing_profile_on_config_shaped_object() -> None:
    obj = SimpleNamespace(routing_profile="incident")
    assert effective_routing_profile(obj) == "incident"


def test_legacy_keys_load_clean_from_config_file(tmp_path) -> None:
    """HS-134-08: a config file with the deleted mir_profile / plugin_profile
    keys loads without error -- _coerce drops unknown keys silently."""
    import json
    from holdspeak.config import Config

    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "meeting": {
            "mir_profile": "architect",
            "plugin_profile": "delivery",
            "routing_profile": "product",
        }
    }))
    loaded = Config.load(path)
    # The unknown keys are dropped; routing_profile survives.
    assert loaded.meeting.routing_profile == "product"
    assert not hasattr(loaded.meeting, "mir_profile")
    assert not hasattr(loaded.meeting, "plugin_profile")


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
