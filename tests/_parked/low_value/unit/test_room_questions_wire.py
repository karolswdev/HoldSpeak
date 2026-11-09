# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_room_questions_wire.py to restore.

# ruff: noqa


# --- TestMcpParity::test_room_has_new_sections: P6: section keys exist and carry a state key; the parity test and each section's own tests stay
# (was a method of class TestMcpParity)
def test_room_has_new_sections(self, db: Database) -> None:
    """The new HS-169-04 sections are present in the room response."""
    project_id = _seed_project(db)
    svc = ProjectService(db)
    room = svc.room(OWNER, project_id)

    new_sections = ["needsYou", "sources", "health", "sinceRead",
                    "decisions", "commitments", "target"]
    for section in new_sections:
        assert section in room, f"Missing section: {section}"
        assert "state" in room[section], f"Section {section} has no state"
