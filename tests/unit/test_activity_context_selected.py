"""HS-53-03 — dictate-with-this-as-context: the selected-record override.

A nudge action puts an ``ActivityRecord.id`` into the dictation pipeline so the
rewrite stage can name "the issue you were looking at" by name. The override
pins the selected record at ``records[0]`` of the bundle and records the id on
the bundle itself. With **no** selection the bundle is byte-identical to the
pre-Phase-53 default — that's the load-bearing invariant.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from holdspeak.activity_context import (
    ActivityContextProvider,
    build_activity_context,
)
from holdspeak.db import Database


@pytest.fixture
def db(tmp_path) -> Database:
    return Database(tmp_path / "holdspeak.db")


def _seed_two(db: Database) -> tuple[int, int]:
    issue = db.activity.upsert_activity_record(
        source_browser="safari",
        url="https://github.com/karol/holdspeak/issues/53",
        title="Activity Pre-Briefing",
        entity_type="github_issue",
        entity_id="karol/holdspeak#53",
        last_seen_at=datetime(2026, 6, 8, 13, 45),
    )
    page = db.activity.upsert_activity_record(
        source_browser="firefox",
        url="https://example.com/spec",
        title="Spec doc",
        last_seen_at=datetime(2026, 6, 8, 14, 0),
    )
    return issue.id, page.id


def test_default_path_is_byte_identical(db: Database) -> None:
    """No selection → no `selected_record_id` in the bundle, records untouched."""
    _seed_two(db)
    bundle = build_activity_context(db=db, limit=5).to_dict()
    assert "selected_record_id" not in bundle
    # The default order is `list_activity_records` (last_seen DESC) — page first.
    titles = [r["title"] for r in bundle["records"]]
    assert titles == ["Spec doc", "Activity Pre-Briefing"]


def test_selected_record_is_pinned_at_front(db: Database) -> None:
    issue_id, _ = _seed_two(db)
    bundle = build_activity_context(
        db=db, limit=5, selected_record_id=issue_id
    ).to_dict()
    assert bundle["selected_record_id"] == issue_id
    assert bundle["records"][0]["id"] == issue_id
    assert bundle["records"][0]["entity_type"] == "github_issue"
    # The other record is still in the bundle.
    assert any(r["title"] == "Spec doc" for r in bundle["records"])


def test_selected_record_outside_default_list_is_fetched(db: Database) -> None:
    """The selected record may be older than the default `limit` window —
    HS-53-03 must still pin it."""
    issue_id, _ = _seed_two(db)
    # Seed many newer records so the issue falls off `limit=2`.
    for i in range(5):
        db.activity.upsert_activity_record(
            source_browser="safari",
            url=f"https://example.com/recent/{i}",
            title=f"Recent {i}",
            last_seen_at=datetime(2026, 6, 8, 14, 30 + i),
        )

    bundle = build_activity_context(
        db=db, limit=2, selected_record_id=issue_id
    ).to_dict()
    assert bundle["selected_record_id"] == issue_id
    assert bundle["records"][0]["id"] == issue_id


def test_unknown_selected_id_is_a_no_op(db: Database) -> None:
    _seed_two(db)
    bundle = build_activity_context(
        db=db, limit=5, selected_record_id=999_999
    ).to_dict()
    assert bundle.get("selected_record_id") is None
    assert "selected_record_id" not in bundle  # the engine refuses to fabricate
    titles = [r["title"] for r in bundle["records"]]
    assert titles == ["Spec doc", "Activity Pre-Briefing"]


def test_provider_reads_selected_id_from_context(db: Database) -> None:
    issue_id, _ = _seed_two(db)
    provider = ActivityContextProvider(db=db, refresh=False)

    out = provider({"selected_activity_record_id": issue_id})
    assert out["activity"]["selected_record_id"] == issue_id
    assert out["activity"]["records"][0]["id"] == issue_id

    # And the convenience shape (a whole nudge payload).
    out2 = provider({"selected_activity": {"record_id": issue_id}})
    assert out2["activity"]["selected_record_id"] == issue_id


def test_provider_default_path_is_unchanged(db: Database) -> None:
    _seed_two(db)
    provider = ActivityContextProvider(db=db, refresh=False)
    out = provider({})
    assert "selected_record_id" not in out["activity"]


def test_provider_ignores_blank_or_garbage_selection(db: Database) -> None:
    _seed_two(db)
    provider = ActivityContextProvider(db=db, refresh=False)
    for value in ("", "not-a-number", None):
        out = provider({"selected_activity_record_id": value})
        assert "selected_record_id" not in out["activity"]


def test_get_activity_record_returns_none_for_unknown(db: Database) -> None:
    assert db.activity.get_activity_record(12345) is None
    assert db.activity.get_activity_record("garbage") is None  # type: ignore[arg-type]
