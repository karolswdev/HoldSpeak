"""Phone (2026-10-28): the wire round-trips the golden fixtures.

``tests/fixtures/phone/`` was recorded from a real ``PhoneService`` run (a
pairing, a message and its reply, a missed, an answered, a held and a
declined call, a reach, a revoke). Each file is read through its pydantic
model in ``holdspeak/phone/contract.py`` and written back unchanged; the
Apple app's Codable twins read the same files.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from holdspeak.phone import contract

PHONE = Path(__file__).resolve().parents[1] / "fixtures" / "phone"
MODELS = {
    "pairing_token.json": contract.PairingToken, "pair_request.json": contract.PairRequest,
    "pair_response.json": contract.PairResponse, "call_answer.json": contract.CallAnswer,
    "replies.empty.json": contract.Replies,
}


def _cases() -> list[Path]:
    return sorted(PHONE.glob("*.json"))


def test_every_event_type_has_a_golden_fixture() -> None:
    have = {path.name[len("event."):-len(".json")] for path in PHONE.glob("event.*.json")}
    assert have == set(contract.EVENT_TYPES) - {"ping"}


@pytest.mark.parametrize("path", _cases(), ids=lambda path: path.name)
def test_the_fixture_round_trips_through_its_model(path: Path) -> None:
    raw = json.loads(path.read_text())
    if path.name.startswith("event."):
        model = contract.Event.model_validate(raw)
        assert model.model_dump(mode="json", exclude_none=True) == raw
        return
    if path.name == "push_data.json":
        data = contract.PushData.model_validate(raw["data"])
        assert data.model_dump(mode="json") == raw["data"]
        contract.Event.model_validate(json.loads(data.event))  # the pushed event is a contract event
        return
    dumped = MODELS[path.name].model_validate(raw).model_dump(mode="json")
    assert {key: dumped[key] for key in raw} == raw
    assert all(dumped[key] is None for key in set(dumped) - set(raw))  # only unset optionals are added


def test_a_stored_event_without_seq_and_an_unknown_field_are_refused() -> None:
    with pytest.raises(ValueError):
        contract.Event.model_validate({"type": "message.read", "ts": "2026-10-28T00:00:00+00:00",
                                       "data": {"msg_id": "m", "at": "2026-10-28T00:00:00+00:00"}})
    with pytest.raises(ValueError):
        contract.Event.model_validate({"seq": 1, "type": "message.read", "ts": "2026-10-28T00:00:00+00:00",
                                       "data": {"msg_id": "m", "at": "x", "extra": 1}})
