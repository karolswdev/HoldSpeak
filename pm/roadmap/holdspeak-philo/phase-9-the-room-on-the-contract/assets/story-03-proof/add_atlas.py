"""Add the PHILO-9-03 face cases to docs/internal/philo/graph/atlas-phase9.json.

Idempotent: the story 03 cases, state and exclusions are replaced by id; the
story 04 cases are kept as they are (story 05 assembles the phase file).
"""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
OUT = REPO / "docs/internal/philo/graph/atlas-phase9.json"
STATE = "state.desk_presentation.p9_room_face"

GATE = [
    {"kind": "ui", "action": "goto", "adapter": "ui-navigation", "url": "/"},
    {"kind": "ui", "action": "click_role", "adapter": "ui-pointer", "role": "button",
     "name": "Continue later", "optional": True},
    {"kind": "api", "method": "PUT", "path": "/api/setup/onboarding", "adapter": "http-route",
     "body": {"disposition": "completed"}, "expect_status": 200,
     "why": "the first-use arrival completed on the hub (the glass does the same): the optional click can "
            "land before the Chair draws it"},
    {"kind": "check", "predicate": {"kind": "protocol_field", "path": "arrival_required", "value": False},
     "observe_at": "protocol: GET /api/setup/status", "timeout_s": 10,
     "why": "the 'Continue later' dismissal is on the hub before any reload"},
]
PROJECT = {"kind": "api", "method": "POST", "path": "/api/projects", "adapter": "http-route",
           "body": {"name": "Atlas ledger cutover"}, "capture_as": "project_id", "capture_path": "project.id",
           "expect_status": 200, "why": "the Room under test"}
LATE = {"kind": "api", "method": "POST", "path": "/api/projects/{project_id}/items", "adapter": "http-route",
        "body": {"item_type": "milestone", "title": "Atlas rehearsal", "due_at": "2020-01-06"},
        "expect_status": 200, "why": "a milestone still planned long after its date: late on any run date"}
DRAFT = {"kind": "api", "method": "POST", "path": "/api/projects/{project_id}/updates/draft", "adapter": "http-route",
         "body": {"generator": "deterministic"}, "capture_as": "update_id", "capture_path": "update.id",
         "expect_status": 200, "why": "an update to publish"}
PUBLISH = {"kind": "api", "method": "POST", "path": "/api/updates/{update_id}/publish", "adapter": "http-route",
           "body": {}, "expect_status": 200, "why": "a published update (the Q0 ruling: delivery needs one)"}
PALETTE = [
    {"kind": "ui", "action": "reload", "adapter": "ui-navigation", "why": "a fresh Desk read after the seed"},
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[aria-controls=desk-tool-shelf]",
     "why": "the palette (DeskToolShelf.tsx: PROJECTS rows `Open <name>`)"},
    {"kind": "ui", "action": "fill", "adapter": "ui-keyboard", "selector": "[aria-controls=desk-palette-listbox]",
     "value": "Atlas ledger cutover"},
]
OPEN_ROOM = {"kind": "ui", "action": "click", "adapter": "ui-pointer",
             "selector": "[id='desk-palette-option-project.open.{project_id}']",
             "why": "Open the project's Room (the one key, open-project-memory, scope project:<id>)"}
ROOM_UP = {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": "[data-testid=room-body]"}
PRE = ["a fresh isolated HOME and browser profile; the hub started against that HOME"]


def case(cid, edge, setup, trigger, predicate, observe_at, words):
    return {
        "id": cid, "job": "p9", "edge_ids": [edge], "state_id": STATE, "applicability": "applicable",
        "preconditions": PRE, "setup": [*GATE, *setup], "trigger": trigger,
        "expected": {"predicate": predicate, "observe_at": observe_at, "words": words},
        "completion_bound_s": 25, "viewports": [1440, 393],
    }


CASES = [
    case("case.p9.room_items.late_row", "edge.face.room_open",
         [PROJECT, LATE, *PALETTE], OPEN_ROOM,
         {"kind": "readable_text", "value": "DAYS LATE"}, "[data-testid=item-row] [data-tone=danger]",
         "the owner opens a Room whose milestone is past its date; ITEMS (after NEEDS YOU) shows it with its "
         "days late in the danger tone, readable in the viewport, as the owner-ratified items canvas draws "
         "it. Red on main at both widths: the Room has no items section."),
    case("case.p9.update_list.head_updates", "edge.face.room_updates",
         [PROJECT, DRAFT, PUBLISH, *PALETTE, OPEN_ROOM, ROOM_UP],
         {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=updates-verb]",
          "why": "the update list (ProjectRoomCore.tsx RoomHead `Draft update`)"},
         {"kind": "readable_text", "value": "UPDATES 1"}, ".update-list .surface-ledger-count",
         "the owner opens the Room's update list holding one published update; its head counts UPDATES, not "
         "DRAFTS (F11). Red on main at both widths: 'DRAFTS 1'."),
    case("case.p9.update.delivered_row", "edge.face.update_mark_delivered",
         [PROJECT, DRAFT, PUBLISH, *PALETTE, OPEN_ROOM, ROOM_UP,
          {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=updates-verb]"},
          {"kind": "ui", "action": "click", "adapter": "ui-pointer",
           "selector": "[data-update-id='{update_id}']", "why": "open the published update"},
          {"kind": "ui", "action": "fill", "adapter": "ui-keyboard", "selector": "[data-testid=deliver-to]",
           "value": "Priya", "why": "the optional To (the Q0 ruling)"}],
         {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=deliver-verb]",
          "why": "Mark delivered: POST /api/updates/{id}/delivered (PHILO-9-02's route)"},
         {"kind": "readable_text", "value": "Priya"}, "[data-testid=delivery-row]",
         "the owner marks the published update delivered to Priya; the update's history lists the row the "
         "hub recorded, readable in the viewport. New (no red claimed): Mark delivered is a new capability."),
    case("case.p9.room_steward_verb.owned", "edge.face.room_open",
         [PROJECT, LATE, *PALETTE, OPEN_ROOM, ROOM_UP],
         {"kind": "ui", "action": "focus", "adapter": "ui-keyboard", "selector": "[data-testid=steward-verb]",
          "why": "keyboard travel to the SOURCES Steward verb scrolls it into view"},
         {"kind": "hit_target", "min_width": 20, "min_height": 20}, "[data-testid=steward-verb]",
         "the Steward verb, once in view, owns its nine hit points: the Ask well is in the flow and covers "
         "no verb (F10). Red on main at 393: the sticky well owns the verb's points; preservation green at 1440."),
]
EXCLUDED = [
    {"id": "excluded.p9.room_face_callers_and_receipts", "applicability": "not_applicable",
     "combination": "F1 (a meeting's project button), F3 (steward counts), F7 (RECEIPTS) as atlas cases",
     "reason": "F1 needs a meeting row, which no HTTP route seeds; F3 compares the face with the hub's run and "
               "steps read in the same test; F7's RECEIPTS section sits below the fold at both widths and the "
               "rig does not scroll an observe_at into view. All three are fenced as rendered at 1440 and 393 "
               "by tests/e2e/test_philo9_03_room_face_glass.py."},
    {"id": "excluded.p9.room_face_op", "applicability": "not_applicable",
     "combination": "case.p9.room_items.late_row, case.p9.update_list.head_updates, "
                    "case.p9.room_steward_verb.owned with an .op sibling",
     "reason": "each proves a FACE fact with no durable outcome of its own; the delivery's durable outcome "
               "and its equivalence with MCP are PHILO-9-02's."},
]


def _line(path, symbol):
    for i, line in enumerate((REPO / path).read_text().splitlines(), 1):
        if symbol in line:
            return i
    raise SystemExit(f"{symbol!r} not in {path}")


SOURCES = [
    ("web/src/features/project-room/ProjectRoomCore.tsx", "function ItemsSection",
     "the ITEMS section, after NEEDS YOU, omitted when empty, UNAVAILABLE + Retry on a failed read"),
    ("web/src/features/project-room/update/UpdatePosture.tsx", "function DeliverySection",
     "To + Mark delivered above the body of a published update, and the delivery history"),
    ("web/src/features/project-room/update/UpdatePosture.tsx", 'countLabel("UPDATES"',
     "the update list's head counts updates"),
    ("web/src/features/project-room/project-room.css", ".room-ask-container {",
     "the Ask well is in the flow at every width"),
    ("web/src/desk/shell.ts", "export function openProjectRoom",
     "the one key that opens a project's Room"),
]

atlas = json.loads(OUT.read_text())
ids = {c["id"] for c in CASES}
atlas["cases"] = [c for c in atlas["cases"] if c["id"] not in ids] + CASES
ex_ids = {e["id"] for e in EXCLUDED}
atlas["excluded"] = [e for e in atlas["excluded"] if e["id"] not in ex_ids] + EXCLUDED
atlas["states"] = [s for s in atlas["states"] if s["id"] != STATE] + [{
    "id": STATE, "family": "desk_presentation",
    "values": {"room": "the Room's face as the owner ratified the story 03 canvases (2026-09-27)",
               "width": "1440 and 393"},
    "phase1_refs": [],
    "sources": [{"path": p, "symbol": s, "line": _line(p, s), "claim": c} for p, s, c in SOURCES],
    "reachable_by": [c["id"] for c in CASES],
}]
OUT.write_text(json.dumps(atlas, indent=2, ensure_ascii=False) + "\n")
print(OUT, len(atlas["cases"]))
