# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_placement_resolver.py to restore.

# ruff: noqa


# --- test_placement_dict_is_the_wire_shape: P1/P8: re-types the source tuple, greps three files for an old pattern, and tests the grep's own regex
def test_placement_dict_is_the_wire_shape(db) -> None:
    res = resolve_placement(db, agent="lan")
    assert res.placement_dict() == {"effective_target_id": "lan", "source": "agent"}
    assert set(PLACEMENT_SOURCES) == {"invocation", "workbench", "agent", "global"}


# --- test_no_inline_this_machine_fallback_in_migrated_files: P1/P8: re-types the source tuple, greps three files for an old pattern, and tests the grep's own regex
def test_no_inline_this_machine_fallback_in_migrated_files() -> None:
    root = _repo_root()
    offenders = []
    for rel in _GUARDED_FILES:
        text = (root / rel).read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _INLINE_FALLBACK.search(line):
                offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "Inline `or \"this_machine\"` placement fallback reintroduced outside "
        "the resolver — route it through resolve_placement instead:\n"
        + "\n".join(offenders)
    )


# --- test_the_guard_actually_fires_on_a_reintroduced_fallback: P1/P8: re-types the source tuple, greps three files for an old pattern, and tests the grep's own regex
def test_the_guard_actually_fires_on_a_reintroduced_fallback() -> None:
    # Prove the guard is not vacuous: the pattern it forbids really matches.
    assert _INLINE_FALLBACK.search('target = resolve(db, wb.profile_id or "this_machine")')
    assert _INLINE_FALLBACK.search("x = y or 'this_machine'")
    assert not _INLINE_FALLBACK.search("target = resolve_placement(db, workbench=wb.profile_id)")
