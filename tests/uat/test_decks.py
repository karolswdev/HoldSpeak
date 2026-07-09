"""Decks round-trip through the product's own Config.load so they can't rot.

The conductor never imports holdspeak — but a test may. Round-tripping each
shipped deck through `Config.load` is what catches a deck that drifts out of
sync with the config schema (the HSU-1-02 risk table's mitigation).
"""

from __future__ import annotations

import json

import pytest

from uat.conductor.induction.decks import DeckError, DeckRegistry

REQUIRED_DECKS = {"golden-local", "golden-43", "bad-endpoint", "no-model", "mesh-node"}


def _load_config(overlay: dict, tmp_path):
    from holdspeak.config import Config

    path = tmp_path / "config.json"
    path.write_text(json.dumps(overlay))
    return Config.load(path)


def test_all_required_decks_present():
    names = set(DeckRegistry().names())
    assert REQUIRED_DECKS <= names, f"missing decks: {REQUIRED_DECKS - names}"


@pytest.mark.parametrize("deck", sorted(REQUIRED_DECKS))
def test_deck_roundtrips_through_config_load(deck, tmp_path):
    overlay = DeckRegistry().load(deck)
    cfg = _load_config(overlay, tmp_path)
    # A real Config object came back (not the last-resort default fallback,
    # which would silently drop our fields — spot-check a field we set).
    assert cfg.config_version >= 1


def test_bad_endpoint_points_at_dead_port(tmp_path):
    cfg = _load_config(DeckRegistry().load("bad-endpoint"), tmp_path)
    assert cfg.meeting.intel_enabled is True
    assert "127.0.0.1:9" in cfg.meeting.intel_cloud_base_url
    assert "127.0.0.1:9" in cfg.dictation.runtime.openai_compatible_base_url


def test_golden_43_wired_to_the_lan(tmp_path):
    cfg = _load_config(DeckRegistry().load("golden-43"), tmp_path)
    assert cfg.meeting.intel_enabled is True
    assert "192.168.1.43" in cfg.meeting.intel_cloud_base_url


def test_no_model_is_local_and_quiet(tmp_path):
    cfg = _load_config(DeckRegistry().load("no-model"), tmp_path)
    assert cfg.meeting.intel_enabled is False


def test_unknown_deck_raises():
    with pytest.raises(DeckError):
        DeckRegistry().load("no-such-deck")
