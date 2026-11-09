# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_phase200_task_resume.py to restore.

# ruff: noqa


# --- test_the_invocation_identity_is_unique: P3: tests SQLite UNIQUE and CHECK constraints
def test_the_invocation_identity_is_unique(svc) -> None:
    _service, db, _project_id = svc
    with db._connection() as conn:
        row = conn.execute("SELECT COUNT(*) c FROM project_ask_tasks").fetchone()
    assert row["c"] == 0
    db.project_ask_tasks.create(
        task_id="asktask_1", project_id=_project_id, invocation_id="ask_same", purpose="a",
    )
    with pytest.raises(sqlite3.IntegrityError):
        db.project_ask_tasks.create(
            task_id="asktask_2", project_id=_project_id, invocation_id="ask_same", purpose="b",
        )


# --- test_an_invalid_state_is_refused_by_the_check: P3: tests SQLite UNIQUE and CHECK constraints
def test_an_invalid_state_is_refused_by_the_check(svc) -> None:
    _service, db, project_id = svc
    db.project_ask_tasks.create(
        task_id="asktask_chk", project_id=project_id,
        invocation_id="ask_chk", purpose="a",
    )
    with pytest.raises(ValueError):
        db.project_ask_tasks.settle("asktask_chk", state="invented")
    with db._connection() as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE project_ask_tasks SET state='invented' WHERE id=?", ("asktask_chk",),
            )
