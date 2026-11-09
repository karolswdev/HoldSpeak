# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/integration/test_review_routes.py to restore.

# ruff: noqa


# --- TestDeltaEmptyState::test_delta_empty_state_shape: P6: checks two keys exist on an empty delta; the values are tested in test_delta_after_accept_shows_last_accepted_at
# (was a method of class TestDeltaEmptyState)
def test_delta_empty_state_shape(self, rig) -> None:
    db, client, _delta = rig
    project_id = _seed_project(db, "proj-delta-empty")

    resp = client.get(f"/api/projects/{project_id}/delta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["open_review"] is None
    assert "last_accepted_at" in body
    assert "source_coverage" in body
