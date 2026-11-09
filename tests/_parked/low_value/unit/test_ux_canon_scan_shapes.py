# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_ux_canon_scan_shapes.py to restore.

# ruff: noqa


# --- test_scanner_a1_reconciles_with_the_doc_claims_registry: P8: reconciles two button counts with each other; a count fence
def test_scanner_a1_reconciles_with_the_doc_claims_registry() -> None:
    """``raw_button_count()`` (HS-200-46) reads every non-test ``.tsx`` under
    ``web/src`` except the two library files; the scanner reads only the face
    directories and also skips ``*.test.*`` and ``_parked``.  The difference
    is exactly the raw buttons in files the scanner does not scan."""
    mod = _load_scanner()
    scanner_a1 = int(mod.scan(REPO_ROOT)["totals"]["per_rule"].get("A1", 0))
    registry = raw_button_count()
    outside = _independent_raw_buttons(
        lambda rel: _in_registry_scope(rel) and not _in_scanner_scope(rel))
    assert registry == scanner_a1 + outside, (
        f"registry {registry} != scanner {scanner_a1} + {outside} outside the "
        "scanner's scope (design/, _parked, *.test.tsx)"
    )
