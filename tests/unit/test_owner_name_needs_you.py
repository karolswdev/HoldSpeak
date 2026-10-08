"""First run (C1): the owner's name and aliases, and the needs-you rule.

The "You" card on the first-run face writes ``owner.name`` and
``owner.aliases`` through ``PUT /api/settings``. The needs-you rule reads
them as "me": an action "Karol to send X" is the owner's own work once he
said his name is Karol, and before that it waits on someone else.

The hub boots on an isolated HOME; the action item is minted through the
real Door producer (``door.add_item``) and read through the real route.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from holdspeak.config import Config, OwnerConfig
from holdspeak.runtime import composition

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_philo5_the_loop import Hub, _boot  # noqa: E402


@pytest.fixture
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from holdspeak.db import reset_database

    monkeypatch.setenv("HOME", str(tmp_path))
    hub = _boot(tmp_path, monkeypatch)
    yield hub
    reset_database()
    composition.install(composition.bare(label="pytest"))


def _ok(response: Any, status: int = 200) -> dict[str, Any]:
    assert response.status_code == status, response.text
    return response.json()


def _karol_to_send(hub: Hub) -> str:
    """An action item owned by "Karol", due next week: it waits on Karol."""
    due = (date.today() + timedelta(days=7)).isoformat()
    is_error, action = hub.mcp("door.add_item", {
        "task": "Send the cutover plan", "owner": "Karol", "due": due,
    })
    assert not is_error, action
    return str(action["id"])


def _row(answer: dict[str, Any], ref: str) -> dict[str, Any]:
    rows = [row for row in answer["items"] if str(row.get("ref") or "") == ref]
    assert len(rows) == 1, answer["items"]
    return rows[0]


def test_owner_config_trims_and_drops_repeats() -> None:
    owner = OwnerConfig(name="  Karol   Sane ", aliases=[" Karol ", "karol", "", "KS", "karol sane", "me "])
    assert owner.name == "Karol Sane"
    assert owner.aliases == ["Karol", "KS", "me"]
    assert owner.names() == ["Karol Sane", "Karol", "KS", "me"]


def test_the_name_round_trips_through_settings(hub: Hub) -> None:
    before = _ok(hub.client.get("/api/settings"))
    assert before["owner"] == {"name": "", "aliases": []}
    saved = _ok(hub.client.put("/api/settings", json={
        "owner": {"name": " Karol Sane ", "aliases": ["Karol", " KS ", "karol"]},
    }))
    assert saved["settings"]["owner"] == {"name": "Karol Sane", "aliases": ["Karol", "KS"]}
    assert Config.load().owner.names() == ["Karol Sane", "Karol", "KS"]
    # A partial write of another section keeps the name.
    _ok(hub.client.put("/api/settings", json={"ui": {"desk_sounds": False}}))
    assert _ok(hub.client.get("/api/settings"))["owner"]["name"] == "Karol Sane"
    refused = hub.client.put("/api/settings", json={"owner": {"aliases": 3}})
    assert refused.status_code == 400, refused.text


def test_karol_to_send_needs_you_once_the_name_is_set(hub: Hub) -> None:
    ref = _karol_to_send(hub)

    # Before: "Karol" is someone else. The row waits on him and is not counted.
    before = _ok(hub.client.get("/api/desk/needs-you"))
    row = _row(before, ref)
    assert row["waiting"] is True and row["why"] == "WAITING ON KAROL", row
    assert ref not in [member["ref"] for member in before["members"]]
    assert "karol" not in before["ownerNames"]

    # He says his name on first run.
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol", "aliases": []}}))

    after = _ok(hub.client.get("/api/desk/needs-you"))
    row = _row(after, ref)
    assert row["waiting"] is False and row["why"] == "YOURS", row
    assert ref in [member["ref"] for member in after["members"]]
    assert after["count"] == before["count"] + 1
    assert "karol" in after["ownerNames"]


def test_an_alias_counts_as_me_case_insensitive(hub: Hub) -> None:
    ref = _karol_to_send(hub)
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol Sane", "aliases": ["  KAROL "]}}))
    answer = _ok(hub.client.get("/api/desk/needs-you"))
    assert _row(answer, ref)["why"] == "YOURS"
    assert ref in [member["ref"] for member in answer["members"]]


def test_a_named_other_person_is_never_claimed_by_the_owner_alias(hub: Hub) -> None:
    """Astra #859 P2: "Karol Other" has the alias "Karol"; the owner "Karol
    Sane" has the alias "Karol" too. A Door item the hub resolved to Karol
    Other (``person_relationship_id``) waits on HIM; the owner's own name
    claims only a bare owner string."""
    _ok(hub.client.post("/api/people/setup"))
    other = _ok(hub.client.post("/api/people/relationships", json={
        "display_name": "Karol Other"}), 201)["relationship"]
    other = _ok(hub.client.post(
        f"/api/people/relationships/{other['id']}/owner-aliases", json={"alias": "Karol"}))["relationship"]
    assert other["owner_aliases"] == ["Karol"], other
    ref = _karol_to_send(hub)
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol Sane", "aliases": ["Karol", "me"]}}))

    answer = _ok(hub.client.get("/api/desk/needs-you"))
    row = _row(answer, ref)
    assert row["_doorCard"].get("person_relationship_id") == other["id"], row
    assert row["why"] == "WAITING ON KAROL" and row["waiting"] is True, row
    assert ref not in [member["ref"] for member in answer["members"]]


def _owned_by(hub: Hub, owner: str) -> str:
    due = (date.today() + timedelta(days=7)).isoformat()
    is_error, action = hub.mcp("door.add_item", {"task": f"Send the plan ({owner})", "owner": owner, "due": due})
    assert not is_error, action
    return str(action["id"])


def test_b57_carol_is_karol_when_speech_misheard_his_name(hub: Hub) -> None:
    """PHILO-15 B57: Whisper heard "Karol" as "Carol"; the action is his."""
    carol = _owned_by(hub, "Carol")
    carl = _owned_by(hub, "Carl")  # two edits from Karol: someone else
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol Sane", "aliases": []}}))

    answer = _ok(hub.client.get("/api/desk/needs-you"))
    members = [member["ref"] for member in answer["members"]]
    assert _row(answer, carol)["why"] == "YOURS" and carol in members
    row = _row(answer, carl)
    assert row["why"] == "WAITING ON CARL" and row["waiting"] is True and carl not in members


def test_b57_a_person_named_carol_keeps_her_work(hub: Hub) -> None:
    """Astra r1 P1: a Person named Carol on the desk, with NO owner alias, is
    a real colleague: her action is hers, never the owner's by a one-edit
    match. The Person is made through the real People routes and the item
    through the real Door producer."""
    _ok(hub.client.post("/api/people/setup"))
    _ok(hub.client.post("/api/people/relationships", json={"display_name": "Carol Diaz"}), 201)
    carol = _owned_by(hub, "Carol")
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol Sane", "aliases": []}}))

    answer = _ok(hub.client.get("/api/desk/needs-you"))
    row = _row(answer, carol)
    assert row["why"] == "WAITING ON CAROL" and row["waiting"] is True, row
    assert carol not in [member["ref"] for member in answer["members"]]


def test_b57_sounds_like_owner_rule() -> None:
    from holdspeak.services.needs_you_membership import sounds_like_owner

    names = ["karol sane", "ks"]
    assert sounds_like_owner("Carol", names)          # first name, one change (no Carol on the desk)
    assert sounds_like_owner("KAROL", names)          # case-insensitive
    assert sounds_like_owner("Karl", names)           # one delete
    assert sounds_like_owner("Carol Sane", names)     # whole name, one change
    assert not sounds_like_owner("Carl", names)       # two edits
    assert not sounds_like_owner("Carol Smith", names)  # another surname
    assert not sounds_like_owner("KT", names)         # short names match exactly only
    assert not sounds_like_owner("Carol", [])         # no name set: nobody is him


def test_b57_the_tolerance_needs_proof_that_no_carol_exists() -> None:
    from holdspeak.services.needs_you_membership import SELF_OWNER_NAMES, _is_me

    row = {"id": "a1", "owner": "Carol", "why": "WAITING ON CAROL"}
    mine = ["karol sane"]
    assert _is_me(row, SELF_OWNER_NAMES, mine, (), set())                  # no Person named Carol
    assert not _is_me(row, SELF_OWNER_NAMES, mine, (), {"carol diaz", "carol"})  # Carol is a Person
    assert not _is_me(row, SELF_OWNER_NAMES, mine, (), None)              # the People store is unreadable


def test_b57_his_exact_first_name_never_depends_on_people() -> None:
    """Astra r2 P1: "Karol" with owner "Karol Nowak" (no alias) is him, with
    the People store unreadable or holding a Person named Karol Nowak. Only
    the ONE-EDIT match is gated; an explicit Person link still wins."""
    from holdspeak.services.needs_you_membership import SELF_OWNER_NAMES, _is_me

    row = {"id": "a1", "owner": "Karol", "why": "WAITING ON KAROL"}
    mine = ["karol nowak"]
    assert _is_me(row, SELF_OWNER_NAMES, mine, (), None)                          # locked store
    assert _is_me(row, SELF_OWNER_NAMES, mine, (), {"karol nowak", "karol"})      # he is that Person
    assert not _is_me({**row, "person_relationship_id": "rel-other"}, SELF_OWNER_NAMES, mine, (), set())
    assert not _is_me({**row, "owner": "Carol"}, SELF_OWNER_NAMES, mine, (), None)  # fuzzy stays gated


def test_b57_a_locked_people_store_keeps_his_first_name_work(hub: Hub, monkeypatch) -> None:
    """Through the real Door producer and needs-you route, with the People
    names read failing (a locked store): "Karol" is still YOURS."""
    import holdspeak.services.needs_you_membership as membership

    monkeypatch.setattr(membership, "_read_people_names", lambda principal: None)
    karol = _owned_by(hub, "Karol")
    carol = _owned_by(hub, "Carol")
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol Nowak", "aliases": []}}))
    answer = _ok(hub.client.get("/api/desk/needs-you"))
    members = [member["ref"] for member in answer["members"]]
    assert _row(answer, karol)["why"] == "YOURS" and karol in members
    assert _row(answer, carol)["why"] == "WAITING ON CAROL" and carol not in members  # unreadable: no fuzzy


def test_b57_a_person_named_like_him_does_not_take_his_first_name(hub: Hub) -> None:
    """A Person "Karol Nowak" on the desk (no alias) and an item owned by
    "Karol": it is his (he is that person)."""
    _ok(hub.client.post("/api/people/setup"))
    _ok(hub.client.post("/api/people/relationships", json={"display_name": "Karol Nowak"}), 201)
    karol = _owned_by(hub, "Karol")
    _ok(hub.client.put("/api/settings", json={"owner": {"name": "Karol Nowak", "aliases": []}}))
    answer = _ok(hub.client.get("/api/desk/needs-you"))
    assert _row(answer, karol)["why"] == "YOURS"
    assert karol in [member["ref"] for member in answer["members"]]

