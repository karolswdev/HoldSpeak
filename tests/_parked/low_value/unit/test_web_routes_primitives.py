# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_web_routes_primitives.py to restore.

# ruff: noqa


# --- test_run_response_source_type_vocab_is_pinned: P1/P5: pins a constant vocabulary set; the iPad card-alias route test proves the fold
def test_run_response_source_type_vocab_is_pinned() -> None:
    """The hub is the canonical authority for run-response `source_type` values.

    Audit follow-up (Phase 22/sync): the iPad authoring port emitted "card" while
    the hub emits "input" — non-breaking but undocumented drift. The hub vocab is
    now pinned here so a future change to any literal is caught (a wire contract
    break for every surface that attaches lineage).
    """
    from holdspeak.web.routes.primitives import (
        CANONICAL_SOURCE_TYPES,
        canonical_source_type,
    )

    # The full canonical set the hub run endpoints emit.
    assert CANONICAL_SOURCE_TYPES == {
        "recipe", "input", "chain", "workflow", "invocation", "attempt"
    }

    # Canonical values pass through unchanged.
    for value in CANONICAL_SOURCE_TYPES:
        assert canonical_source_type(value) == value

    # The iPad synonym "card" folds to the canonical "input" (tolerated alias).
    assert canonical_source_type("card") == "input"
    assert canonical_source_type("CARD") == "input"  # case + strip tolerant
    assert canonical_source_type(" card ") == "input"

    # An unknown tag is NOT rejected — returned lowercased/stripped, untouched
    # (non-breaking: we never claim it canonical, but never drop it either).
    assert canonical_source_type("mystery") == "mystery"
    assert canonical_source_type("") == ""
