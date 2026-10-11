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


def test_the_rows_the_chair_opens_carry_their_objects(hub: Any) -> None:
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
    # The hub writes the card's words as `text` (FollowThroughCard.text); the
    # face reads `title || text` (web/src/desk/needsYou.ts), so the
    # openGrammar fixture's `title` reaches the same row by its fallback.
    cards = [c for lane in door["board"].values() for c in lane]
    commitment = [c for c in cards if c.get("text") == COMMITMENT]
    assert commitment, [c.get("text") for c in cards]
    assert commitment[0]["source"] == "people_commitment"
    assert commitment[0]["target_ref"] == f"people:{priya}"

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

    # The week, then the 1:1 row's open: THAT person, in her own window, in front.
    post("chair:week", "open")
    person = f"pullout:people:{ids['priya']}"
    opened = post(person, "open")
    assert opened["front"] is True
    listed = _http(base, "GET", "/api/desk/windows")
    assert [w["id"] for w in listed["windows"] if w["front"]] == [person]
    assert {w["id"] for w in listed["windows"]} == {"chair:week", person}

    # A second open of the same person raises the one window; no second window.
    post("chair:week", "raise")
    again = post(person, "open")
    assert again["front"] is True
    listed = _http(base, "GET", "/api/desk/windows")
    assert [w["id"] for w in listed["windows"]].count(person) == 1
