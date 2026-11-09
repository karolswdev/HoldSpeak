# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_ux_canon_scan.py to restore.

# ruff: noqa


# --- TestMicAllowlist::test_every_entry_names_a_reason: P1/P8: hand-kept counts of the scanner's allowlists ('len(MIC_ALLOWLIST) == 19'); no user outcome
# (was a method of class TestMicAllowlist)
def test_every_entry_names_a_reason(self):
    mod = _load_scanner()
    for path, needle, reason in mod.MIC_ALLOWLIST:
        assert path and needle and len(reason) > 10, (path, needle, reason)


# --- TestMicAllowlist::test_the_ledger_matches_the_census: P1/P8: hand-kept counts of the scanner's allowlists ('len(MIC_ALLOWLIST) == 19'); no user outcome
# (was a method of class TestMicAllowlist)
def test_the_ledger_matches_the_census(self):
    """23 census - retired Thread checkbox + R13 + Workbench grammar
    - the Thread number field parked with the Thread window (Q4) = 23,
    + DIR10's briefing-page answer field (the thin kit has no mic) = 24,
    + the Programs wizard's Folder path and Check command (#1833) = 26,
    - the six ModelLibraryCore/TopologyMapView entries parked with the
    Models chain (2026-11-08) = 20, - the Workbench grammar entry parked
    with WorkbenchWindow (#2039) = 19."""
    mod = _load_scanner()
    assert len(mod.MIC_ALLOWLIST) == 19
    assert len({(p, n) for p, n, _ in mod.MIC_ALLOWLIST}) == 19


# --- TestMicHostAuthorities::test_authorities_are_exact_named_fields_present_in_tree: P1/P8: hand-kept counts of the scanner's allowlists ('len(MIC_ALLOWLIST) == 19'); no user outcome
# (was a method of class TestMicHostAuthorities)
def test_authorities_are_exact_named_fields_present_in_tree(self):
    scanner = _load_scanner()
    assert {(path, label) for path, label, _ in scanner.MIC_HOST_AUTHORITIES} == {
        (path, label) for path, _species, label in _MIC_HOST_FIELDS
    }
    assert len(scanner.MIC_HOST_AUTHORITIES) == 4  # DeskComposer owns both reply editor variants; + the Room and Memory composer rows (W2); ThreadComposer parked 2026-11-08
    src = Path(__file__).resolve().parents[2] / "web" / "src"
    for path, label, reason in scanner.MIC_HOST_AUTHORITIES:
        assert label in (src / path).read_text()
        assert len(reason) > 10
