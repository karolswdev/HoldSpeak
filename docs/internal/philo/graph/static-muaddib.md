# The static pass — Muad'Dib (PHILO-2-02)

**PASS:** static
**BRAIN:** muaddib
**SOURCE:** `c42963bcd154b7d199de501370f1643e14a3921d`, tree DIRTY — three untracked files, all of this lane: `docs/internal/philo/briefs/static-pass-lane-brief.md` (the lane brief, delivered to the worktree), `docs/internal/philo/graph/static-muaddib.json` and this file. No tracked file was modified; nothing was staged or committed.
**CONTRACT:** brief `graph-audit-brief.md` DRAFT round two (sha256 `ba5477fd07dba564…`); lane brief `static-pass-lane-brief.md` (`7f67064a82595d5b…`); schema `graph.schema.json` schema_version 1 (`bddbdcfac56b787b…`); atlas `atlas.json` schema_version 1 at source_commit `1cd55bc8` (`807056bce2b91c37…`); rig `scripts/graph_walk.py` v1.0.0 (`5f0485edb18baa62…`, not run in this pass).
**RUNTIME:** none. No hub, no browser, no product process, no e2e. Nothing was executed and nothing was observed on the owner's desk.

**Line numbers.** The atlas was written at `1cd55bc8`. Between `1cd55bc8` and `c42963bc` no file under `holdspeak/` or `web/src/` changed (`git diff --stat 1cd55bc8..HEAD` names 18 files, all under `docs/`, `pm/`, `scripts/` and `tests/`), so every atlas line citation still lands, and this graph re-stamps them at `c42963bc`. Every source reference in `static-muaddib.json` was resolved from the file itself at build time by its anchor text; 2153 references, 0 mismatches on re-check.

---

## JOBS

The eleven jobs are story 01's owner selection. A static pass can say **wired**, **broken** or **unverifiable-statically** — never pass or fail.

### J1 — Get past the gate · **wired**

*Expected:* the desk; or the words kept with a receipt.

Both branches close. `Continue later` → `dismiss()` keeps any draft as a note first, then `completeHandoff()` calls `POST /api/desk/seed` and `PUT /api/setup/onboarding`, and the hub's `arrival_required` reads that same disposition back (`FirstWords.tsx:254,213,216`; `setup_status.py:306`). `Keep as Note` → `POST /api/notes`, the created id is staged so the desk opens it, and the face states "Kept as a note" (`FirstWords.tsx:288,296,306`). A failed handoff keeps the words and offers `Retry finishing your Desk` (`FirstWords.tsx:233,235`). Every named failure category draws its own contract message (`FirstWords.tsx:412`).

*Limit:* the voice branch needs a READY `speech.transcribe` assignment. Whether a fresh desk's migrated speech profile resolves as ready is a live question; it is unverifiable statically.

### J2 — See what the desk asks of me · **wired**

*Expected:* one SETUP row naming what is missing; the head counts what asks.

`meetingPathBlockers` is a pure function of the roster and of how the read went (`meetingPathBlocker.ts:71`). A read still in flight draws nothing and the headline withholds the all-clear (`meetingPathBlocker.ts:75`; `ChairHome.tsx:640`). A failed read is its own row, "Could not read setup · Try again" (`meetingPathBlocker.ts:77`), and that verb re-reads in place (`ChairHome.tsx:969`). Both halves missing is one state and one row (`meetingPathBlocker.ts:91`). The calendar offer is drawn and never counted (`ChairHome.tsx:633`, `:920`).

### J3 — Give the desk a summary engine · **broken** (one of two paths)

*Expected:* READY; the SETUP row gone.

The **Add an engine** path is wired: `Check` → `POST /api/setup/discover-models`, and READY needs a model name, not a 200 (`useConciergeController.ts:654,667`); `Use this for summaries` → `define-endpoint` then `POST /api/concierge/summary-selection`, and the face reads `result.state`, not the HTTP status (`useConciergeController.ts:706,716,724`); success fires the one readiness signal the Chair re-reads its roster on, so the SETUP row leaves without another gesture (`useConciergeController.ts:751`; `ChairHome.tsx:506`).

The **Download a preset** path is broken. `downloadPreset` writes a progress record once and never polls — its own comment says so — and the verb is withheld while the row is "downloading", so it cannot be pressed again (`useConciergeController.ts:484,488`; `ConciergeCore.tsx:113`). The hub really starts the acquisition and answers a constant `{received: 0, total: 0}` with a receipt *kind* in the `jobId` field (`concierge_service.py:1797,1799`). See `fnd.concierge.download_never_finishes`.

### J4 — Have one meeting on the desk · **wired**, with a silent face

*Expected:* a meeting row with its length; no summary yet; no error.

`Record meeting` → `startRecording()` → `POST /api/meeting/start`, and a refusal is named with a retry (`ChairHome.tsx:2371`; `recordingSlice.ts:47,59`). Stop re-reads the desk and marks the new meeting (`recordingSlice.ts:63,82`). Import shares the normal persistence tail and refuses an empty upload by name (`holdspeak/web/routes/meeting_import.py:52,81`).

But the arrival never says a recording is running, and it has no Stop: `ChairHome` never reads the store's `recording` state, and the dock's key — which also opens the Live window — is the only Stop on the desk (`RecordOrb.tsx:62,64,70,72`). See `fnd.arrival.record_says_nothing`.

### J5 — Know where the summary will run · **wired**

*Expected:* the planned host, before the click.

`RouteDisclosure` draws the planned route beside the verb, before the click, on both faces (`ChairHome.tsx:2007`; `CatalogRail.tsx:243`). With no resolvable route the verb is withheld rather than disabled in place, and the disclosure says why (`ChairHome.tsx:2009`; `CatalogRail.tsx:179`). The route the face disclosed is the object the request binds (`ChairHome.tsx:2014`; `HistoryCore.tsx:296`).

### J6 — Get the summary · **broken** on the arrival

*Expected:* the host that DID run it; the summary text.

The run is wired: `postSummaryRun` → `POST /api/meetings/{id}/intelligence/run` → `request_intel_retry`, the hub's drainer is woken and its existence is reported honestly, and a 409 comes back as a refusal with its plain reason (`meeting_intel_service.py:160,194,202`; `ChairHome.tsx:736`).

The **result never reaches the arrival**. The Chair refreshes the desk once, immediately after the POST (`ChairHome.tsx:756`). Nothing refreshes it again: `intel_complete` and `intel_status` are consumed only by the Live window (`LiveCore.tsx:177`), and `desk_changed` — the one frame the desk re-reads on — is emitted for a meeting IMPORT and for nothing else on the meeting path (`meeting_service.py:289`). The Meetings window polls every three seconds for exactly this reason; the Chair does not (`HistoryCore.tsx:336`). See `fnd.arrival.summary_never_lands`, the top finding of this pass.

### J7 — Find it again after a restart · **wired** (the move count is not a static question)

*Expected:* the same summary in two moves or less.

The job and its artifacts are durable rows, not process state (`meeting_intel_service.py:185`). Shutdown stops every conductor the lifespan started, and a hub that does not own the database runs no scheduled work and says so (`web_server.py:1375,1389`; `runtime/ownership.py:140`). A deep-linked meeting is fetched from the record, not from a list cache (`HistoryCore.tsx:152`). **Two moves or less is an owner observation**; this pass cannot count moves.

### J8 — Type by voice into another app · **unverifiable-statically**

*Expected:* words at the cursor of the other app.

The chain exists: the default trigger is `alt_r`, displayed `⌥R` (`config/ui.py:15,16`); the listener is started by the web runtime outside the browser and an unavailable hotkey is recorded as a named runtime status (`web_runtime.py:514,528`); `_transcribe_and_type` is the one path from a released hotkey to delivered text (`runtime/dictation_capture.py`), under one delivery policy (`operation_policy.py`). Native keystrokes and other-application delivery cannot be inspected from source. The atlas already marks `case.j8.hotkey_option_r.other_app_delivery` **unreachable** for the rig.

### J9 — Open what the desk remembered · **wired**, with two broken neighbours

*Expected:* the Rhythm face opens; a doorless receipt shows no Open.

Both hold. The sweep's pipeline receipt is minted `resolved` with `detail_url "/cadence"`, and every other service gets an empty door (`db/projections.py:692,706`). The shade draws a verb only where a door exists, and the `/cadence` branch opens the Rhythm face (`SystemShade.tsx:192,194,199`; `applications.ts:191,193`). Acknowledge and Dismiss write through `PUT …/presentation` and then re-read both the list and the ambient set, so the face never keeps a state the hub refused (`projections.ts:134,143`).

Two neighbours are broken: a dictation-journal receipt's Open opens the Meetings window with a ref it cannot resolve (`fnd.shade.dictation_door_wrong_target`), and a dismissed card can never come back (`fnd.projections.dismiss_is_forever`).

### J10 — Get a brief, and another · **wired**, with two findings

*Expected:* the brief's own words stay after a reload; the RETURNED brief is the one DISPLAYED and it is retained.

`generateBrief` sets the face from the RETURNED brief and sets the receipt from it (`ChairHome.tsx:559,561`). The third branch keeps the section alive for a brief with nothing untriaged, with its headline and its receipt (`ChairHome.tsx:1136,1163`), which is the HS-202-02 fix for the sitting's defect. The producer returns an existing same-date brief unchanged (`monday_brief_service.py:197`).

Two findings sit on it: a failed read is drawn as "No brief yet" (`fnd.brief.unknown_drawn_as_absence`) and the face never says which day the brief is from although the route computes both labels (`fnd.brief.no_date_on_the_face`). The next-day variant is **unreachable** in the atlas: no mechanism in scope moves the producer's clock.

### J11 — Develop a thought · **wired**

*Expected:* a note, kept, with "Kept · time"; nothing hidden.

`Write a thought` mints the note (POST `/api/thoughts` refuses an empty raw_text, so it cannot start the job), adopts it through the same service the note pullout's Develop uses, and opens it; a refused create is named with a retry (`newThought.ts:27,45,38`). A thought-owned note routes to the Thought window by itself (`Pullout.tsx:123`). `Finish` joins a typed answer to the note first and then keeps, in one gesture (`ThoughtWorkspaceWindow.tsx:289,494`), and the foot states the filing status rather than a blank (`ThoughtWorkspaceWindow.tsx:486`).

*Ledger line, not filed as a finding:* the Thought window's foot reads `KEPT`, without a time. The ordinary inline editor reads `Kept · 3:42 PM` (`keptReceipt.ts:16`). The owner's expected result in story 01 says "Kept · time". The atlas's own predicate for this case is `text_contains "KEPT"`, so the case passes either way; the difference is recorded here for the council.

---

## GRAPH

`docs/internal/philo/graph/static-muaddib.json` — validates clean.

```
$ HOME=$(mktemp -d) uv run --extra dev python scripts/philo_graph_validate.py \
      docs/internal/philo/graph/static-muaddib.json
OK docs/internal/philo/graph/static-muaddib.json
```

(`uv run python …`, the command the lane brief prints, fails: `jsonschema` is declared only in the test and dev extras. Filed as `fnd.tooling.validator_needs_dev_extra`.)

The file is generated by a deterministic builder: two runs produce identical bytes (md5 `c6f861ff6f6fa167df93da1cc08c54eb` twice).

---

## COVERAGE

**Nodes: 1780.** edge 1658 · state 58 · interface 28 · action 28 · connection 8.
**Links: 138.** calls 44 · produces 41 · triggers 22 · presents 18 · renders 7 · reads 6.
**Cases: 69**, copied verbatim from the atlas — 67 applicable, 2 unreachable. By job: J1 8, J2 4, J3 8, J4 5, J5 2, J6 9, J7 2, J8 1, J9 9, J10 11, J11 3, beyond 7.
**Claim reviews: 13** — 9 verified, 2 contradicted, 2 unresolved.
**Findings: 15** — 11 product-defect, 2 tooling-debt, 2 doc-drift.
**Observations: 0.** A static pass has none.

**Deep trace.** All **38** edges the atlas names have a node and at least one typed link; 174 of the nodes are the hand-authored trace (edges, interfaces, connections, actions, states), the rest are the census. Faces traced control by control: the arrival/Chair, the SETUP row and `meetingPathBlocker`, the Concierge engine door, the Meetings review row and the summary face, the Desk-memory shade and the attention-drawer window, the BRIEF section, the Thought window and the note editor, and the first-value gate.

**Census (breadth, one node per edge, no links).**

| Family | Count | Exposure notes |
|---|---|---|
| Desk applications | 23 | active; 2 alias actions on top |
| Desk verbs (`verbRegistry`) | 52 | conditional (a ghost reason withholds them); 12 carry a key |
| Keyboard bindings | 12 | from the same registry, bound by `useKeymap` |
| Global hotkeys | 1 | `alt_r` / `⌥R`, outside the browser |
| WebSocket frame kinds | 44 | declared vocabulary; 1 (`wake_armed`) emitted without a consumer, named as a deliberate exception |
| Runtime timers and conductors | 7 | 6 active, 1 conditional (Cadence Engine, opt-in) |
| CLI commands | 29 | 20 top level + 9 sub-commands |
| MCP tools | 225 | integration exposure; every one anchored to its declaration |
| Connector inputs | 5 | gh, jira, confluence, meeting, calendar ingest — conditional |
| Engine-response boundaries | 3 | internal: extract, parse, validate |
| Production control sites | 1223 | 1037 active · 108 parked · 78 library-internal |
| — of those, library controls | 951 | Button 657, StringGadget 110, CycleGadget 39, CheckGadget 33, PadGadget 21, TransportKey 21, … |
| — of those, raw elements | 243 | **183 on active faces, in 58 files** → `fnd.faces.raw_controls_outside_the_library` |
| — unclassified owner | 29 | recorded as unclassified rather than guessed |
| HTTP surface | 569 paths / 665 operations | one census node; the traced routes carry their own nodes |

A control site and a semantic edge can both exist for the same button (for example `Run summary` has `edge.face.arrival_run_intel` and an `edge.ui.…` census node). Do not add the two columns.

**Exercised: 0 of 67 applicable cases.** A static pass exercises nothing. Every case is `not-run` for this pass.

---

## FINDINGS

Ranked by what it costs the owner on a Tuesday. Full evidence in `static-muaddib.json`.

| # | ID | Bin | What it costs him |
|---|---|---|---|
| 1 | `fnd.arrival.summary_never_lands` | product-defect | He presses Run summary on the arrival and the row keeps saying QUEUED. The summary is really written; he cannot see it without reloading or opening another window. This is J6, the job the sitting is about. |
| 2 | `fnd.capture.recovery_has_no_face` | product-defect | A meeting degrades mid-recording. The desk says audio may be lost and offers neither of the two actions its own producer names. `POST /api/meetings/{id}/capture/recover` has no caller in the web, the CLI or MCP. |
| 3 | `fnd.arrival.talk_key_drops_words` | product-defect | The Talk key on his arrival transcribes and throws the words away: `handleMicText` is empty, and `pipeline: true` is a server-side processing flag, not a delivery. No text, no note, no refusal. |
| 4 | `fnd.concierge.download_never_finishes` | product-defect | Download a preset engine → `0 B / 3.9 GB` for ever, no poll, no completion, and the verb is replaced by the frozen token so it cannot be retried. |
| 5 | `fnd.projections.dismiss_is_forever` | product-defect | One stray Dismiss and the card is gone for good: no face calls `restore`, no face asks for `include_dismissed`. He learns not to press Dismiss. |
| 6 | `fnd.shade.dictation_door_wrong_target` | product-defect | A "Dictation needs review" row's Open opens the **Meetings** window with a `project:` ref it silently ignores. |
| 7 | `fnd.brief.unknown_drawn_as_absence` | product-defect | A failed brief read is drawn as "No brief yet" — the opposite of the rule the SETUP row keeps two hundred lines earlier. He then generates over a brief that may exist. |
| 8 | `fnd.brief.no_date_on_the_face` | product-defect | The BRIEF section never says which day the brief is from, although the route computes `period_label` and `generated_label` on every read. `get_latest` does not filter by date. |
| 9 | `fnd.arrival.record_says_nothing` | product-defect | `Record meeting` on the arrival changes nothing on the arrival, and does not open the Live window the dock's key opens. Two doors, one job, two behaviours. |
| 10 | `fnd.desk_memory.one_name_three_faces` | product-defect | "Desk memory" is the dock launcher (the shade), the shade's own verb (Project memory), and a third window with the receipt detail. One name, three faces. |
| 11 | `fnd.faces.raw_controls_outside_the_library` | product-defect | 183 raw controls on active faces, in 58 files. They do not wear the library's states; the owner's standing ruling calls a raw control a bounce. |
| 12 | `fnd.atlas.placeholder_triggers` | tooling-debt | Five atlas cases would be fired by clicking `main.chair` instead of the verb they name (`j9.shade_receipt_open`, `j9.shade_open.door_stale`, `j9.shade_acknowledge`, `j9.shade_dismiss`, `j11.thought_keep`); one also FILLS `main.chair` with text. A live pass would record a verdict about a gesture that never happened. **This must be paid before story 04/05.** |
| 13 | `fnd.tooling.validator_needs_dev_extra` | tooling-debt | The documented validator command does not run in a default environment. |
| 14 | `fnd.docs.desk_changed_comment_drift` | doc-drift | `useDeskChangedRefresh` says meeting writes emit no `desk_changed` frame; the import path emits one. |
| 15 | `fnd.docs.model_assignment_exposure` | doc-drift | `model.assignment` is recorded `exposure: operator`, `status: internal`, surfaces "model assignment settings" — it is in fact what his first screen asks him for, written by a user verb in Models. |

The top ten for the council are rows 1–10.

---

## ORPHANS

Classified against declared exposure and execution ownership (brief §2), not against "has a button".

- **`POST /api/meetings/{meeting_id}/capture/recover` — a true orphan.** No caller in `web/src`, in `holdspeak/main.py` or in the MCP tool list. Its state is produced by a real producer and its attention row promises the action. Filed as finding 2.
- **`present(id, "restore")` — an orphan branch.** The repository, the service and the store's own type all support it; no production caller exists. Filed as finding 5.
- **The attention-drawer window ("Desk memory") — conditional, not orphaned.** Its only pointer entry is the RAILS belt's attention chip, drawn only when the ambient count is above zero (`MissionControlConveyor.tsx:638`), plus a voice intent on the GL stage (`web/src/desk/gl/WorldStage.tsx:230`). Reachable, but by a door most owners will not find. Named in finding 10.
- **Ten registry verbs with an empty `run` — NOT dead verbs.** `thread.keep`, `.fork`, `.stop`, `.new`, `.mode`, `.prompt`, `.tools`, `.todo`, `.compact`, `.guardrail` (`verbRegistry.ts:698–781`) all carry `palette: false` and are executed by `ThreadComposer`'s slash commands, which map each id to its own handler (`ThreadComposer.tsx:89–100`). Execution ownership sits outside the registry, exactly as the Phase 1 record says. No finding.
- **225 MCP tools and 29 CLI commands with no face — correct.** Integration and operator exposure; an internal capability needs no button.
- **108 control sites under `_parked/` — correct.** A parked surface is not an active edge.
- **`wake_armed`, emitted with no consumer — correct.** A named, deliberate exception in `realtime_frames.py`.
- **The Live window's `capture_recovery` subscription — a half-orphan.** It consumes the frame and drops the `actions` the frame carries. Counted inside finding 2, not separately.

---

## UNKNOWN

What this pass could **not** settle, and what that does to the verdicts.

1. **Nothing was executed.** Every verdict above is a source-inspection verdict. "Wired" means the chain closes in the tree; it is not a claim that it runs. No JOBS verdict is pass or fail.
2. **J7's "two moves or less" is an owner observation.** The retention is durable in source; the move count cannot be inspected.
3. **J8 is unverifiable statically** and is already unreachable for the rig: native hotkey, native keystrokes, other-application delivery.
4. **J1's voice branch needs a READY speech assignment on a fresh desk.** Whether the migrated `speech-…` profile resolves as ready was not settled; it is a live-pass question and the atlas's own precondition says so.
5. **Semantic quality is out of scope.** Whether a generated summary or brief is *useful* is the owner's verdict, not a static one (brief §5).
6. **The command deck was not traced.** `desk.execute`'s claim review names it as a limit; the window menu, floor menu and keyboard were traced.
7. **`inference_targets.resolve_placement` was not traced deeply**, so `cr.model_destination_readiness.limitations` stays *unresolved*: two different notions of readiness (a configuration projection and a live endpoint read) sit under one record, and which the record means is a council question.
8. **`cr.voice_delivery.surfaces` stays unresolved.** Whether the arrival's transport key is a fourth surface of `voice.delivery` or a defect in its caller is a council question; the defect itself is filed as finding 3.
9. **Path drift in the lane brief, recorded, not filed.** The lane brief names `web/src/pages/cores/ConciergeCore.tsx` and the file is `web/src/features/concierge/ConciergeCore.tsx`. `CatalogRail.tsx`, `SystemShade.tsx`, `AttentionDrawer.tsx`, `NoteEditor.tsx` and `FirstWords.tsx` are where the brief says, or one directory away. Nothing was skipped.
10. **The census is a census.** 1223 control sites, 225 MCP tools, 44 frame kinds, 665 HTTP operations: these are counts of declared entry points at this revision, not claims that each one works. The raw-vs-library classification is by the nearest opening tag, which is a heuristic; 29 sites were left **unclassified** rather than guessed.
11. **Sealing held.** `../wt-philo-2-03`, `audit/philo-2-03-*` and any `static-astra.*` were not read. Every `positions.astra` in the findings says "not recorded"; none was invented.
