# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_steward_receipt_ref.py to restore.

# ruff: noqa


# --- test_the_recorded_steward_answers_have_the_hubs_shape: P6: compares the shape of a recorded fixture to the live answer, not a value the face shows
def test_the_recorded_steward_answers_have_the_hubs_shape(recorded: dict[str, Any]) -> None:
    stored = json.loads(recorder.OUT.read_text())
    live = {"schema": "steward-recorded@1", "recordedBy": "scripts/record_steward_fixture.py", **recorded}
    diffs = _same_shape(_shape(stored), _shape(json.loads(json.dumps(live, default=str))))
    assert not diffs, (
        f"{recorder.OUT.name}: the stored answers are not the hub's shape "
        f"(run scripts/record_steward_fixture.py and read the diff): {diffs[:10]}"
    )
