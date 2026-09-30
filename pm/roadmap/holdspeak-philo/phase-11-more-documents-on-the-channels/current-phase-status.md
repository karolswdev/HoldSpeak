# Phase 11 - More documents on the channels

**Last updated:** 2026-09-29 (Story 01 built and verified in `feat/philo-11-01`; counsel-on-built pending Muad'Dib. Full-suite fallout classified and proved in `lane-01-astra.md`. Earlier: RATIFIED by the owner, "Ratify, build it"; Q1 → refuse above 39,000 characters. Earlier: round two: Astra r1 RATIFY-WITH-CONDITIONS paid (`checks/charter-astra-r1.md`) — the decision kinds mapped to their real face seats, the Settings exclusion of the old webhook, `channel.destinations` in the thread palette, the same-day brief id, story 01 owns the inline Send caller, D1 recorded as a capability deferral, the failure-transition boards, Q1 worded as our limit. Earlier: DRAFTED by the Fedaykin docs lane for Muad'Dib.)

**Status:** RATIFIED by the owner 2026-09-29 ("Ratify, build it") after Astra's check r1 (RATIFY-WITH-CONDITIONS, paid). Q1 ruled: "Higher limit, still refuse" → Muad'Dib set the limit at **39,000** characters of Slack text (Slack truncates above 40,000; he can change it).

## Goal

The owner sends a brief, a decision or a meeting summary the way he sends a project update today: he opens the document where it lives, picks a saved destination, sees the exact words, and presses Send. Slack joins the channels. The old meeting Slack export moves onto the same Send. An agent or a thread may prepare a send; only he sends.

## Authority

The owner, 2026-09-29, his pick for Phase 11: **"More documents on the channels"** — Phase 10 sends project updates only; next, briefs, decisions and meeting summaries through the same channels, plus Slack.

Carried from Phase 10 (`../phase-10-the-channels/current-phase-status.md`, "Authority"): **"Payload: Any document; updates first"**; **"Who sends: You, every time"**; **"Saved destinations"**; the email provider interface (Q1) and SendGrid and Resend (story 07).

## The owner's rulings (2026-09-29, verbatim)

Recorded in `docs/internal/philo/phase-11/grounding/faces.md` §7. They are law for this charter. The questions they answer are in §7a there.

| # | His word | What it rules |
|---|---|---|
| R1 | "Both." Then: "for 1 - why aren't we sending person things? We must. Stop being so paranoid." | The brief goes out whole: its items **and** its person sections. No People gate on the send. |
| R2 | "All." | Every kind of decision: the desk record, the meeting decision, the decision record ("the decision receipt" on the face). |
| R3 | "All." | Every meeting summary form: the summary and topics, the digest, the follow-up. Never the transcript. |
| R4 | "In all those." | A SEND well on every face where each document lives today. |
| R5 | "Ok." | One destination list, no filter. |
| R6 | "Ok." | Slack by incoming webhook. |
| R7 | "As long as everything can use the same thing - we are golden. No need to 'migrate', just rewrite it. I'm the only user, remember?" | The aftercare Slack export is rewritten onto the Slack channel. No migration: he adds one Slack destination. The old webhook setting and the aftercare rows go. |
| R8 | "OK" | Copy stays as it is. Mark delivered stays on the update only. |
| R9 | "I mean, if it changes, we re-send. How is it so difficult for you to comprehend?" | Nothing is frozen for him to track. When a document changes, the well shows the new preview and he presses Send again. No old-version rows, no stale-date words. |

Carried, unchanged: the Seven Tenets (`docs/internal/CONSTITUTION.md:18-60`); Article III, honest egress; Article XI, the kernel; UX-CANON §A (every verb the library Button, the canvas before build, no prose, no modals, no counter of zero, egress where egress happens), §B (a recurring element goes into the library first), §E (the review protocol) (`docs/internal/UX-CANON.md`); the Phase 10 Send lifecycle (`../phase-10-the-channels/design/send-lifecycle.md`); the owner's ruling that MCP flows through the services (2026-09-23); his ruling on thread authority: a thread stops for his press on EGRESS, AUTHORITY and CONFIG (2026-09-29).

## The roots

- **Tenet 7 (a Senior Architect with reports):** the brief, a decision and a meeting's outcome are what he tells his team and his boss. Today he copies them, or cannot (grounding faces.md §1: the brief and the meeting summary have no Copy).
- **Tenet 3 (help and accelerate; never a million interfaces):** one well, one list of destinations, one Send, on every document. Not a second Slack door (faces.md F2).
- **Tenet 1 (no over-engineering for safety):** a registry table of sources, not a framework; three frozen names, not a provenance system (R9); no migration (R7).
- **Tenet 2 (not even pre-alpha):** the old Slack path is rewritten, not kept beside the new one.
- **Tenet 5 (component framework):** the SEND well becomes one library species, composed on each face (UX-CANON §B; faces.md F3).
- **Tenet 6 (Workbench 2.0+):** the canvases come first; he ratifies them before any face build.
- **Tenet 4 (ASD-STE100):** face words are verbs and states: SEND, SENT, POSTED, REFUSED, FAILED, UNKNOWN, PREPARED.

## Status of this charter

DRAFT, 2026-09-29, written by the Fedaykin docs lane (Opus 5.5) for Muad'Dib. **Round two, 2026-09-29:** Astra's check r1 (`checks/charter-astra-r1.md`, session `01a0f012-2580-7a40-9660-117b3a1ef714`) is RATIFY-WITH-CONDITIONS; its conditions (findings 1–5, 7, 8; 6 and 9 ratified) are paid in this file, `design/document-sources.md` (§§3, 4, 6, 6a, 6b) and stories 01, 02, 03, 05. Inputs: the faces half (`docs/internal/philo/phase-11/grounding/faces.md`, Muad'Dib's lane) and the backend half (`docs/internal/philo/phase-11/grounding/backend.md`, Astra's lane), with Muad'Dib's check of the backend half (`docs/internal/philo/phase-11/grounding/checks/backend-muaddib.md`, RATIFY-WITH-CONDITIONS: R1–R9 replace five of its §5 recommendations). The settled design is `design/document-sources.md`. Owed: the owner's ratification and his answer to Q1. Nothing is built. The stories stay `backlog` until he ratifies.

## The grounding (main `7e09c8b4`)

- **The faces** (faces.md): where each document lives (§1); the eight update bindings in the SEND well, B1–B8 (§2); destinations and the Slack form (§3); the two Slack doors (§4); findings F1–F9 (§5); the canvas board list A–E (§6).
- **The backend** (backend.md): the contract is almost generic, but preview, prepare, naming and history are update-bound (§1); the three sources (§2); Slack transports, pinned outcomes and limits (§3); MCP and thread authority (§4); findings F1–F7 (§5).
- **What the rulings changed in backend.md §5** (backend-muaddib.md finding 2): the whole brief with person sections (R1), not "omit personal triage state"; all three decision kinds (R2), not the decision record only; all three meeting forms (R3), not one document; the incoming webhook (R6), not a bot token first; minimal provenance (R9), not a snapshot digest and a renderer version.

## Scope

- **In:**
  1. **The document sources (story 01),** as `design/document-sources.md` §§1–4 settles them. One declared `DocumentSource` interface and one registry table. The update becomes the first source. Seven new kinds: `monday_brief`, `desk_decision`, `meeting_decision`, `decision_record`, `meeting_summary`, `meeting_digest`, `meeting_followup`. Each reads its stored record by id and renders Markdown. No meeting form carries the transcript. The generic descriptors: `channel.preview`, `channel.prepare` and the inline `channel.send` take `document_ref` in place of `update_id`; `channel.sends` filters by `document_ref`. The minimal provenance: `kind` and `source_id` from `document_ref`; the frozen title, slug and label in one additive column. The kernel target mapping names the document. The thread's chat palette gains `channel.destinations`, preview, prepare and sends. Story 01 also changes the two client callers (`channels.ts` and the inline Send body in `SendWell.tsx:429`) so the update face never breaks between merges.
  2. **The Slack channel and the aftercare rewrite (story 02),** as design §§5–6 settles them. Slack by incoming webhook: the URL in the native keyring, the exact host `hooks.slack.com:443`, redirects refused, the pinned outcomes, `200 ok` = POSTED with no link, a size limit refused by name (Q1). The aftercare Slack path rewritten onto the channel with no migration: the old webhook setting, its every reader, the aftercare Slack proposal and executor, and the posture auto-execute path go. Settings reads and writes drop `meeting.slack_webhook_url` explicitly, so the ignored field never leaks (design §6). The desk actuator's free-text Slack target and its face affordance are parked: a deliberate capability deferral (D1).
  3. **The canvases A–E (story 03),** faces.md §6, at 1440 and 393, on the real product with a harness shim for the new wire. They include the failure transitions (design §6b): the over-limit Slack refusal, `preview_changed` → a fresh preview → another press, the Chair after its last brief item is triaged. The owner ratifies them before any face build.
  4. **The SEND well as one library species (story 04):** the eight update bindings (faces.md B1–B8) replaced by a document reference; the species in the library and in `web/src/desk/surface/contract.md`; the update face composes it first, with no visible change.
  5. **The faces (story 05):** the species composed on every face where each document lives (R4), and Destinations with Slack; the old Slack face rows removed.
  6. **The atlas cases (story 06)** for the new kinds and for Slack, at both widths.
  7. **The closing use (story 07):** real sends of each kind on the channels he has, and a cold agent prepares, he sends.
- **Out (with their homes):**
  - **A Slack bot token, a message link, `chat.getPermalink`:** R6 picked the webhook. BACKLOG.
  - **Long Slack documents split into several posts, truncated, or uploaded as a file:** Q1 default refuses by name. BACKLOG if he rules otherwise.
  - **Other briefs:** the Room's preparation brief, the 1:1 brief, the Cadence brief (faces.md §1a; backend.md §2). Not "the brief". BACKLOG.
  - **The full meeting export as a sent document** (it carries the transcript; faces.md F9). The MD and SRT downloads stay as they are.
  - **Mark delivered on the new kinds** (R8). A free-text document kind (D1). Stale-version tracking (R9).
  - **Moving the other outbound paths** (Cadence Telegram, the generic webhook actuator, `gh issue create`, the intel alert): Phase 10's BACKLOG row stands. Only the Slack paths move here (R7).
  - **An agent that sends:** "You, every time" stands.

## Admission by effect

Unchanged from Phase 10 (`../phase-10-the-channels/current-phase-status.md`, "Admission by effect"), with two changes:

| Operation | Change |
|---|---|
| `channel.preview`, `channel.prepare`, inline `channel.send` | the argument is `document_ref`; the admission and the receipt name it (`holdspeak/services/project_kernel.py:184`) |
| its effect: the Slack POST | `external.egress`, a child of the send, with its parent, the authenticated owner principal, the broker and the frozen `payload_digest`; allowed host exactly `hooks.slack.com:443`; data class `slack_message`; the URL only in the dispatch opener |

Story 01 applies Constitution XI.5 to the first row: preview returns `document_ref` but remains exempt computation, with no admission or receipt. Prepare and inline Send identify the document in their admissions and receipts. The original row's conflicting preview wording and this precedence are recorded in [Astra's lane record](lane-01-astra.md) for Muad'Dib's counsel-on-built.

The aftercare Slack proposal and its executor leave the table: they no longer exist (design §6).

## Exit criteria (evidence required)

"Red on main" applies where a defect exists (the posture path that posts without his press; the update-only descriptors). Everywhere else the proof is new capability through the real hub on an isolated HOME, never a test double that lies about the field a check reads. "At both widths" means 1440x900 and 393x852.

- [ ] 1. **Every kind over MCP alone, and from a thread.** A fence reads only the real `tools/list` answer and maps "send my brief / this decision / the meeting summary to <destination>", "prepare a send" and "what was sent" to a tool and an argument path, for each kind. No description says an agent can send. A thread prepares a send through the thread gate (the chat palette), not only over MCP: "prepare my brief for #leads" with **no destination id given to the test** (the thread finds it through `channel.destinations`). Two boundaries, two fences: a thread's `channel.send` is refused by the palette gate (no operation); an external agent's `channel.send` is refused `owner_principal_required` with a receipt. Route, MCP and the rig's `op` step reach one descriptor and one service.
- [ ] 2. **Each kind renders from its stored record, by id.** One case per kind through the real producer: the brief with its person sections (R1); the three decision kinds (R2); the three meeting forms (R3). An unknown kind refuses `document_kind_unknown`; a missing source `document_not_found`; a meeting with no summary `no_summary`. A transcript sentinel never appears in any meeting form's payload. No model runs at preview or Send.
- [ ] 3. **The Phase 10 lifecycle, unchanged, on the new kinds.** The Phase 10 fences stay green, and the lifecycle fences (R1–R6, preview equals payload, one winner, owner press, `preview_changed`) run over at least one new kind. A prepared send of a new kind keeps its frozen bytes and names its file with no source read (the source deleted in the fence). An inline Send after the source changed refuses `preview_changed`; a new preview and a new press send the new text (R9).
- [ ] 4. **Slack, as design §5 pins it.** Each pinned outcome through a recording HTTPS edge: POSTED on `200 ok` with no link; each FAILED pair; UNKNOWN on a timeout after send, a `5xx`, a `3xx` (never followed), `200` without `ok`, an unlisted answer. The exact host; any other host refused at save. The URL never in a row, payload, receipt, log, API answer or error (a sentinel fence). Above the limit, `payload_too_large:slack` before any byte leaves. The egress child carries parent, principal, broker and digest. No repost after UNKNOWN or `429`.
- [ ] 5. **The old Slack path is gone (R7).** No code reads `meeting.slack_webhook_url` to send. The posture path cannot post: red on main (`holdspeak/services/meeting_aftercare_service.py:170` executes), green here (it prepares at most). The digest and the follow-up reach Slack only through `channel.send` by his press. An old `config.json` with the field still loads, and a Settings read with a sentinel URL there never returns it (Astra r1 finding 2: removing the credential registration alone leaks it). No migration step exists.
- [ ] 6. **The face, as ratified.** Canvases A–E ratified by the owner (his word recorded) before the build commit. The SEND well is one library species, in `web/src/desk/surface/contract.md`, composed on every face R4 names; the update face shows no change. Each ratified board built and fenced through the real hub at both widths, the face's outcome equal to the hub's record in the same fence. Mark delivered only on the update (R8). Every verb the library Button; the egress chip on each row that leaves the machine; no modal; nothing covers Send at 393 or in the 400 px decision window at 1440 (faces.md F7). Rendered-transition fences at both widths for the over-limit Slack refusal (a real refusal word, never `NO ANSWER`), `preview_changed` → a fresh preview → another press, and the Chair after its last brief item is triaged. The web baseline has zero branch-new failures.
- [ ] 7. **The atlas** has face cases for each new kind that has a face seat (picked, sent, prepared; `meeting_decision` has none today, design §6a, so it gets `.op` cases only) and for Slack (POSTED, FAILED, UNKNOWN, the long-document refusal) at both widths, with `.op` siblings where the outcome is durable. The Phase 7, 8, 9 and 10 atlas cases still pass.
- [ ] 8. **The closing use.** Real sends, on his own session, to the targets he authorizes (the Phase 10 Q6 ruling carries): each of the three families (brief, decision, meeting summary) on each channel he has — file, GitHub (scratch issue #699), email through Resend, Slack if he gives a webhook, Jira and Confluence if his accounts are set — each proof read back from the far side; each of the eight kinds at least once on the file channel; or a named limit with its reason. A cold Codex session prepares one send of a new kind from the MCP catalogue alone; he presses Send on the face at both widths. Secrets, addresses and the webhook URL redacted at capture. Rehearsed, owner-reviewed shots; never recorded as a sitting.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| PHILO-11-01 | The document sources | done | [story-01-the-document-sources](./story-01-the-document-sources.md) | [evidence-story-01](./evidence-story-01.md) |
| PHILO-11-02 | The Slack channel and the aftercare rewrite | backlog | [story-02-the-slack-channel-and-the-aftercare-rewrite](./story-02-the-slack-channel-and-the-aftercare-rewrite.md) | — |
| PHILO-11-03 | The canvases A–E | backlog | [story-03-the-canvases](./story-03-the-canvases.md) | — |
| PHILO-11-04 | The SEND well as one library species | done | [story-04-the-send-well-species](./story-04-the-send-well-species.md) | [evidence-story-04](./evidence-story-04.md) |
| PHILO-11-05 | The faces: the well on every document, Destinations with Slack | backlog | [story-05-the-faces](./story-05-the-faces.md) | — |
| PHILO-11-06 | The atlas cases for the new kinds and Slack | backlog | [story-06-the-atlas-cases](./story-06-the-atlas-cases.md) | — |
| PHILO-11-07 | The closing use | backlog | [story-07-the-closing-use](./story-07-the-closing-use.md) | — |

**The order differs from the brief's proposal in one place:** the canvases are story 03 and the species is story 04. The species is a build. UX-CANON §A.2 puts the canvas before any build, and canvas E ("the same object never drawn two ways") is the drawing of the species. So the canvases come first.

## Lanes (proposed)

| Lane | Stories | Owner | Checker | Worktree | Branch |
|---|---|---|---|---|---|
| The sources | 01 | Astra (Luna, xhigh) | Muad'Dib | ../wt-philo-11-01 | feat/philo-11-01 |
| Slack | 02 | Astra (Luna, xhigh) | Muad'Dib | ../wt-philo-11-02 | feat/philo-11-02-slack |
| The canvases | 03 | Muad'Dib (Fedaykin, Opus 5.5) | Astra | ../wt-philo-11-03 | feat/philo-11-03-canvases |
| The species and the faces | 04 → 05 | Muad'Dib (Fedaykin, Opus 5.5) | Astra | ../wt-philo-11-04, ../wt-philo-11-05 | feat/philo-11-04-send-well-species, feat/philo-11-05-faces |
| The atlas | 06 | Astra (Luna, xhigh) | Muad'Dib | ../wt-philo-11-06 | feat/philo-11-06-atlas |
| The closing use | 07 | Muad'Dib | Astra | ../wt-philo-11-07 | feat/philo-11-07-closing-use |

- **The Slack destination form** is face work: it follows canvas D (story 05), not the parallel start of 02's backend module.
- **Why this split** (TWO-BRAINS §4): Astra takes the backend and the verification harness (01, 02, 06); Muad'Dib takes the faces and the owner-facing close (03, 04, 05, 07).
- **What runs in parallel.** 01 and 03 start at once: 03 draws on a harness shim of the new wire, and design §4 fixes that wire. 02 starts with 01, in two parts: the Slack channel module, its registry row and its destination form touch new files and one registry row, so they run in parallel with 01; the aftercare rewrite needs 01's `meeting_digest` and `meeting_followup` sources, so it lands after 01. 02 and 01 both touch `holdspeak/services/channel_contract.py` and `channel_service.py`: 01 merges first and 02 rebases on it. 04 builds after 03 is ratified and 01 has merged. 05 follows 04. 06 follows 01, 02 and 05. 07 is last.
- **The face removals** (the aftercare rows, the Settings webhook row) are story 05's files. Story 02 removes the hub side. The aftercare rows already hide when no webhook is set (`web/src/pages/cores/history/AftercareGadgets.tsx:20`), so the face does not break between the two merges.
- A lane runs its scoped fences and rig cases only. The orchestrator runs the full suite before the done call. CI does not gate a merge (the owner, 2026-09-28).

## Where we are

2026-09-30, round four: Astra's built-check r3 on PHILO-11-04 is RATIFY-WITH-CONDITIONS (`checks/story-04-built-astra-r3.md`). Condition 1 paid: UNKNOWN and no answer survive the click that leaves the row on both hosts (four fences, red on `f4127c441`, green now). Condition 2 owed: the merge with main after #707.

2026-09-30, round three: PHILO-11-04 pays Astra's built-check r2 (DO-NOT-RATIFY, `checks/story-04-built-astra-r2.md`): a FAILED, REFUSED or no-answer receipt stays on its destination row after the click that closes it or picks another row — at the row's last-send seat, the one the canvas draws (A3, B2, T1: line 2, beside the egress chip) — for the update and for every document (four transition cases, red on `f4127c441`). Not proven here: G2's producer and route (story 02), the Chair and the picker (story 05). #708 merges after #707; the merge with main is owed then.

2026-09-30, round two: PHILO-11-04 pays Astra's built-check r1 (DO-NOT-RATIFY, `checks/story-04-built-astra-r1.md`) on Muad'Dib's rulings: the well's reads and actions are keyed by the document (Astra's two probes red on `13ec2a7b3`, green now); the Slack size contract recorded for story 02 (top-level integer `size`, `limit`); the update's DELIVERY rows back to their ratified Phase 10 look (BACKLOG: unify them on the owner's canvas); the kit CSS guard scans nested files. G4 and the chip-head rule are implemented; their proof on the Chair and the picker is story 05's.

2026-09-30: PHILO-11-04 is built and verified (stacked on story 01, #707). The SEND well is one library species (`web/src/desk/surface/send/`, contract.md "SendWell") on a document reference; the update composes it with its own DELIVERY history in the slot. G3 built; G2 built as consumer behaviour; G4 and the head rules implemented. The Phase 10 update glass passes at 1440 and 393; six actual Phase 10 atlas walks PASS; the web baseline has zero branch-new. Next: story 05 composes the species on every document face.

2026-09-29: PHILO-11-01 is built and verified. Eight stored sources use the generic channel contract; the existing update face passes at 1440 and 393. Six actual Phase 10 atlas walks PASS. The final full run is red (38 failed, 13,498 passed): (a) ten stale wording/reference failures corrected; (b) two catalogue guidance losses corrected; (c) 26 glass failures pass twice serially, all 52 invocations. The final focused capture collects and passes 48 checks; the web suite passes 2,970. See [Astra's lane record](lane-01-astra.md). The PR goes to Muad'Dib for counsel-on-built; no merge verdict is claimed. Story 02 has not started in this lane, and story 03's canvas/shim files are untouched. The broader graph census remains red for story 06 reconciliation.

2026-09-29: PHILO-11-01 is building in Astra's assigned worktree `../wt-philo-11-01`, branch `feat/philo-11-01` (the dispatch brief's branch name). Three Luna workers own sources, the channel contract, and callers with lifecycle fences. Muad'Dib's counsel-on-built follows the PR. Story 02 is not started in this lane. Story 03's canvas and shim remain its lane's files.

2026-09-29: the owner RATIFIED the charter ("Ratify, build it"). Q1: "Higher limit, still refuse" — Muad'Dib set the limit at 39,000 characters of Slack text (under Slack's 40,000 truncation). Next: story 01 (Astra) and story 03 canvases (Muad'Dib) in parallel.

2026-09-29, round two: Astra r1 RATIFY-WITH-CONDITIONS paid (`checks/charter-astra-r1.md`). Owed: the owner's ratification and Q1.

2026-09-29: DRAFTED (PR #705). The two grounding halves are carried in this branch (draft PRs #702 and #704, superseded by #705).

**Estimate (PROVISIONAL; calibrated on Phase 10):** effort **9–13 engineering days** — 01 2.5–3.5 (the interface, seven renderers, the generic descriptors, the column, the palette, the fences over a new kind); 02 1.5–2 (one channel module, the pinned outcomes, the keyring slot, the rewrite and the census of every reader of the old setting); 03 1–1.5 (five canvases, about 24 boards at two widths); 04 about 1 (the species, B1–B8, no visible change on the update); 05 2–3 (about nine faces, Destinations with Slack, the removals); 06 about 1; 07 about 1, plus the real-send legs. Calibration: Phase 10's 11–15 engineering days were built in about 1.5 elapsed days, plus the check rounds. **Elapsed forecast: about 2–3 days, gated by the canvas ratification, the check rounds and a Slack webhook from him.**

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A document framework grows (publishing, versions, snapshot digests) | medium | one Protocol and one table; three frozen names (R9; design §2) | a snapshot-digest column, a renderer version, a "stale" state or word |
| A meeting form sends the transcript | medium | the meeting renderers never call the exports (design §3); a sentinel fence | a transcript sentinel in any meeting payload |
| The wrong "brief" or "decision" is sent (faces.md F1) | medium | each kind is named by its table and its face (design §3) | a source reads "latest" instead of the id; a kind reads another store |
| The old Slack path survives beside the new one (two doors, faces.md F2) | medium | every reader of the setting censused and removed (design §6); exit 5 | a Slack post that is not a `channel.send`; the aftercare rows on screen with a Slack destination saved |
| The posture path becomes "an agent sends" | medium | the path goes; agents prepare only; a fence red on main | any Slack egress without an owner principal |
| The webhook URL leaks | medium | keyring only, dispatch opener only; a sentinel fence | the URL in a row, payload, receipt, log, API answer or error |
| The SEND well forks per face | medium | one species first (story 04), canvas E | a second well component, or a face that hand-rolls the rows |
| The well does not fit a narrow window (faces.md F7) | medium | the canvas proves the 400 px and 640 px windows at 1440, and 393 | Send covered or cut in a real-width shot |

## Decisions for the owner

- **Q1 — RULED 2026-09-29: "Higher limit, still refuse"; Muad'Dib set 39,000 characters.** The question as asked: **"Our Slack limit is 4,000 characters. A document over it?"** 4,000 is **our chosen limit**, not Slack's hard limit: Slack recommends 4,000 characters and truncates above 40,000. **Recommended: (a).**
  - (a) Refuse it by name before anything leaves (`payload_too_large:slack`, above our 4,000 characters of Slack text). He sends it by another channel. No truncation, no split, no upload, no automatic shortening.
  - (b) A higher limit he names, below 40,000.
  - (c) Split into several posts. *Several posts, several results; a partial post is possible.*

**Tuesday (conditional):** he opens his brief, picks Slack, reads the whole document and presses Send — **if his brief fits the limit Q1 sets.** No representative whole-brief length was measured (Astra r1 UNKNOWN); story 07 records the lengths of the real briefs it sends.

## Stated defaults (not questions)

- **D1 — a deliberate capability deferral: the desk's free-text Slack send is parked.** The desk actuator (`holdspeak/services/actuator_service.py:51-54`; its affordance in `web/src/desk/contextual.ts:130`) posts free text to Slack through the old setting. Free text is not one of the documents R1–R3 name, and **R7 did not order its removal.** Phase 11 parks it on purpose, rather than invent a free-text kind: the endpoint refuses `slack_moved_to_channel`, and the face affordance is parked too. Historical proposals and receipts stay readable. Its webhook and GitHub targets do not change. **What he loses until a free-text kind exists:** posting an arbitrary desk text to Slack. BACKLOG row. (Ratified by Astra r1 finding 7.)
- **D2 — the thread may prepare.** `channel.destinations`, preview, prepare and sends join the chat palette; the thread finds a destination by name. Send, Discard, saving or removing a destination and secrets stay his press (his ruling of 2026-09-29 on thread authority).
- **D3 — the real sends go to targets he names** (the Phase 10 Q6 ruling carries): the scratch issue #699, his own address through Resend, a Slack scratch channel if he makes a webhook.

## Decisions made (this phase)

- 2026-09-29 — the owner ruled R1–R9 on the faces grounding's nine questions (verbatim above).
- 2026-09-29 — Muad'Dib checked the backend grounding: RATIFY-WITH-CONDITIONS; the charter adopts R1–R9 over its §5 recommendations (`docs/internal/philo/phase-11/grounding/checks/backend-muaddib.md`).
- 2026-09-29 — round two: Astra r1 RATIFY-WITH-CONDITIONS paid — `meeting_decision` has no rendered face seat today (no well, no board; design §6a); the Room's decision rows are `decision_record`; Settings excludes the old webhook field on read and write; `channel.destinations` joins the palette; the brief keeps its same-day id; story 01 owns the inline Send caller; D1 a capability deferral; the three failure transitions drawn and fenced; Q1 worded as our limit — Fedaykin docs lane for Muad'Dib.
- 2026-09-29 — DRAFTED: seven stories; one source interface; Slack by webhook; the aftercare path rewritten; the canvases before the species — Fedaykin docs lane for Muad'Dib.

## Decisions deferred

- The name of the Slack key operation: story 02's first commit, checked by Muad'Dib (design §5).
- The well's seat and words on each face, the history head word (faces.md F8), the Slack form and the POSTED row: canvases A–E, ratified by the owner.
- The Slack text conversion's exact rules: story 02, fenced by preview equals payload.
