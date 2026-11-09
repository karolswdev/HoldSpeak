# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_presence_panel_frame.py to restore.

# ruff: noqa


# --- test_passive_frame_is_the_exact_phase41_geometry: P1/P3/P8: pins a 408x132 literal, dict-copy semantics, substrings of a JS constant, and that two class constants equal a third
def test_passive_frame_is_the_exact_phase41_geometry() -> None:
    # The mascot-off regression lock: with no card ever presented the panel
    # keeps today's geometry and stays click-through.
    frame = presence_panel_frame(False)
    assert frame == {"width": 408, "height": 132, "interactive": False}


# --- test_frames_are_fresh_copies: P1/P3/P8: pins a 408x132 literal, dict-copy semantics, substrings of a JS constant, and that two class constants equal a third
def test_frames_are_fresh_copies() -> None:
    frame = presence_panel_frame(True)
    frame["width"] = 1
    assert PANEL_FRAME_CARD["width"] != 1
    assert presence_panel_frame(True)["width"] != 1


# --- test_card_probe_matches_the_shell_contract: P1/P3/P8: pins a 408x132 literal, dict-copy semantics, substrings of a JS constant, and that two class constants equal a third
def test_card_probe_matches_the_shell_contract() -> None:
    # The HS-56-02 shell slides the card in by adding `is-in` to #qlippy-card;
    # with the mascot off the class never appears, so the probe stays False.
    assert "qlippy-card" in PANEL_CARD_PROBE_JS
    assert "is-in" in PANEL_CARD_PROBE_JS


# --- test_cocoa_panel_passive_constants_come_from_the_policy: P1/P3/P8: pins a 408x132 literal, dict-copy semantics, substrings of a JS constant, and that two class constants equal a third
def test_cocoa_panel_passive_constants_come_from_the_policy() -> None:
    assert _CocoaPresenceUI.WIDTH == PANEL_FRAME_PASSIVE["width"]
    assert _CocoaPresenceUI.HEIGHT == PANEL_FRAME_PASSIVE["height"]


# --- test_gtk_overlay_passive_constants_come_from_the_policy: P1/P3/P8: pins a 408x132 literal, dict-copy semantics, substrings of a JS constant, and that two class constants equal a third
def test_gtk_overlay_passive_constants_come_from_the_policy() -> None:
    assert _GtkWebKitOverlay.WIDTH == PANEL_FRAME_PASSIVE["width"]
    assert _GtkWebKitOverlay.HEIGHT == PANEL_FRAME_PASSIVE["height"]
