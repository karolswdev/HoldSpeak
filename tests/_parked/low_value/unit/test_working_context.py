# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_working_context.py to restore.

# ruff: noqa


# --- test_the_three_tables_and_three_indexes_exist: P3: asserts SQLite tables, indexes, the absence of a CHECK constraint and a UNIQUE key
def test_the_three_tables_and_three_indexes_exist(tmp_path: Path) -> None:
    db = Database(tmp_path / "tables.db")
    with db._connection() as conn:
        names = {
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','index')"
            )
        }
    assert {
        "context_promotions",
        "context_promotion_suppressions",
        "context_dependents",
        "idx_context_promotions_target",
        "idx_context_promotions_source",
        "idx_context_dependents_consumer",
    } <= names


# --- test_target_kind_and_disclosure_state_carry_no_check_constraint: P3: asserts SQLite tables, indexes, the absence of a CHECK constraint and a UNIQUE key
def test_target_kind_and_disclosure_state_carry_no_check_constraint(
    tmp_path: Path,
) -> None:
    """Stories 11, 13, 17 and 20 widen this vocabulary; widening a SQLite
    CHECK is a table rebuild, so the service validates instead."""
    db = Database(tmp_path / "nocheck.db")
    with db._connection() as conn:
        _insert_promotion(db, "note:x", fact_id="widened", conn=conn)
        conn.execute(
            "UPDATE context_promotions SET target_kind='project_facet',"
            " disclosure_state='superseded' WHERE target_ref='note:x'"
        )
        row = conn.execute(
            "SELECT target_kind, disclosure_state FROM context_promotions"
            " WHERE target_ref='note:x'"
        ).fetchone()
    assert row["target_kind"] == "project_facet"
    assert row["disclosure_state"] == "superseded"


# --- test_one_fact_may_carry_several_promotions_into_one_record: P3: asserts SQLite tables, indexes, the absence of a CHECK constraint and a UNIQUE key
def test_one_fact_may_carry_several_promotions_into_one_record(
    tmp_path: Path,
) -> None:
    """`UNIQUE (thread_id, fact_id, target_ref)` deliberately permits N
    promotions into one target_ref -- the append mode is the design's own
    second mode -- which is what makes P0-3's revoke rule necessary."""
    db = Database(tmp_path / "unique.db")
    _insert_promotion(db, "note:n1", fact_id="f1")
    _insert_promotion(db, "note:n1", fact_id="f2")
    with db._connection() as conn:
        count = conn.execute(
            "SELECT count(*) FROM context_promotions WHERE target_ref='note:n1'"
        ).fetchone()[0]
        try:
            _insert_promotion(db, "note:n1", fact_id="f1", conn=conn)
            duplicated = True
        except sqlite3.IntegrityError:
            duplicated = False
    assert count == 2
    assert duplicated is False
