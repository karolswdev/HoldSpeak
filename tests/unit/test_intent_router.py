from __future__ import annotations

from holdspeak.plugins.router import (
    DEFAULT_PROFILE,
    available_profiles,
    normalize_intent_scores,
    normalize_profile,
    preview_route,
    preview_route_from_transcript,
    select_active_intents,
)


def test_available_profiles_include_balanced_and_domain_profiles() -> None:
    profiles = available_profiles()
    assert "balanced" in profiles
    assert "architect" in profiles
    assert "delivery" in profiles
    assert "product" in profiles
    assert "incident" in profiles


def test_normalize_profile_falls_back_to_default() -> None:
    assert normalize_profile("architect") == "architect"
    assert normalize_profile("  DELIVERY  ") == "delivery"
    assert normalize_profile("unknown") == DEFAULT_PROFILE
    assert normalize_profile(None) == DEFAULT_PROFILE


def test_normalize_intent_scores_clamps_unknowns_and_invalids() -> None:
    scores = normalize_intent_scores(
        {
            "architecture": 1.7,
            "delivery": -0.3,
            "product": "0.75",
            "unknown": 0.9,
            "incident": "not-a-number",
        }
    )
    assert scores["architecture"] == 1.0
    assert scores["delivery"] == 0.0
    assert scores["product"] == 0.75
    assert scores["incident"] == 0.0
    assert "unknown" not in scores


def test_select_active_intents_uses_threshold_and_hysteresis() -> None:
    # delivery is below threshold but remains active from previous window due to hysteresis.
    selected = select_active_intents(
        {"architecture": 0.71, "delivery": 0.57, "product": 0.58},
        threshold=0.6,
        previous_intents=["delivery", "product"],
        hysteresis=0.05,
    )
    assert selected == ["architecture", "product", "delivery"]


def test_preview_route_honors_override_intents_and_profile_chain() -> None:
    decision = preview_route(
        profile="architect",
        intent_scores={"product": 0.9, "delivery": 0.65},
        override_intents=["incident", "comms"],
    )
    assert decision.profile == "architect"
    assert decision.active_intents == ["incident", "comms"]
    assert decision.override_intents == ["incident", "comms"]
    assert "mermaid_architecture" in decision.plugin_chain
    assert "stakeholder_update_drafter" in decision.plugin_chain


def test_preview_route_uses_scores_when_no_override() -> None:
    decision = preview_route(
        profile="balanced",
        intent_scores={"architecture": 0.82, "delivery": 0.66, "incident": 0.3},
        threshold=0.6,
    )
    assert decision.active_intents == ["architecture", "delivery"]
    assert decision.hysteresis_applied is False
    assert decision.threshold == 0.6
    assert "requirements_extractor" in decision.plugin_chain


def test_preview_route_from_transcript_extracts_signals_before_routing() -> None:
    decision = preview_route_from_transcript(
        profile="balanced",
        transcript="Incident severity update and mitigation recap for stakeholders.",
        tags=["incident"],
        threshold=0.2,
    )
    assert "incident" in decision.active_intents
    assert "stakeholder_update_drafter" in decision.plugin_chain
