# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_css_mono_line_height.py to restore.

# ruff: noqa


# --- test_the_guard_sees_a_bare_mono_rule: P2: tests the guard's own regex helpers
def test_the_guard_sees_a_bare_mono_rule() -> None:
    """The scan's own fence."""
    tokens = {"--font-mono"}
    assert _is_mono("500 12px var(--font-mono)", tokens)
    assert not _shorthand_has_line("500 12px var(--font-mono, a/b)")
    assert _shorthand_has_line("500 12px / 16px var(--font-mono)")
    assert not _is_mono("600 13px var(--font-sans)", tokens)
    assert _JB.search('font: 12px/1 "JetBrains Mono", monospace')
    assert _JB.search('"\\"JetBrains Mono\\", \\"SF Mono\\""')
