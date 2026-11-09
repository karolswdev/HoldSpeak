# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_phase200_voice_custody.py to restore.

# ruff: noqa


# --- test_every_permission_carries_its_pane_path_and_deep_link: P1: re-types the permission table's own literals (pane path, URL suffixes, tokens)
def test_every_permission_carries_its_pane_path_and_deep_link() -> None:
    """The row must be able to name the walk without writing a sentence."""
    by_id = {p.id: p for p in perms.permissions()}
    assert set(by_id) == {"microphone", "input_monitoring", "accessibility"}
    assert by_id["accessibility"].path == [
        "SYSTEM SETTINGS",
        "PRIVACY & SECURITY",
        "ACCESSIBILITY",
    ]
    assert by_id["input_monitoring"].settings_url.endswith("?Privacy_ListenEvent")
    assert by_id["microphone"].settings_url.endswith("?Privacy_Microphone")
    assert by_id["accessibility"].settings_url.endswith("?Privacy_Accessibility")
    # One token naming what breaks, never a sentence.
    assert [by_id[k].needed_for for k in perms.ORDER] == ["CAPTURE", "HOTKEY", "TYPING"]
