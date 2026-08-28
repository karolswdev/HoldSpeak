# HS-144-06 — Cold walk and close implementation plan

**Planning basis:** committed code at `f37704b1877196c8a40aa36221922a0fe8b10783`; dirty phase-144 docs and shot assets were deliberately not used as code evidence.  The charter is [story-06-walk-and-close.md](../story-06-walk-and-close.md); the settled design and carried ledger are in [current-phase-status.md](../current-phase-status.md).  This plan does not amend either.

## 1. Obligation register → execution slices

| Obligation | Required proof | Existing proof that may be retained | HS-144-06 slice |
|---|---|---|---|
| 1. Cold First Sentence; first capture/transcript within 3 minutes | Fresh, isolated hub starts on the one-job First Sentence surface; no Door/chrome leaks; the lawful first-value outcome is recorded with timing | `test_hs144_door_glass.py:245-270` proves the untouched one-job cold surface only | A — cold boot and first-value truth |
| 2. Reveal lands on a truthful Door | After the first-value handoff, real source-owned fixture records make board, rail, and count labels agree with `GET /api/door` | Board/content/count geometry in `test_hs144_door_glass.py:275-429`; rail chronology in `:480-570` | B — production-source reveal and wide/narrow/200% capture |
| 3. Card completes; receipt within 500 ms | A real Door verb changes authoritative state; visual evidence must match the settled receipt grammar and time assertion | Success action/removal is covered at `:368-381`; only a **failure** receipt is covered at `:383-398` | C — resolve receipt semantics, then time a real click-to-observable completion |
| 4. In-world schedule creation | Door rail opens its own form; a submitted schedule appears on the Door rail | `:575-618` covers open/cancel/create/rail round trip | D — repeat through the reusable walk and include in click-depth/captures |
| 5. ICS feed through Settings; egress fact | Settings owns the actual subscription input; actual parsed fixture event appears in the rail; the exact subscription transport shows its factual egress badge | Local-file settings/API → production conductor → rail at `:188-225`, `:521-545`; Settings’s HTTPS fact at `:659-720` | E — connected Settings → fixture reader → rail flow, with separately scoped egress assertion |
| 6. Click-depth delta | Auditable table: tasks `0` vs `1`; upcoming `0` vs `1+`; open schedule creation `≤1` vs `2` | Audit B table at `assets/audit-b-front-door-walk.md:89-99` is the before measurement | F — instrumented interaction ledger and generated table |
| 7. Doorframe survives | 393px Go menu opens a real registered app; `/meetings` always reaches its registered surface from independent fresh documents | Go test `:621-654`; 15 desktop deep-link arrivals `:724-766` | G — rerun both in this walk at applicable viewports, including deterministic fresh-context deep links |
| Before/after owner review | Named before/after manifest, desktop and narrow pairs, plus 200% evidence; owner sees the pairs before any merge word; beauty verdict and Tuesday answer are recorded | Before pictures are in `assets/audit-b-shots/`; current phase shots exist, but are not the close walk | H — artifact manifest, hashes, pair board, owner handoff |
| Full sweep and close record | Detached isolated-HOME full sweep, baseline-exact triage, evidence capture, status/README updates, terminal summary, clean `dw check` | Each completed story has a sweep/triage precedent | I — full sweep, ledger consolidation, final summary, phase close |

The implementation is deliberately one **reusable standalone script** plus retained pytest regressions, not a new monolithic test-only rig.  Proposed new tracked harness: `scripts/door_walk_hs144.py`; proposed durable artifacts: `pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/walk/`.  The script must return non-zero when any required assertion fails and must print one stable PASS/FAIL table, timing values, click ledger, SHA-256 shot manifest, cleanup report, and artifact paths.

## 2. Verified inventory: what exists versus what the cold walk adds

### Existing `test_hs144_door_glass.py`

| Walk concern | What the existing e2e genuinely proves | Why the close harness still adds it / what is absent |
|---|---|---|
| Fresh First Sentence | A fresh temporary HOME starts at `chair-first-value`, shows `Dictate one sentence` and `Continue later`, and renders no `.door-board-section` (`:245-270`). | No mic/capture attempt, no transcript or typed-fallback custody, no elapsed time, and no reusable standalone output/cleanup transcript. |
| Door board/counted reveal | Real HTTP authorities produce action items, a Thought, and schedule (`:91-170`); scoped board columns/count labels and source facts are asserted (`:299-325`). | The seeding/reload happens after an automated normal-Chair dismissal; it is not a recorded cold-first-value → reveal story, and it does not emit a before/after manifest. |
| Rail data | Schedule-only and mixed calendar/schedule chronology, row source attributes, location, and meeting link are asserted (`:480-570`). | No linked before/after report or click-depth ledger. |
| Completing a card | A true Door descriptor sends the production completion route, detaches the card, and is checked through `GET /api/door` (`:368-381`). | No success receipt is rendered or measured.  The later receipt assertion is intentionally a stale `HTTP 409` failure receipt (`:383-398`), not a completion-success receipt. |
| Door schedule form | Door’s `Schedule recording` opens the in-world form, cancellation writes nothing, form submission creates a schedule, and the rail refreshes (`:575-618`). | No interaction-count measurement and no standalone artifact/cold-walk transcript. |
| Calendar | `_seed_calendar_fixture_via_settings` writes a local ICS subscription through the Settings HTTP authority, calls the real production conductor, and checks the actual Door aggregate (`:188-225`).  A separate glass test enters a syntactically valid HTTPS subscription, opens the actual Settings module, and scopes the egress text to Settings (`:659-720`). | It does **not** drive the settings form itself into a fixture then demonstrate the rail and the Settings egress fact as one documented end-to-end leg.  A local file correctly has `egress: false`; the current HTTPS badge test deliberately does not fetch a fixture. |
| Narrow Go and deep link | Go at `393px` opens Meetings (`:621-654`).  Fifteen independent `/meetings` documents wait for registry state then visible Meetings (`:724-766`). | The deep-link repeat is desktop-only, and neither result is in the requested reusable cold-walk report. |
| 200% review and overflow | Board test uses `720×450` CSS viewport at DSF 2, asserts focus/cleanliness, and makes `door-populated-1440-zoom200.png` (`:406-423`).  Rail test follows the same convention (`:547-566`). | The close walk must include its own final visual evidence, pair manifest, and cross-leg console/overflow checks. |

### Established harness precedent to follow

Use the **Phase 138 People walk** as the primary shape, not the old hard-coded Phase 129 endpoint:

- `scripts/people_walk_full.py:47-63` imports the reusable hub/shooter/reporting primitives; `:694-729` makes cleanup explicit and prints what it removes; `:905-924` gives a stable, failable summary.  Its two-mode treatment (`:735-816`, `:821-902`) is the correct precedent if an attended actual-mic addendum is later approved.
- `scripts/chair_walk.py:66-132` provides the real child-hub lifecycle under an isolated HOME; `:145-190` captures page errors, console errors, shots, and controlled navigation.  The new harness should reuse those reporting conventions but provide a **cold, unseeded serve mode**; `chair_walk.Hub` itself starts the seeded Phase-132 server and therefore cannot be used unchanged for leg 1.
- `scripts/walk_one_admission_path.py:124-144` is the isolation precedent: construct `HOME`, `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, and `TMPDIR`, strip inherited token/credential variables, and pass that environment only to the child leg.  Its per-leg result record at `:202-256` is the model for a content-free timing/result row.
- `scripts/walk-129.mjs:54-66, 491-502` is the useful assertion/reporting precedent: collect explicit violations and exit non-zero; `:426-474` shows separate narrow contexts rather than resizing a polluted desktop context.  Do **not** copy its fixed URL/token or its broad, unscoped selectors.

## 3. Slice A — cold boot and the First-Value truth

### Cold server and state rules

1. `door_walk_hs144.py serve` boots a genuine `MeetingWebServer` in a child process under a newly-created walk HOME.  It must not call `DeskService.seed()` before the first browser navigation, must bind only loopback, and must print `HOME=…`, `XDG_CONFIG_HOME=…`, `XDG_DATA_HOME=…`, `TMPDIR=…`, port, PID, and masked fixed walk-token label.
2. The parent creates the HOME and all XDG/TMP children before boot; it removes inherited HoldSpeak token/profile-key variables, as Phase 131 does.  It also gives any child which can invoke macOS credential APIs the same HOME.  This Door walk has no lawful Keychain operation, so it must not create or touch the owner’s login Keychain.  If a future extension introduces one, use the explicit walk-scoped keychain setup/teardown pattern in `scripts/people_walk_full.py:103-137, 694-729`, never the owner keychain.
3. Start from a new browser context, navigate to `/?token=…`, and scope all assertions to `[data-testid="chair-first-value"]` / `.desk-first-words`: heading, editable text pad, `Click to speak`, and continue verb must coexist; Desk chrome and `.door-board-section` must not exist.  Capture `cold-first-value-{1440,393}.png` before anything creates Door data.
4. Capture console/page errors per context, assert no body/document horizontal overflow, and fail on an unexpected dialog or a fake fallback state.  Do not satisfy a first-value assertion with a similarly named element behind an open surface.

### Model-less reality and the 3-minute claim

The committed cold hub has no transcription callback in the harness pattern.  `MeetingWebServer` instances constructed in `test_hs144_door_glass.py:68-88` and `scripts/walk_working_desk.py:333-352` do not supply `on_transcribe`.  The production stream route consequently returns the named `transcription_unavailable` refusal when `ctx.on_transcribe is None` (`holdspeak/web/routes/system/voice_stream.py:134-144`).  A fresh HOME also has no configured/downloaded local transcription model.  It is therefore false to claim that an automated, model-less fresh cold hub can yield a real spoken transcript.

The harness must make this distinction visible rather than mocking an answer:

- **Required cold proof:** first sentence is untouched and is the only job; invoking the control may produce the named unavailable path (when browser mic capability can be controlled), and the owner can type the text into the real editable FirstWords pad, use the real `Keep as Note`/handoff path, and observe the resulting real note/Desk reveal.  Start a monotonic clock immediately before the first real capture interaction (or typed fallback entry, depending on the resolved scope); stop only once the visible field contains the text and custody/handoff is confirmed.  Report `first_value_mode=typed_fallback` or `named_unavailable`, never `dictation_success`.
- **What not to do:** no `on_transcribe=lambda: "fixture transcript"`, no direct projection-table insert, no test-only DOM fill presented as speech, and no bound that claims microphone-to-transcript success without an actual configured model and real audio source.
- **Optional attended metal addendum only if explicitly ordered:** isolated HOME plus an explicitly configured real local/LAN model and an owner-visible microphone action; record model/source and actual spoken result separately.  It is a capability proof, not the model-less cold default, and must not silently borrow the owner’s config/model credentials.

> **[ORCH-CALL 1 — recommend amend the interpretation of leg 1.]** Treat the current automated cold leg as **First Value to visible, editable text/custody within 3 minutes using the honest typed fallback** plus the named model-less refusal if exerciseable.  Do not certify “visible transcript ≤3 min” on the model-less fresh hub.  If the exact spoken-transcript wording is non-negotiable, authorize a separately labeled attended real-model leg and state its model provenance; otherwise change the close evidence wording to “first capture/fallback text visible ≤3 min.”

After the cold assertion/capture, the real `Continue later` or typed `Keep as Note` path is the only permitted browser transition to normal Chair/Door state.  Then populate the remaining test data only through existing production HTTP/UI authorities (as the existing glass test does), reload normally, and begin slice B.  The data is synthetic but true: it exists in the isolated real database, is read through `/api/door`, and must never be called owner data.

## 4. Slice B–G — failable walked legs

### B. Truthful reveal and capture matrix

Create a fixed, labelled fixture set through production authorities only:

- four action-item lanes (overdue/now/waiting/unassigned), one unfinished Thought, one schedule, and one calendar event;
- source IDs/titles deliberately distinctive and checked both in `GET /api/door` and inside the owning DOM containers;
- no direct SQL against `action_items`, `calendar_events`, or Door projections.

On reveal, assert **all** of the following in conjunction:

1. `.door-board-section` owns the summary and all named board columns;
2. each named `.door-board-column` contains its expected card and its own count label, while the unassigned column remains truthfully countless if the aggregate does not expose one;
3. the `.door-upcoming-rail` contains each expected source-labelled row in chronology;
4. `GET /api/door` is the exact source of the expected count values and source IDs; and
5. source cards are absent from unrelated retained lanes where the Door contract says they must not be duplicated.

Use one fresh browser context for each `1440×900` and `393×852` final capture and the project’s existing 200% convention (`720×450` CSS viewport, device scale factor 2) in another fresh context.  At each width assert console/page cleanliness and no document/body horizontal overflow; preserve intentional board-viewport horizontal scroll at narrow width as a container-scoped exception, not a body overflow exemption.

### C. completion timing and receipt mismatch

For whichever genuinely actionable fixture card has the simple `Done` descriptor:

1. Locate the exact card within its named owning board column; assert the actual production `/api/door` descriptor exposes the verb before clicking.
2. In the page immediately before the real Playwright click, store a `performance.now()` mark.  After the target observable occurs, read the same page clock.  This measures UI-to-UI elapsed time, not Python scheduling or assertion polling.
3. Assert both the authoritative state (real API response/next Door projection has the card gone or changed) **and** the scoped visual observable.  Write raw timestamps and `elapsed_ms` to the walk JSON and console report; `elapsed_ms <= 500` is a hard failure only after the receipt semantic is settled.

There is a material conflict to resolve before an implementation writes an impossible test.  `useWriteReceipt` deliberately renders **only failures** and clears success (`web/src/desk/hooks/useWriteReceipt.ts:1-8, 120-151`); Door simply reloads after a successful action (`DoorBoardLane.tsx:296-310`).  The completion endpoint returns `{card_id, verb, loop_ids, commitment_ids}`, not a displayed receipt (`holdspeak/services/follow_through_service.py:412-417`).  The current glass test correctly proves a stale **failure** receipt, not a success receipt.

> **[ORCH-CALL 2 — recommend preserve the settled quiet-success grammar.]** Amend the leg to: “a card completes from the board and its authoritative Door update is visible within 500 ms; a named in-place receipt remains proven on the refusal path.”  Retain/add a ≤500 ms success projection timing assertion and retain the existing 409 receipt regression.  If the charter instead requires a success receipt visibly on glass, that is a product behavior change contrary to Story 06’s no-feature close scope and must be explicitly amended into scope before coding.

### D. in-world schedule

From the scoped `.door-upcoming-rail`, click the actual `Schedule recording` affordance, prove its in-world form/voice-enabled title field, fill it through the browser, submit, and wait for that exact title in the same rail.  Verify the schedule from the production list authority too.  Take a screenshot after the rail update.  Do not satisfy this leg by the fixture’s pre-created schedule; use a separate schedule title for this interaction.

### E. Settings-fed ICS and egress badge

Implement this as two deliberately connected, honestly scoped subassertions:

1. **Actual feed:** write an RFC-like ICS fixture in the walk temp area, open Settings through its registered UI, select Meetings, fill the real Calendar subscription control with that path, and save through the UI.  Trigger the real `CalendarIngestConductor.refresh()` against that saved configuration (never write `calendar_events` directly), reload Door, then AND-assert the expected event title/source/order inside `.door-upcoming-rail` and the aggregate response.
2. **Egress fact:** in a fresh Settings presentation, set a valid HTTPS source and assert the Settings-owned egress fact/badge is scoped to the subscription control/Meetings settings container, not the always-present global chrome badge.  Then restore the local fixture configuration before cleanup.  The report must call this a **transport fact**, not claim the local file fixture was egress.

> **[ORCH-CALL 3 — recommend the simple truthful two-subassertion method.]** A local fixture correctly has no egress; an HTTPS fact has an egress badge but cannot be fetched as the local file.  Keep both facts in the same named leg but do not misrepresent them as one source.  If one exact subscription must both fetch a fixture and display the badge, approve a loopback TLS fixture server with an ephemeral certificate trusted only by the walk child; report it as `https://127.0.0.1:<port>` (transport classified as egress, network physically loopback), clean certificate/server/home in the printed cleanup, and never contact a real calendar.

### F. click-depth measurement

The reference measurements are exactly Audit B’s Chair-state table (`assets/audit-b-front-door-walk.md:89-99`), not a reconstructed guess.  The after measure starts **after** first-value handoff, fixture creation, Door reload, and settled rendering—the same navigable front-door state from which Audit B measured.  It does not count setup/fixture writes or the first-value gate.

Make a tiny `ClickLedger` in the harness with these rules:

- The three measurement blocks may call browser `.click()` only via `ledger.click(locator, label)`, which increments and records label/selector/time.  Queries, waits, API comparisons, reloads, keyboard focus checks, and screenshots do not increment the ledger.
- Enforce this structurally in the harness: the measurement helper receives the ledger and has no raw locator `.click()` calls.  Print JSON and Markdown rows including baseline path, start condition, every recorded click, final evidence selector, and result.
- **Tasks:** immediately assert the scoped Door board/card/count source from the settled Door; ledger stays `0` (baseline `1`).
- **Upcoming:** immediately assert the scoped rail/source row; ledger stays `0` (baseline `1+`).
- **Schedule create reachability:** from that same settled Door, invoke only `ledger.click(rail.get_by_role("button", name="Schedule recording"), ...)`, then assert the form is visible; ledger is `1` (baseline `2`; acceptance `≤1`).  Form submission is an independent write in slice D and must not be hidden in this reachability metric.

Fail if a claim is satisfied by an element outside its owner container, if a count is inferred rather than asserted, or if the interaction log conflicts with the row.  This makes `0` a documented absence of route clicks, not an untestable claim that no human action ever occurred.

### G. doorframe repair regression

- At `393×852`, scope `Go` to the visible Desk chrome button, open it, scope the menu to `role=menu[name="Go menu"]`, assert `Meetings` exists, activate it, and assert `#surface-meetings` is visible.  Capture this exact repair state.
- For `/meetings`, use fresh documents (not retry loops) and wait for `[data-surface-registry-state="registered"]` before asserting visible `#surface-meetings`.  Run the existing 15 independent-arrival strength at desktop; add a narrow fresh arrival to show the repair did not depend on width.  Report every ordinal/viewport/route/result, fail first missing surface, and retain console checks.

## 5. Assertion honesty and visual-pair protocol

### Required assertion law

Every leg must use conjunctive, owner-container assertions.  Examples of prohibited substitutions:

- a global `get_by_text("Meeting link")` for a rail-row assertion;
- any `.egress-badge` for the calendar egress assertion when Desk chrome has a global egress badge;
- a card text match without first scoping the named Door column;
- an API-only source check without its owning glass element, or vice versa.

Attach a one-line `assertion_scope` explanation to each walk report row.  Do not turn a known allowed `.door-board-viewport` narrow overflow into a blanket page-overflow waiver.

### Pair manifest and hash guard

Create `assets/walk/pairs.json` and a concise `assets/walk/pairs.md`; each row names: audit-before path, new-after path, viewport/mode, state, the exact claim, assertion IDs, SHA-256(before), SHA-256(after), expected byte relationship, and owner-review status.  Start with these required pairs:

| Before (Audit B) | After (close walk) | Relation / claim |
|---|---|---|
| `assets/audit-b-shots/chair-home-1440.png` | `assets/walk/door-populated-1440.png` | `different`: Chair’s scattered lanes → populated Door board + upcoming rail |
| `assets/audit-b-shots/chair-home-393.png` | `assets/walk/door-populated-393.png` | `different`: same Door claim at narrow width, including usable Go separately |
| `assets/audit-b-shots/cadence-surface-1440.png` | `assets/walk/door-schedule-form-1440.png` | `different`: schedule create begins on the Door rather than by opening Cadence |
| `assets/audit-b-shots/cadence-surface-393.png` | `assets/walk/door-schedule-form-393.png` | `different`: narrow version of the same reachability claim |
| `assets/audit-b-shots/first-value-capture-1440.png` | `assets/walk/cold-first-value-1440.png` | `parity`, not an improvement claim: First Sentence remains one job |
| `assets/audit-b-shots/first-value-capture-393.png` | `assets/walk/cold-first-value-393.png` | `parity`, not an improvement claim: First Sentence remains one job |

Add standalone 200% shots (`door-populated-zoom200.png`, rail, and keyboard-focus state) to the manifest as **accessibility evidence**, explicitly marked `no comparable Audit-B 200% before`.  Do not invent a before pair where none exists.

For every `different` row, equal SHA-256 bytes is a hard false-positive tell: fail with “claimed changed pair is byte-identical; inspect state/paths.”  Hash inequality is only a tripwire, never visual proof; the scoped assertions and human pair review supply the proof.  For a `parity` First Sentence row, byte equality may be noted but is not required because clock/render timing can vary; never label equal bytes “the Door changed.”

> **[ORCH-CALL 4 — recommend manifest-driven pair review.]** Treat 1440 and 393 as true before/after pairs and 200% as a separately named final accessibility set because Audit B has no 200% before image.  Require owner review of `pairs.md`/images before any merge word; record `beauty verdict` and answer the exact Tuesday question in evidence.  Do not create a visually similar but semantically unpaired 200% “before/after” claim.

## 6. Harness form, artifacts, and cleanup

> **[ORCH-CALL 5 — recommend a standalone script with pytest retained.]** Ship `scripts/door_walk_hs144.py`, not a second `tests/e2e` class.  The charter expressly requires a reusable `scripts/` walk; a script can own child process lifecycle, temp HOME/XDG/keychain/TLS cleanup, report/shot manifest, click ledger, owner-readable tables, and an optional `--only` leg interface.  Keep `tests/e2e/test_hs144_door_glass.py` as fast regression coverage and call its focused subset before the script; do not delete or weaken it.

Suggested CLI:

```text
uv run python scripts/door_walk_hs144.py \
  --out pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/walk \
  --only cold --only reveal --only completion --only schedule --only calendar \
  --only click-depth --only doorframe
```

The default should run every leg; `--only` is for diagnosis only and must say “partial walk” in the report.  Artifacts include:

```text
assets/walk/
  report.json                 # machine-readable legs, timings, click ledger, hashes
  report.md                   # PASS/FAIL/finding summary and exact scope notes
  pairs.json
  pairs.md
  cold-first-value-1440.png
  cold-first-value-393.png
  door-populated-1440.png
  door-populated-393.png
  door-populated-zoom200.png
  door-schedule-form-1440.png
  door-schedule-form-393.png
  door-calendar-rail-1440.png
  go-menu-393.png
  meetings-deep-link-*.png
```

Use unique run-local scratch paths beneath the current session scratch directory or a `mktemp -d` directory; never use the repository’s `assets/audit-b-shots/` as a writable output.  The `finally`/signal cleanup must:

1. stop the hub and any TLS fixture process and report PID/exit result;
2. remove only the run-created HOME, XDG/TMP trees, local ICS/TLS fixtures, and walk-scoped keychain if one was explicitly created;
3. preserve committed audit shots and the durable `assets/walk/` evidence outputs;
4. print every path it deletes and a final `cleanup=pass|fail` record; and
5. leave a failed run’s report/artifacts intact for diagnosis while still reaping processes and private state.

## 7. Slice I — full sweep, ledger, and phase close

### Full-sweep procedure

1. Run the detached full suite from the final candidate tree with a fresh isolated HOME and `-n auto`, excluding only `tests/e2e/test_metal.py` as project law requires.
2. Save/read the complete raw output before writing the evidence/triage verdict.  The `dw evidence capture` result is expected to exit `1` while the inherited baseline persists; it is still the lawful captured record.  Never call that result “green.”
3. Compare failing node IDs to `pm/roadmap/holdspeak/phase-143-intelligence-router/assets/story-08-inherited-failure-baseline.txt`.  The required verdict is **baseline-exact, zero branch-new**.
4. For every non-baseline failure, run the exact node serially twice under isolated HOME.  Both green means a named flake family only where history supports it; any red rerun is REAL and must be fixed before the Story 06 flip.  The following two are carried watch items, not automatic flake exemptions:
   - `tests/unit/test_phase143_inference_capability_census.py::test_phase143_call_site_fixture_is_complete_and_fail_closed` — first observed in Story 02, serial-green and absent in Story 03; still record recurrence and diagnose before casually relabelling it.
   - `tests/unit/test_calendar_ingest_conductor.py::test_boot_and_tick_contain_fetch_and_parse_failures` — Story 04 xdist timing watch item, serial-green twice; recurrence requires diagnosis.
5. The prior `test_hs141_thought_workbench_glass[1440]` / assignments glass behavior may be named family context, but does not supersede the explicit baseline comparison or the two named watch rules.
6. The glass suite overwrites Phase 141 PNG assets.  Before every full sweep, snapshot any pre-existing diff for the known Phase-141 asset directories (`phase-141-from-thought-to-work/assets/story-04`, `story-05`, `story-05a`); after the run restore the generated PNGs to the pre-sweep state, then re-apply any user pre-existing binary diff.  Print the pre/post asset status and never overwrite a pre-existing dirty file blindly.

### Carried-ledger consolidation

The final summary and status-doc closeout must preserve these exact, named items; none becomes “fixed” merely because a closing sweep passes:

| Carried item | Current honest disposition | Required close record |
|---|---|---|
| Story 01 `_active_thoughts` pagination race | Theoretical non-advancing cursor under concurrent mid-pagination write; outside YOLO bar | Carry as open theoretical ledger note; owner/candidate future owner named |
| Story 02 calendar conductor double-start | Theoretical single-call-site/reachability concern | Carry open; no invented reproduction or fix claim |
| Story 02 sleeping calendar conductor when unconfigured | Consistent sibling-conductor pattern | Carry open; record it separately from double-start |
| Scheduled-recording conductor shutdown gap | Pre-existing, beyond the ruled one-line Story-02 boundary; no lifecycle pattern | Carry open as product gap, not a Door regression |
| Calendar trust-destinations registry gap | Central registry lacks a calendar-fetch entry; docs must state truth, not add a fake entry | Carry open and owner-visible |
| Xdist watch 1 | Inference-capability census, as named above | Record final sweep occurrence/non-occurrence and serial diagnosis if it recurs |
| Xdist watch 2 | Calendar conductor boot/tick test, as named above | Record final sweep occurrence/non-occurrence and serial diagnosis if it recurs |

### `final-summary.md` skeleton and actual DW requirements

Delivery Workbench does **not** validate mandatory prose sections inside a final summary.  Its actual structural rule is: once all story rows are done, `final-summary.md` must exist (`.githooks/dw_pmo/validate.py:192-194`).  `dw phase close` refuses an open story row (`.githooks/dw_pmo/mutations.py:393-406`) and renders only the required terminal header/status/date plus supplied body (`.githooks/dw_pmo/render.py:144-152`).  Therefore do not claim that `dw check` demands a particular “Proof” or “Pointers” heading.

Use this project-quality body skeleton after all six story rows are done and before final `dw check`:

```markdown
## What shipped
- Dashboard Door outcome in one factual paragraph: board, rail, ICS-first integration,
  schedule entry, and doorframe repairs; explicitly say First Sentence was retained.

## Outcome against exit criteria
- Cold-walk verdict and exact first-value scope/mode.
- Seven-leg table: pass/fail, elapsed `first_value_ms` / `completion_ms`, click-depth deltas.
- Before/after owner review, beauty verdict, and Tuesday answer.
- Full sweep result: exact counts, inherited-baseline comparison, branch-new verdict.

## Proof and artifacts
- `evidence-story-01.md` through `evidence-story-06.md`.
- `assets/walk/report.md`, `report.json`, pair manifest, and specific shot directory.
- The reusable `scripts/door_walk_hs144.py` command and focused regression command.

## Judgment calls / carried ledger
- The five carried product/race/trust items and both xdist watch items, with their
  current dispositions; no erased ledger entries.
- Any resolved [ORCH-CALL] wording, including the receipt and first-value decisions.

## Owner handoff
- Owner shot-review status and the explicit rule that no merge word preceded the nod.
- Pointers to `current-phase-status.md`, phase README/status updates, and next owner decision.
```

Write the final file through `dw phase close holdspeak 144 --from-file …` so the terminal header, project README phase status, and gate behavior stay canonical.  Update the phase status document’s 6/6 row/Where-we-are and the project README’s Last updated line as the operating cadence requires, then run `dw check holdspeak`.  The current unrelated Phase 101 checker error must be reported separately if still present; do not disguise it as a Phase 144 failure.

## 8. Focused commands and environment-ordering law

All commands below preserve the owner browser cache **before** replacing `HOME`.  Do not write `HOME="$(mktemp -d)" PLAYWRIGHT_BROWSERS_PATH="$HOME/…"`: after HOME changes, that points at an empty browser cache and makes a false infrastructure failure.

### Focused e2e regression

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME_REAL="$HOME"
PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright"
HOME="$(mktemp -d)"
export HOME PLAYWRIGHT_BROWSERS_PATH
trap 'rm -rf "$HOME"' EXIT
uv run pytest -q -n auto tests/e2e/test_hs144_door_glass.py
```

### Reusable cold walk

```bash
cd /Users/karol/dev/tools/HoldSpeak
HOME_REAL="$HOME"
PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright"
HOME="$(mktemp -d)"
export HOME PLAYWRIGHT_BROWSERS_PATH
trap 'rm -rf "$HOME"' EXIT
uv run python scripts/door_walk_hs144.py \
  --out pm/roadmap/holdspeak/phase-144-the-dashboard-door/assets/walk
```

The harness must make its own child HOME/XDG sandbox as well; the outer HOME only isolates Python/Playwright process-level state.  Its cleanup transcript, not the shell trap, is the evidence for the hub/fixture/keychain cleanup.

### Detached full sweep and captured close proof

Run this only after focused tests and the full walk pass, and read the raw output/triage before flipping Story 06:

```bash
cd /Users/karol/dev/tools/HoldSpeak
.githooks/dw evidence capture holdspeak 144 06 -- bash -lc '
  set -o pipefail
  HOME_REAL="$HOME"
  PLAYWRIGHT_BROWSERS_PATH="$HOME_REAL/Library/Caches/ms-playwright"
  npm_config_cache="$HOME_REAL/.npm"
  HOME="$(mktemp -d)"
  export HOME PLAYWRIGHT_BROWSERS_PATH npm_config_cache
  trap '"'"'rm -rf "$HOME"'"'"' EXIT
  uv run pytest -q -n auto --ignore=tests/e2e/test_metal.py
'
```

If that full command exits `1`, preserve and read the capture, then perform the baseline/serial triage above.  A baseline-exact capture can support the Tests-ran certification only after its output is read and the explicit triage note is appended.  Run the relevant isolated-HOME node twice serially for every non-baseline result before any status flip.

### Close sequence after the evidence is complete

```bash
cd /Users/karol/dev/tools/HoldSpeak
# status change only after the walk/evidence output and sweep triage have been read
.githooks/dw story status holdspeak 144 06 done
.githooks/dw phase close holdspeak 144 --from-file /absolute/path/to/final-summary-body.md
.githooks/dw check holdspeak
```

The final-summary body file is transient input; the durable terminal receipt is `pm/roadmap/holdspeak/phase-144-the-dashboard-door/final-summary.md`.  The implementation worker must not stage/commit until the actual phase process and the PMO contract are performed by the orchestrator.

## Orchestrator dispositions (ruled 2026-08-28)

1. **Leg-1 model-less scope: ACCEPTED.** A cold fresh HOME has no
   transcription model; the walk certifies the TYPED first-value path
   (capture → custody → visible result ≤3 min) plus the NAMED
   unavailable behavior for speech — never a faked transcript. A
   real-model speech leg is an explicitly labelled attended addendum,
   optional, on the owner's word (the .43 box exists if wanted).
2. **Completion semantics: ACCEPTED.** The Door grammar renders
   failure receipts only — success IS the board changing. The walk
   measures card completion → authoritative visual update ≤500 ms and
   keeps the stale-refusal receipt proof. No success toast is
   invented to satisfy a criterion's wording; the criterion is met by
   truth moving fast.
3. **ICS pairing: ACCEPTED.** Settings → fixture feed → real
   conductor refresh → rail, with the HTTPS egress-fact proof scoped
   separately.
4. **Before/after + byte-identical tell: ACCEPTED** as specified.
5. **Harness: ACCEPTED.** Standalone reusable
   `scripts/door_walk_hs144.py` (Phase 138 cleanup/reporting +
   Phase 131 env pattern); the pytest glass suite stays as regression
   coverage.

Close duties (sweep triage, serial rules, PNG restoration, the five
ledger items + two watch items, final-summary) run as the plan
writes them. Build after HS-144-05 closes.
