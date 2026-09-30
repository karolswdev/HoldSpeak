# The document sources and the Slack channel (PHILO-11 design)

**Status:** CHECKED by Astra (r1 RATIFY-WITH-CONDITIONS, paid) — awaiting the owner's ratification. Written 2026-09-29 by the Fedaykin docs lane (Opus 5.5) for Muad'Dib; round two pays `../checks/charter-astra-r1.md` findings 1–5, 7 and 8 here. It binds stories 01 and 02, and it gives stories 03–05 their wire.

**Inputs:** the owner's rulings R1–R9 (`docs/internal/philo/phase-11/grounding/faces.md` §7, verbatim; they are law here); the backend grounding (`docs/internal/philo/phase-11/grounding/backend.md`); Muad'Dib's check of it (`docs/internal/philo/phase-11/grounding/checks/backend-muaddib.md`). Where `backend.md` §5 recommends against R1–R9, the ruling wins, as that check lists.

**The Phase 10 lifecycle does not change.** `../../phase-10-the-channels/design/send-lifecycle.md` stays binding, section by section: the durable dispatch boundary; one winner between Send and Discard; recovery never dispatches again (take-over, reaper, restart and replay, fences R1–R6); the prepared bytes stay frozen; the inline Send renders again and refuses `preview_changed` when the digest differs from the one he saw; the frozen target and park-not-delete; one byte contract for every channel; redirects refused and exceptions sanitized on the network seam. This design adds document kinds and one channel. It adds no second lifecycle.

## 1. The document-source interface

One declared interface. One registry table. No discovery, no entry points, no publish workflow (Tenet 1; backend.md §1 last paragraph).

```text
DocumentSource (Protocol)
  kind                        "project_update", "monday_brief", ...
  render(db, source_id) -> Document       reads the stored source by its id; never "latest"
                                          refuses by name when it cannot render

Document (exists: holdspeak/services/channel_contract.py:65)
  ref        "<kind>:<source_id>"         the document_ref (unchanged)
  title      the frozen title
  body_md    the Markdown body
  slug       for file names
  label      a short display label, for example "BRIEF 2026-09-29", "REV 4", "DECISION D-12"

DOCUMENT_SOURCES = {kind: source, ...}    the registry TABLE
```

- **Resolve.** A `document_ref` is `<kind>:<source_id>`. The service splits it, finds the kind in `DOCUMENT_SOURCES`, and calls `render`. An unknown kind refuses `document_kind_unknown`. A missing source refuses `document_not_found`. A source reads its own stored record by id. It never takes a body from the caller (backend.md §1: "never an agent-supplied body").
- **The update stays as it is.** `render_update` (`holdspeak/services/channel_contract.py:195`) becomes the `project_update` source, with its `not_published` refusal. Its `label` is `REV <draft_revision>`.
- **Adding a kind** means one class and one table row. Channels do not change.

## 2. The provenance (minimal, R9)

The owner: "I mean, if it changes, we re-send. How is it so difficult for you to comprehend?" (R9).

- **Kept:** `kind` and `source_id` are the two halves of `document_ref`. No new column holds them.
- **Frozen at prepare:** `title`, `slug` and `label`, in one additive, nullable column `channel_sends.document_json`. The declarative schema adds it. There is no migration step and no backfill. A row with no `document_json` is a Phase 10 update row and reads as today.
- **Why freeze these three:** a prepared Send names its file and its row without a live source read. Today `naming` reads the update again at Send (`holdspeak/services/channel_contract.py:213`; `holdspeak/services/channel_service.py:473`). That read goes. A prepared send of a deleted decision still sends its frozen bytes under its frozen name.
- **Not added (R9, Tenet 1):** no source-snapshot digest, no renderer version, no source revision column, no stale-version state and no "old version" word on the face. The two Phase 10 guards already cover change: the inline Send renders again and compares the preview digest; a prepared send keeps its frozen bytes. When a document changes, the well shows the new preview, and he presses Send again.
- **People read:** the brief renderer reads the People overlay with an internal OWNER principal, so an agent's preview or prepare includes names and owe counts. This is the ratified consequence of R1 and D2.
- Chat palette: `channel.destinations` + `channel.prepare` only (Muad'Dib, 2026-09-30, budget); preview/sends stay on MCP/HTTP.
- `project_update_deliveries` keeps its Phase 10 shape and stays update-only (backend.md §1 row "Delivery projection"; R8).

## 3. The kinds

| Kind | `document_ref` | Source (read by id) | What the body carries | Never | Refusals |
|---|---|---|---|---|---|
| Project update (exists) | `project_update:<id>` | `project_updates` (`holdspeak/services/channel_contract.py:195`) | as Phase 10 | — | `not_published` |
| The brief (R1) | `monday_brief:<id>` | `monday_briefs` + `monday_brief_items` (`holdspeak/db/schema.py:2466`, `:2476`) loaded by id (`holdspeak/services/monday_brief_service.py:1492`), **composed with the real person overlay** (`holdspeak/services/person_overlay.py:3`), as the Intelligence BRIEF view reads it. `generate()` alone does not produce the overlay. | the whole brief: period, generated time, headline, every section and item, **and the person sections** | — | `document_not_found` |
| Desk decision (R2) | `desk_decision:<id>` | `desk_decisions` (`holdspeak/db/schema.py:1102`), through `PrimitiveService.get_decision` (`holdspeak/services/primitive_service.py:164`) | title, status, deciders, context, decision, consequences, alternatives | — | `document_not_found` |
| Meeting decision, the lifecycle row (R2) | `meeting_decision:<id>` | `decisions` (`holdspeak/db/schema.py:387`), through `DecisionLifecycleService` (`holdspeak/web/routes/decisions.py:47`) | the decision text, its meeting (title, date), its lifecycle state, owner when set | — | `document_not_found` |
| Decision record: "the decision receipt" in Intelligence → DECISIONS **and** the Room's DECISIONS & COMMITMENTS rows, including rows marked `source="meeting"` (R2) | `decision_record:<id>` | `decision_records` + sources, work (`holdspeak/db/schema.py:1129`, `:1144`, `:1154`), through `DecisionRecordService.get` (`holdspeak/services/decision_record_service.py:428`) | decision, rationale, owner, review date, sources, lifecycle and successor when set | the field-revision history; raw kernel receipts | `document_not_found` |
| Meeting summary (R3) | `meeting_summary:<meeting_id>` | the meeting and its stored intelligence (`holdspeak/db/meetings.py:558`) | meeting title and date, the summary, the topics | **the transcript** | `no_summary` |
| Meeting digest (R3) | `meeting_digest:<meeting_id>` | the aftercare digest (`holdspeak/services/meeting_aftercare_service.py`; its sections in `holdspeak/slack_export.py:101-147`) | what was decided, what is still open, what changed since the last meeting | the transcript | `no_summary` when the digest has nothing to say |
| Meeting follow-up (R3) | `meeting_followup:<meeting_id>` | the aftercare follow-up (`holdspeak/slack_export.py:159-161`) | the follow-up draft | the transcript | as above |

Rules for all kinds:

- **Read the stored record.** No model runs at preview or at Send (backend.md §2, the meeting summary).
- **The meeting forms never carry the transcript.** The meeting exports do (`holdspeak/meeting_exports.py:118`, `:159`, `:170`). No meeting form uses them. A sentinel fence proves it.
- **The brief is the one he sees, by id.** The well names the brief the face shows. Generate on the **same day** returns the existing brief with the **same id** (`holdspeak/services/monday_brief_service.py:398-406`); a new id comes only on a later day. The renderer reads the stored brief and the overlay at preview, so the preview always shows the current words. When they change, the well shows the new preview and he presses Send again (R9).
- **The brief goes out whole (R1).** Every item, acknowledged, deferred or not, and the person sections. No People gate on the send. The Ack and Defer marks are his desk state, not text of the brief; they are not rendered, and an acknowledged item keeps its text in the sent brief. (Ratified by Astra r1 finding 4.)
- **The digest and follow-up renderers are kept** (backend.md §3 C4 recommendation). They produce Markdown. The 3,800-character truncation (`holdspeak/slack_export.py:36`, `:73`) goes: a channel limit refuses by name; it never cuts text.
- **Copy stays as it is (R8).** The decision window's Copy builds its text in the browser (`web/src/desk/pullouts/DecisionPullout.tsx:31-35`). The owner ruled "OK" on keeping it. The two texts can differ; this is accepted, not engineered away.

## 4. The declared operations, generic

The Phase 10 operation names stay. Their arguments change once. No compatibility shim (Tenet 2).

| Operation | Before (Phase 10) | After |
|---|---|---|
| `channel.preview` | `update_id`, `destination_id` (`holdspeak/channel_operations.py:174`) | `document_ref`, `destination_id` |
| `channel.prepare` | `update_id`, `destination_id` (`:198`) | `document_ref`, `destination_id` |
| `channel.send` (inline form) | `update_id`, `destination_id`, `preview_digest` | `document_ref`, `destination_id`, `preview_digest` |
| `channel.send` (`send_id` form), `channel.discard` | `send_id` | unchanged |
| `channel.sends` | filter `update_id` (`:294`) | filter `document_ref` (the DB already lists by it, `holdspeak/db/channels.py:142`) |

- **One service, three transports.** HTTP, MCP and the rig's `op` step reach the same descriptor (the Phase 5 law).
- **The client callers change in the same commit (story 01).** The wire in `web/src/features/channels/channels.ts:499-506` **and** the inline Send body built in `web/src/features/channels/SendWell.tsx:429` (today `update_id: uid`) send `document_ref: "project_update:<id>"`. Story 01 owns this surgical change and its fences (the Phase 10 update glass stays green), so nothing breaks between the merges of 01 and 04. The Phase 10 atlas `.op` cases get the same one-word change. Nothing else on the update face moves in story 01.
- **The kernel target mapping** (`holdspeak/services/project_kernel.py:184`) names the `document_ref` for preview, prepare and the inline send, so the receipt and the admission name the real source (backend.md §1).
- **Authority (unchanged classes):** `channel.preview`, `channel.prepare`, `channel.sends` are WORK (`holdspeak/mcp/tool_authority.py:265`). `channel.send`, `channel.discard` are EGRESS with `owner_press=True` (`holdspeak/channel_operations.py:241`, `:288`). Saving and removing a destination is AUTHORITY. A secret save is HTTP only, held, owner press (`holdspeak/channel_operations.py:319`).
- **The thread may prepare.** `channel.destinations` and `channel.prepare` join the chat palette (`holdspeak/services/thread_tools.py:344`). `channel.preview` and `channel.sends` stay public on MCP and HTTP, outside the chat palette. Prepare's answer carries the preview the owner will read. `channel.destinations` is needed: prepare takes a destination id, and the thread finds it there (`holdspeak/channel_operations.py:23`). A fence proves "prepare my brief for #leads" through the thread gate with **no destination id given to the test**: the thread looks it up by name. Saving and removing destinations, secrets, Send and Discard stay his press.
- **Two boundaries, not one.** (1) **The thread palette:** a thread's call to a tool outside its palette (for example `channel.send`) is refused by the thread gate before any operation exists: "Tool outside the admitted palette" (`holdspeak/services/thread_tools.py:591`). (2) **The owner press:** a direct external agent over MCP reaches `channel.send`, which is admitted and refused `owner_principal_required` with a receipt (`holdspeak/channel_operations.py:241`). Each has its own fence.
- **History.** A new kind reads its history from `channel.sends` filtered by its `document_ref`: the ended sends. No manual row and no Mark delivered (R8). The update keeps its Phase 10 history and its manual row.
- **File names.** `<YYYY-MM-DD>-<slug>-<label slug>-<first 8 hex of send id>.md`, from the frozen `document_json`. Exclusive create and the `-2`, `-3` suffix stay as Phase 10 section 5.

## 5. The Slack channel (R6: incoming webhook)

Slack is one more channel on the Phase 10 contract: one module, one registry row, one destination form. It follows the email seam (`holdspeak/services/channel_email.py`), without a provider table, because there is one transport.

- **The destination.** `channel: slack`. `account`: `{key_ref}`. `target`: `{channel_label}`, the name he types (for example `#leads`). A webhook does not report its channel name, so the label is only his label. The egress chip is `hooks.slack.com`.
- **The secret.** The whole webhook URL is the credential. He types it once. It goes into the native keyring (`holdspeak/services/channel_email.py:396`, the email precedent) under `slack:<key_ref>`. It is never in the destination row, the payload, a receipt, argv, a log, an API answer or a file. The save is an HTTP-only held-secret operation with the owner's press, as `channel.save_email_key` is (`holdspeak/channel_operations.py:319`). Story 02's first commit names the operation: a sibling of the email key operation, or that one operation widened to take the channel. Muad'Dib checks the name.
- **At save:** the URL must be `https://hooks.slack.com/services/...`. Any other scheme, host or port refuses `slack_webhook_invalid`. `key_ref` is minted per save.
- **A new webhook is a new destination.** Destination rows never change their target (Phase 10 section 1: Edit parks the old row and makes a new one). A new URL gets a new `key_ref`. A send prepared on the old row then refuses `destination_parked`. No credential fingerprint is added.
- **The payload.** At prepare the channel converts the Markdown body to Slack text (headings and bold to `*bold*`, links to `<url|text>`, lists kept) and serializes the exact request body `{"text": "<slack text>"}`. Those bytes are the frozen payload. The readable preview is the text, parsed back from those bytes. Dispatch sends those bytes and nothing else.
- **The size limit.** Above 39,000 characters of Slack text (owner Q1: "Higher limit, still refuse"; the number is Muad'Dib's, under Slack's 40,000 truncation), prepare and the inline Send refuse `payload_too_large:slack`, before any byte leaves. The refusal answer carries `size` (the Slack text's character count) and `limit` (39,000), so the face shows `41,099 / 39,000 CHARACTERS` (canvas T1; Astra canvas check r2, condition 1): top-level integers beside `code` / `error_code`, never nested (PHILO-11-04 ruling). No truncation, no split into several posts, no file upload. (Owner question Q1; this is its default.)
- **The egress.** `POST` to exactly `hooks.slack.com:443`, as an `external.egress` child of the send, with the parent, the authenticated owner principal, the broker and the frozen `payload_digest` (the network seam Phase 10 story 03 built), data class `slack_message`. Exact host, no wildcard. Redirects are refused. Transport exceptions are sanitized before the native record. Only the dispatch opener reads the URL from the keyring.
- **The outcomes** (backend.md §3, the webhook row; pinned; an unlisted answer is UNKNOWN):

| Result | When |
|---|---|
| SENT, face word **POSTED** | `200` and the body is exactly `ok`. The proof is the time and the destination. **There is no message link.** The face never makes one up. |
| FAILED (a known non-delivery) | `400` + `invalid_payload`; `403` + `action_prohibited`; `404` + `channel_not_found`; `410` + `channel_is_archived`; a documented `429` (keep a bounded `Retry-After` in the reason); a connect, DNS or TLS failure before any byte left |
| UNKNOWN | a timeout or a dropped connection after the request left; `500` + `rollup_error`; any other `5xx`; a `3xx` (redirect refused); `200` without the exact `ok`; any unlisted status and body |
| REFUSED (before the boundary) | `slack_webhook_missing` (no key in the keyring), `payload_too_large:slack`, `destination_changed`, `destination_parked`, and the Phase 10 refusals |

- **No automatic repost.** Not after UNKNOWN, not after `Retry-After`. A new Send is a new press with a new key (Phase 10 section 4).
- **Check.** A webhook has no read call. Check reports what is known without a post: the key is in the keyring, and the URL passes the host rule. It never posts a test message.

## 6. The aftercare Slack path, rewritten (R7)

The owner: "As long as everything can use the same thing - we are golden. No need to 'migrate', just rewrite it. I'm the only user, remember?" (R7).

- **The digest and the follow-up are documents** (`meeting_digest`, `meeting_followup`, section 3). They reach Slack only through the SEND well and `channel.send`, by his press.
- **Removed from the product:** the `DIGEST → SLACK` and `FOLLOW-UP → SLACK` rows (`web/src/pages/cores/history/AftercareGadgets.tsx:9-48`); the `Slack webhook` row in Settings → Credentials (`web/src/pages/cores/SettingsCore.tsx:84`, `:2311-2321`); the aftercare Slack proposal and its executor (`holdspeak/services/meeting_aftercare_service.py:103-111`, `:157-170`; `holdspeak/web/routes/actuator_shared.py:241-283`); `build_slack_connector` (`holdspeak/slack_export.py:166`).
- **Settings keeps an explicit exclusion.** Removing the Slack credential registration (`holdspeak/services/credential_service.py:27`, `:36`) alone makes the Settings serializers stop redacting the field: they redact only through `SECRET_PATHS` (`holdspeak/services/credential_service.py:57`; `holdspeak/services/settings_service.py:173`). Astra reproduced the URL returned in a Settings read (`../checks/charter-astra-r1.md` finding 2). So both Settings reads **and** writes drop `meeting.slack_webhook_url` explicitly (one named field in the existing `LEGACY_ENDPOINT_FIELDS` pop, `holdspeak/services/settings_service.py:165-171`, and its write twin): a read never returns it, a write never sets it. A fence reads Settings with a sentinel URL in `config.json`. Small; no credential framework.
- **Every reader of `meeting.slack_webhook_url` goes** (census at base: `holdspeak/config/meeting.py:133`, `:263-271`; `holdspeak/services/settings_service.py:38`, `:181`, `:610-621`, `:1026-1031`; `holdspeak/services/credential_service.py:27`, `:36`, `:188-192`; `holdspeak/trust_destinations.py:71`; `holdspeak/services/actuator_service.py:54`; `holdspeak/web/routes/desk_actuators.py:28`). The config field may stay in the dataclass as an ignored value, so an old `config.json` still loads. Nothing reads it. It is not copied into the keyring (backend.md §3: no silent credential migration).
- **No migration.** He adds one Slack destination. That is the whole move.
- **The posture path does not survive.** Today, when the captured policy allows `control_posture`, the aftercare producer approves and executes in the same call (`holdspeak/services/meeting_aftercare_service.py:170`). With the rewrite, no path posts to Slack without his press. An agent, the steward or a posture policy can at most **prepare** a send. A fence proves it: red on the base (the posture path executes), green after (it prepares or does nothing).
- **The desk actuator's Slack target: a deliberate capability deferral.** It (`holdspeak/services/actuator_service.py:51-54`; `holdspeak/web/routes/desk_actuators.py:28`; its face affordance in the desk's contextual integrations, `web/src/desk/contextual.ts:130`) posts free text to Slack. Free text is not one of the ruled document kinds, and **R7 did not order its removal**. Phase 11 parks it on purpose: the endpoint refuses `slack_moved_to_channel`, and the face affordance is parked too, so no verb offers a send that cannot happen. Its webhook and GitHub targets do not change. Historical proposals and receipts stay readable. **What he loses until a free-text kind exists:** posting an arbitrary desk text to Slack. A free-text document kind is BACKLOG. (Stated default D1; ratified by Astra r1 finding 7.)
- **Parked, not deleted, where the law asks.** Historical aftercare proposals and their receipts stay readable. Code that nothing calls is removed; its record is the BACKLOG row and this section.

## 6a. The face seats of the decision kinds (Astra r1 finding 1)

- **`decision_record`** has two seats: Intelligence → DECISIONS (`web/src/desk/pullouts/views/DecisionsView.tsx:124` reads `/api/decision-records/<id>`), and the Room's DECISIONS & COMMITMENTS rows. The Room's rows come from `decision_records` joined to their sources (`holdspeak/services/project_service.py:2034`), and a row that came from a meeting proposal is only **labelled** `source="meeting"` (`:2103`). Its id is a decision record id. Its well sends `decision_record:<id>`, never `meeting_decision:<id>`.
- **`desk_decision`** has one seat: the decision window (`web/src/desk/pullouts/DecisionPullout.tsx`), opened for a desk primitive.
- **`meeting_decision` (the lifecycle `decisions` row) has no rendered seat today.** The Room controller fetches these rows (`web/src/features/project-room/api.ts:43-46`, `/api/decisions?project_id=`; `web/src/features/project-room/useProjectRoomController.ts:118-125`) and returns `openMoment` and `transition` (`:163-205`, `:343-344`), but no component consumes them (a search of `web/src` for `openMoment` outside the controller finds none; `transition` is returned the same way). No face lists a lifecycle row. **Consequence:** `meeting_decision` is a source kind (R2), reachable through preview and prepare over MCP and from a thread, and it gets **no face well and no canvas board** in Phase 11. Phase 11 does not build a new list to host it (Tenet 1). Story 03 confirms this on glass before canvas B; if it finds a rendered seat, that seat gets the well and a board.
- **Unknown:** the Room row's `Open` opens `decision:<record id>` in the decision window (`web/src/features/project-room/ProjectRoomCore.tsx:1504`, `:1525`), which reads `/api/decisions/<id>` (the desk and lifecycle stores, `holdspeak/web/routes/decisions.py:61-72`), not `decision_records`. Whether that window renders a record id was not verified. Story 03 records what the glass shows; a defect found there is ledgered, not fixed in passing.

## 6b. The failure transitions the face must draw (Astra r1 finding 8)

- **Over the Slack limit:** the preview answers the named refusal `payload_too_large:slack`, and the well shows a real refusal word for it, never `NO ANSWER` (today a preview error collapses to that, `web/src/features/channels/SendWell.tsx:361`).
- **`preview_changed`:** the inline Send refuses; the well fetches a fresh preview for the same document and destination (today the refresh keys on the id and destination only, `web/src/features/channels/SendWell.tsx:476`); he presses Send again.
- **The Chair after its last brief item is acknowledged or deferred:** the Chair changes branch (`web/src/desk/chair/ChairHome.tsx:1388`); the brief's well stays on the section in that branch.
- Each has a board (story 03) and a rendered-transition fence at both widths (story 05). The full well fitting at 393 is a canvas obligation, not an established fact.

## 7. What this design does not decide

- The face: the well's seat on each face, its words (including the history head word, faces.md F8), the Slack form and the POSTED row. Canvases A–E (story 03), ratified by the owner before any face build.
- The name of the Slack key operation (section 5): story 02's first commit, checked by Muad'Dib.
- The Slack text conversion's exact rules beyond section 5: story 02, fenced by preview-equals-payload.
