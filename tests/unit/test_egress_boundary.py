"""HS-130-04 — one egress vocabulary: the four lies become one truth.

Egress truth used to be derived in four places that disagreed, and the
disagreements were shown to users as safety claims: a LAN ``192.168.x`` box was
badged ``cloud``; a mesh-routed run was badged "Local only"; a cloud badge with
no URL stamped a ``DEFAULT_CLOUD_HOST`` the run never contacted.

This locks the consolidation: ONE classifier (`egress_boundary`) computes the
four-value vocabulary ``{local, private_network, mesh, cloud}``; the badge, the
run egress, and the posture string all read it; and the frozen mapping below
FAILS if any endpoint shape's verdict silently moves.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from holdspeak.intel import providers
from holdspeak.intel.providers import (
    egress_boundary,
    endpoint_egress,
    intel_egress_posture,
    run_egress,
)

# ── the frozen endpoint-shape → boundary table ───────────────────────────────
# Adding/removing a row is a deliberate, reviewed act. A silently MOVED verdict
# (e.g. a LAN box drifting back to "cloud") fails this test.
FROZEN_EGRESS_MAP: list[tuple[dict, str]] = [
    # localhost / loopback → local (the run never leaves this machine)
    (dict(base_url="http://localhost:8080/v1"), "local"),
    (dict(base_url="http://127.0.0.1:8080/v1"), "local"),
    (dict(base_url="http://[::1]:8080/v1"), "local"),
    (dict(base_url="http://dev.localhost/v1"), "local"),
    # private LAN ranges + private-suffix names → private_network
    (dict(cloud=True, base_url="http://192.168.1.43:8080/v1"), "private_network"),
    (dict(cloud=True, base_url="http://10.0.0.5:8080/v1"), "private_network"),
    (dict(cloud=True, base_url="http://172.16.4.2:8080/v1"), "private_network"),
    (dict(base_url="http://169.254.10.10/v1"), "private_network"),  # link-local
    (dict(base_url="http://box.local/v1"), "private_network"),
    (dict(base_url="http://server.lan/v1"), "private_network"),
    (dict(base_url="http://hub.internal/v1"), "private_network"),
    (dict(base_url="http://nas.home/v1"), "private_network"),
    # a mesh node pointer → mesh (never "Local only")
    (dict(node="walk-edge"), "mesh"),
    (dict(node="walk-edge", base_url="http://192.168.1.9/v1"), "mesh"),  # node wins
    # public cloud hosts → cloud
    (dict(cloud=True, base_url="https://api.openai.com/v1"), "cloud"),
    (dict(cloud=True, base_url="https://api.anthropic.com/v1"), "cloud"),
    (dict(base_url="http://8.8.8.8/v1"), "cloud"),
    # no host: default public endpoint (cloud=True) vs stays-here (cloud=False),
    # and an unparseable/empty host is a SAFE value — never a fabricated host.
    (dict(cloud=True, base_url=None), "cloud"),
    (dict(cloud=False, base_url=None), "local"),
    (dict(base_url=""), "local"),
    (dict(cloud=True, base_url="http://"), "cloud"),
]


@pytest.mark.parametrize("kwargs, expected", FROZEN_EGRESS_MAP)
def test_frozen_endpoint_boundary_map(kwargs: dict, expected: str) -> None:
    assert egress_boundary(**kwargs) == expected


def test_boundary_vocabulary_is_exactly_four() -> None:
    assert set(providers.EGRESS_BOUNDARIES) == {
        "local",
        "private_network",
        "mesh",
        "cloud",
    }


# ── no host the run did not contact is ever named ────────────────────────────


def test_cloud_badge_with_no_url_names_no_host() -> None:
    # The old DEFAULT_CLOUD_HOST fabrication ("api.openai.com") is gone.
    badge = endpoint_egress(cloud=True, base_url=None)
    assert badge == {"scope": "cloud"}
    assert "host" not in badge
    assert endpoint_egress(cloud=True, base_url="http://")["scope"] == "cloud"
    assert "host" not in endpoint_egress(cloud=True, base_url="http://")


def test_lan_badge_is_private_network_with_the_real_host() -> None:
    badge = endpoint_egress(cloud=True, base_url="http://192.168.1.43:8080/v1")
    assert badge == {"scope": "private_network", "host": "192.168.1.43"}


def test_mesh_badge_names_the_node() -> None:
    assert endpoint_egress(node="walk-edge") == {"scope": "mesh", "host": "walk-edge"}


# ── run_egress: LAN endpoint is private_network, mesh is mesh ─────────────────


def test_run_egress_lan_profile_is_private_network() -> None:
    profile = SimpleNamespace(
        kind="openAICompatible", base_url="http://192.168.1.43:8080/v1", model="Q6"
    )
    egress, model = run_egress(profile, SimpleNamespace(active_provider=""), default_model="")
    assert egress == {"scope": "private_network", "host": "192.168.1.43"}
    assert model == "Q6"


def test_run_egress_mesh_profile_is_mesh() -> None:
    profile = SimpleNamespace(kind="meshNode", node="walk-edge", model="qwen3.5-4b")
    egress, model = run_egress(profile, SimpleNamespace(active_provider="cloud"), default_model="")
    assert egress == {"scope": "mesh", "host": "walk-edge"}
    assert model == "qwen3.5-4b"


def test_run_egress_local_default_stays_local() -> None:
    egress, model = run_egress(None, SimpleNamespace(active_provider=""), default_model="hub-4b")
    assert egress == {"scope": "local"}
    assert model == "hub-4b"


# ── intel_egress_posture derives from the RESOLVED route, not intel_provider ──


def test_posture_mesh_route_is_never_local_only(monkeypatch) -> None:
    # intel_provider="local" BUT the intel_profile_id points at a mesh node: the
    # run routes to the relay, so the posture must be mesh — NOT "Local only".
    monkeypatch.setattr(
        providers,
        "_lookup_profile_record",
        lambda pid: SimpleNamespace(
            kind="meshNode", node="walk-edge", model="qwen3.5-4b", deleted=False
        ),
    )
    cfg = SimpleNamespace(intel_provider="local", intel_profile_id="p-phone")
    can_transmit, description = intel_egress_posture("local", meeting_cfg=cfg)
    assert can_transmit is True
    assert "local only" not in description.lower()
    assert "mesh" in description.lower()
    assert providers.configured_egress_boundary(cfg) == "mesh"


def test_posture_lan_route_is_private_network(monkeypatch) -> None:
    monkeypatch.setattr(
        providers,
        "_lookup_profile_record",
        lambda pid: SimpleNamespace(
            kind="openAICompatible",
            base_url="http://192.168.1.43:8080/v1",
            model="Q6",
            node="",
            deleted=False,
        ),
    )
    cfg = SimpleNamespace(intel_provider="cloud", intel_profile_id="p-43")
    can_transmit, description = intel_egress_posture("cloud", meeting_cfg=cfg)
    assert can_transmit is True
    assert "private network" in description.lower()
    assert providers.configured_egress_boundary(cfg) == "private_network"


def test_posture_local_no_profile_never_transmits() -> None:
    cfg = SimpleNamespace(intel_provider="local", intel_profile_id="")
    can_transmit, description = intel_egress_posture("local", meeting_cfg=cfg)
    assert can_transmit is False
    assert "never leave" in description.lower()


# ── exactly ONE function computes the boundary ───────────────────────────────


def test_badge_and_run_egress_route_through_the_one_classifier(monkeypatch) -> None:
    """Every egress surface reads its verdict from `egress_boundary` — patch it
    and both the badge and the run egress change in lockstep."""
    monkeypatch.setattr(providers, "egress_boundary", lambda **kw: "private_network")
    assert endpoint_egress(cloud=False)["scope"] == "private_network"
    egress, _ = run_egress(None, SimpleNamespace(active_provider=""), default_model="x")
    assert egress["scope"] == "private_network"


def test_posture_routes_through_the_one_classifier(monkeypatch) -> None:
    # A non-mesh, non-local config resolves its boundary via egress_boundary.
    monkeypatch.setattr(
        providers,
        "_lookup_profile_record",
        lambda pid: SimpleNamespace(kind="openAICompatible", base_url="http://x/v1", model="", node="", deleted=False),
    )
    monkeypatch.setattr(providers, "egress_boundary", lambda **kw: "cloud")
    cfg = SimpleNamespace(intel_provider="cloud", intel_profile_id="p-x")
    can_transmit, description = intel_egress_posture("cloud", meeting_cfg=cfg)
    assert (can_transmit, description) == providers._EGRESS_POSTURE["cloud"]
