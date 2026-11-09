# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_activity_nudges.py to restore.

# ruff: noqa


# --- test_nudge_serialization_is_jsonable: P6: asserts key names and that json.dumps does not raise
def test_nudge_serialization_is_jsonable(db: Database, now: datetime) -> None:
    db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/k/h/issues/1",
        entity_type="github_issue",
        entity_id="k/h#1",
        last_seen_at=now - timedelta(minutes=10),
    )
    nudges = compute_nudges(db, now=now)
    assert nudges
    payload = [n.to_dict() for n in nudges]
    # Keys present and stable.
    assert {"key", "kind", "title", "body", "score", "citations"} <= set(payload[0])
    import json

    json.dumps(payload)  # must not raise
