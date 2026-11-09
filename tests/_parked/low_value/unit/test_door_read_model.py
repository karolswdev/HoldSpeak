# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_door_read_model.py to restore.

# ruff: noqa


# --- test_door_never_needs_refinement_thought_schema_fields_beyond_existing_projection: P6: pins the key set of a card
def test_door_never_needs_refinement_thought_schema_fields_beyond_existing_projection(db: Database) -> None:
    _working_thought(db, "existing-projection")

    card = _door(db).get(OWNER)["board"]["active"][0]

    assert set(card) == {
        "id", "source", "target_ref", "open_ref", "title", "body_preview", "state",
        "continuity_state", "updated_at", "aggregate_revision", "lifecycle_revision",
        "filing_status", "lawful_verbs",
    }
    assert {"owner", "due", "priority"}.isdisjoint(card)


# --- test_person_label_memoization_single_resolve_per_series: P7: counts resolver calls on a spy; the label value is checked by the tests beside it
def test_person_label_memoization_single_resolve_per_series(db: Database, tmp_path: Path) -> None:
    """HS-149-03: multiple occurrences of the same series -> one resolve call."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from unittest.mock import patch

    store = EncryptedPeopleStore(tmp_path / "people-memo.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(OWNER, {"display_name": "Jan"})
    people.link_calendar_series(OWNER, rel["id"], "uid-memo", "cal-1", "Recurring sync")

    starts_at = FIXED_NOW + timedelta(hours=1)
    # Insert two occurrences of the same series (same uid + source_id).
    db.calendar_events.replace_projection(
        "rev-memo",
        [
            CalendarEventCandidate(
                id="ce_memo_1",
                uid="uid-memo",
                title="Recurring sync",
                starts_at=starts_at.isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
            CalendarEventCandidate(
                id="ce_memo_2",
                uid="uid-memo",
                title="Recurring sync",
                starts_at=(starts_at + timedelta(hours=168)).isoformat().replace("+00:00", "Z"),
                ends_at=(starts_at + timedelta(hours=168, minutes=30)).isoformat().replace("+00:00", "Z"),
                location=None,
                meeting_url=None,
            ),
        ],
        seen_at=FIXED_NOW.timestamp(),
        source_id="cal-1",
    )

    with patch.object(people, "resolve_relationship_by_series", wraps=people.resolve_relationship_by_series) as spy:
        upcoming = _door(db, people_service=people).get(OWNER)["upcoming"]

    calendar_events = [item for item in upcoming if item["source"] == "calendar_event"]
    assert len(calendar_events) == 2
    assert all(item["person_label"] == "Jan" for item in calendar_events)
    # Pin: exactly one call per distinct (uid, source_id), not per event.
    assert spy.call_count == 1


# --- test_board_person_index_memoizes_one_resolve_per_owner_string: P7: counts resolver calls on a spy; the label value is checked by the tests beside it
def test_board_person_index_memoizes_one_resolve_per_owner_string(
    db: Database, tmp_path: Path,
) -> None:
    """HS-150-02: multiple cards with same owner -> one resolve call."""
    from holdspeak.people import EncryptedPeopleStore, MemoryKeyStore
    from unittest.mock import patch

    store = EncryptedPeopleStore(tmp_path / "people-memo-owner.sqlite3", MemoryKeyStore())
    store.initialize()
    people = PeopleService(store)
    rel = people.create_relationship(OWNER, {"display_name": "Ada"})
    people.link_owner_alias(OWNER, rel["id"], "Ada")

    _insert_action(db, "card-1", owner="Ada")
    _insert_action(db, "card-2", owner="Ada")
    _insert_action(db, "card-3", owner="Grace")

    with patch.object(
        people, "resolve_owner_candidates",
        wraps=people.resolve_owner_candidates,
    ) as spy:
        _door(db, people_service=people).get(OWNER)

    # One call per distinct owner string: "Ada" and "Grace".
    assert spy.call_count == 2
