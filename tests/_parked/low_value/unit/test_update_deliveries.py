# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_update_deliveries.py to restore.

# ruff: noqa


# --- test_the_reconcile_creates_the_table_on_an_existing_database: P3/P8/P2: SQLite columns, foreign keys and indexes; a public-method list and a source scan; a test that tests the test's own helper
def test_the_reconcile_creates_the_table_on_an_existing_database(tmp_path: Path) -> None:
    from holdspeak.db import Database

    path = tmp_path / "existing.db"
    Database(path)
    conn = sqlite3.connect(path)
    conn.execute("DROP TABLE project_update_deliveries")  # the database as main left it
    conn.commit()
    assert not conn.execute("SELECT name FROM sqlite_master WHERE name='project_update_deliveries'").fetchone()
    conn.close()
    Database(path)  # opening it reconciles
    conn = sqlite3.connect(path)
    columns = [row[1] for row in conn.execute("PRAGMA table_info(project_update_deliveries)")]
    foreign = {(row[2], row[3]) for row in conn.execute("PRAGMA foreign_key_list(project_update_deliveries)")}
    indexes = {row[1] for row in conn.execute("PRAGMA index_list(project_update_deliveries)")}
    conn.close()
    # PHILO-10-01: four additive columns (how it left, its send, its outcome, its proof).
    assert columns == ["id", "update_id", "project_id", "delivered_at", "delivered_to", "operation_id",
                       "channel", "send_id", "outcome", "proof_json"]
    assert foreign == {("project_updates", "update_id"), ("kernel_operations", "operation_id")}
    assert "idx_project_update_deliveries_update" in indexes


# --- test_the_repository_has_no_update_or_delete_path: P3/P8/P2: SQLite columns, foreign keys and indexes; a public-method list and a source scan; a test that tests the test's own helper
def test_the_repository_has_no_update_or_delete_path() -> None:
    from holdspeak.db.updates import UpdateDeliveriesRepository

    public = sorted(name for name in vars(UpdateDeliveriesRepository) if not name.startswith("_") and name != "table")
    assert public == ["insert_delivery", "insert_delivery_in_transaction", "list_for_update", "list_for_updates"]
    writers = []
    for path in (REPO / "holdspeak").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"(UPDATE|DELETE\s+FROM)\s+project_update_deliveries", text, re.IGNORECASE):
            writers.append(str(path.relative_to(REPO)))
    assert writers == [], f"a row is final; these modules rewrite it: {writers}"


# --- test_the_untouched_fence_turns_red_on_a_delivery_that_writes_the_update: P3/P8/P2: SQLite columns, foreign keys and indexes; a public-method list and a source scan; a test that tests the test's own helper
def test_the_untouched_fence_turns_red_on_a_delivery_that_writes_the_update(hub: Hub) -> None:
    """The MUTATION: a delivery that also stamps the published update."""
    _pid, update_id = _published(hub)
    real = hub.db.project_update_deliveries.insert_delivery

    def mutant(**kwargs: Any) -> dict[str, Any]:
        row = real(**kwargs)
        with hub.db._connection() as conn:
            conn.execute("UPDATE project_updates SET updated_at = '2099-01-01T00:00:00+00:00' WHERE id = ?",
                         (kwargs["update_id"],))
        return row

    with pytest.raises(AssertionError, match="a delivery wrote project_updates"):
        _assert_the_update_is_untouched(hub, update_id, mutant)
