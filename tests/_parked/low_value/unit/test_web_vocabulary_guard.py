# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_web_vocabulary_guard.py to restore.

# ruff: noqa


# --- test_web_copy_speaks_the_canon: P4/P8: wording pins (hand-kept allowlist, banned-word regex self-test, a message string read from source)
def test_web_copy_speaks_the_canon() -> None:
    """Offenders must equal the allowlist exactly, both directions."""
    found = _scan()
    new = {
        f"{rel}: {sorted(words - _ALLOWLIST.get(rel, frozenset()))}"
        for rel, words in found.items()
        if words - _ALLOWLIST.get(rel, frozenset())
    }
    assert not new, (
        "Banned vocabulary in NEW web copy (canon: 'intelligence' not "
        "'intel', 'agents' not 'personas', never an absolute path):\n  "
        + "\n  ".join(sorted(new))
    )
    stale = {
        f"{rel}: {sorted(words - found.get(rel, set()))}"
        for rel, words in _ALLOWLIST.items()
        if words - found.get(rel, set())
    }
    assert not stale, (
        "Allowlist entries whose offender is fixed — DELETE them (the "
        "list only shrinks):\n  " + "\n  ".join(sorted(stale))
    )


# --- test_guard_patterns_catch_seeded_violations: P4/P8: wording pins (hand-kept allowlist, banned-word regex self-test, a message string read from source)
def test_guard_patterns_catch_seeded_violations() -> None:
    """Proven both ways, like the voice guard."""
    for hit in ("Intel model not found", "the intel summary", "New Persona",
                "Personas and coders", "Persona", "Intel"):
        assert any(rx.search(hit) for rx in _BANNED.values()), hit
    for keep in ("Meeting intelligence", "intelligent routing",
                 "personal notes stay local"):
        assert not _BANNED["intel"].search(keep) and not _BANNED[
            "persona"
        ].search(keep), keep


# --- test_backend_refusal_names_its_fix: P4/P8: wording pins (hand-kept allowlist, banned-word regex self-test, a message string read from source)
def test_backend_refusal_names_its_fix() -> None:
    """The model-missing refusal points at Settings and carries no path
    (the trace-C conviction, UIUX_JUDGMENT §1/§5.5)."""
    providers = (_REPO / "holdspeak" / "intel" / "providers.py").read_text()
    engine = (_REPO / "holdspeak" / "intel" / "engine.py").read_text()
    for src in (providers, engine):
        assert "Intel model not found" not in src
        assert "No language model on this hub" in src
