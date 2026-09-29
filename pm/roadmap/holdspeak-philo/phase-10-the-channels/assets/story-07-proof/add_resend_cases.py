#!/usr/bin/env python3
"""PHILO-10-07 (Codex Astra r1 on #701, P2): the Resend cases in atlas-phase10.json.

Five face cases at 1440 and 393, each read with its hub outcome in the SAME
observation (all_of: a face half and a hub half), through the rig's recording
edge (boundary `cli_runner` with an `https` script: the email channel's real
plan, the kernel's external.egress admission with its real allow-list, the
real opener; only the socket canned; the key in the hub's memory, never the
OS keychain):

* resend_setup    -- the Room's Add destination opens the Destinations form; he
                     picks Email, then Resend, types the key (Resend key: SET),
                     saves: the row's egress chip reads API.RESEND.COM.
* resend_accepted -- Send on the Resend destination: ACCEPTED BY RESEND, one
                     request to api.resend.com/emails.
* resend_prepared -- a prepared send's own Send: the prepared row turns to
                     ACCEPTED BY RESEND.
* resend_history  -- a send made earlier: the DELIVERY history reads ACCEPTED BY
                     RESEND with the id.
* resend_unknown  -- an answer that is not Resend's: RESULT UNKNOWN; Check goes
                     to the Resend activity page.

Appends to the file story 05 wrote (add_atlas.py rewrites it whole: run this
after it). Idempotent: the Resend cases are replaced, and every state source
line is anchored again from the tree.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
ATLAS = REPO / "docs/internal/philo/graph/atlas-phase10.json"
FIX = "tests/fixtures/philo10_atlas"
DEST = "ResendPriya"
KEY_REF = "resend-atlas"
IDS = [f"case.p10.send.resend_{n}" for n in ("setup", "accepted", "prepared", "history", "unknown")]
NEW = ("New (no red claimed): Resend is a new provider (PHILO-10-07); on main 05d01ffb the Provider "
       "cycle has SendGrid only and the hub has no Resend provider.")


def main() -> None:
    atlas = json.loads(ATLAS.read_text())
    cases = [c for c in atlas["cases"] if c["id"] not in IDS]
    by_id = {c["id"]: c for c in cases}
    base = by_id["case.p10.send.unknown"]
    gate, seed = base["setup"][:4], base["setup"][5:8]   # the gate; project, draft, publish
    room = list(base["setup"][9:16])               # reload .. update-list wait
    assert room[0]["action"] == "reload" and room[-1]["selector"] == "[data-testid=update-list]", room
    open_update = copy.deepcopy(base["setup"][16])
    assert "update-list-item" in open_update["selector"]

    def edge(script: str) -> dict:
        return {"kind": "boundary", "substitute": "cli_runner", "label": f"the email HTTPS edge: {script}",
                "adapter": "email-https-edge", "reply": f"{FIX}/{script}",
                "why": "the email channel's real plan, the kernel's external.egress admission and the real opener "
                       "run; only the socket is canned, and the key lives in the hub's memory (never the OS keychain)"}

    def api(method: str, path: str, body: dict, why: str, capture: str | None = None, at: str | None = None) -> dict:
        step = {"kind": "api", "method": method, "path": path, "adapter": "http-route", "body": body,
                "expect_status": 200, "why": why}
        if capture:
            step.update({"capture_as": capture, "capture_path": at})
        return step

    def ui(action: str, selector: str | None = None, why: str | None = None, **extra) -> dict:
        step = {"kind": "ui", "action": action, "adapter": "ui-keyboard" if action in ("press", "fill", "focus") else "ui-pointer"}
        if selector:
            step["selector"] = selector
        step.update(extra)
        if why:
            step["why"] = why
        return step

    saved = api("POST", "/api/channels/destinations",
                {"name": DEST, "channel": "email", "provider": "resend", "from_email": "karol@example.com",
                 "from_name": "Karol", "key_ref": KEY_REF, "to": ["priya@example.com"]},
                "a saved Resend destination (it names its key by NAME)", "key_ref", "destination.account.key_ref")
    found = {"kind": "api", "method": "GET", "path": "/api/channels/destinations", "adapter": "http-route",
             "body": None, "expect_status": 200, "why": "the saved destination's id, by its name",
             "capture_as": "dest_id", "capture_path": "destinations", "capture_match": {"name": DEST}}
    put_key = api("PUT", "/api/channels/email-keys/{key_ref}", {"api_key": "re_atlas_synthetic_key_0000", "provider": "resend"},
                  "the Resend key saved under that name (a synthetic key, into the hub's MEMORY key store)")
    well = [open_update, ui("wait_for", "[data-testid=send-well]")]
    pick = [ui("wait_for", f"[data-testid=destination-row]:has([data-destination='{DEST}'])"),
            ui("click", f"[data-testid=destination-row]:has([data-destination='{DEST}'])",
               "A1: the pick opens the preview and Send in place, under the row"),
            ui("wait_for", f"[data-testid=send-open][data-destination='{DEST}'] [data-testid=send-preview]",
               "the readable preview the hub derived from the frozen request (Send waits for it)"),
            ui("scroll_into_view", f"[data-testid=send-open][data-destination='{DEST}'] [data-testid=send-verbs]",
               "the owner scrolls Send to the middle of the window, so its answer lands in view", block="center")]
    press = {"kind": "ui", "action": "click", "adapter": "ui-pointer",
             "selector": f"[data-testid=send-open][data-destination='{DEST}'] [data-testid=send-verb]",
             "why": "the owner's press: POST /api/channels/send (update, destination, the preview's digest, a new key)",
             "trigger_route": {"method": "POST", "path": "/api/channels/send"}}
    wire = {"kind": "cli_calls", "argv_prefix": ["https", "POST", "api.resend.com", "/emails"], "count": 1}
    reads = [{"method": "GET", "path": "/api/channels/sends?update_id={update_id}"},
             {"method": "GET", "path": "/api/projects/{project_id}/updates"}]
    sent_rows = {"kind": "protocol_reads", "expect": [
        {"status": 200, "row": {"path": "sends", "match": {"state": "sent", "destination_id": "{dest_id}",
                                                            "proof.provider": "resend",
                                                            "proof.word": "ACCEPTED BY RESEND"}, "count": 1}},
        {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}", "deliveries.0.channel": "email",
                                                              "deliveries.0.outcome": "sent"}}}]}

    def case(cid: str, setup: list, trigger: dict, parts: list, observe: str, reads_: list, words: str) -> dict:
        return {"id": cid, "job": "p10", "edge_ids": ["edge.face.channel_send"],
                "state_id": base["state_id"], "applicability": "applicable",
                "preconditions": ["a fresh isolated HOME and browser profile; the hub started against that HOME"],
                "setup": setup, "trigger": trigger,
                "expected": {"predicate": {"kind": "all_of", "predicates": parts}, "observe_at": observe,
                             "reads": reads_, "words": f"{words} {NEW}"},
                "completion_bound_s": 30, "viewports": [1440, 393]}

    form = "[data-testid=dest-form]"
    new = [
        case(IDS[0],
             [*gate, edge("resend-accepted.json"), *seed, *room, open_update,
              ui("wait_for", "[data-testid=send-add-destination]"),
              ui("click", "[data-testid=send-add-destination]", "B2: the Room's Add destination opens Settings AT the group, the form open"),
              ui("wait_for", form),
              ui("focus", f"{form} select[aria-label=Channel]"),
              ui("press", key="e", why="the Channel cycle: E is Email (the select's own type-ahead)"),
              ui("wait_for", f"{form}[data-channel=email] select[aria-label=Provider]"),
              ui("focus", f"{form} select[aria-label=Provider]"),
              ui("press", key="r", why="the Provider cycle: R is Resend"),
              ui("fill", "[data-testid=dest-from]", value="karol@example.com"),
              ui("fill", "[data-testid=dest-to]", value="priya@example.com"),
              ui("click", "[data-testid=dest-key-row] button:has-text('Replace')", "the key row: Replace arms the one field"),
              ui("fill", "[data-testid=dest-key-row] input[type=password]", value="re_atlas_synthetic_key_0000"),
              ui("press", key="Enter", why="the key goes to the hub once (PUT /api/channels/email-keys/resend-karol@example.com)"),
              {"kind": "check", "predicate": {"kind": "text_contains", "value": "Resend key"},
               "observe_at": "[data-testid=dest-key-row]", "timeout_s": 10,
               "why": "the key row names Resend (never SendGrid) once Resend is picked"},
              {"kind": "check", "predicate": {"kind": "text_contains", "value": "SET"},
               "observe_at": "[data-testid=dest-key-row] .gadget-chip[data-set]", "timeout_s": 10,
               "why": "the key went to the hub once: the row reads SET before the Save (the key is never shown)"},
              ui("scroll_into_view", "[data-testid=dest-save]", "the owner scrolls Save into view", block="center")],
             {"kind": "ui", "action": "click", "adapter": "ui-pointer", "selector": "[data-testid=dest-save]",
              "why": "Save: POST /api/channels/destinations (provider resend, the key's NAME)",
              "trigger_route": {"method": "POST", "path": "/api/channels/destinations"}},
             [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/destinations", "status": 200,
               "body_fields": {"destination.channel": "email", "destination.account.provider": "resend",
                               "destination.account.key_ref": "resend-karol@example.com"}},
              {"kind": "readable_text", "value": "API.RESEND.COM"},
              {"kind": "protocol_reads", "expect": [
                  {"status": 200, "row": {"path": "destinations", "match": {"channel": "email", "account.provider": "resend",
                                                                             "account.from_email": "karol@example.com"},
                                          "count": 1}}]},
              {"kind": "cli_calls", "argv_prefix": ["https"], "count": 0}],
             "[data-testid=dest-list] [data-testid=dest-row]",
             [{"method": "GET", "path": "/api/channels/destinations"}],
             "the owner sets up a Resend destination from the Room's Add destination: the Destinations form opens in "
             "Settings, he picks Email then Resend, the key row reads Resend key and SET after the key is typed once, "
             "and Save lists the row whose egress chip reads API.RESEND.COM, readable in the viewport; the hub holds "
             "one email destination with provider resend and the key's name resend-karol@example.com; no request "
             "left for Resend."),
        case(IDS[1],
             [*gate, edge("resend-accepted.json"), *seed, saved, found, put_key, *room, *well, *pick],
             press,
             [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
               "body_fields": {"outcome": "sent", "send.proof.provider": "resend",
                               "send.proof.word": "ACCEPTED BY RESEND", "send.proof.message_id": "re-atlas-4ef9-0001",
                               "receipt.state": "succeeded", "receipt.actor_kind": "owner"}},
              {"kind": "readable_text", "value": "ACCEPTED BY RESEND"},
              sent_rows, wire],
             f"[data-testid=send-open][data-destination='{DEST}'] [data-testid=send-sent]", reads,
             "the owner presses Send on the Resend destination and Resend accepts it (200 and its id): the answer is "
             "SENT with the id as proof and the owner's succeeded receipt; the row reads ACCEPTED BY RESEND, readable "
             "in the viewport; the hub holds one sent send whose proof names Resend and ONE history row; ONE request "
             "to api.resend.com/emails."),
        case(IDS[2],
             [*gate, edge("resend-accepted.json"), *seed, saved, found, put_key,
              api("POST", "/api/channels/sends", {"update_id": "{update_id}", "destination_id": "{dest_id}"},
                  "prepare (the owner): a prepared row with the frozen request and preview", "send_id", "send.id"),
              *room, *well, ui("wait_for", "[data-testid=prepared-open] [data-testid=prepared-send]")],
             {"kind": "ui", "action": "click", "adapter": "ui-pointer",
              "selector": "[data-testid=prepared-open] [data-testid=prepared-send]",
              "why": "the prepared row's Send: POST /api/channels/send {send_id}",
              "trigger_route": {"method": "POST", "path": "/api/channels/send"}},
             [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
               "body_fields": {"outcome": "sent", "send.id": "{send_id}", "send.proof.word": "ACCEPTED BY RESEND",
                               "receipt.state": "succeeded"}},
              {"kind": "readable_text", "value": "ACCEPTED BY RESEND"},
              {"kind": "protocol_reads", "expect": [
                  {"status": 200, "row": {"path": "sends", "match": {"id": "{send_id}", "state": "sent",
                                                                      "proof.provider": "resend"}, "count": 1}}]},
              wire],
             "[data-testid=prepared-result-word][data-state=sent]", reads[:1],
             "a transition, PREPARED to SENT: a send prepared to the Resend destination waits in the SEND well; the "
             "owner presses its own Send and the prepared row turns to ACCEPTED BY RESEND, readable in the viewport; "
             "the hub holds that send sent with Resend's proof; ONE request to api.resend.com/emails."),
        case(IDS[3],
             [*gate, edge("resend-accepted.json"), *seed, saved, found, put_key,
              api("POST", "/api/channels/preview", {"update_id": "{update_id}", "destination_id": "{dest_id}"},
                  "the preview's digest", "digest", "payload_digest"),
              api("POST", "/api/channels/send", {"update_id": "{update_id}", "destination_id": "{dest_id}",
                                                 "preview_digest": "{digest}", "command_id": "atlas-p10-07-earlier"},
                  "an earlier send to Resend (the owner's token, the send route)", "sent_op", "operation_id"),
              *room],
             {**open_update, "then": [
                 ui("wait_for", "[data-testid=delivery-history] [data-testid=delivery-row]"),
                 ui("scroll_into_view", "[data-testid=delivery-history] [data-testid=delivery-row]",
                    "he scrolls down to the DELIVERY history under the SEND well", block="center")]},
             [{"kind": "readable_text", "value": "ACCEPTED BY RESEND"},
              {"kind": "readable_text", "value": "ID re-atlas-4ef9-0001"},
              sent_rows, wire],
             "[data-testid=delivery-history] [data-testid=delivery-row]", reads,
             "the DELIVERY history after a send to Resend: he opens the update and its history row reads ACCEPTED BY "
             "RESEND with Resend's id, readable in the viewport; the hub holds one sent send with Resend's proof and "
             "ONE history row; ONE request to api.resend.com/emails."),
        case(IDS[4],
             [*gate, edge("resend-unknown.json"), *seed, saved, found, put_key, *room, *well, *pick],
             press,
             [{"kind": "protocol_status", "method": "POST", "path": "/api/channels/send", "status": 200,
               "body_fields": {"outcome": "unknown", "send.reason": "unpinned_503", "receipt.state": "indeterminate"}},
              {"kind": "readable_text", "value": "Check priya@example.com"},
              {"kind": "attr_equals", "attr": "data-href", "value": "https://resend.com/emails"},
              {"kind": "protocol_reads", "expect": [
                  {"status": 200, "row": {"path": "sends", "match": {"state": "unknown", "reason": "unpinned_503"},
                                          "count": 1}},
                  {"status": 200, "row": {"path": "updates", "match": {"id": "{update_id}",
                                                                        "deliveries.0.outcome": "unknown"}}}]},
              wire],
             f"[data-testid=send-open][data-destination='{DEST}'] [data-testid=send-check]", reads,
             "the owner presses Send on the Resend destination and the answer is not Resend's (a 503 page from an "
             "edge): RESULT UNKNOWN, the receipt indeterminate, never a false NOTHING SENT; the row offers Check "
             "priya@example.com and its far side is the Resend activity page (https://resend.com/emails), readable "
             "in the viewport; the hub holds one unknown send and ONE history row (outcome unknown); ONE request to "
             "api.resend.com/emails."),
    ]
    atlas["cases"] = cases + new

    for entry in atlas["excluded"]:
        if entry["id"] == "excluded.p10.other_channels":
            entry["combination"] = ("the Jira, Confluence and SendGrid email variants of SENT, FAILED and UNKNOWN "
                                    "(COMMENTED, BLOG POSTED, ACCEPTED BY SENDGRID)")
            entry["reason"] = (
                "each Send state has its atlas case on the file channel (a real write), on GitHub (the recording runner) "
                "or on Resend (PHILO-10-07: the recording HTTPS edge and a memory key store in the hub); the other "
                "channels' words are the same states. Jira and Confluence need acli switch/status answers and a "
                "connected account through the Phase 9 connection producer; SendGrid is the same email channel as "
                "Resend with its own answer shape. Fenced as rendered at 1440 and 393 by "
                "tests/e2e/test_philo10_04_send_face_glass.py::TestSendChannelsGlass::test_jira_and_confluence and "
                "::TestSendEmailGlass::test_the_email_boards; their real sends are story 06's leg B.")
    atlas["excluded"] = [e for e in atlas["excluded"] if e["id"] != "excluded.p10.resend_op"] + [{
        "id": "excluded.p10.resend_op", "applicability": "not_applicable",
        "combination": ", ".join(IDS) + " with an .op sibling",
        "reason": ("each Resend face case reads its durable outcome in the same observation (the press's own answer "
                   "with its receipt, the hub's send and history rows, the recording edge's count); the operation "
                   "form of every Resend answer is fenced through the real save, prepare and send routes by "
                   "tests/unit/test_philo10_email_channel.py test_c7_*.")}]

    # Every state source line anchored again from the tree (story 07 moved channel_service.py).
    for state in atlas["states"]:
        for ref in state.get("sources", []):
            lines = (REPO / ref["path"]).read_text(encoding="utf-8").splitlines()
            hits = [i + 1 for i, line in enumerate(lines) if ref["symbol"] in line]
            assert hits, ref
            ref["line"] = hits[0]
    ATLAS.write_text(json.dumps(atlas, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(atlas['cases'])} cases; Resend: {len(new)}")


if __name__ == "__main__":
    main()
