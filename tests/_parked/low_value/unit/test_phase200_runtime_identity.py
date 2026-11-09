# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_phase200_runtime_identity.py to restore.

# ruff: noqa


# --- test_identity_carries_every_c1_field: P6/P1: checks fields are non-empty and pins schema_version_loaded == 76, which breaks on every schema bump
def test_identity_carries_every_c1_field(tmp_path, monkeypatch):
    """C1's six identity axes are all present and populated."""
    bundle = tmp_path / "_built"
    _stamp(bundle, "bundle-aaa")
    monkeypatch.setattr(ri, "built_dir", lambda: bundle)
    db = _make_db(tmp_path / "holdspeak.db")

    identity = ri.capture_runtime_identity(db_path=db, force=True)

    assert identity.backend_version  # the package version
    assert identity.backend_revision  # a sha, or the honest "unknown"
    assert identity.process_start
    assert identity.pid == os.getpid()
    assert identity.frontend_build == "bundle-aaa"
    assert identity.database_id and len(identity.database_id) == 16
    assert identity.schema_version_expected is not None
    assert identity.schema_version_loaded == 76
    assert identity.config_revision
