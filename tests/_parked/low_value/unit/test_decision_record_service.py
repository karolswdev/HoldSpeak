# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_decision_record_service.py to restore.

# ruff: noqa


# --- test_records_from_each_origin_have_the_same_shape: P6: compares key sets of two records, not values
def test_records_from_each_origin_have_the_same_shape(tmp_path):
    db = Database(tmp_path / "records.db")
    _accepted_meeting_decision(db)
    db.desk_decisions.upsert(
        decision_id="desk-127",
        decision_markdown="Choose the record origin.",
    )
    service = DecisionRecordService(db)

    meeting_record = service.create_from_meeting(None, "dec-127")
    desk_record = service.create_from_desk(None, "desk-127")

    assert set(meeting_record) == set(desk_record)
