# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_workbench_triage.py to restore.

# ruff: noqa


# --- TestTriageRejectDB::test_rejected_artifact_still_in_db: P5: test_reject_archives_artifact_and_dismisses_item already reads the rejected row back
# (was a method of class TestTriageRejectDB)
def test_rejected_artifact_still_in_db(self, db):
    wb = _create_workbench(db)
    item = _create_item(db)
    art_id = _create_pending_review_artifact(db)

    now_iso = datetime.now().isoformat()
    with db._connection() as conn:
        conn.execute(
            "UPDATE artifacts SET status = 'rejected', updated_at = ? WHERE id = ?",
            (now_iso, art_id),
        )

    # Still fetchable by ID (lineage)
    art = db.plugins.get_artifact(art_id)
    assert art is not None
    assert art.status == "rejected"
