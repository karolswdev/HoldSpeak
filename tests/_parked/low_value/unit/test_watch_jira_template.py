# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_watch_jira_template.py to restore.

# ruff: noqa


# --- TestConflictProposalRefusesAccept::test_handler_map_conflict_refuses: P1: reads two entries of a constant HANDLER_MAP; the decide test below proves the refusal
# (was a method of class TestConflictProposalRefusesAccept)
def test_handler_map_conflict_refuses(self):
    from holdspeak.services.project_delta_service import HANDLER_MAP
    assert HANDLER_MAP["conflict"] == "refuse", (
        f"HANDLER_MAP['conflict'] should be 'refuse', "
        f"got {HANDLER_MAP['conflict']!r}"
    )


# --- TestConflictProposalRefusesAccept::test_observation_attention_accepts: P1: reads two entries of a constant HANDLER_MAP; the decide test below proves the refusal
# (was a method of class TestConflictProposalRefusesAccept)
def test_observation_attention_accepts(self, db):
    """An observation_attention proposal CAN be accepted (record_only handler)."""
    from holdspeak.services.project_delta_service import HANDLER_MAP
    assert HANDLER_MAP["observation_attention"] == "record_only"
