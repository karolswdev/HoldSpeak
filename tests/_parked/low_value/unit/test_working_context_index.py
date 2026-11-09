# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_working_context_index.py to restore.

# ruff: noqa


# --- test_the_promotion_spec_is_registered_before_the_note_spec: P7/P5: pins registry order; test_the_sweep_holds_when_the_registry_order_is_reversed proves order does not matter
def test_the_promotion_spec_is_registered_before_the_note_spec() -> None:
    """Registry order IS apply order: `push` iterates the tuple."""
    from holdspeak.services.sync_service import SYNC_REGISTRY
    buckets = [spec.bucket for spec in SYNC_REGISTRY]
    assert "context_promotions" in buckets
    assert buckets.index("context_promotions") < buckets.index("notes")
    spec = next(s for s in SYNC_REGISTRY if s.bucket == "context_promotions")
    assert spec.merger is not None
    # NOT the last-write-wins primitive merge: `revoked` is a monotone join.
    from holdspeak.services.sync_service import _merge_primitive_spec
    assert spec.merger is not _merge_primitive_spec
