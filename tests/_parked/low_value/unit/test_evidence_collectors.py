# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_evidence_collectors.py to restore.

# ruff: noqa


# --- TestObservationShape::test_observation_has_all_fields: P6: fields are non-empty strings and an id has a prefix; no value checked
# (was a method of class TestObservationShape)
def test_observation_has_all_fields(self, rig):
    db = rig
    pid = _seed_project(db)
    _seed_meeting(db, "m-040", "Shape test")
    _associate_meeting(db, pid, "m-040")

    collector = ProjectEvidenceCollector(db)
    collector.collect_all(pid)

    obs_list = db.project_observations.list_observations(pid)
    assert len(obs_list) >= 1

    obs = obs_list[0]
    # SS5.5 required fields
    assert obs["id"].startswith("pobs_")
    assert obs["project_id"] == pid
    assert obs["observation_kind"] != ""
    assert obs["observed_at"] != ""
    assert obs["fact_json"] != ""
    assert obs["content_hash"] != ""
