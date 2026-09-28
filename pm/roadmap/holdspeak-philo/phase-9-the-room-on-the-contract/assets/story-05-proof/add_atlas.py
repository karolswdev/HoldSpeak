#!/usr/bin/env python3
"""PHILO-9-05: add the census's proven gaps to docs/internal/philo/graph/atlas-phase9.json.

Idempotent: a case or state with the same id is replaced. Line anchors are
found in the tree (the fence `test_every_source_reference_lands_on_its_symbol`
checks each one). The four earlier story cases are not touched.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase9.json"

GATE = [
    {"kind": "ui", "action": "goto", "adapter": "ui-navigation", "url": "/"},
    {"kind": "ui", "action": "click_role", "adapter": "ui-pointer", "role": "button",
     "name": "Continue later", "optional": True},
    {"kind": "api", "method": "PUT", "path": "/api/setup/onboarding", "adapter": "http-route",
     "body": {"disposition": "completed"}, "expect_status": 200,
     "why": "the first-use arrival completed on the hub (the glass does the same): the optional click can land before the Chair draws it"},
    {"kind": "check", "predicate": {"kind": "protocol_field", "path": "arrival_required", "value": False},
     "observe_at": "protocol: GET /api/setup/status", "timeout_s": 10,
     "why": "the 'Continue later' dismissal is on the hub before any reload"},
]


def palette(value: str, option: str, why: str) -> list[dict]:
    return [
        {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[aria-controls=desk-tool-shelf]",
         "why": "the palette (DeskToolShelf.tsx: SETTINGS rows, one per preference module)"},
        {"kind": "ui", "action": "fill", "adapter": "ui-keyboard", "selector": "[aria-controls=desk-palette-listbox]",
         "value": value},
        {"kind": "ui", "action": "click", "adapter": "ui-pointer",
         "selector": f"[id='desk-palette-option-settings:{option}']", "why": why},
    ]


def anchor(path: str, symbol: str, claim: str) -> dict:
    lines = (REPO / path).read_text(encoding="utf-8").splitlines()
    hits = [i + 1 for i, line in enumerate(lines) if symbol in line]
    assert hits, f"{path}: {symbol!r} not found"
    return {"path": path, "symbol": symbol, "line": hits[0], "claim": claim}


REMOTE_ON = {"kind": "api", "method": "PUT", "path": "/api/settings/remote", "adapter": "http-route",
             "body": {"enabled": True}, "expect_status": 200, "why": "Remote Access ON (the ledger lists credentials)"}


def credential(identity: str, name: str, capture: str, field: str = "id") -> dict:
    return {"kind": "api", "method": "POST", "path": "/api/settings/remote/credentials", "adapter": "http-route",
            "body": {"identity": identity, "palette": name}, "capture_as": capture, "capture_path": field,
            "expect_status": 200, "why": f"a real Settings-issued {name} credential for {identity!r}"}


PROJECT = {"kind": "api", "method": "POST", "path": "/api/projects", "adapter": "http-route",
           "body": {"name": "Atlas ledger cutover"}, "capture_as": "project_id", "capture_path": "project.id",
           "expect_status": 200, "why": "the project the grant names"}
RELOAD = {"kind": "ui", "action": "reload", "adapter": "ui-navigation", "why": "a fresh Desk read after the seed"}
SYSTEM = palette("System", "system", "Settings > System: the Remote access ledger (SettingsCore.tsx)")

CASES = [
    {
        "id": "case.p9.grant.project_allowed",
        "job": "p9",
        "edge_ids": ["edge.face.project_grant"],
        "state_id": "state.desk_presentation.p9_grant_face",
        "applicability": "applicable",
        "preconditions": ["a fresh isolated HOME and browser profile; the hub started against that HOME"],
        "setup": GATE + [REMOTE_ON, credential("sweep-runner", "PROJECT", "identity", "identity"), PROJECT, RELOAD] + SYSTEM + [
            {"kind": "ui", "action": "click", "adapter": "ui-pointer",
             "selector": "button[aria-label='Projects: {identity}']",
             "why": "the library Disclosure opens the row's per-project lines in place"},
            {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer",
             "selector": "[data-testid='project-line-{project_id}'] [data-testid=project-grant-verb]"},
        ],
        "trigger": {"kind": "ui", "action": "click", "adapter": "ui-pointer",
                    "selector": "[data-testid='project-line-{project_id}'] [data-testid=project-grant-verb]",
                    "why": "Allow run and publish on the project line: PUT /api/settings/remote/delegations/{identity}/projects/{project_id}",
                    "trigger_route": {"method": "PUT",
                                      "path": "/api/settings/remote/delegations/{identity}/projects/{project_id}"}},
        "expected": {
            "predicate": {"kind": "all_of", "predicates": [
                {"kind": "protocol_status", "method": "PUT",
                 "path": "/api/settings/remote/delegations/{identity}/projects/{project_id}", "status": 200,
                 "body_fields": {"receipt.state": "succeeded", "receipt.actor_kind": "owner",
                                 "agent_identity": "sweep-runner", "project_id": "{project_id}"}},
                {"kind": "readable_text", "value": "RUN AND PUBLISH ALLOWED"},
                {"kind": "protocol_reads", "expect": [
                    {"status": 200, "row": {"path": "credentials", "match": {
                        "identity": "sweep-runner", "project_delegations.0.project_id": "{project_id}",
                        "project_delegations.0.state": "LIVE"}}}]},
            ]},
            "observe_at": "[data-testid='project-line-{project_id}'] [data-testid=project-grant-chip]",
            "reads": [{"method": "GET", "path": "/api/settings/remote"}],
            "words": "the owner allows run and publish for a PROJECT credential on one project from the Remote access ledger: the grant answers 200 with the owner's succeeded receipt, the line's chip reads RUN AND PUBLISH ALLOWED, readable in the viewport, and the hub's ledger holds the LIVE grant on that project. New (no red claimed): the project grant is a new capability (PHILO-9-07).",
        },
        "completion_bound_s": 25,
        "viewports": [1440, 393],
    },
    {
        "id": "case.p9.grant_route.project_allowed",
        "job": "p9",
        "edge_ids": ["edge.route.project_delegation_grant"],
        "state_id": "state.desk_presentation.p9_grant_face",
        "applicability": "applicable",
        "preconditions": ["A fresh isolated hub; no browser. project.delegation.grant is HTTP only (in no MCP palette), so its non-face path is the route."],
        "setup": [REMOTE_ON, credential("sweep-runner", "PROJECT", "identity", "identity"), PROJECT],
        "trigger": {"kind": "api", "method": "PUT",
                    "path": "/api/settings/remote/delegations/{identity}/projects/{project_id}",
                    "adapter": "http-route", "body": {}, "capture_as": "grant_op", "capture_path": "operation_id",
                    "why": "the owner's grant, the same route the face's Allow calls"},
        "expected": {
            "predicate": {"kind": "protocol_reads", "expect": [
                {"status": 200, "row": {"path": "credentials", "match": {
                    "identity": "sweep-runner", "project_delegations.0.project_id": "{project_id}",
                    "project_delegations.0.state": "LIVE"}}},
                {"status": 200, "row": {"path": "objects", "match": {
                    "operation.name": "project.delegation.grant", "operation.operation_id": "{grant_op}",
                    "receipt.state": "succeeded", "receipt.actor_kind": "owner",
                    "receipt.target_ref": "project:{project_id}"}}}]},
            "observe_at": "protocol: GET /api/settings/remote",
            "reads": [{"method": "GET", "path": "/api/settings/remote"},
                      {"method": "GET", "path": "/api/kernel/read?refs=operation:{grant_op}&view=receipt"}],
            "words": "the same grant through the route (captured from its own answer): the hub's ledger holds the LIVE grant; the kernel holds ONE project.delegation.grant operation with its succeeded receipt, actor the owner, target the project",
        },
        "completion_bound_s": 20,
        "viewports": [],
    },
    {
        "id": "case.p9.grant.desk_reads_desk",
        "job": "p9",
        "edge_ids": ["edge.face.project_grant"],
        "state_id": "state.desk_presentation.p9_grant_face",
        "applicability": "applicable",
        "preconditions": ["a fresh isolated HOME and browser profile; the hub started against that HOME"],
        "setup": GATE + [REMOTE_ON, credential("desk-agent", "DESK", "desk_cred"), RELOAD] + SYSTEM + [
            {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer",
             "selector": "[data-testid='credential-row-{desk_cred}']"},
        ],
        "trigger": {"kind": "ui", "action": "focus", "adapter": "ui-keyboard",
                    "selector": "[data-testid='credential-row-{desk_cred}'] [data-testid=credential-revoke]",
                    "why": "keyboard travel to the row's verb brings the row into view"},
        "expected": {
            "predicate": {"kind": "all_of", "predicates": [
                {"kind": "protocol_reads", "expect": [
                    {"status": 200, "row": {"path": "credentials", "match": {
                        "identity": "desk-agent", "palette": "DESK"}}}]},
                {"kind": "readable_text", "value": "DESK"},
            ]},
            "observe_at": "[data-testid='credential-row-{desk_cred}'] .surface-token",
            "reads": [{"method": "GET", "path": "/api/settings/remote"}],
            "words": "a credential issued as DESK reads back as DESK on the wire and in the row's palette token (the row's first token, on main and on the branch). Red on main 1f332bc3 at both widths: the token and the wire read ALL.",
        },
        "completion_bound_s": 25,
        "viewports": [1440, 393],
    },
    {
        "id": "case.p9.connections.never_checked_face",
        "job": "p9",
        "edge_ids": ["edge.face.connections"],
        "state_id": "state.desk_presentation.p9_connections_face",
        "applicability": "applicable",
        "preconditions": ["a fresh isolated HOME and browser profile; the hub started against that HOME; no connection was ever checked in this HOME"],
        "setup": GATE + palette("Connections", "integrations", "Settings > Connections (ConnectionsPane.tsx)")[:2],
        "trigger": {"kind": "ui", "action": "click", "adapter": "ui-pointer",
                    "selector": "[id='desk-palette-option-settings:integrations']",
                    "why": "open Settings > Connections (ConnectionsPane.tsx)"},
        "expected": {
            "predicate": {"kind": "all_of", "predicates": [
                {"kind": "readable_text", "value": "NEVER CHECKED"},
                {"kind": "protocol_reads", "expect": [
                    {"status": 200, "row": {"path": "tools", "match": {
                        "provider_id": "github", "state": "never_checked", "last_checked_at": None}}}]},
            ]},
            "observe_at": "[data-testid=connections-github] .surface-state-chip",
            "reads": [{"method": "GET", "path": "/api/connections"}],
            "words": "on a fresh hub the owner opens Connections: the GitHub card's chip reads NEVER CHECKED (the chip's words \"Never checked\" in its capitals), readable in the viewport, and the hub's cached list says never_checked with no check time (B1). Red on main 1f332bc3 at both widths: the list probes on read and the chip says another state.",
        },
        "completion_bound_s": 25,
        "viewports": [1440, 393],
    },
    {
        "id": "case.p9.update.delivered_row.op",
        "job": "p9",
        "edge_ids": ["edge.tool.project_mark_update_delivered"],
        "state_id": "state.desk_presentation.p9_room_face",
        "applicability": "applicable",
        "preconditions": ["A fresh isolated hub; no browser. Every id is captured from this run's own producer."],
        "setup": [
            {"kind": "op", "name": "project.create", "args": {"name": "Atlas ledger cutover"}, "adapter": "mcp-http",
             "capture_as": "project_id", "capture_path": "project.id", "why": "the Room under test"},
            {"kind": "op", "name": "project.draft_update", "args": {"project_id": "{project_id}", "generator": "deterministic"},
             "adapter": "mcp-http", "capture_as": "update_id", "capture_path": "update.id", "why": "an update to publish"},
            {"kind": "op", "name": "project.publish_update", "args": {"update_id": "{update_id}"}, "adapter": "mcp-http",
             "why": "a published update (the Q0 ruling: delivery needs one)"},
        ],
        "trigger": {"kind": "op", "name": "project.mark_update_delivered",
                    "args": {"update_id": "{update_id}", "delivered_to": "Priya", "command_id": "atlas-p9-05-delivered"},
                    "adapter": "mcp-http", "capture_as": "mark_op", "capture_path": "operation_id",
                    "why": "Mark delivered, To Priya: the face's act through MCP"},
        "expected": {
            "predicate": {"kind": "op_facts", "facts": [
                {"source": "observe", "path": "updates", "contains": {"id": "{update_id}", "lifecycle": "published"}},
                {"source": "observe", "path": "updates.0.deliveries", "length": 1},
                {"source": "observe", "path": "updates.0.deliveries.0.delivered_to", "value": "Priya"},
                {"source": "observe", "path": "updates.0.deliveries.0.operation_id", "value": "{mark_op}"},
                {"source": "read", "index": 0, "path": "objects.0.operation.name", "value": "project.mark_update_delivered"},
                {"source": "read", "index": 0, "path": "objects.0.receipt.state", "value": "succeeded"},
                {"source": "read", "index": 0, "path": "objects.0.receipt.actor_kind", "value": "owner"},
            ]},
            "observe_at": {"kind": "op", "name": "project.list_updates",
                           "args": {"project_id": "{project_id}", "lifecycle": "published"}},
            "reads": [{"kind": "op", "name": "kernel.receipt.read", "args": {"operation_id": "{mark_op}"}}],
            "words": "the operation sibling of case.p9.update.delivered_row: the published update lists ONE delivery To Priya whose operation is the mark's; the kernel holds its succeeded receipt with the owner as actor. New (no red claimed).",
        },
        "completion_bound_s": 30.0,
        "viewports": [],
    },
]

STATES = [
    {
        "id": "state.desk_presentation.p9_grant_face",
        "family": "desk_presentation",
        "values": {"ledger": "Settings > System > Remote access, as the owner ratified the grant canvas (set A)",
                   "width": "1440 and 393"},
        "phase1_refs": [],
        "sources": [
            anchor("web/src/pages/cores/SettingsCore.tsx", 'data-testid="project-grant-chip"',
                   "the project line's chip: RUN AND PUBLISH ALLOWED or STOPPED"),
            anchor("web/src/pages/cores/SettingsCore.tsx", "data-testid={`credential-row-${cred.id}`}",
                   "one ledger row per credential"),
            anchor("web/src/pages/cores/SettingsCore.tsx", 'data-testid="palette-token"',
                   "the row's palette token reads the issued name"),
            anchor("holdspeak/web/routes/mcp_http.py", '@router.put("/api/settings/remote/delegations/{identity}/projects/{project_id}")',
                   "the owner's project grant: admitted, owner-only, HTTP only"),
        ],
        "reachable_by": ["case.p9.grant.project_allowed", "case.p9.grant_route.project_allowed",
                         "case.p9.grant.desk_reads_desk"],
    },
    {
        "id": "state.desk_presentation.p9_connections_face",
        "family": "desk_presentation",
        "values": {"connections": "Settings > Connections on a hub that never checked a remote provider",
                   "width": "1440 and 393"},
        "phase1_refs": [],
        "sources": [
            anchor("web/src/pages/cores/connections/ConnectionsPane.tsx", 'case "never_checked": return "Never checked";',
                   "the chip's words for a provider never checked"),
        ],
        "reachable_by": ["case.p9.connections.never_checked_face"],
    },
]

EXCLUDED = [
    {"id": "excluded.p9.agent_side_grant", "applicability": "not_applicable",
     "combination": "an agent's run, stop or publish with and without a project grant, and an agent refused grant or revoke, as atlas cases",
     "reason": "the rig speaks with the owner's token only (scripts/graph_walk.py Hub: X-HoldSpeak-Token / Bearer of the hub's owner token); an agent principal is rig work outside PHILO-9-05. Each is fenced with a real Settings-issued PROJECT credential over MCP and HTTP by tests/unit/test_philo9_project_grant.py, test_philo9_project_grant_lifecycle.py and test_philo9_project_grant_restart.py (PHILO-9-07)."},
    {"id": "excluded.p9.grant_face_op", "applicability": "not_applicable",
     "combination": "case.p9.grant.desk_reads_desk and case.p9.connections.never_checked_face with an .op sibling",
     "reason": "the palette token is a read of the issued credential (no operation to pair; the case reads the wire in the same observation). The Connections face's operation twin is PHILO-9-02's case.p9.connections.never_checked in atlas-phase9-steward.json (connection.list), kept in that file."},
]


# Codex Astra r1 finding 3: the browser delivery case reads the durable outcome
# of ITS OWN click (the route's answer: the delivery row and the owner's
# receipt) and the hub's stored row, beside the face's words.
DELIVERED_EXPECTED = {
    "predicate": {"kind": "all_of", "predicates": [
        {"kind": "protocol_status", "method": "POST", "path": "/api/updates/{update_id}/delivered", "status": 200,
         "body_fields": {"delivery.update_id": "{update_id}", "delivery.delivered_to": "Priya",
                         "delivery.operation_id": {"nonempty": True}, "receipt.state": "succeeded",
                         "receipt.actor_kind": "owner", "receipt.target_ref": "project_update:{update_id}"}},
        {"kind": "readable_text", "value": "Priya"},
        {"kind": "protocol_reads", "expect": [
            {"status": 200, "row": {"path": "updates", "match": {
                "id": "{update_id}", "lifecycle": "published", "deliveries.0.delivered_to": "Priya"}}}]},
    ]},
    "observe_at": "[data-testid=delivery-row]",
    "reads": [{"method": "GET", "path": "/api/projects/{project_id}/updates"}],
    "words": "the owner marks the published update delivered to Priya: that click's POST answers 200 with the delivery row for this update and the owner's succeeded receipt, the hub's stored update lists the delivery To Priya, and the update's history shows the row, readable in the viewport. New (no red claimed): Mark delivered is a new capability. (Story 05 round two, Codex Astra r1 finding 3: the durable halves added; story 03's face half unchanged.)",
}


def main() -> None:
    atlas = json.loads(ATLAS.read_text())
    face = next(c for c in atlas["cases"] if c["id"] == "case.p9.update.delivered_row")
    face["expected"] = DELIVERED_EXPECTED
    face["trigger"]["trigger_route"] = {"method": "POST", "path": "/api/updates/{update_id}/delivered"}
    for key, new in (("cases", CASES), ("states", STATES), ("excluded", EXCLUDED)):
        ids = {item["id"] for item in new}
        atlas[key] = [item for item in atlas[key] if item["id"] not in ids] + new
    room = next(s for s in atlas["states"] if s["id"] == "state.desk_presentation.p9_room_face")
    if "case.p9.update.delivered_row.op" not in room["reachable_by"]:
        room["reachable_by"].append("case.p9.update.delivered_row.op")
    ATLAS.write_text(json.dumps(atlas, indent=2) + "\n")
    print(f"{ATLAS.relative_to(REPO)}: {len(atlas['cases'])} cases, {len(atlas['states'])} states, "
          f"{len(atlas['excluded'])} exclusions")


if __name__ == "__main__":
    main()
