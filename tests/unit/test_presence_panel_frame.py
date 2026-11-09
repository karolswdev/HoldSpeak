"""HS-56-05 — the native HUD's card-frame policy.

One pure function (`presence_panel_frame`) decides both native renderers'
geometry + pointer-event posture: passive (ring/dock only) is the exact
Phase-41 click-through frame; a presented Qlippy card sizes the panel up and
accepts pointer events — never keyboard focus (the non-activating /
no-accept-focus window flags are not this policy's to touch and stay put).
The renderers learn about cards from the page itself via one shared JS probe.
"""
from __future__ import annotations


from holdspeak.desktop_presence import (
    PANEL_CARD_PROBE_JS,
    PANEL_FRAME_CARD,
    PANEL_FRAME_PASSIVE,
    presence_panel_frame,
)
from holdspeak.desktop_presence_cocoa import _CocoaPresenceUI
from holdspeak.desktop_presence_gtk import _GtkWebKitOverlay


# ── the policy ────────────────────────────────────────────────────────────────


def test_card_frame_sizes_up_and_accepts_pointer_events() -> None:
    frame = presence_panel_frame(True)
    assert frame["interactive"] is True
    assert frame["height"] > PANEL_FRAME_PASSIVE["height"]
    # Same width: the panel grows downward from its anchored top-right corner.
    assert frame["width"] == PANEL_FRAME_PASSIVE["width"]


# ── both renderers source the same policy ─────────────────────────────────────


# ── frame-sync behavior (no GUI deps: stub the apply seam) ───────────────────


def _bare(cls):
    return cls.__new__(cls)


def test_cocoa_sync_applies_only_on_change() -> None:
    ui = _bare(_CocoaPresenceUI)
    applied: list[bool] = []
    ui.apply_card_frame = applied.append
    ui._card_seen = True
    ui._card_visible = False
    ui.sync_card_frame()
    assert applied == [True]

    ui._card_visible = True  # the real apply would set this
    ui.sync_card_frame()
    assert applied == [True], "no churn when the probe answer matches the panel"


def test_gtk_sync_applies_only_on_change() -> None:
    overlay = _bare(_GtkWebKitOverlay)
    applied: list[bool] = []
    overlay.apply_card_frame = applied.append
    overlay._card_seen = True
    overlay._card_visible = False
    overlay.sync_card_frame()
    assert applied == [True]

    overlay._card_visible = True
    overlay.sync_card_frame()
    assert applied == [True]


def test_cocoa_hide_defers_to_a_live_card() -> None:
    # A card awaiting the user outlives the activity linger: hide() while a
    # card shows leaves the panel up; the card's resolution drops it.
    class _PanelSpy:
        def __init__(self) -> None:
            self.order_out_calls = 0

        def orderOut_(self, _sender) -> None:
            self.order_out_calls += 1

    ui = _bare(_CocoaPresenceUI)
    ui.panel = _PanelSpy()
    ui._panel_shown = True
    ui._card_visible = True
    ui.hide()
    assert ui.panel.order_out_calls == 0
    assert ui._panel_shown is False  # the policy's say is still recorded


def test_gtk_hide_defers_to_a_live_card() -> None:
    class _WinSpy:
        def __init__(self) -> None:
            self.hide_calls = 0

        def hide(self) -> None:
            self.hide_calls += 1

    overlay = _bare(_GtkWebKitOverlay)
    overlay.win = _WinSpy()
    overlay._shown = True
    overlay._card_visible = True
    overlay.hide()
    assert overlay.win.hide_calls == 0
    assert overlay._shown is False
