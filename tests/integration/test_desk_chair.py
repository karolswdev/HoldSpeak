"""The Chair's open grammar, the hub half (the test diet, 2026-10-11).

replaces: tests/e2e/test_philo13_06_open_glass.py::TestOneOpenGrammar::test_j1_opens_in_their_own_windows (hub half)
replaces: tests/e2e/test_philo13_06_open_glass.py::TestOneOpenGrammar::test_j3_prep_from_a_fresh_chair (hub half)

The glass walked J1 on a real hub seeded with the canvas week, a calendar and
Priya's accepted request (tests/e2e/open_rig.py). Each row's open is a face
fact, proved in web/src/desk/__tests__/openGrammar.philo1306.test.tsx and
web/src/desk/__tests__/chair.app.test.tsx. Those face tests read fixtures of
/api/door, /api/brief/latest and /api/decisions/{id}. This test boots the same
hub with the same seed (no browser) and proves the real producers write every
field the face fixtures read, so the fixtures cannot lie (SCAR LAW). It also
proves the object windows the rows open are hub windows: a person, a decision,
on top and in front.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote

import pytest

from tests.e2e.glass_infra import _boot
from tests.e2e.open_rig import COMMITMENT, ONE_ON_ONE, TOKEN, _http, _seed

pytestmark = pytest.mark.timeout(240, method="thread")


@pytest.fixture()
def hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Any:
    keyfile = tmp_path / "people.key"
    keyfile.write_text("{}")
    keyfile.chmod(0o600)
    monkeypatch.setenv("HOLDSPEAK_PEOPLE_KEYSTORE_FILE", str(keyfile))
    server, base = _boot(tmp_path, monkeypatch, token=TOKEN)
    try:
        ids = _seed(tmp_path / "home", base)
        yield base, ids
    finally:
        server.stop()


def test_the_rows_the_chair_opens_carry_their_objects(hub: Any, tmp_path: Path) -> None:
    from tests.integration.test_desk_agents_wire import _fence

    base, ids = hub
    priya = ids["priya"]

    # The week: the 1:1 names its person; the sync names its Room.
    door = _http(base, "GET", "/api/door")
    upcoming = {e["title"]: e for e in door["upcoming"]}
    one = upcoming[ONE_ON_ONE]
    assert one["person_relationship_id"] == priya
    assert one["person_label"] == "Priya Nair"
    assert "project_id" not in one
    sync = upcoming["Ledger cutover sync"]
    assert sync["project_id"] == "p-ledger"
    assert sync["project_name"] == "Payments ledger cutover"
    assert "person_relationship_id" not in sync

    # Needs you: Priya's accepted request is a commitment card that names her.
    # The hub writes the card's words as `text` (FollowThroughCard.text), never
    # `title`. The openGrammar face test replays this card as the hub sent it:
    # web/src/desk/__tests__/wire/door-people-commitment.wire.json, fenced
    # here (HOLDSPEAK_WIRE_WRITE=1 rewrites it).
    cards = [c for lane in door["board"].values() for c in lane]
    commitment = [c for c in cards if c.get("text") == COMMITMENT]
    assert commitment, [c.get("text") for c in cards]
    assert commitment[0]["source"] == "people_commitment"
    assert commitment[0]["target_ref"] == f"people:{priya}"
    assert "title" not in commitment[0]
    _fence("door-people-commitment", commitment[0], tmp_path, base, by="tests/integration/test_desk_chair.py")

    # Brief: the decision row's source_ref resolves to that decision.
    brief = _http(base, "GET", "/api/brief/latest")
    rows = [r for r in brief["sections"]["decisions"] if r["text"] == ids["decision_row"]]
    assert rows, brief["sections"]["decisions"]
    kind, _, decision_id = rows[0]["source_ref"].partition(":")
    assert kind == "decision" and decision_id
    decision = _http(base, "GET", f"/api/decisions/{decision_id}")["decision"]
    assert decision["title"] == ids["decision_title"]

    # Brief -> People: the person sections name a relationship by id.
    sections = {p["display_name"]: p for p in brief["person_sections"]}
    assert sections["Avery Chen"]["relationship_id"]


def test_a_row_open_is_a_hub_window_on_top_and_in_front(hub: Any) -> None:
    base, ids = hub

    def post(wid: str, verb: str) -> dict[str, Any]:
        return _http(base, "POST", f"/api/desk/windows/{quote(wid, safe='')}/{verb}", {})

    # A fresh desk: no Chair window (J3 starts here).
    listed = _http(base, "GET", "/api/desk/windows")
    assert [w["id"] for w in listed["windows"] if w["id"].startswith("chair:")] == []

    # Needs you, then the 1:1 row's open: THAT person, in her own window, in front.
    post("chair:needs", "open")
    person = f"pullout:people:{ids['priya']}"
    opened = post(person, "open")
    assert opened["front"] is True
    listed = _http(base, "GET", "/api/desk/windows")
    assert [w["id"] for w in listed["windows"] if w["front"]] == [person]
    assert {w["id"] for w in listed["windows"]} == {"chair:needs", person}

    # A second open of the same person raises the one window; no second window.
    post("chair:needs", "raise")
    again = post(person, "open")
    assert again["front"] is True
    listed = _http(base, "GET", "/api/desk/windows")
    assert [w["id"] for w in listed["windows"]].count(person) == 1


def test_a_retired_brief_or_week_row_still_closes_on_the_hub(hub: Any) -> None:
    """Betterment daily D5: Brief and The week retired into Today. A desk saved
    with one open still holds its row; the hub keeps the ids so the browser's
    close (web/src/desk/compositor/hubWindows.ts, then Today opens in its
    place) is taken, and the list is clean after it."""
    base, _ids = hub

    def post(wid: str, verb: str) -> dict[str, Any]:
        return _http(base, "POST", f"/api/desk/windows/{quote(wid, safe='')}/{verb}", {})

    for wid in ("chair:brief", "chair:week"):
        post(wid, "open")
    listed = _http(base, "GET", "/api/desk/windows")
    assert {w["id"] for w in listed["windows"]} >= {"chair:brief", "chair:week"}
    assert listed["registry"]["static"]["chair:brief"] == "chair"
    for wid in ("chair:brief", "chair:week"):
        assert post(wid, "close")["closed"] is True
    listed = _http(base, "GET", "/api/desk/windows")
    assert not {w["id"] for w in listed["windows"]} & {"chair:brief", "chair:week"}


# ── People: Add on "They owe you", then the saved item (Astra r1 on #1100) ──

PEOPLE_WIRE = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "people-wire"
OWED = "Send me the API migration estimate"


def _people_invented(fixture: Any, live: Any, path: str = "$") -> list[str]:
    """Every field the stored answer carries that the hub's answer does not,
    at every depth and in every list element (SCAR LAW)."""
    if isinstance(fixture, dict):
        if not isinstance(live, dict):
            return [f"{path} is an object, the hub sends {type(live).__name__}"]
        out: list[str] = []
        for key, value in fixture.items():
            out += [f"{path}.{key}"] if key not in live else _people_invented(value, live[key], f"{path}.{key}")
        return out
    if isinstance(fixture, list) and fixture and isinstance(live, list) and live:
        return [d for i, item in enumerate(fixture) for d in _people_invented(item, live[min(i, len(live) - 1)], f"{path}[{i}]")]
    return []


def test_they_owe_you_add_saves_and_the_next_read_carries_the_item(hub: Any, tmp_path: Path) -> None:
    """The hub half of web/src/desk/__tests__/people.app.test.tsx "Add on They
    owe you": the hub's own answers before the press, to the POST and after
    it, recorded into fixtures/people-wire/ (HOLDSPEAK_WRITE_WIRE_FIXTURES=1)
    and fenced here against invented fields on every run."""
    import json
    import os

    base, ids = hub
    rel = ids["priya"]
    wire: dict[str, Any] = {
        "readiness.json": _http(base, "GET", "/api/people/readiness"),
        "relationships.json": _http(base, "GET", "/api/people/relationships"),
        "relationship-before.json": _http(base, "GET", f"/api/people/relationships/{rel}"),
        "one-on-ones.json": _http(base, "GET", f"/api/people/relationships/{rel}/one-on-ones"),
        "brief.json": _http(base, "GET", f"/api/people/relationships/{rel}/brief"),
        "door.json": _http(base, "GET", "/api/door"),
        "projects.json": _http(base, "GET", "/api/projects"),
    }
    before = wire["relationship-before.json"]["relationship"]
    assert OWED not in [o.get("body") for o in before.get("owed_to_you") or []]
    wire["owed-created.json"] = _http(base, "POST", f"/api/people/relationships/{rel}/owed",
                                      {"body": OWED, "visibility": "shared_intent"})
    wire["relationship-after.json"] = after = _http(base, "GET", f"/api/people/relationships/{rel}")
    owed = [o for o in after["relationship"].get("owed_to_you") or [] if o.get("body") == OWED]
    assert owed and owed[0].get("state", "open") == "open", after["relationship"].get("owed_to_you")
    assert OWED not in [c.get("body") for c in after["relationship"].get("commitments") or []]

    text = json.dumps(wire).replace(str(tmp_path), "/Users/owner")
    wire = json.loads(text)
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        PEOPLE_WIRE.mkdir(parents=True, exist_ok=True)
        for name, body in wire.items():
            (PEOPLE_WIRE / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    for name, body in wire.items():
        stored = json.loads((PEOPLE_WIRE / name).read_text())
        assert not _people_invented(stored, body), (name, _people_invented(stored, body))


AGENDA_WIRE = Path(__file__).resolve().parents[2] / "web" / "src" / "desk" / "__tests__" / "fixtures" / "people-agenda-wire"


def test_agenda_remove_takes_the_item_off_to_raise(hub: Any, tmp_path: Path) -> None:
    """The hub half of web/src/desk/__tests__/people.app.test.tsx "Remove on a
    TO RAISE row": two agenda items on Priya's 1:1, the brief before, the
    remove answer, and the brief after (only the kept item stays), recorded
    into fixtures/people-agenda-wire/ (HOLDSPEAK_WRITE_WIRE_FIXTURES=1) and
    fenced here against invented fields on every run."""
    import json
    import os

    base, ids = hub
    rel = ids["priya"]
    session = _http(base, "POST", f"/api/people/relationships/{rel}/one-on-ones", {"visibility": "shared_intent"})["one_on_one"]["id"]
    for body in ("Pick the cutover date", "Ask about the EU shard backup plan"):
        _http(base, "POST", f"/api/people/one-on-ones/{session}/agenda",
              {"body": body, "visibility": "shared_intent", "state": "open", "source": {"kind": "manual"}})
    wire: dict[str, Any] = {
        "readiness.json": _http(base, "GET", "/api/people/readiness"),
        "relationships.json": _http(base, "GET", "/api/people/relationships?counts=1"),
        "relationship.json": _http(base, "GET", f"/api/people/relationships/{rel}"),
        "one-on-ones.json": _http(base, "GET", f"/api/people/relationships/{rel}/one-on-ones"),
        "brief-before.json": _http(base, "GET", f"/api/people/relationships/{rel}/brief"),
    }
    agenda = wire["brief-before.json"]["brief"]["agenda_items"]
    drop = next(item for item in agenda if item["body"] == "Ask about the EU shard backup plan")
    wire["agenda-removed.json"] = _http(base, "POST", f"/api/people/agenda/{drop['id']}/transition", {"to": "removed"})
    assert wire["agenda-removed.json"]["agenda_item"]["state"] == "removed"
    wire["brief-after.json"] = _http(base, "GET", f"/api/people/relationships/{rel}/brief")
    after = [item["body"] for item in wire["brief-after.json"]["brief"]["agenda_items"]]
    assert "Ask about the EU shard backup plan" not in after and "Pick the cutover date" in after, after

    text = json.dumps(wire).replace(str(tmp_path), "/Users/owner")
    wire = json.loads(text)
    if os.environ.get("HOLDSPEAK_WRITE_WIRE_FIXTURES") == "1":
        AGENDA_WIRE.mkdir(parents=True, exist_ok=True)
        for name, body in wire.items():
            (AGENDA_WIRE / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    for name, body in wire.items():
        stored = json.loads((AGENDA_WIRE / name).read_text())
        assert not _people_invented(stored, body), (name, _people_invented(stored, body))
