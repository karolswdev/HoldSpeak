# Parked 2026-11-09 (tests/low-value-read): functions below, one reason each
# Kept, not run; move back to tests/unit/test_phone_contract.py to restore.

# ruff: noqa


# --- test_every_event_type_has_a_golden_fixture: P8/P3: a fixture-coverage census and pydantic's required/extra-forbid behaviour; the golden round trip stays
def test_every_event_type_has_a_golden_fixture() -> None:
    have = {path.name[len("event."):-len(".json")] for path in PHONE.glob("event.*.json")}
    assert have == set(contract.EVENT_TYPES) - {"ping"}


# --- test_a_stored_event_without_seq_and_an_unknown_field_are_refused: P8/P3: a fixture-coverage census and pydantic's required/extra-forbid behaviour; the golden round trip stays
def test_a_stored_event_without_seq_and_an_unknown_field_are_refused() -> None:
    with pytest.raises(ValueError):
        contract.Event.model_validate({"type": "message.read", "ts": "2026-10-28T00:00:00+00:00",
                                       "data": {"msg_id": "m", "at": "2026-10-28T00:00:00+00:00"}})
    with pytest.raises(ValueError):
        contract.Event.model_validate({"seq": 1, "type": "message.read", "ts": "2026-10-28T00:00:00+00:00",
                                       "data": {"msg_id": "m", "at": "x", "extra": 1}})
