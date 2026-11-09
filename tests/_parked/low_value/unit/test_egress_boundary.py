# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_egress_boundary.py to restore.

# ruff: noqa


# --- test_boundary_vocabulary_is_exactly_four: P1: a constant set equals four literals
def test_boundary_vocabulary_is_exactly_four() -> None:
    assert set(providers.EGRESS_BOUNDARIES) == {
        "local",
        "private_network",
        "mesh",
        "cloud",
    }


# --- test_badge_and_run_egress_route_through_the_one_classifier: P2: patches the classifier and asserts the patched value comes back
def test_badge_and_run_egress_route_through_the_one_classifier(monkeypatch) -> None:
    """Every egress surface reads its verdict from `egress_boundary` — patch it
    and both the badge and the run egress change in lockstep."""
    monkeypatch.setattr(providers, "egress_boundary", lambda **kw: "private_network")
    assert endpoint_egress(cloud=False)["scope"] == "private_network"
    egress, _ = run_egress(None, SimpleNamespace(active_provider=""), default_model="x")
    assert egress["scope"] == "private_network"


# --- test_posture_routes_through_the_one_classifier: P2: patches the classifier and asserts the patched value comes back
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
