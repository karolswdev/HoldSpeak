# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_people_calendar_link.py to restore.

# ruff: noqa


# --- TestSchemaGrepPin: P5: the same People-column schema scan as test_owner_gesture.py::TestSchemaGrepPin
class TestSchemaGrepPin:
    def test_no_person_or_relationship_referencing_columns_in_schema(self) -> None:
        """The 138 law made mechanical: no People-referencing column in the
        plaintext DB schema. This test fails if anyone adds a person_id,
        people_id, relationship_id, or display_name column to schema.py.
        """
        from holdspeak.db.schema import SCHEMA_SQL

        schema_text = SCHEMA_SQL

        # Extract only CREATE TABLE / column definitions (skip comments).
        lines = []
        for line in schema_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            lines.append(stripped)
        body = "\n".join(lines)

        # These patterns are People-domain identifiers that must NEVER appear
        # as column names in the plaintext schema.
        forbidden_columns = [
            r"\bperson_id\b",
            r"\bpeople_id\b",
            r"\brelationship_id\b",
            r"\bdisplay_name\b",
            r"\bpeople_relationship\b",
        ]
        for pattern in forbidden_columns:
            matches = re.findall(pattern, body, re.IGNORECASE)
            assert not matches, (
                f"People-referencing column pattern {pattern!r} found in "
                f"holdspeak/db/schema.py (the 138 law): {matches}"
            )
