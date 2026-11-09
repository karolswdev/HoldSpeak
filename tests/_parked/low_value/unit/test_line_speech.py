# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_line_speech.py to restore.

# ruff: noqa


# --- test_aupipe_carries_a_bsd_3_header_naming_holdspeak: P4: pins a licence-header sentence in a C file's comment
def test_aupipe_carries_a_bsd_3_header_naming_holdspeak() -> None:
    source = (ROOT / "holdspeak" / "line" / "aupipe" / "aupipe.c").read_text()
    assert "Neither the name of HoldSpeak nor the names of its contributors" in source
    assert "GPL" not in source
