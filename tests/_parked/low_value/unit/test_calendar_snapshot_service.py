# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_calendar_snapshot_service.py to restore.

# ruff: noqa


# --- TestCapabilityRegistered: P1: asserts registry constants; the 'refusal' test only re-reads requires.vision, nothing is refused
class TestCapabilityRegistered:
    def test_calendar_snapshot_extract_in_registry(self):
        from holdspeak.inference_capabilities import builtin_capability_definitions

        defs = builtin_capability_definitions()
        ids = {d.id for d in defs}
        assert "calendar.snapshot_extract" in ids

    def test_capability_requires_vision(self):
        from holdspeak.inference_capabilities import builtin_capability_definitions

        defs = builtin_capability_definitions()
        cap = next(d for d in defs if d.id == "calendar.snapshot_extract")
        assert cap.requires.vision is True
        assert cap.requires.structured_output is True
        assert cap.group_id == "background"

    def test_vision_claim_refusal_via_compat_check(self):
        """Profiles without the vision claim refuse this capability."""
        from holdspeak.inference_capabilities import builtin_capability_definitions

        cap = next(
            d
            for d in builtin_capability_definitions()
            if d.id == "calendar.snapshot_extract"
        )
        # The capability requires vision=True; a profile without the "vision"
        # claim in its deployment would be refused by the compat check at
        # inference_assignment_service.py:1876.
        assert cap.requires.vision is True
