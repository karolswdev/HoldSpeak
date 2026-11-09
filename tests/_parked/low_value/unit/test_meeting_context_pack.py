# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_meeting_context_pack.py to restore.

# ruff: noqa


# --- test_manifest_is_pipeline_with_three_upstreams: P1: asserts the pack manifest constant's kind, upstream ids and permissions
def test_manifest_is_pipeline_with_three_upstreams():
    manifest = meeting_context.MANIFEST
    assert manifest.kind == "pipeline"
    upstream_ids = sorted(c.pack_id for c in manifest.consumes)
    assert upstream_ids == ["calendar_activity", "gh", "jira"]
    # Downstream of `consumes`, the validator already enforced
    # that read:* permissions match. Spot-check that the pack
    # actually carries them.
    perms = set(manifest.permissions)
    for needed in (
        "read:activity_annotations",
        "read:activity_meeting_candidates",
        "write:activity_annotations",
    ):
        assert needed in perms
