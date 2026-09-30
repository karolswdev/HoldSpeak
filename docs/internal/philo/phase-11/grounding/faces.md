# PHILO Phase 11 grounding: the faces half

**Date:** 2026-09-29. **Base:** main `7e09c8b4`. **Lane:** the Fedaykin docs lane (Opus 5.5) for Muad'Dib.
**Other half:** Astra's lane grounds the backend (payload contract, producers, Slack transport) in `backend.md`.
**Isolation:** the shots came from a hub on a throwaway HOME (`mktemp -d`, removed after the run). The seed was one project, one decision, one meeting with a summary, and one brief, made through the real routes (the meeting through the DB layer in that HOME). No real HOME, no owner DB, no account. Nothing was sent.

The owner's pick: briefs, decisions and meeting summaries go out through the Phase 10 channels (file, GitHub, Jira, Confluence, email through SendGrid or Resend), plus Slack. The rulings that bind the faces: "You, every time" (an agent can prepare a send; only he presses Send). Saved destinations. Every verb is the library Button. No prose, no modals, no counters of zero. The egress chip goes where egress happens. The canvas comes before the build (`docs/internal/UX-CANON.md` §A.1–A.9, §E).

## Shots (`shots/`, today's product, before any Phase 11 change)

| File | What it shows |
|---|---|
| `01-brief-chair-1440.png`, `01-brief-chair-393.png` | The Chair's BRIEF section: one item with Ack and Defer, the THIS DEVICE chip, Generate. No Copy, no export. At 1440 the meeting row below it also shows the meeting SUMMARY. |
| `02-brief-intelligence-1440.png` | The Intelligence window, BRIEF view: the brief as a document (period, GENERATED stamp, SINCE MONDAY, items, `PEOPLE · UNAVAILABLE`). The footer has Acknowledge, Defer and Speak. No Copy. |
| `05-decision-1440.png`, `05-decision-393.png` | The decision window (`DecisionPullout`): status, deciders, DECISION CONTEXT, DECISION, CONSEQUENCES, Filed. The footer has Copy, Dictate about this and Edit. At 1440 the window is about 400 px wide. |
| `04-meetings-record-1440.png` | The Meetings window, OUTCOMES, the record: NEEDS YOU, SUMMARY with topics, TRANSCRIPT. The footer has MD, SRT and Delete. The window is about 640 px wide. |
| `03-meeting-pullout-1440.png` | The meeting window (`MeetingPullout`): the summary in quotes, topics, Filed. The footer has Dictate about this and Record follow-up. No Copy, no export. |

No 393 shot of the Meetings record or the Intelligence brief: at 393 the Dock shows only icons, and my rig did not reach those two windows at that width (not a product finding; the canvas rig owes both).

## 1. Where each document lives on the face today

### 1a. The brief

"The brief" in the owner's words is the Monday brief. Phase 10 names it (`pm/roadmap/holdspeak-philo/phase-10-the-channels/current-phase-status.md:9`, `:82`). The chief-of-staff part is its person overlay (`holdspeak/services/person_overlay.py:1`, "Read-time chief-of-staff overlay for the Monday Brief"). Hub: `GET /api/brief/latest`, `POST /api/brief/generate` (`holdspeak/web/routes/monday_brief.py:101-131`).

| Face | File | What he sees | Copy or export today |
|---|---|---|---|
| Chair home, BRIEF section | `web/src/desk/chair/ChairHome.tsx:1304-1420`; head verbs `:727-760`; the badge `web/src/desk/chair/briefEgress.tsx:18-26` | the untriaged items as rows with Ack and Defer, the date line, the receipt line (shot 01) | none |
| Intelligence window, BRIEF view | `web/src/desk/pullouts/views/BriefView.tsx:157`; mounted at `web/src/desk/pullouts/IntelligencePullout.tsx:135`; footer `BriefView.tsx:470-500` | THIS WEEK, SINCE <day>, the person sections, the triage footer (shot 02) | none |

Three other things in the code are also called a brief. They are **not** the Monday brief: the Room's preparation brief (`holdspeak/web/routes/project_briefs.py:1-11`, face `web/src/features/project-room/prepare/PreparePosture.tsx`), the 1:1 relationship brief (`holdspeak/web/routes/people.py:141`), and the Cadence brief (`holdspeak/web/routes/cadence.py:44`).

### 1b. A decision

Three stores carry the word "decision":

| Kind | Hub | Face | Copy today |
|---|---|---|---|
| The desk decision record (context, decision, consequences, alternatives) | `holdspeak/web/routes/primitives/decisions.py:58-103` | `web/src/desk/pullouts/DecisionPullout.tsx` (shot 05). The Room's DECISIONS & COMMITMENTS rows open it: `web/src/features/project-room/ProjectRoomCore.tsx:1431-1530`, `Open` at `:1504`, `:1525` | **yes**: `Copy` builds Markdown in the browser (`DecisionPullout.tsx:31-35`, verb `:153-160`) |
| The meeting decision lifecycle (accept, reject, supersede, promote) | `holdspeak/web/routes/decisions.py:39-127` | the Room controller (`web/src/features/project-room/useProjectRoomController.ts:163-205`) | none |
| The decision receipt (Phase 127, the "WHY" on work) | `/api/decision-records/…` | `web/src/desk/components/WhyControl.tsx:10-45` opens Intelligence → DECISIONS (`web/src/desk/pullouts/views/DecisionsView.tsx`) | none |

The first two routers share the `/api/decisions` prefix. Whether their paths collide is a backend question (Astra's half); it is not verified here.

### 1c. A meeting summary

The summary is `intel.summary` plus `intel.topics` on the meeting detail (`web/src/meetings/MeetingSummarySlab.tsx:1-13`). It shows in three places:

| Face | File | Copy or export today |
|---|---|---|
| The Chair's MEETINGS row, unfolded (shot 01) | `ChairHome.tsx` meetings section | none |
| The Meetings window, OUTCOMES, the record (shot 04) | `web/src/pages/cores/history/MeetingDetail.tsx:171-173` → `MeetingSummarySlab.tsx:38-71` | footer **MD** and **SRT**: a download of the **whole meeting**, not the summary (`web/src/pages/cores/HistoryCore.tsx:436-455`, `:646-651`) |
| The meeting window (shot 03) | `web/src/desk/pullouts/MeetingPullout.tsx:123-124` | none |

The Slack "digest" is a different text: what was decided, what is still open, what changed since the last meeting. It does **not** carry the summary text (`holdspeak/slack_export.py:101-147`). The "follow-up" is a third text (`:159-161`).

## 2. The Phase 10 SendWell: what is bound to the project update

`web/src/features/channels/SendWell.tsx` is mounted once, on a published update (`web/src/features/project-room/update/UpdatePosture.tsx:438`); its list chips at `:302`.

**Bound to the update (each must change to compose the well on another face):**

| # | Where | The binding |
|---|---|---|
| B1 | `SendWell.tsx:351-353` | the prop is `update: ProjectUpdate` |
| B2 | `channels.ts:499-506` | the wire sends `update_id` to `sends`, `preview` and `send`. The hub resolves only `project_update:<id>` (`holdspeak/services/channel_contract.py:195-226`; `holdspeak/services/channel_service.py:148`, `:158`, `:361`, `:454`) |
| B3 | `SendWell.tsx:338-347` | `mergeKnown` filters on `project_update:${updateId}` |
| B4 | `SendWell.tsx:57-62`, `:297-318` | the press store is keyed `${updateId}\|${target}` (the key shape is general; only the name is update) |
| B5 | `SendWell.tsx:547` | the prepared row shows `REV ${update.draftRevision}` |
| B6 | `SendWell.tsx:593-665` | `DeliveryHistory` takes the `UpdateController`: the manual To + Mark delivered row, and `update.deliveries` (the update's history table, written by the hub at `channel_service.py:522`) |
| B7 | `SendWell.tsx:670-682` | `ListChips` counts from `update.deliveries` |
| B8 | `SendWell.tsx:685-698` | `PublishedWells` re-reads through `ctrl.reloadDeliveries` |
| B9 | `SendWell.tsx:404` | Add destination opens Settings; general, no binding |

**Reusable as they are (no word of "update" inside):** `accountChip` (`:139-168`), `useConnections` (`:124-134`), `Unreadable` (`:196-203`), `OutcomeLine` (`:205-223`), `LastChip` (`:226-233`), `LatestReceipt` (`:236-263`), `proofLink` (`:268-275`), `latestFor` (`:323-330`), and in `channels.ts` the words, `previewOf`, `egressOf`, `farSide`, `targetToken`, `sentWord`, `refusedWord`/`failedWord`/`unknownWord`. Three are private today and must be exported or moved: `PreviewWell` (`:174-193`), `ProofCell` (`:278-293`), `useDestinations` (`:109-122`).

**What it takes:** the well takes a document reference (`{ref, title, revision?}`) in place of the update. The preview, the prepared rows, the press rule and the receipt stay as ratified. Only the history needs a new source for the new documents (finding F4).

## 3. Destinations

- **One list or a filter per document kind.** Nothing in the saved destination is about a document: its fields are a channel, an account and a target (`web/src/features/channels/channels.ts:21-38`; the form `web/src/pages/cores/connections/Destinations.tsx:99-218`). The GitHub and Jira kinds point at one issue or one work item (`Destinations.tsx:159-173`). That fits an update for that item better than a Monday brief, but it is still a true place to post. **Recommendation: one list, no filter.** A filter is a second interface (Tenet 3). Each row's last-send chip is already per document (`SendWell.tsx:416`, `latestFor`).
- **Slack in the form.** The form picks the channel with a `CycleGadget` (`Destinations.tsx:46-52`, `:144-146`). Email adds a Provider `CycleGadget` and a key typed once into the keychain through `SecretRow` (`:187-203`; the key store `channels.ts:494-498`). Slack follows the same pattern:
  - Channel: `Slack` (a sixth `CHANNELS` row; `Channel`, `CHANNEL_WORD`, `SENT_WORD` gain `slack`: `channels.ts:19`, `:99-105`, `:120-127`).
  - Webhook: a `SecretRow`, typed once, kept in the keychain, never shown again. This matches today's credential rule: the webhook URL is a secret and never appears in an API answer (`holdspeak/slack_export.py:22-27`).
  - Channel name: a `StringGadget` he types (for example `#leads`). A webhook does not tell its channel name, so this is only a label. It fills the row's target token and the name (`autoName`, `Destinations.tsx:84-93`: "Slack #leads").
  - Egress chip: the webhook host (`hooks.slack.com`), from the same host check the export uses (`slack_export.py:49-70`).
  - Check and proof depend on the transport (Astra's half). A webhook answers only `ok`: no message link, so the SENT row has a word and no link (`ProofCell`, `SendWell.tsx:278-293`, needs a Slack case). A bot token answers with a message you can link to, but needs a token and a channel id.

## 4. The existing Slack face and the collision

- **The meeting record:** `AftercareGadgets` (`web/src/pages/cores/history/AftercareGadgets.tsx:9-48`), mounted under the transcript (`MeetingDetail.tsx:190-195`). Two rows, `DIGEST → SLACK` and `FOLLOW-UP → SLACK`, each with a `Send` Button. The group shows only when a webhook is set (`:20`; `holdspeak/services/meeting_aftercare_service.py:83`). It was hidden in shot 04 (no webhook on the throwaway HOME).
- **Its `Send` does not send.** It creates a proposal (`web/src/pages/cores/history/useMeetingData.tsx:180-199`, receipt `PROPOSED DIGEST`). He then approves it in another place (`useMeetingData.tsx:158-175`). The row has no egress chip (UX-CANON A.9) and its verb names an act it does not do (A.11).
- **Settings:** the webhook is a `SecretRow` in the Credentials group, `Slack webhook` (`web/src/pages/cores/SettingsCore.tsx:77-86`, `:2311-2321`). That group is directly **under** the Phase 10 Destinations group on the same pane (`SettingsCore.tsx:2325-2338`).
- **The collision:** with a Slack channel, the meeting record would carry two Slack doors (the aftercare rows and the SEND well). The Connections pane would carry two Slack homes, one above the other (a Slack destination and the Credentials webhook). They send different texts (1c). Phase 10 left this path Out on purpose (`current-phase-status.md:84`, `:247`).

## 5. FINDINGs, ranked by what they cost the owner

- **F1: each of the three words names more than one thing.** "Brief" = the Monday brief, the preparation brief, the 1:1 brief, the Cadence brief (1a). "Decision" = the desk record, the meeting lifecycle row, the Phase 127 receipt (1b). "Meeting summary" = `intel.summary` + topics, the Slack digest, the follow-up draft, the MD export (1c). If the charter does not name one, the build can send the wrong document. Questions Q1–Q3.
- **F2: two Slack doors, and today's one says Send but only proposes.** See section 4. Question Q7.
- **F3: the SendWell is bound to the update at eight points (B1–B8; B9 is general), and it is a feature module, not a library species.** On four faces it is a recurring element; UX-CANON §B says it goes into the library and `web/src/desk/surface/contract.md` first, and then the faces use it. The species it composes are all library species already.
- **F4: the SEND history is the update's own table.** `DeliveryHistory` reads `update.deliveries` and carries the manual Mark delivered row (B6). The brief, a decision and a meeting have no delivery table and no manual row. The new documents need a history: the ended sends of that document, from the sends read (`wire.sends`, `channels.ts:499-500`). Question Q8.
- **F5: the brief has no document form on the face.** The Chair shows it as a triage list; only the Intelligence BRIEF view reads like a document, and it has no Copy (1a, shots 01, 02). Each Generate makes a new brief with new item ids (`ChairHome.tsx:1362-1363`), so a send names one brief by id and date. The person sections are People data (`BriefView.tsx:40-41`); sending them to others crosses the People boundary. Question Q1.
- **F6: the decision's Copy is built in the browser.** `DecisionPullout.tsx:31-35` joins the three fields as Markdown. The Send payload is rendered by the hub (the previewed bytes are the sent bytes). The two texts of one decision can differ. A decision can be edited at any time and has no publish step, so an open preview can go stale; the Phase 10 refusal `PREVIEW CHANGED` covers the send (`channels.ts:179-180`), but the face must show it (a canvas board).
- **F7: the host windows are narrow at 1440.** The decision window is about 400 px wide, the Meetings window about 640 px (shots 04, 05). The SEND row has up to five chips (`SendWell.tsx:463-469`). The narrow-window layout happens at desktop width, not only at 393. The canvas must prove it in the real window width.
- **F8: the word DELIVERY is on two things on one screen.** The SEND history head is `DELIVERY` (`channels.ts:85`). The Dock has a `Delivery` item, the roadmap board (`web/src/desk/components/DeliveryBoard.tsx:386`; shot 01). On the Chair or in Intelligence both show at once. Phase 10 grounding F12 flagged the word; the head is inherited.
- **F9: the MD export is not a channel.** The footer `MD` downloads the whole meeting (`HistoryCore.tsx:436-455`). It stays as a download (Phase 10 census C7). It is not the "meeting summary" document.

## 6. The canvases the charter will owe

Each board at 1440 × 900 and 393 × 852, on the real product with a harness shim for the new wire (the Phase 10 pattern: `pm/roadmap/holdspeak-philo/phase-10-the-channels/assets/story-04-send-canvas/README.md`, "What the boards are").

**Canvas A: the brief** (on the Chair BRIEF section and the Intelligence BRIEF view, per ruling R4)
- A1 no destination (`NO DESTINATION` + Add destination)
- A2 a destination picked: the preview fields and the brief body, Send, the egress chip
- A3 sent (one channel, with proof), and the history of this brief
- A4 a send the steward prepared (`PREPARED`, `BY STEWARD`) and the Chair's BRIEF head with its `PREPARED ×1` chip
- A5 a new Generate after a send: the well offers Send again with the new preview (ruling R9)
- A6 the person sections in the preview (ruling R1)

**Canvas B: a decision** (in every decision face, per ruling R4)
- B1 picked, in the about-400 px window at 1440 and at 393
- B2 sent
- B3 Edit after a send: the preview shows the new text; Send again (ruling R9)
- B5 the meeting decision row and the decision receipt (Intelligence → DECISIONS) with their SEND wells (ruling R2)
- B4 prepared by an agent, and the Room's decision row with its `PREPARED ×1` chip

**Canvas C: a meeting summary** (in every meeting face, per ruling R4)
- C1 the record: SUMMARY, then SEND, at about 640 px and at 393
- C2 Slack picked: the preview in Slack text, the `HOOKS.SLACK.COM` chip
- C3 posted to Slack; history
- C4 a meeting with no summary: no SEND well (the draft rule of Phase 10 board 36)
- C5 the aftercare digest and follow-up as documents in the same SEND well; the old `DIGEST → SLACK` rows gone (ruling R7)
- C6 the meeting window (`MeetingPullout`) and the Chair's MEETINGS row with the well (ruling R4)

**Canvas D: Destinations with Slack**
- D1 the form, Slack chosen: Webhook, Channel name, Name, the egress chip
- D2 the webhook saved (`KEY SET` pattern), and refused (`KEY NOT SAVED` + why)
- D3 the Slack row in the list, open, with Check
- D4 the Credentials group without the `Slack webhook` row (ruling R7: no migration; he adds a Slack destination)

**Canvas E: the shared well** (one board per face, the same species)
- E1 the four SEND wells side by side: update, brief, decision, meeting, to prove "the same object never drawn two ways" (UX-CANON §D, first rule)

## 7. The owner's rulings (2026-09-29, verbatim, to the nine questions below)

| # | His word | What it rules for the faces |
|---|---|---|
| R1 | "Both." | The Monday brief goes out with its items **and** its person sections. |
| R2 | "All." | Every kind of decision: the desk record, the meeting decision, the decision receipt. |
| R3 | "All." | Every meeting summary form: the summary and topics, the digest, the follow-up. |
| R4 | "In all those." | A SEND well on every face where each document lives today (1a, 1b, 1c). This makes F3 binding: one library species, composed on every face. |
| R5 | "Ok." | One destination list, no filter. |
| R6 | "Ok." | Slack by incoming webhook. |
| R7 | "As long as everything can use the same thing - we are golden. No need to 'migrate', just rewrite it. I'm the only user, remember?" | The aftercare Slack export is rewritten onto the Slack channel. It has no migration step: he adds a Slack destination once. The old webhook setting and the aftercare rows go. |
| R8 | "OK" | Copy stays as it is. Mark delivered stays on the update only. |
| R9 | "I mean, if it changes, we re-send. How is it so difficult for you to comprehend?" | Nothing is frozen for him to track. When a document changes, the well shows the new preview and he presses Send again. No old-version rows or stale-date words. |

## 7a. The questions as asked (the defaults were the lane's; the rulings above replace them)

1. **Which brief?** Default: **the Monday brief** (Chair and Intelligence), items only. The person sections are **not** sent (People data leaving the machine; he can widen this later).
2. **Which decision?** Default: **the desk decision record** (the window the Room's decision rows open). Any status; the status shows in the preview fields. The Copy verb reads the hub's text too (F6), so there is one text of a decision.
3. **Which meeting summary?** Default: **one document**: the SUMMARY text and topics, then what was decided and what is still open (the digest's sections). This one document takes the place of the Slack digest and the follow-up for sending.
4. **Where the SEND well sits.** Default: brief → the Intelligence BRIEF view (the Chair gets only a `PREPARED ×K` chip, when K > 0); decision → the decision window, above the footer; meeting → the Meetings record, OUTCOMES, under SUMMARY. Not on the Chair rows, not in the meeting window.
5. **Destinations: one list for every document?** Default: **yes, one list, no filter.**
6. **Slack transport.** Default: **incoming webhook** (one secret, no app, no token; the path HoldSpeak already has). The cost: no message link as proof, only `ok`. (The transport is Astra's to ground; this is the face default.)
7. **The old Slack doors.** Default: the saved webhook is moved **once** into a Slack destination; then the aftercare Slack rows and the Credentials `Slack webhook` row are **parked**, not deleted.
8. **Copy and Mark delivered on the new documents.** Default: Copy stays where it is (the decision window); **no** Mark delivered row on a brief, a decision or a meeting; the history is the ended sends only.
9. **A brief that changed.** Default: a send names the brief he sees (by id and generated date). A prepared send of an older brief keeps its frozen text and shows its date.

## 8. Unknown (not verified here)

- The 393 layout of the Meetings record and the Intelligence brief view (my rig did not reach them at 393).
- Whether the two `/api/decisions` routers collide on any path (backend half).
- The Slack proof and the Slack Check for each transport (backend half).
- The aftercare Slack group on screen: hidden without a webhook, so it is read from code only (`AftercareGadgets.tsx:20`).
