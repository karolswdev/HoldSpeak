"""Write docs/internal/philo/graph/atlas-phase9.json: the PHILO-9-04 cases."""
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
OUT = REPO / "docs/internal/philo/graph/atlas-phase9.json"

GATE = [
    {"kind": "ui", "action": "goto", "adapter": "ui-navigation", "url": "/"},
    {"kind": "ui", "action": "click_role", "adapter": "ui-pointer", "role": "button",
     "name": "Continue later", "optional": True},
    {"kind": "check", "predicate": {"kind": "protocol_field", "path": "arrival_required", "value": False},
     "observe_at": "protocol: GET /api/setup/status", "timeout_s": 10,
     "why": "the 'Continue later' dismissal is on the hub before any reload"},
]
SEED = [
    {"kind": "api", "method": "POST", "path": "/api/notes", "adapter": "http-route",
     "body": {"title": f"Atlas list note {i}", "body_markdown": "A row for the list face"},
     "capture_as": f"note_{i}", "capture_path": "note.id", "expect_status": 201,
     "why": "more than 16 objects, so the Floor opens as the list at 393 (store/types.ts defaultViewFor)"}
    for i in range(1, 7)
]
TO_LIST = [
    {"kind": "ui", "action": "reload", "adapter": "ui-navigation", "why": "a fresh Desk read after the seed"},
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=chair-floor-toggle]",
     "why": "go to the Floor (Dock.tsx chair-floor-toggle)"},
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[aria-controls=desk-tool-shelf]",
     "at_width": 1440},
    {"kind": "ui", "action": "fill", "adapter": "ui-keyboard", "selector": "[aria-controls=desk-palette-listbox]",
     "value": "List view", "at_width": 1440},
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[id='desk-palette-option-desk.toggle-view']",
     "at_width": 1440,
     "why": "at 1440 the Floor opens spatial; the palette's List view (desk.toggle-view) opens the list"},
    {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": ".desk-listmode",
     "why": "at 393 the Floor opens as the list (more than 16 objects)"},
    {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer",
     "selector": ".desk-listmode .desk-list-name-cell[aria-label='Atlas list note 6']"},
]
PRE = [
    "a fresh isolated HOME and browser profile; the hub started against that HOME",
    {"kind": "check", "predicate": {"kind": "attr_equals", "attr": "aria-pressed", "value": "true"},
     "observe_at": "[data-testid=chair-floor-toggle]", "why": "the Floor is the surface in front (the toggle is pressed)"},
]
DIVE = {"kind": "ui", "action": "click", "adapter": "ui-pointer",
        "selector": ".desk-listmode .desk-sortable-table-open[aria-label^='Personal zone']",
        "why": "dive into the starter zone Personal (two starter notes: About me, How I like help)"}
STATE = "state.desk_presentation.p9_list_face"


def case(cid, edge, trigger, predicate, observe_at, words, setup_extra=()):
    return {
        "id": cid, "job": "p9", "edge_ids": [edge], "state_id": STATE, "applicability": "applicable",
        "preconditions": PRE, "setup": [*GATE, *SEED, *TO_LIST, *setup_extra], "trigger": trigger,
        "expected": {"predicate": predicate, "observe_at": observe_at, "words": words},
        "completion_bound_s": 25, "viewports": [1440, 393],
    }


CASES = [
    case("case.p9.list_status.shown", "edge.face.list_zone_dive", DIVE,
         {"kind": "readable_text", "value": "2 SHOWN OF 2"}, ".desk-list-status",
         "the owner dives into a zone of two notes; the list's status reads '2 SHOWN OF 2' (the status "
         "style sets capitals), readable, in the viewport. Red on main: '2 SHOWNS OF 2' at both widths."),
    case("case.p9.list_columns.in_view", "edge.face.list_zone_dive", DIVE,
         {"kind": "readable_text", "value": "PERSONAL"},
         ".desk-listmode tbody tr:has(.desk-list-name-cell[aria-label^=About])",
         "the owner dives into a zone; the row 'About me' is wholly inside the viewport and names its zone "
         "PERSONAL: in the Zone column at 1440, on the fold line in the name Button at 393. Red on main at "
         "393: the Kind, Zone and Attention cells run past the right edge, so the row is not in the viewport; "
         "preservation green at 1440."),
    case("case.p9.list_sort.zone_pressed", "edge.face.list_sort",
         {"kind": "ui", "action": "click_role", "adapter": "ui-pointer", "role": "button", "name": "Zone",
          "exact": True,
          "why": "the Zone sort verb: a column header at 1440, in the Name header at 393 (DeskSortableTable.tsx SortButton)"},
         {"kind": "attr_equals", "attr": "aria-pressed", "value": "true"},
         ".desk-listmode thead .desk-sortable-table-sort.is-current",
         "the owner sorts the list by Zone; the sorted verb is the library Button and says it is pressed "
         "(aria-pressed true). Red on main at both widths: the sort verbs are raw buttons with no pressed state."),
    case("case.p9.list_row_menu.delete_in_view", "edge.face.list_row_menu",
         {"kind": "ui", "action": "press", "adapter": "ui-keyboard", "key": "Shift+F10",
          "why": "the row menu from the keyboard (DeskListView.tsx onRowKeyDown: ContextMenu or Shift+F10) on the focused last row"},
         {"kind": "hit_target", "min_width": 44, "min_height": 28, "min_height_by_viewport": {"393": 44}},
         ".desk-work-menu [role=menuitem]:last-of-type",
         "the owner opens the row menu on the list's last row, at the bottom edge; the menu's last entry "
         "(Delete) is wholly inside the viewport and owns its nine hit points; at 393 it is 44 px tall. "
         "Red on main at 393: the panel's guessed clamp leaves Delete cut 15 px, rows 28 px; preservation "
         "green at 1440.",
         setup_extra=[
             {"kind": "ui", "action": "focus", "adapter": "ui-keyboard",
              "selector": ".desk-listmode tbody tr.desk-sortable-table-row:last-child .desk-list-name-cell",
              "why": "keyboard travel to the list's LAST row scrolls the page to its end; the row sits at the bottom edge"},
         ]),
]

atlas = {
    "schema_version": 1,
    "atlas_version": "phase9-room",
    "extends": "docs/internal/philo/graph/atlas.json",
    "source_commit": subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True).strip(),
    "cases": CASES,
    "states": [],
    "clocks": [{"id": "clock.python_wall", "source": "datetime.datetime.now() inside the hub process",
                "mechanism": "none: no Phase 9 case moves a clock", "status": "available", "used_by": []}],
    "excluded": [
        {"id": "excluded.p9.list_face_op", "applicability": "not_applicable",
         "combination": "case.p9.list_status.shown, case.p9.list_columns.in_view, case.p9.list_sort.zone_pressed, "
                        "case.p9.list_row_menu.delete_in_view with an .op sibling",
         "reason": "each proves a FACE fact with no durable outcome: a status word, a row's geometry, a sort "
                   "verb's pressed state, a menu's seat. There is no operation to pair."},
        {"id": "excluded.p9.selection_and_text_floor", "applicability": "not_applicable",
         "combination": "the selection contrast (>= 3:1) and the list's 12 px text floor as atlas cases",
         "reason": "the rig has no predicate that reads a computed style or a composited contrast "
                   "(scripts/graph_walk.py check_predicate); a new predicate kind is rig work outside "
                   "PHILO-9-04. Both are fenced as rendered at 1440 and 393 by "
                   "tests/e2e/test_philo9_04_desk_debts_glass.py (test_the_selection_is_visible, "
                   "test_the_list_text_is_12px_and_readable)."},
    ],
    "council_readings": [],
}


def _line(path, symbol):
    for i, line in enumerate((REPO / path).read_text().splitlines(), 1):
        if symbol in line:
            return i
    raise SystemExit(f"{symbol!r} not in {path}")


sources = [
    ("web/src/desk/components/DeskListView.tsx", "function FoldLine",
     "the fold: Kind, Zone and Attention ride the name Button in a surface of 720 px or less"),
    ("web/src/desk/components/DeskListView.tsx", 'countToken(visible.length, "SHOWN", "SHOWN")',
     "the status says SHOWN for any count"),
    ("web/src/desk/components/DeskSortableTable.tsx", "function SortButton",
     "the one sort verb is the library Button, aria-pressed on the sorted column"),
    ("web/src/desk/components/DeskMenu.tsx", "useLayoutEffect(() => {",
     "the work menu keeps its measured panel inside the viewport"),
    ("web/src/desk/components/list-view.css", "container-name: surface;",
     "the list face is a surface container, so its @container rules apply on the Floor's list"),
]
atlas["states"] = [{
    "id": STATE, "family": "desk_presentation",
    "values": {"list": "the list face as the owner ratified it (2026-09-27)",
               "width": "four columns at 1440; the fold line at 393"},
    "phase1_refs": [],
    "sources": [{"path": p, "symbol": s, "line": _line(p, s), "claim": c} for p, s, c in sources],
    "reachable_by": [c["id"] for c in CASES],
}]
OUT.write_text(json.dumps(atlas, indent=2, ensure_ascii=False) + "\n")
print(OUT)
