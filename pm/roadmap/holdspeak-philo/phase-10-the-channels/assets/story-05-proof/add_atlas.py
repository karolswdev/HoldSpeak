#!/usr/bin/env python3
"""PHILO-10-05: write docs/internal/philo/graph/atlas-phase10.json -- the atlas cases for Send.

One face case per Send state of the charter's matrix (1440 and 393), each read
with its durable hub outcome in the SAME observation (all_of: the face half and
the hub half), an `.op` sibling (headless, MCP, the kernel receipt read back)
where the outcome is durable, and the named transitions: a restart during
dispatching, a replay of the same key, a destination changed after prepare,
Send and Discard together, a receipt across Back and return.

The file channel writes a REAL file into the run's isolated HOME (`{hub_home}`,
bound by the rig). The GitHub cases use the rig's recording runner at the CLI
process edge (boundary `cli_runner`, scripts under tests/fixtures/philo10_atlas/):
the channel's real plan, the kernel's subprocess.exec child, only the process
canned; egress is never run in the atlas. Line anchors are found in the tree
(the fence `test_every_source_reference_lands_on_its_symbol` checks each one).
Idempotent: the file is rewritten whole.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase10.json"
FIX = "tests/fixtures/philo10_atlas"
PROJECT_NAME = "Atlas send ledger"
FOLDER = "Payments"
GH = "Issue42"
GH_URL = "https://github.com/acme/payments/issues/42#issuecomment-99001"
FACE = [1440, 393]


def anchor(path: str, symbol: str, claim: str) -> dict:
    lines = (REPO / path).read_text(encoding="utf-8").splitlines()
    hits = [i + 1 for i, line in enumerate(lines) if symbol in line]
    assert hits, f"{path}: {symbol!r} not found"
    return {"path": path, "symbol": symbol, "line": hits[0], "claim": claim}


# ── steps ──────────────────────────────────────────────────────────────

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


def api(method: str, path: str, body: dict | None, why: str, capture: str | None = None,
        at: str | None = None, status: int = 200) -> dict:
    step = {"kind": "api", "method": method, "path": path, "adapter": "http-route", "body": body,
            "expect_status": status, "why": why}
    if capture:
        step.update(capture_as=capture, capture_path=at or "id")
    return step


PUBLISHED = [
    api("POST", "/api/projects", {"name": PROJECT_NAME}, "the Room under test", "project_id", "project.id"),
    api("POST", "/api/projects/{project_id}/updates/draft", {"generator": "deterministic"}, "an update to publish",
        "update_id", "update.id"),
    api("POST", "/api/updates/{update_id}/publish", {}, "a published update (only a published update has a Send well)"),
]


def folder_dest(name: str = FOLDER, synced: bool = False, capture: str = "dest_id", replaces: str | None = None) -> dict:
    body = {"name": name, "channel": "file", "folder": "{hub_home}", "synced": synced}
    if replaces:
        body["replaces"] = replaces
    return api("POST", "/api/channels/destinations", body,
               ("Edit in Settings: the destination saved again replacing the old one (the old one parks)" if replaces else
                f"a saved folder on the run's isolated HOME ({'marked synced' if synced else 'this device'})"),
               capture, "destination.id")


def gh_dest(capture: str = "gh_id") -> dict:
    return api("POST", "/api/channels/destinations",
               {"name": GH, "channel": "github", "repo": "acme/payments", "kind": "issue", "number": 42},
               "a saved GitHub issue: the save reads the gh login at the recording runner (gh api user)",
               capture, "destination.id")


def runner(script: str) -> dict:
    return {"kind": "boundary", "substitute": "cli_runner", "label": f"the CLI process edge: {script}",
            "adapter": "cli-process-edge", "reply": f"{FIX}/{script}",
            "why": "the channel's real plan and the kernel's subprocess.exec child run; only gh is canned (egress never runs in the atlas)"}


RELOAD = {"kind": "ui", "action": "reload", "adapter": "ui-navigation", "why": "a fresh Desk read after the seed"}
ROOM = [
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[aria-controls=desk-tool-shelf]",
     "why": "the palette (DeskToolShelf.tsx: PROJECTS rows `Open <name>`)"},
    {"kind": "ui", "action": "fill", "adapter": "ui-keyboard", "selector": "[aria-controls=desk-palette-listbox]",
     "value": PROJECT_NAME},
    {"kind": "ui", "action": "click", "adapter": "ui-pointer",
     "selector": "[id='desk-palette-option-project.open.{project_id}']",
     "why": "Open the project's Room (the one key, open-project-memory, scope project:<id>)"},
    {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": "[data-testid=room-body]"},
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=updates-verb]"},
    {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": "[data-testid=update-list]"},
]
OPEN_UPDATE_SEL = "[data-testid=update-list-item] [data-update-id='{update_id}']"
OPEN_UPDATE = {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": OPEN_UPDATE_SEL,
               "why": "open the published update: its SEND well and its DELIVERY history"}
WELL = {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": "[data-testid=send-well]"}


def row(name: str) -> str:
    return f"[data-testid=destination-row]:has([data-destination='{name}'])"


def opened(name: str) -> str:
    return f"[data-testid=send-open][data-destination='{name}']"


def pick(name: str) -> list[dict]:
    return [
        {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": row(name)},
        {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": row(name),
         "why": "A1: the pick opens the preview and Send in place, under the row"},
        {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": f"{opened(name)} [data-testid=send-preview]",
         "why": "the readable preview the hub derived from the frozen bytes (Send waits for it)"},
        seat(f"{opened(name)} [data-testid=send-verbs]", "center",
             "the owner scrolls Send to the middle of the window, so its answer lands in view (at 393 the Room's footer sits below it)"),
    ]


def seat(selector: str, block: str, why: str) -> dict:
    return {"kind": "ui", "action": "scroll_into_view", "adapter": "ui-pointer", "selector": selector, "block": block, "why": why}


def press(name: str) -> dict:
    return {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": f"{opened(name)} [data-testid=send-verb]",
            "why": "the owner's press: POST /api/channels/send (update, destination, the preview's digest, a new key)",
            "trigger_route": {"method": "POST", "path": "/api/channels/send"}}


def face_case(cid: str, words: str, setup: list, trigger: dict, predicates: list, observe_at: str,
              reads: list, bound: int = 30) -> dict:
    return {"id": cid, "job": "p10", "edge_ids": ["edge.face.channel_send"],
            "state_id": "state.desk_presentation.p10_send_face", "applicability": "applicable",
            "preconditions": ["a fresh isolated HOME and browser profile; the hub started against that HOME"],
            "setup": GATE + setup, "trigger": trigger,
            "expected": {"predicate": {"kind": "all_of", "predicates": predicates}, "observe_at": observe_at,
                         "reads": reads, "words": words},
            "completion_bound_s": bound, "viewports": FACE}


def op(name: str, args: dict, why: str, capture: str | None = None, at: str | None = None,
       refusal: bool = False) -> dict:
    step = {"kind": "op", "name": name, "args": args, "adapter": "mcp-http", "why": why}
    if capture:
        step.update(capture_as=capture, capture_path=at or "id")
        if refusal:
            step["capture_from"] = "refusal"
    return step


OP_PUBLISHED = [
    op("project.create", {"name": PROJECT_NAME}, "the Room under test", "project_id", "project.id"),
    op("project.draft_update", {"project_id": "{project_id}", "generator": "deterministic"}, "an update to publish",
       "update_id", "update.id"),
    op("project.publish_update", {"update_id": "{update_id}"}, "a published update"),
]


def op_folder(name: str = FOLDER, synced: bool = False, capture: str = "dest_id", replaces: str | None = None) -> dict:
    args = {"name": name, "channel": "file", "folder": "{hub_home}", "synced": synced}
    if replaces:
        args["replaces"] = replaces
    return op("channel.save_destination", args,
              "Edit: saved again replacing the old one (the old one parks)" if replaces else "a saved folder on the run's isolated HOME",
              capture, "destination.id")


def op_gh(capture: str = "gh_id") -> dict:
    return op("channel.save_destination",
              {"name": GH, "channel": "github", "repo": "acme/payments", "kind": "issue", "number": 42},
              "a saved GitHub issue (the save reads the gh login at the recording runner)", capture, "destination.id")


def op_preview(dest: str) -> dict:
    return op("channel.preview", {"update_id": "{update_id}", "destination_id": "{" + dest + "}"},
              "the preview the owner sees; its digest is what the press names", "digest", "payload_digest")


def op_case(cid: str, words: str, setup: list, trigger: dict, facts: list, observe_at: dict, reads: list,
            extra: list | None = None, bound: int = 30) -> dict:
    predicate = {"kind": "op_facts", "facts": facts}
    if extra:
        predicate = {"kind": "all_of", "predicates": [predicate, *extra]}
    return {"id": cid, "job": "p10", "edge_ids": ["edge.tool.channel_send"],
            "state_id": "state.desk_presentation.p10_send_face", "applicability": "applicable",
            "preconditions": ["A fresh isolated hub; no browser. Every id is captured from this run's own producer."],
            "setup": setup, "trigger": trigger,
            "expected": {"predicate": predicate, "observe_at": observe_at, "reads": reads, "words": words},
            "completion_bound_s": bound, "viewports": []}


def receipt(op_var: str) -> dict:
    return {"kind": "op", "name": "kernel.receipt.read", "args": {"operation_id": "{" + op_var + "}"}}


def receipt_facts(index: int, name: str, state: str, op_var: str) -> list:
    return [
        {"source": "read", "index": index, "path": "objects.0.operation.name", "value": name},
        {"source": "read", "index": index, "path": "objects.0.receipt.operation_id", "value": "{" + op_var + "}"},
        {"source": "read", "index": index, "path": "objects.0.receipt.state", "value": state},
        {"source": "read", "index": index, "path": "objects.0.receipt.actor_kind", "value": "owner"},
    ]


SENDS_READ = {"method": "GET", "path": "/api/channels/sends?update_id={update_id}"}
UPDATES_READ = {"method": "GET", "path": "/api/projects/{project_id}/updates"}
OP_SENDS = {"kind": "op", "name": "channel.sends", "args": {"update_id": "{update_id}"}}
OP_UPDATES = {"kind": "op", "name": "project.list_updates", "args": {"project_id": "{project_id}"}}


def sends_rows(count: int, **match) -> dict:
    return {"status": 200, "row": {"path": "sends", "match": match, "count": count}}


def gh_creates(count: int) -> dict:
    return {"kind": "cli_calls", "argv_prefix": ["gh", "issue", "comment"], "count": count}


NEW = "New (no red claimed): the Send is a new capability (Phase 10); on the pre-Phase-10 main the case fails (no SEND well)."

CASES: list[dict] = []

# 1. No destination saved
CASES.append(face_case(
    "case.p10.send.no_destination",
    "a published update with no destination saved: the SEND well says NO DESTINATION with the verb that opens the setup (Add destination), readable in the viewport, and the hub holds zero destinations. " + NEW,
    PUBLISHED + [RELOAD] + ROOM, OPEN_UPDATE,
    [{"kind": "readable_text", "value": "NO DESTINATION"},
     {"kind": "readable_text", "value": "Add destination"},
     {"kind": "protocol_reads", "expect": [{"status": 200, "row": {"path": "destinations", "match": {}, "count": 0}}]}],
    "[data-testid=send-none]", [{"method": "GET", "path": "/api/channels/destinations"}]))

# 2. Destinations listed (+ .op: the save)
CASES.append(face_case(
    "case.p10.send.destinations_listed",
    "two saved destinations are two rows, each with its channel and host chip: the folder (FILE, THIS DEVICE) and the GitHub issue (GITHUB, GITHUB.COM), readable in the viewport; the hub lists the same two active destinations. (A third, synced, row does not fit the 393 viewport with the run's long HOME path; the SYNCED FOLDER chip is fenced by the story 04 glass.) " + NEW,
    [runner("gh-posted.json")] + PUBLISHED + [folder_dest(), gh_dest(), RELOAD] + ROOM,
    {**OPEN_UPDATE, "then": [seat("[data-testid=destination-list]", "center", "the owner looks at the three rows (at 393 the list runs under the Room's footer)")]},
    [{"kind": "readable_text", "value": "THIS DEVICE"},
     {"kind": "readable_text", "value": "GITHUB.COM"},
     {"kind": "readable_text", "value": "Issue42"},
     {"kind": "protocol_reads", "expect": [{"status": 200, "row": {"path": "destinations", "match": {"state": "active"}, "count": 2}}]}],
    "[data-testid=destination-list]", [{"method": "GET", "path": "/api/channels/destinations"}]))
CASES.append(op_case(
    "case.p10.send.destinations_listed.op",
    "the operation sibling of case.p10.send.destinations_listed: the GitHub issue saved over MCP (the login read at the recording runner) is the second active destination beside the folder; the kernel holds the save's succeeded receipt with the owner as actor. New (no red claimed).",
    [runner("gh-posted.json"), op_folder()],
    {**op_gh(), "capture_more": [{"as": "save_op", "path": "operation_id"}], "why": "save the GitHub destination: the owner's act through MCP"},
    [{"source": "observe", "path": "destinations", "length": 2},
     {"source": "observe", "path": "destinations", "contains": {"id": "{gh_id}", "channel": "github", "state": "active"}},
     {"source": "observe", "path": "destinations", "contains": {"id": "{dest_id}", "channel": "file", "state": "active"}},
     *receipt_facts(0, "channel.save_destination", "succeeded", "save_op")],
    {"kind": "op", "name": "channel.destinations", "args": {}}, [receipt("save_op")]))

# 3. Destination picked
CASES.append(face_case(
    "case.p10.send.destination_picked",
    "the owner picks the folder: its row opens the preview as the channel will get it and Send, in place (A1), readable in the viewport; a preview writes nothing (the hub holds no send for the update). " + NEW,
    PUBLISHED + [folder_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL, {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": row(FOLDER)}],
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": row(FOLDER),
     "why": "A1: the pick (POST /api/channels/preview)", "trigger_route": {"method": "POST", "path": "/api/channels/preview"}},
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/preview", "status": 200,
      "body_fields": {"payload_digest": {"nonempty": True}}},
     {"kind": "readable_text", "value": "Send"},
     {"kind": "readable_text", "value": "THIS DEVICE"},
     {"kind": "protocol_reads", "expect": [sends_rows(0)]}],
    f"{opened(FOLDER)} [data-testid=send-verbs]", [SENDS_READ]))

# 4. Sending (held at the recording runner)
CASES.append(face_case(
    "case.p10.send.sending",
    "the owner presses Send on the GitHub issue and the create is held at the process edge after the dispatch boundary: the row reads SENDING, readable in the viewport; the hub holds ONE send, dispatching, and the recording runner saw ONE gh issue comment. " + NEW,
    [runner("gh-held.json")] + PUBLISHED + [gh_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(GH),
    {**press(GH), "why": "the owner's press (its answer never comes: the create is held)"},
    [{"kind": "readable_text", "value": "SENDING"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, state="dispatching", destination_id="{gh_id}")]},
     gh_creates(1)],
    f"{opened(GH)} [data-testid=send-running]", [SENDS_READ]))

# 5. SENT, the file channel: a real write on the isolated HOME (+ .op)
CASES.append(face_case(
    "case.p10.send.sent",
    "the owner presses Send on the folder: that press answers SENT with the file's path and sha256 read back and the owner's succeeded receipt; the row reads SAVED with the path, readable in the viewport; the hub holds one sent send and one DELIVERY history row (channel file, outcome sent). " + NEW,
    PUBLISHED + [folder_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(FOLDER), press(FOLDER),
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
      "body_fields": {"outcome": "sent", "send.state": "sent", "send.proof.path": {"nonempty": True},
                      "send.proof.sha256": {"nonempty": True}, "receipt.state": "succeeded", "receipt.actor_kind": "owner"}},
     {"kind": "readable_text", "value": "SAVED"},
     {"kind": "protocol_reads", "expect": [
         sends_rows(1, state="sent", destination_id="{dest_id}", channel="file"),
         {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries.0.channel": "file",
                                                                "deliveries.0.outcome": "sent"}}}]}],
    f"{opened(FOLDER)} [data-testid=send-sent]", [SENDS_READ, UPDATES_READ]))
CASES.append(op_case(
    "case.p10.send.sent.op",
    "the operation sibling of case.p10.send.sent: the owner's send over MCP (the inline form the face uses: update, destination, the preview's digest) writes the file; the send is sent with the file's sha256 equal to the preview's digest; ONE history row names the send's operation; the kernel holds its succeeded receipt with the owner as actor. New (no red claimed).",
    OP_PUBLISHED + [op_folder(), op_preview("dest_id")],
    op("channel.send", {"update_id": "{update_id}", "destination_id": "{dest_id}", "preview_digest": "{digest}",
                        "command_id": "atlas-p10-05-sent"}, "the owner's press through MCP", "send_op", "operation_id"),
    [{"source": "trigger", "path": "outcome", "value": "sent"},
     {"source": "observe", "path": "updates.0.deliveries", "length": 1},
     {"source": "observe", "path": "updates.0.deliveries.0.outcome", "value": "sent"},
     {"source": "observe", "path": "updates.0.deliveries.0.channel", "value": "file"},
     {"source": "observe", "path": "updates.0.deliveries.0.operation_id", "value": "{send_op}"},
     *receipt_facts(0, "channel.send", "succeeded", "send_op"),
     {"source": "read", "index": 1, "path": "sends", "length": 1},
     {"source": "read", "index": 1, "path": "sends.0.state", "value": "sent"},
     {"source": "read", "index": 1, "path": "sends.0.proof.sha256", "value": "{digest}"}],
    OP_UPDATES, [receipt("send_op"), OP_SENDS]))

# 6. SENT, GitHub through the recording runner (+ .op)
CASES.append(face_case(
    "case.p10.send.github_posted",
    "the owner presses Send on the GitHub issue: the channel's real plan runs gh issue comment as a subprocess.exec child (the process canned at the recording runner): the press answers SENT with the comment URL and the owner's succeeded receipt; the row reads POSTED, readable in the viewport; the hub holds one sent send and one history row; ONE gh create. " + NEW,
    [runner("gh-posted.json")] + PUBLISHED + [gh_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(GH), press(GH),
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
      "body_fields": {"outcome": "sent", "send.proof.url": GH_URL, "receipt.state": "succeeded", "receipt.actor_kind": "owner"}},
     {"kind": "readable_text", "value": "POSTED"},
     {"kind": "protocol_reads", "expect": [
         sends_rows(1, state="sent", destination_id="{gh_id}", channel="github"),
         {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries.0.channel": "github",
                                                                "deliveries.0.outcome": "sent"}}}]},
     gh_creates(1)],
    f"{opened(GH)} [data-testid=send-sent]", [SENDS_READ, UPDATES_READ]))
CASES.append(op_case(
    "case.p10.send.github_posted.op",
    "the operation sibling of case.p10.send.github_posted: the owner's send over MCP; the send is sent with the comment URL; one history row names the send's operation; the kernel holds its succeeded receipt with the owner as actor; ONE gh create at the recording runner. New (no red claimed).",
    [runner("gh-posted.json")] + OP_PUBLISHED + [op_gh(), op_preview("gh_id")],
    op("channel.send", {"update_id": "{update_id}", "destination_id": "{gh_id}", "preview_digest": "{digest}",
                        "command_id": "atlas-p10-05-posted"}, "the owner's press through MCP", "send_op", "operation_id"),
    [{"source": "trigger", "path": "outcome", "value": "sent"},
     {"source": "trigger", "path": "send.proof.url", "value": GH_URL},
     {"source": "observe", "path": "updates.0.deliveries", "length": 1},
     {"source": "observe", "path": "updates.0.deliveries.0.channel", "value": "github"},
     {"source": "observe", "path": "updates.0.deliveries.0.operation_id", "value": "{send_op}"},
     *receipt_facts(0, "channel.send", "succeeded", "send_op")],
    OP_UPDATES, [receipt("send_op")], extra=[gh_creates(1)]))

# 7. REFUSED: the destination removed between the pick and the press (+ .op)
CASES.append(face_case(
    "case.p10.send.refused",
    "the owner picked the folder, then it was removed in Settings (another hand); his press is REFUSED before the boundary: the answer names destination_parked with a refused receipt; the row reads REFUSED, DESTINATION PARKED, NOTHING SENT, readable in the viewport; the hub holds no send and no history row. " + NEW,
    PUBLISHED + [folder_dest(capture="destination_id"), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(FOLDER) +
    [api("DELETE", "/api/channels/destinations/{destination_id}", None, "Remove in Settings after the pick: the destination parks")],
    press(FOLDER),
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 409,
      "body_fields": {"code": "destination_parked", "receipt.state": "refused"}},
     {"kind": "readable_text", "value": "DESTINATION PARKED"},
     {"kind": "readable_text", "value": "NOTHING SENT"},
     {"kind": "protocol_reads", "expect": [sends_rows(0),
                                           {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries": []}}}]}],
    f"{opened(FOLDER)} [data-testid=send-refused]", [SENDS_READ, UPDATES_READ]))
CASES.append(op_case(
    "case.p10.send.refused.op",
    "the operation sibling of case.p10.send.refused: a send to a removed (parked) destination is refused by name destination_parked; its REFUSAL receipt is read back (state refused, the owner); no send and no history row exist. New (no red claimed).",
    OP_PUBLISHED + [op_folder(), op_preview("dest_id"),
                    op("channel.remove_destination", {"destination_id": "{dest_id}"}, "Remove: the destination parks")],
    op("channel.send", {"update_id": "{update_id}", "destination_id": "{dest_id}", "preview_digest": "{digest}",
                        "command_id": "atlas-p10-05-refused"}, "the owner's press on a parked destination",
       "refused_op", "operation_id", refusal=True),
    [{"source": "trigger", "refused": {"code": "destination_parked"}, "path": "code", "value": "destination_parked"},
     {"source": "observe", "path": "sends", "length": 0},
     *receipt_facts(0, "channel.send", "refused", "refused_op"),
     {"source": "read", "index": 0, "path": "objects.0.receipt.outcome", "value": "destination_parked"},
     {"source": "read", "index": 1, "path": "updates.0.deliveries", "length": 0}],
    OP_SENDS, [receipt("refused_op"), OP_UPDATES]))

# 8. FAILED: a pinned known non-delivery (+ .op)
CASES.append(face_case(
    "case.p10.send.failed",
    "the owner presses Send on the GitHub issue and gh answers the pinned 'could not resolve to an issue': FAILED (a known non-delivery), the owner's failed receipt; the row reads FAILED · ISSUE NOT FOUND · NOTHING SENT (the channel's reason in a plain word, never the raw code), readable in the viewport; the hub holds one failed send and no history row; ONE gh create. " + NEW,
    [runner("gh-not-found.json")] + PUBLISHED + [gh_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(GH), press(GH),
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
      "body_fields": {"outcome": "failed", "send.reason": "github_target_not_found", "receipt.state": "failed"}},
     {"kind": "readable_text", "value": "FAILED"},
     {"kind": "readable_text", "value": "ISSUE NOT FOUND"},
     {"kind": "readable_text", "value": "NOTHING SENT"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, state="failed", reason="github_target_not_found"),
                                           {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries": []}}}]},
     gh_creates(1)],
    f"{opened(GH)} [data-testid=send-failed]", [SENDS_READ, UPDATES_READ]))
CASES.append(op_case(
    "case.p10.send.failed.op",
    "the operation sibling of case.p10.send.failed: the send over MCP ends FAILED github_target_not_found; the kernel holds its failed receipt with the owner as actor; no history row; ONE gh create. New (no red claimed).",
    [runner("gh-not-found.json")] + OP_PUBLISHED + [op_gh(), op_preview("gh_id")],
    op("channel.send", {"update_id": "{update_id}", "destination_id": "{gh_id}", "preview_digest": "{digest}",
                        "command_id": "atlas-p10-05-failed"}, "the owner's press through MCP", "send_op", "operation_id"),
    [{"source": "trigger", "path": "outcome", "value": "failed"},
     {"source": "observe", "path": "sends.0.state", "value": "failed"},
     {"source": "observe", "path": "sends.0.reason", "value": "github_target_not_found"},
     *receipt_facts(0, "channel.send", "failed", "send_op"),
     {"source": "read", "index": 1, "path": "updates.0.deliveries", "length": 0}],
    OP_SENDS, [receipt("send_op"), OP_UPDATES], extra=[gh_creates(1)]))

# 9. UNKNOWN: an unpinned answer (+ .op)
CASES.append(face_case(
    "case.p10.send.unknown",
    "the owner presses Send on the GitHub issue and gh exits nonzero with an answer on no pinned list: RESULT UNKNOWN, the receipt indeterminate; the row offers Check <the issue> (the far side; the verb renders only for an UNKNOWN latest send), readable in the viewport; the hub holds one unknown send and ONE history row (outcome unknown); ONE gh create, never a second. " + NEW,
    [runner("gh-unpinned.json")] + PUBLISHED + [gh_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(GH), press(GH),
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
      "body_fields": {"outcome": "unknown", "send.reason": "github_exit_1", "receipt.state": "indeterminate"}},
     {"kind": "readable_text", "value": "Check acme/payments #42"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, state="unknown"),
                                           {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries.0.outcome": "unknown"}}}]},
     gh_creates(1)],
    f"{opened(GH)} [data-testid=send-check]", [SENDS_READ, UPDATES_READ]))
CASES.append(op_case(
    "case.p10.send.unknown.op",
    "the operation sibling of case.p10.send.unknown: the send over MCP ends UNKNOWN github_exit_1; ONE history row (outcome unknown) names the send's operation; the kernel holds its indeterminate receipt with the owner as actor; ONE gh create. New (no red claimed).",
    [runner("gh-unpinned.json")] + OP_PUBLISHED + [op_gh(), op_preview("gh_id")],
    op("channel.send", {"update_id": "{update_id}", "destination_id": "{gh_id}", "preview_digest": "{digest}",
                        "command_id": "atlas-p10-05-unknown"}, "the owner's press through MCP", "send_op", "operation_id"),
    [{"source": "trigger", "path": "outcome", "value": "unknown"},
     {"source": "observe", "path": "updates.0.deliveries", "length": 1},
     {"source": "observe", "path": "updates.0.deliveries.0.outcome", "value": "unknown"},
     {"source": "observe", "path": "updates.0.deliveries.0.operation_id", "value": "{send_op}"},
     *receipt_facts(0, "channel.send", "indeterminate", "send_op")],
    OP_UPDATES, [receipt("send_op")], extra=[gh_creates(1)]))

# 10. UNKNOWN after a restart during dispatching (transition)
CASES.append(face_case(
    "case.p10.send.unknown_after_restart",
    "a transition: the owner's press on the GitHub issue is held after the dispatch boundary, the hub is restarted (a new process on the same HOME and database) while the send is dispatching; he opens the update again: the history row reads RESULT UNKNOWN, CHECK Issue42, INTERRUPTED, readable in the viewport; the hub holds that send unknown (interrupted) with ONE history row; the recording runner saw ONE gh create across both processes (no second dispatch). " + NEW,
    [runner("gh-held.json")] + PUBLISHED + [gh_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(GH) + [
        {**press(GH), "why": "the owner's press (held after its boundary)"},
        {"kind": "check", "predicate": {"kind": "protocol_field", "path": "sends.0.state", "value": "dispatching"},
         "observe_at": "protocol: GET /api/channels/sends?update_id={update_id}", "timeout_s": 15,
         "why": "the send crossed its durable dispatch boundary before the restart"},
        {"kind": "cli", "action": "restart_hub", "adapter": "process",
         "why": "a restart during dispatching: the same port, HOME, flags and database"},
    ] + ROOM,
    {**OPEN_UPDATE, "then": [seat("[data-testid=delivery-history]", "center", "the owner reads the DELIVERY history (below the SEND well)")]},
    [{"kind": "readable_text", "value": "INTERRUPTED"},
     {"kind": "readable_text", "value": "RESULT UNKNOWN"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, state="unknown", reason="interrupted"),
                                           {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries.0.outcome": "unknown"}}}]},
     gh_creates(1)],
    "[data-testid=delivery-history]", [SENDS_READ, UPDATES_READ], bound=40))

# 11. DESTINATION CHANGED on a prepared row (transition) (+ .op)
PREPARE_API = api("POST", "/api/channels/sends", {"update_id": "{update_id}", "destination_id": "{dest_id}"},
                  "prepare (the owner): a prepared row with the frozen target and preview", "send_id", "send.id")
CASES.append(face_case(
    "case.p10.send.destination_changed",
    "a transition: a prepared send, then its destination edited in Settings (saved again; the old one parks); the owner's Send on the prepared row is REFUSED destination_parked with a refused receipt; the row shows DESTINATION PARKED and stays prepared on the hub (Discard and prepare again). " + NEW,
    PUBLISHED + [folder_dest(), PREPARE_API, folder_dest(FOLDER, replaces="{dest_id}", capture="edited_id"), RELOAD] + ROOM + [
        OPEN_UPDATE, WELL,
        {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": "[data-testid=prepared-open] [data-testid=prepared-send]"}],
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=prepared-open] [data-testid=prepared-send]",
     "why": "Send on the prepared row: POST /api/channels/send {send_id}", "trigger_route": {"method": "POST", "path": "/api/channels/send"}},
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 409,
      "body_fields": {"code": "destination_parked", "receipt.state": "refused"}},
     {"kind": "readable_text", "value": "DESTINATION PARKED"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, id="{send_id}", state="prepared")]}],
    "[data-testid=prepared-refused-chip]", [SENDS_READ]))
CASES.append(op_case(
    "case.p10.send.destination_changed.op",
    "the operation sibling of case.p10.send.destination_changed: a prepared send whose destination was edited (parked) is refused destination_parked over MCP; its refusal receipt is read back; the row stays prepared. New (no red claimed).",
    OP_PUBLISHED + [op_folder(),
                    op("channel.prepare", {"update_id": "{update_id}", "destination_id": "{dest_id}"}, "prepare", "send_id", "send.id"),
                    op_folder(FOLDER, replaces="{dest_id}", capture="edited_id")],
    op("channel.send", {"send_id": "{send_id}", "command_id": "atlas-p10-05-changed"}, "Send on the prepared row",
       "refused_op", "operation_id", refusal=True),
    [{"source": "trigger", "refused": {"code": "destination_parked"}, "path": "code", "value": "destination_parked"},
     {"source": "observe", "path": "sends", "length": 1},
     {"source": "observe", "path": "sends.0.id", "value": "{send_id}"},
     {"source": "observe", "path": "sends.0.state", "value": "prepared"},
     *receipt_facts(0, "channel.send", "refused", "refused_op")],
    OP_SENDS, [receipt("refused_op")]))

# 12. PREPARED (+ .op)
CASES.append(face_case(
    "case.p10.send.prepared",
    "a send prepared by the owner waits in the SEND well: its row reads PREPARED, BY YOU, with its preview, Send and Discard (A3: the first one open), readable in the viewport; the hub holds that send prepared by the owner. " + NEW,
    PUBLISHED + [folder_dest(), PREPARE_API, RELOAD] + ROOM, OPEN_UPDATE,
    [{"kind": "readable_text", "value": "PREPARED"},
     {"kind": "readable_text", "value": "BY YOU"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, id="{send_id}", state="prepared", **{"prepared_by.kind": "owner"})]}],
    "[data-testid=prepared-row]", [SENDS_READ]))
CASES.append(op_case(
    "case.p10.send.prepared.op",
    "the operation sibling of case.p10.send.prepared: prepare over MCP leaves ONE prepared send under the preparer's identity (the owner), nothing sent, no history row; the kernel holds the prepare's succeeded receipt. New (no red claimed).",
    OP_PUBLISHED + [op_folder()],
    {**op("channel.prepare", {"update_id": "{update_id}", "destination_id": "{dest_id}"}, "prepare: the owner's act through MCP",
          "send_id", "send.id"), "capture_more": [{"as": "prepare_op", "path": "operation_id"}]},
    [{"source": "observe", "path": "sends", "length": 1},
     {"source": "observe", "path": "sends.0.state", "value": "prepared"},
     {"source": "observe", "path": "sends.0.prepared_by.kind", "value": "owner"},
     {"source": "observe", "path": "sends.0.prepare_operation_id", "value": "{prepare_op}"},
     *receipt_facts(0, "channel.prepare", "succeeded", "prepare_op"),
     {"source": "read", "index": 1, "path": "updates.0.deliveries", "length": 0}],
    OP_SENDS, [receipt("prepare_op"), OP_UPDATES]))

# 13. Several sends (+ .op)
PREVIEW_API = api("POST", "/api/channels/preview", {"update_id": "{update_id}", "destination_id": "{dest_id}"},
                  "the preview's digest", "digest", "payload_digest")
FIRST_SEND_API = api("POST", "/api/channels/send", {"update_id": "{update_id}", "destination_id": "{dest_id}",
                                                    "preview_digest": "{digest}", "command_id": "atlas-p10-05-first"},
                     "an earlier send to the folder (its own row and receipt)", "first_op", "operation_id")
CASES.append(face_case(
    "case.p10.send.several",
    "a second send to the same folder (Send again, a new key): that press answers SENT with a NEW operation and the owner's succeeded receipt; the row reads SAVED, readable in the viewport; the hub holds TWO sent sends and two history rows, each with its own operation. " + NEW,
    PUBLISHED + [folder_dest(), PREVIEW_API, FIRST_SEND_API, RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(FOLDER), press(FOLDER),
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
      "body_excludes": "{first_op}",
      "body_fields": {"outcome": "sent", "receipt.state": "succeeded", "operation_id": {"nonempty": True}}},
     {"kind": "readable_text", "value": "SAVED"},
     {"kind": "protocol_reads", "expect": [sends_rows(2, state="sent", destination_id="{dest_id}"),
                                           {"status": 200, "row": {"path": "updates", "match": {
                                               "id": "{update_id}", "deliveries.0.outcome": "sent", "deliveries.1.outcome": "sent"}}}]}],
    f"{opened(FOLDER)} [data-testid=send-sent]", [SENDS_READ, UPDATES_READ]))
CASES.append(op_case(
    "case.p10.send.several.op",
    "the operation sibling of case.p10.send.several: two sends over MCP with two keys are two sent rows, two history rows, two succeeded receipts. New (no red claimed).",
    OP_PUBLISHED + [op_folder(), op_preview("dest_id"),
                    op("channel.send", {"update_id": "{update_id}", "destination_id": "{dest_id}", "preview_digest": "{digest}",
                                        "command_id": "atlas-p10-05-first"}, "the first send", "first_op", "operation_id")],
    op("channel.send", {"update_id": "{update_id}", "destination_id": "{dest_id}", "preview_digest": "{digest}",
                        "command_id": "atlas-p10-05-second"}, "Send again: a NEW key", "second_op", "operation_id"),
    [{"source": "observe", "path": "updates.0.deliveries", "length": 2},
     {"source": "observe", "path": "updates.0.deliveries", "contains": {"operation_id": "{first_op}", "outcome": "sent"}},
     {"source": "observe", "path": "updates.0.deliveries", "contains": {"operation_id": "{second_op}", "outcome": "sent"}},
     *receipt_facts(0, "channel.send", "succeeded", "first_op"),
     *receipt_facts(1, "channel.send", "succeeded", "second_op"),
     {"source": "read", "index": 2, "path": "sends", "length": 2}],
    OP_UPDATES, [receipt("first_op"), receipt("second_op"), OP_SENDS]))

# 14. Send and Discard together (transition) (+ .op, both orders)
CASES.append(face_case(
    "case.p10.send.discard_after_send",
    "a transition, Send and Discard together: a prepared send open on the face is sent by another hand (the same hub, the send route); the owner's Discard on the stale face (Discard, then Discard? inside the confirm window: one gesture) is REFUSED send_already_settled with a refused receipt; the face reads the sends again and the prepared row now shows its result, SAVED (the send won), readable in the viewport; the hub keeps the send SENT (one wins). " + NEW,
    PUBLISHED + [folder_dest(), PREPARE_API, RELOAD] + ROOM + [
        OPEN_UPDATE, WELL,
        {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": "[data-testid=prepared-open] [data-testid=prepared-discard]"},
        api("POST", "/api/channels/send", {"send_id": "{send_id}", "command_id": "atlas-p10-05-other-hand"},
            "the other hand sends the prepared row first (the face does not know)", "send_op", "operation_id")],
    {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=prepared-open] [data-testid=prepared-discard]",
     "why": "Discard arms (ConfirmVerb)", "trigger_route": {"method": "POST", "path": "/api/channels/sends/{send_id}/discard"},
     "then": [{"kind": "ui", "action": "click", "adapter": "ui-pointer",
               "selector": "[data-testid=prepared-open] [data-testid=prepared-discard]",
               "why": "Discard? confirms inside the window: POST /api/channels/sends/{send_id}/discard"}]},
    [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/sends/{send_id}/discard", "status": 409,
      "body_fields": {"code": "send_already_settled", "receipt.state": "refused"}},
     {"kind": "readable_text", "value": "SAVED"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, id="{send_id}", state="sent")]}],
    "[data-testid=prepared-result-word][data-state=sent]", [SENDS_READ]))
CASES.append(op_case(
    "case.p10.send.discard_after_send.op",
    "the operation sibling of case.p10.send.discard_after_send: Send won, so Discard over MCP is refused send_already_settled; its refusal receipt is read back; the row stays sent. New (no red claimed).",
    OP_PUBLISHED + [op_folder(),
                    op("channel.prepare", {"update_id": "{update_id}", "destination_id": "{dest_id}"}, "prepare", "send_id", "send.id"),
                    op("channel.send", {"send_id": "{send_id}", "command_id": "atlas-p10-05-wins"}, "Send wins", "send_op", "operation_id")],
    op("channel.discard", {"send_id": "{send_id}"}, "Discard after Send", "refused_op", "operation_id", refusal=True),
    [{"source": "trigger", "refused": {"code": "send_already_settled"}, "path": "code", "value": "send_already_settled"},
     {"source": "observe", "path": "sends.0.id", "value": "{send_id}"},
     {"source": "observe", "path": "sends.0.state", "value": "sent"},
     *receipt_facts(0, "channel.discard", "refused", "refused_op")],
    OP_SENDS, [receipt("refused_op")]))
CASES.append(op_case(
    "case.p10.send.send_after_discard.op",
    "Send and Discard together, the other order: Discard won, so Send over MCP is refused send_already_settled before any effect; its refusal receipt is read back; the row stays discarded; no history row. New (no red claimed).",
    OP_PUBLISHED + [op_folder(),
                    op("channel.prepare", {"update_id": "{update_id}", "destination_id": "{dest_id}"}, "prepare", "send_id", "send.id"),
                    op("channel.discard", {"send_id": "{send_id}"}, "Discard wins")],
    op("channel.send", {"send_id": "{send_id}", "command_id": "atlas-p10-05-late"}, "Send after Discard",
       "refused_op", "operation_id", refusal=True),
    [{"source": "trigger", "refused": {"code": "send_already_settled"}, "path": "code", "value": "send_already_settled"},
     {"source": "observe", "path": "sends.0.state", "value": "discarded"},
     *receipt_facts(0, "channel.send", "refused", "refused_op"),
     {"source": "read", "index": 1, "path": "updates.0.deliveries", "length": 0}],
    OP_SENDS, [receipt("refused_op"), OP_UPDATES]))

# 15. A replay of the same key (transition, .op)
CASES.append(op_case(
    "case.p10.send.replay_same_key.op",
    "a transition, a replay of the same key: the owner's send of a prepared row, then the SAME command_id again: the second call answers the first result (the same operation, sent, the same comment URL); ONE sent send, ONE history row, ONE succeeded receipt; the recording runner saw ONE gh create. New (no red claimed).",
    [runner("gh-posted.json")] + OP_PUBLISHED + [
        op_gh(), op("channel.prepare", {"update_id": "{update_id}", "destination_id": "{gh_id}"}, "prepare", "send_id", "send.id"),
        op("channel.send", {"send_id": "{send_id}", "command_id": "atlas-p10-05-replay"}, "the first press", "first_op", "operation_id")],
    op("channel.send", {"send_id": "{send_id}", "command_id": "atlas-p10-05-replay"}, "the same key again (a replay)",
       "replay_op", "operation_id"),
    [{"source": "trigger", "path": "operation_id", "value": "{first_op}"},
     {"source": "trigger", "path": "send.state", "value": "sent"},
     {"source": "trigger", "path": "send.proof.url", "value": GH_URL},
     {"source": "observe", "path": "sends", "length": 1},
     {"source": "observe", "path": "sends.0.state", "value": "sent"},
     *receipt_facts(0, "channel.send", "succeeded", "first_op"),
     {"source": "read", "index": 1, "path": "updates.0.deliveries", "length": 1}],
    OP_SENDS, [receipt("first_op"), OP_UPDATES], extra=[gh_creates(1)]))

# 16. Receipts survive the face's branch change (transition)
CASES.append(face_case(
    "case.p10.send.receipt_after_return",
    "a transition: the owner sends to the folder (SAVED), goes Back to the update list and opens the update again: the destination row still reads SAVED (its last send, from the hub's record), readable in the viewport; the hub holds the one sent send and its one history row. " + NEW,
    PUBLISHED + [folder_dest(), RELOAD] + ROOM + [OPEN_UPDATE, WELL] + pick(FOLDER) + [
        {**press(FOLDER), "why": "the owner's press: SAVED"},
        {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": f"{opened(FOLDER)} [data-testid=send-sent]"},
        {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=update-verb-back]",
         "why": "Back: the face's branch changes to the update list"},
        {"kind": "ui", "action": "wait_for", "adapter": "ui-pointer", "selector": "[data-testid=update-list]"}],
    {**OPEN_UPDATE, "why": "open the update again (the return)"},
    [{"kind": "readable_text", "value": "SAVED"},
     {"kind": "protocol_reads", "expect": [sends_rows(1, state="sent", destination_id="{dest_id}"),
                                           {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries.0.outcome": "sent"}}}]}],
    f"{row(FOLDER)} [data-testid=send-last-sent]", [SENDS_READ, UPDATES_READ]))

STATES = [{
    "id": "state.desk_presentation.p10_send_face",
    "family": "desk_presentation",
    "values": {"send": "the SEND well, the PREPARED rows and the DELIVERY history as the owner ratified the story 04 canvases (2026-09-29)",
               "width": "1440 and 393"},
    "phase1_refs": [],
    "sources": [
        anchor("web/src/features/channels/SendWell.tsx", "export function SendWell", "the SEND well: destinations, the pick, the preview, Send, the latest receipt"),
        anchor("web/src/features/channels/SendWell.tsx", "function PreparedRow", "a prepared send: Send and Discard while it waits; its result when it ended"),
        anchor("web/src/features/channels/SendWell.tsx", "export function DeliveryHistory", "the one DELIVERY history (story 01's table)"),
        anchor("holdspeak/services/channel_service.py", "def send(self, principal", "the owner's press: the checks, the durable dispatch boundary, one settle"),
        anchor("holdspeak/services/channel_service.py", "def discard(self, principal", "prepared -> discarded by one conditional write; against Send, one wins"),
        anchor("holdspeak/services/channel_cli.py", "CLI_RUNNER: Any = subprocess.run", "the CLI channels' process edge (the atlas's recording runner replaces it inside the hub)"),
        anchor("scripts/graph_walk.py", "def _install_cli_runner", "the rig's recording runner (PHILO-10-05)"),
    ],
    "reachable_by": [c["id"] for c in CASES],
}]

EXCLUDED = [
    {"id": "excluded.p10.face_only_op", "applicability": "not_applicable",
     "combination": "case.p10.send.no_destination, case.p10.send.destination_picked, case.p10.send.sending, case.p10.send.unknown_after_restart, case.p10.send.receipt_after_return with an .op sibling",
     "reason": "no destination and a pick write nothing (a preview is a computation, exempt: no receipt); SENDING is a moment, not an outcome, and an op send held at the runner would hold the rig's one MCP request forever; the restart's durable outcome is read in the same observation (the hub's row, its history row, the one gh create), and the operation form of R3 is fenced through a real process restart by tests/unit/test_philo10_send_restart.py; the return is a face fact over case.p10.send.sent's durable outcome."},
    {"id": "excluded.p10.face_replay", "applicability": "not_applicable",
     "combination": "case.p10.send.replay_same_key as a face case",
     "reason": "the face mints one key per press; its own replay is Retry after a lost answer, which needs the request to REACH the hub with its answer dropped. The rig's http_fault answers in the browser (the hub never sees it), so it cannot make that state. Fenced as rendered at 1440 and 393 by tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_a_lost_answer_and_every_unreadable_read_are_named."},
    {"id": "excluded.p10.agent_side", "applicability": "not_applicable",
     "combination": "an agent's prepare (PREPARED BY <agent>) and an agent's send refused owner_principal_required as atlas cases",
     "reason": "the rig speaks with the owner's token only (scripts/graph_walk.py Hub); an agent principal is rig work outside this story. Fenced with a real Settings-issued credential by tests/unit/test_philo10_send_contract.py and, as rendered, by tests/e2e/test_philo10_04_send_face_glass.py::TestSendFaceGlass::test_prepared_sends_and_the_latest_result."},
    {"id": "excluded.p10.other_channels", "applicability": "not_applicable",
     "combination": "the Jira, Confluence and email variants of SENT, FAILED and UNKNOWN (COMMENTED, BLOG POSTED, ACCEPTED BY SENDGRID)",
     "reason": "each Send state has its atlas case on the file channel (a real write) or on GitHub (the recording runner); the other channels' words are the same states. Jira and Confluence need acli switch/status answers and a connected account through the Phase 9 connection producer; email needs the HTTPS edge and a memory keyring inside the hub, seams the rig's hub does not carry. Fenced as rendered at 1440 and 393 by tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence and ::TestSendEmailGlass::test_the_email_boards; their real sends are story 06's leg B."},
]


def main() -> None:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
    atlas = {"schema_version": 1, "atlas_version": "phase10-send", "extends": "docs/internal/philo/graph/atlas.json",
             "source_commit": head, "cases": CASES, "states": STATES,
             "clocks": [{"id": "clock.python_wall", "source": "datetime.datetime.now() inside the hub process",
                         "mechanism": "none: no Phase 10 case moves a clock", "status": "available", "used_by": []}],
             "excluded": EXCLUDED, "council_readings": []}
    ATLAS.write_text(json.dumps(atlas, indent=2) + "\n")
    faces = sum(1 for c in CASES if c["viewports"])
    print(f"{ATLAS.relative_to(REPO)}: {len(CASES)} cases ({faces} face, {len(CASES) - faces} op), "
          f"{len(STATES)} state, {len(EXCLUDED)} exclusions")


if __name__ == "__main__":
    main()
