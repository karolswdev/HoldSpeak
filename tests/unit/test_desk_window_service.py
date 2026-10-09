"""PHILO-16 (16b): the hub owns the desk's windows (COMPOSITOR.md §13 L1, L3, L5).

The service is the behaviour: depth is a counter the hub increments, front is
derived, geometry is share+px, every write takes the desk's next revision and refuses a
stale one, and every write announces ONE change set (kind ``windows``).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest

from holdspeak.db import Database
from holdspeak.services.desk_window_service import (
    STATIC_WINDOWS,
    DeskWindowService,
    WindowStale,
    parse_value,
    window_app,
)
from holdspeak.services.errors import NotFound, ValidationError

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture()
def svc(tmp_path: Path) -> Any:
    events: list[tuple[str, list[str]]] = []
    service = DeskWindowService(Database(tmp_path / "w.db"), on_changed=lambda op, ids: events.append((op, ids)))
    service.events = events  # type: ignore[attr-defined]
    return service


def _front(listed: dict[str, Any]) -> list[str]:
    return [w["id"] for w in listed["windows"] if w["front"]]


def _order(listed: dict[str, Any]) -> list[str]:
    return [w["id"] for w in listed["windows"]]


# ---- open, raise, front ---------------------------------------------------


def test_open_puts_each_window_on_top_and_front_is_derived(svc: Any) -> None:
    for n, wid in enumerate(("chair:brief", "chair:week", "chair:needs"), start=1):
        row = svc.open(wid)
        assert row["front"] is True and row["revision"] == n  # one counter per desk
    listed = svc.list()
    assert _order(listed) == ["chair:brief", "chair:week", "chair:needs"]
    assert [w["depth"] for w in listed["windows"]] == [1, 2, 3]
    assert _front(listed) == ["chair:needs"]
    assert listed["windows"][0]["app"] == "chair" and listed["windows"][0]["object_ref"] is None
    assert svc.events == [("open", ["chair:brief"]), ("open", ["chair:week"]), ("open", ["chair:needs"])]


def test_open_is_idempotent_and_raises_an_open_window(svc: Any) -> None:
    svc.open("chair:brief")
    svc.open("chair:week")
    row = svc.open("chair:brief")
    assert row["front"] is True and row["depth"] == 3 and row["revision"] == 3
    assert len(svc.list()["windows"]) == 2
    svc.events.clear()
    again = svc.open("chair:brief")  # already front: nothing changes, nothing announced
    assert again["revision"] == 3 and svc.events == []


def test_object_window_carries_its_app_and_object_ref(svc: Any) -> None:
    row = svc.open("zone:dir-7", geometry={"x": "-1/2", "y": "-1/2 + 4", "w": "1/2", "h": "100%"})
    assert row["app"] == "zone" and row["object_ref"] == "dir-7"
    assert (row["x"], row["y"], row["w"], row["h"]) == ("-1/2", "-1/2 + 4", "1/2", "100%")
    assert row["arranged"] is True
    assert svc.open("drawer:project:p-1")["app"] == "drawer"
    assert svc.open("surface-people", app="open-people")["app"] == "open-people"


def test_raise_is_plus_plus_highest_and_a_no_op_when_front(svc: Any) -> None:
    for wid in ("chair:brief", "chair:week", "chair:needs"):
        svc.open(wid)
    svc.events.clear()
    row = svc.raise_("chair:brief")
    assert row["depth"] == 4 and row["front"] is True
    assert _order(svc.list()) == ["chair:week", "chair:needs", "chair:brief"]
    same = svc.raise_("chair:brief")
    assert same["depth"] == 4 and same["revision"] == row["revision"]
    assert svc.events == [("raise", ["chair:brief"])]


def test_the_counter_never_reuses_a_depth_after_a_close(svc: Any) -> None:
    svc.open("chair:brief")
    svc.open("chair:week")
    svc.close("chair:week")
    assert svc.open("chair:needs")["depth"] == 3


def test_send_back_goes_under_the_lowest_shown_window(svc: Any) -> None:
    for wid in ("chair:brief", "chair:week", "chair:needs"):
        svc.open(wid)
    svc.seat("chair:brief", True)  # seated: not counted
    row = svc.send_back("chair:needs")
    assert row["depth"] == 1  # under chair:week (2), the lowest SHOWN
    assert _front(svc.list()) == ["chair:week"]


def test_seat_keeps_depth_and_unseat_raises(svc: Any) -> None:
    for wid in ("chair:brief", "chair:week"):
        svc.open(wid)
    seated = svc.seat("chair:week", True)
    assert seated["minimized"] is True and seated["depth"] == 2 and seated["front"] is False
    assert _front(svc.list()) == ["chair:brief"]
    shown = svc.seat("chair:week", False)
    assert shown["minimized"] is False and shown["front"] is True and shown["depth"] == 2
    svc.raise_("chair:brief")
    svc.seat("chair:brief", True)
    svc.raise_("chair:week")  # front among the shown: no-op
    assert svc.seat("chair:brief", False)["depth"] == 3  # still the highest: front without a bump
    svc.seat("chair:week", True)
    svc.raise_("chair:brief")
    svc.seat("chair:brief", True)
    svc.open("chair:needs")
    assert svc.seat("chair:week", False)["depth"] == 5  # under needs (4): unseat raises it


def test_open_restores_a_seated_window(svc: Any) -> None:
    svc.open("chair:brief")
    svc.seat("chair:brief", True)
    assert svc.open("chair:brief")["minimized"] is False


def test_zoom_keeps_its_rect_and_raises(svc: Any) -> None:
    svc.open("chair:brief", geometry={"x": 0, "y": 0, "w": 400, "h": 300})
    svc.open("chair:week")
    row = svc.zoom("chair:brief", True, {"x": "-1/2", "y": "-1/2", "w": "100%", "h": "100%"})
    assert row["zoomed"] is True and row["front"] is True
    assert row["zoom"] == {"x": "-1/2", "y": "-1/2", "w": "100%", "h": "100%"}
    assert (row["w"], row["h"]) == (400, 300)  # the normal rect is untouched
    back = svc.zoom("chair:brief", False)
    assert back["zoomed"] is False and back["zoom"] == row["zoom"]


def test_move_resize_and_set_geometry(svc: Any) -> None:
    svc.open("chair:brief")
    moved = svc.move("chair:brief", "-1/2 + 10", "-50%")
    assert (moved["x"], moved["y"], moved["w"]) == ("-1/2 + 10", "-50%", None)
    sized = svc.resize("chair:brief", "1/3", 400)
    assert (sized["x"], sized["w"], sized["h"]) == ("-1/2 + 10", "1/3", 400)
    whole = svc.set_geometry("chair:brief", {"x": 1, "y": 2, "w": 3, "h": 4})
    assert (whole["x"], whole["y"], whole["w"], whole["h"]) == (1, 2, 3, 4) and whole["arranged"]
    forgot = svc.set_geometry("chair:brief", None)
    assert forgot["x"] is None and forgot["arranged"] is False


def test_close_drops_the_row_and_an_unknown_open_window_is_not_found(svc: Any) -> None:
    svc.open("chair:brief")
    closed = svc.close("chair:brief")
    assert closed["id"] == "chair:brief" and closed["closed"] is True and closed["revision"] == 2
    assert svc.list()["windows"] == []
    with pytest.raises(NotFound):
        svc.raise_("chair:brief")
    with pytest.raises(NotFound):
        svc.close("chair:brief")


# ---- arrange: one transaction, one change set -----------------------------


def test_arrange_is_one_transaction_and_one_announcement(svc: Any) -> None:
    svc.open("chair:brief")
    svc.open("chair:week")
    svc.events.clear()
    out = svc.arrange({
        "chair:brief": {"x": "-1/2", "y": "-1/2", "w": "1/2", "h": "100%"},
        "chair:week": {"x": "0%", "y": "-1/2", "w": "1/2", "h": "100%"},
    })
    assert {w["id"] for w in out["windows"]} == {"chair:brief", "chair:week"}
    assert svc.events == [("arrange", ["chair:brief", "chair:week"])]
    # A closed id refuses the whole arrangement: nothing is written.
    with pytest.raises(NotFound):
        svc.arrange({"chair:brief": {"x": 1, "y": 1, "w": 1, "h": 1}, "chair:needs": {"x": 1, "y": 1, "w": 1, "h": 1}})
    assert svc.get("chair:brief")["x"] == "-1/2"


# ---- CAS: a lost update is refused ----------------------------------------


def test_a_stale_revision_is_refused_on_every_verb(svc: Any) -> None:
    svc.open("chair:brief")
    svc.open("chair:week")
    rev = svc.get("chair:brief")["revision"]
    svc.move("chair:brief", 1, 1, expected_revision=rev)  # client A wins
    calls = [
        lambda: svc.open("chair:brief", expected_revision=rev),
        lambda: svc.move("chair:brief", 2, 2, expected_revision=rev),
        lambda: svc.resize("chair:brief", 2, 2, expected_revision=rev),
        lambda: svc.set_geometry("chair:brief", {"x": 1, "y": 1, "w": 1, "h": 1}, expected_revision=rev),
        lambda: svc.raise_("chair:brief", expected_revision=rev),
        lambda: svc.send_back("chair:brief", expected_revision=rev),
        lambda: svc.seat("chair:brief", True, expected_revision=rev),
        lambda: svc.zoom("chair:brief", True, expected_revision=rev),
        lambda: svc.arrange({"chair:brief": {"x": 1, "y": 1, "w": 1, "h": 1}}, expected_revisions={"chair:brief": rev}),
        lambda: svc.close("chair:brief", expected_revision=rev),
    ]
    for call in calls:
        with pytest.raises(WindowStale) as caught:
            call()
        assert caught.value.code == "window_stale"
        assert caught.value.context["revision"] == svc.get("chair:brief")["revision"] > rev
    assert svc.get("chair:brief")["x"] == 1


def test_stage_shelf_is_a_desk_setting_with_its_own_revision(svc: Any) -> None:
    assert svc.list()["stage_shelf"] == "left"
    out = svc.set_stage_shelf("right")
    assert out == {"stage_shelf": "right", "revision": 1}
    with pytest.raises(WindowStale):
        svc.set_stage_shelf("left", expected_revision=0)
    with pytest.raises(ValidationError):
        svc.set_stage_shelf("top")


# ---- validation (L10) -------------------------------------------------------


def test_a_window_the_registry_does_not_know_is_refused(svc: Any) -> None:
    for bad in ("nonsense", "zone:", "chair:sofa", "a b", "x" * 300, ""):
        with pytest.raises(ValidationError):
            svc.open(bad)
    with pytest.raises(ValidationError) as caught:
        svc.open("chair:brief", app="dictate")
    assert caught.value.code == "window_app_mismatch"
    assert svc.list()["windows"] == []


@pytest.mark.parametrize("value, parsed", [
    (10, (0.0, 10.0)),
    (-4.5, (0.0, -4.5)),
    ("50%", (0.5, 0.0)),
    ("-1/2", (-0.5, 0.0)),
    ("50% + 10", (0.5, 10.0)),
    ("1/2 - 4", (0.5, -4.0)),
    ("-1/2 + 4", (-0.5, 4.0)),
    ("12px", (0.0, 12.0)),
    ("  25%   +   3 ", (0.25, 3.0)),
    ("33.3333% - 0.5", (0.333333, -0.5)),
])
def test_parse_value_reads_the_geometry_ts_grammar(value: Any, parsed: tuple[float, float]) -> None:
    share, px = parse_value(value)
    assert share == pytest.approx(parsed[0]) and px == pytest.approx(parsed[1])


@pytest.mark.parametrize("value", [
    float("nan"), float("inf"), True, None, "", "abc", "50% + 10%", "1 + 2", "1/0", "50%+10",
    "x" * 65, [1], {"x": 1}, 1e9,
])
def test_parse_value_refuses_what_it_does_not_read(value: Any) -> None:
    with pytest.raises(ValidationError):
        parse_value(value)


def test_a_rect_with_a_bad_value_writes_nothing(svc: Any) -> None:
    svc.open("chair:brief")
    with pytest.raises(ValidationError):
        svc.set_geometry("chair:brief", {"x": 1, "y": 1, "w": "wide", "h": 1})
    with pytest.raises(ValidationError):
        svc.set_geometry("chair:brief", {"x": 1, "y": 1, "w": 1})
    with pytest.raises(ValidationError):
        svc.arrange({"chair:brief": {"x": 1, "y": 1, "w": 1, "h": 1, "z": 9}})
    assert svc.get("chair:brief")["x"] is None and svc.get("chair:brief")["revision"] == 1  # unchanged


# ---- reload order: depth is the state --------------------------------------


def test_a_new_service_on_the_same_database_keeps_the_order(tmp_path: Path) -> None:
    first = DeskWindowService(Database(tmp_path / "w.db"), on_changed=lambda *_: None)
    for wid in ("chair:brief", "chair:week", "chair:needs"):
        first.open(wid)
    first.raise_("chair:brief")
    first.seat("chair:week", True)
    again = DeskWindowService(Database(tmp_path / "w.db"), on_changed=lambda *_: None).list()
    assert _order(again) == ["chair:week", "chair:needs", "chair:brief"]
    assert _front(again) == ["chair:brief"]
    assert [w["minimized"] for w in again["windows"]] == [True, False, False]


# ---- the registry knows every application window ---------------------------


def test_every_window_id_in_applications_ts_is_known() -> None:
    source = (REPO / "web" / "src" / "desk" / "applications.ts").read_text()
    pairs = re.findall(r'action: "([^"]+)",\s*windowId: "([^"]+)"', source)
    assert len(pairs) >= 20
    actions_by_window: dict[str, set[str]] = {}
    for action, window_id in pairs:
        actions_by_window.setdefault(window_id, set()).add(action)
    from holdspeak.services.desk_window_service import NOT_ON_HUB

    for window_id, actions in actions_by_window.items():
        if window_id in NOT_ON_HUB:
            continue  # refused by name (window_not_on_hub), with its reason
        app, _ref = window_app(window_id)
        assert app in actions, (window_id, app, actions)
    assert set(actions_by_window) <= set(STATIC_WINDOWS) | set(NOT_ON_HUB)


def test_one_write_is_one_desk_changed_frame_on_the_bus(tmp_path: Path) -> None:
    """With a hub's composition root installed, the default announcer sends
    ONE frame per write (kind ``windows``) and ``arrange`` names every id."""
    from holdspeak.runtime import composition

    frames: list[tuple[str, Any]] = []
    db = Database(tmp_path / "w.db")
    root = composition.RuntimeServices(db=db, broadcast=lambda kind, data: frames.append((kind, data)))
    composition.install(root)
    try:
        svc = DeskWindowService(db)
        svc.open("chair:brief")
        svc.open("chair:week")
        svc.raise_("chair:week")  # already front: no frame
        svc.arrange({"chair:brief": {"x": 1, "y": 1, "w": 1, "h": 1}, "chair:week": {"x": 2, "y": 2, "w": 2, "h": 2}})
    finally:
        composition.uninstall()
    assert [kind for kind, _ in frames] == ["desk_changed"] * 3
    assert frames[0][1]["kind"] == "windows" and frames[0][1]["id"] == "chair:brief" and frames[0][1]["op"] == "open"
    assert [c["id"] for c in frames[2][1]["changes"]] == ["chair:brief", "chair:week"]
    assert {c["kind"] for c in frames[2][1]["changes"]} == {"windows"}


# ---- Astra r1 on #16b: revisions never repeat; adoption is the hub's fact ----


def test_a_reopened_window_never_repeats_a_revision_aba(svc: Any) -> None:
    """M3: an old revision-1 move against a window closed and reopened is
    refused (one revision counter per desk; a row keeps its last write's)."""
    old = svc.open("chair:brief", geometry={"x": 1, "y": 1, "w": 100, "h": 100})
    closed = svc.close("chair:brief")
    reopened = svc.open("chair:brief", geometry={"x": 900, "y": 900, "w": 400, "h": 400})
    assert closed["revision"] > old["revision"] and reopened["revision"] > closed["revision"]
    with pytest.raises(WindowStale):
        svc.move("chair:brief", 20, 20, expected_revision=old["revision"])
    assert svc.get("chair:brief")["x"] == 900


def test_every_write_takes_the_desks_next_revision(svc: Any) -> None:
    svc.open("chair:brief")
    svc.open("chair:week")
    out = svc.arrange({"chair:brief": {"x": 1, "y": 1, "w": 1, "h": 1}, "chair:week": {"x": 2, "y": 2, "w": 2, "h": 2}})
    assert {w["revision"] for w in out["windows"]} == {3}
    shelf = svc.set_stage_shelf("right")
    assert shelf["revision"] == 4 and svc.list()["revision"] == 4
    assert svc.raise_("chair:brief")["revision"] == 5


def test_adoption_is_recorded_once_and_an_empty_desk_stays_empty(svc: Any) -> None:
    """M2: the hub records that it holds the desk's windows on the first write;
    after that an empty list means an empty desk (no cache re-seeds it)."""
    assert svc.list()["adopted"] is False
    svc.open("chair:brief")
    svc.close("chair:brief")
    listed = svc.list()
    assert listed["windows"] == [] and listed["adopted"] is True


def test_windows_no_view_can_open_from_a_row_are_refused(svc: Any) -> None:
    """M4: never a silent row: a window id whose opener needs state the row
    does not carry is refused by name."""
    from holdspeak.services.desk_window_service import NOT_ON_HUB

    for wid in ("attention", "inspector", "ask", "drawer-info:note:n1", "conductor-info:x", "editor:note:n1"):
        with pytest.raises(ValidationError) as caught:
            svc.open(wid)
        assert caught.value.code == "window_not_on_hub", wid
    assert "inspector" in NOT_ON_HUB and svc.list()["windows"] == []
    assert svc.list()["registry"]["not_on_hub"]["inspector"]


def test_a_project_drawer_row_names_its_project(svc: Any) -> None:
    row = svc.open("drawer:project:p-ledger")
    assert row["app"] == "drawer" and row["object_ref"] == "project:p-ledger"
    assert svc.open("drawer:parked")["app"] == "drawer"
    assert svc.open("conductor")["app"] == "open-conductor"


# ---- Astra r2 on #16b: one snapshot; the lane follows ------------------------


def test_list_rows_and_revision_are_one_snapshot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """M1 (her producer repro): a window opened between the list's two reads
    never yields a list whose revision names a write its rows do not hold."""
    from concurrent.futures import ThreadPoolExecutor

    db = Database(tmp_path / "race.db")
    svc = DeskWindowService(db, on_changed=lambda *_: None)
    svc.open("chair:brief")
    svc.close("chair:brief")
    real_rows = svc._rows
    written: list[dict[str, Any]] = []

    def after_rows(conn: Any) -> Any:
        rows = real_rows(conn)
        with ThreadPoolExecutor(1) as pool:
            written.append(pool.submit(
                lambda: DeskWindowService(db, on_changed=lambda *_: None).open("chair:brief")).result())
        return rows

    monkeypatch.setattr(svc, "_rows", after_rows)
    listed = svc.list()
    monkeypatch.setattr(svc, "_rows", real_rows)
    assert listed["windows"] or listed["revision"] < written[0]["revision"], (listed, written)
    assert svc.list()["revision"] == written[0]["revision"]


def test_the_lane_is_on_the_hub_with_its_launch(svc: Any) -> None:
    """M3: the agent lane follows to another view: its row names the launch,
    and opening it on another launch re-targets the same window."""
    row = svc.open("lane", object_ref="launch:L-1")
    assert row["app"] == "lane" and row["object_ref"] == "launch:L-1"
    again = svc.open("lane", object_ref="launch:L-2")
    assert again["object_ref"] == "launch:L-2" and again["revision"] > row["revision"]
    assert len(svc.list()["windows"]) == 1
