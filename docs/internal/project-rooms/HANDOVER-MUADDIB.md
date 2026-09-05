# HANDOVER: MUAD'DIB IX — Phase 170 The Great Pass, mid-flight (2026-09-05, late)

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. The owner's standing goal (Stop-hook, verbatim):
«Fedaykin satisfied all phases all the way up to 180, delivering all
their might into making HoldSpeak an ultimately useful, beautiful,
cohesive system». The road: pm/roadmap/holdspeak/THE-TUESDAY-ARC.md
§6. The face canon: docs/internal/UX-CANON.md. One phase active at a
time; every face still needs his word on its canvas; each phase merges
on its gates. Muad'Dib VIII (below) holds 169 and the arc's birth.

## 0. State (branch `feat/the-great-pass`, Phase 170 ACTIVE 2/7)

- **01 DONE** the census (36 after-shots re-captured green after the
  sweep). **02 DONE** the species sweep: three Fable lanes (P pages/
  cores @3dbe8a82 · T thought/threads/project-room + parking @b540dd3a
  · D desk chrome/pullouts/chair/voice/patterns @bd47897e); tree
  671 → 222 → 151 real hits after the scanner's own false positives
  were fixed; raw `<button>` 147 → 4 (allowlisted with reasons), accent
  rails 0, egress misses 0; vitest 2184 green, zero branch-new; build
  ok. **The ratchet**: `tests/unit/test_ux_canon_ratchet.py` +
  `tests/ux_canon_ceiling.json` (per rule + per face; lower it only via
  `python scripts/ux_canon_scan.py --write-ceiling tests/ux_canon_ceiling.json`;
  hard zeros DS6 + A9). Library gained `countToken`/`countLabel`
  (web/src/desk/surface/count.ts). The retired setup wizard is PARKED
  under web/src/features/project-room/_parked/setup/ (vitest excludes
  `**/_parked/**`).
- **03 DESIGNED** the Concierge: settled-design-concierge.md + six
  boards (Main = found+proposed, Picker, Adjust, Cold, Downloading,
  Phone). Counsel RATIFY-W-C, every condition PAID (Use these disabled
  beside any WAITING row; Anthropic in FOUND; headline = FOUND count;
  cloud rows carry ghost `Check` + `1 TOKEN · $`; Adjust unfolds UNDER
  the set with a host chip per capability row; `Chat` not `Chat
  practice`; the `MLX` runtime token is vocabulary).
- **04 DESIGNED** the four faces: settled-design-four-faces.md + twelve
  boards (arrival needs-you/quiet/393 · Settings hub 640/393 · Speak
  idle/landed/unset/393 · Meetings list/detail/393). Counsel RATIFY-W-C
  PAID (one egress vocabulary — `THIS DEVICE`, `LOCAL` retired; the OFF
  detail placement; the two wire reads behind the Models row;
  the THOUGHTS section of the arrival is its OWN section fed by the
  unfinished-thoughts read — the Chair lane vocabulary is retired by the
  doc-drift guard, so no lane is revived; the needs-you aggregate is
  N+1 until 171).
- **THE CANVAS (18 boards, both pages, counsel paid):**
  https://claude.ai/code/artifact/3fc26e25-1d5f-4796-b2e9-0d4bae9bff20
  Seeded from pm/roadmap/holdspeak/phase-170-the-great-pass/assets/mockups/
  (`*.dc.html` + canvas.json) into the session scratchpad
  `the-great-pass.html`; republish = same path, `contract: "0.1.31"`,
  favicon 🧭, no capabilities. Every board needs the head line
  `<script src="./support.js"></script>` (seven Speak/Meetings boards
  were born without it — the helper warns, the editor cannot edit
  without it).
- **IN FLIGHT when this was written:** two WIRE workers (no face work
  — faces wait for his word): the Concierge routes
  `/api/concierge/detect|propose|probe|apply|download` + MCP parity +
  tests/unit/test_hs170_concierge_wire.py; the four faces' routes
  `POST /api/meetings/{id}/intelligence/run` (+ `transcriptWords`),
  `GET /api/desk/needs-you`, `GET /api/settings/hub` + MCP parity +
  tests/unit/test_hs170_faces_wire.py. Verify by hand (scoped pytest
  with `HOME=$(mktemp -d)`), then commit under 03 / 04 (stories stay
  in-progress until the faces are built and rigged).

- **The suite (2026-09-05 01:50, CI shape):** 9392 passed / 9 failed —
  6 inherited or environment-bound (zero diff vs main in every file
  involved; three need the owner's real gguf under an isolated HOME),
  3 xdist-only (green serially). Both wires are committed. Triage law:
  after any `-n auto` run, re-run the FAILED ids SERIALLY before
  believing them (106 → 13 real on the same tree), and capture the
  full list with `-rf > file`, never `| tail`.

- **Decision 02:00:** faces build NOW to the ratified boards (the
  standing goal says do not pause); his word gates the MERGE, not the
  build. Five builders by file ownership: Concierge (Settings → Models),
  the arrival (desk/chair), the Settings hub (pages/cores/SettingsCore
  + settingsPrefs), Speak (features/dictation), Meetings
  (features/meetings). Each ships its glass rig asserting its boards.

- **State at 04:40 (the close):** every face built and bounced to its
  board; counsel on the built phase RATIFY-W-C, all conditions PAID;
  the lost-doors audit paid (five doors re-homed on the arrival); the
  real-desk pre-walk at ZERO defects after seven runs (the last defect
  was DATA — the 143 migration's `legacy-legacy-intel` entry — found by
  reading his projection in-process, see memory
  reference_legacy_double_prefixed_profile_ids); 06 DONE; the final
  summary written; the PR body drafted (scratchpad/pr-170-body.md).
  The full suite (CI shape) is the last gate before `gh pr create`;
  stories 03/04/05/07 keep the boxes that name HIS word open. The
  faces' evidence captures live untracked until the flips (the gate
  refuses orphan evidence).

- **PR #553 is OPEN** (https://github.com/karolswdev/HoldSpeak/pull/553,
  05:50): 99 commits; the final suite 9404 green / 6 inherited / 11
  xdist-only green alone. On his word: merge → flip 03/04/05/07 with
  the untracked evidence captures (`dw evidence capture` again if stale)
  → final-summary loses its DRAFT tag → Phase 171 activates
  (`.githooks/dw story status holdspeak phase-171-the-heartbeat
  story-01-the-design in-progress`, README "Current phase" line).

- **171's design ground is DRAFTED** (pm/roadmap/holdspeak/phase-171-the-heartbeat/assets/settled-design-heartbeat.md, pending 170's merge): six faces with species; recon binds the wire (the txn hook already writes `next_evaluation_at` — nothing ever calls `evaluate_due`; the Cocoa host has AppKit and zero notification calls; the daily brief push never regenerates). His three new questions: the notification's click target (shade or desk); one flat 15-min interval or an active/idle split; whether a muted project vanishes from the shade or only from the count.

- **06:20 — Phase 171 ACTIVATED, STACKED** on branch `feat/the-heartbeat`
  off `feat/the-great-pass` (the standing goal outranks "one phase at a
  time" the way it outranked "his word before build"; every MERGE stays
  his — 170's PR #553 first, then 171's stacked PR). In flight: two
  artboard lanes (shade PROJECTS · notification · dock badge · ⌘K;
  Rhythm's cadence row · the brief) from settled-design-heartbeat.md,
  and two wire lanes (the sweep loop + scheduler + `heartbeat` MCP
  family; the aggregate cache + the brief's cadence + the notifier).
  Then counsel on the boards → faces → rigs → his-desk walk → docs →
  close → stacked PR. If he bounces 170's faces, 171 rebuilds on his
  ruling.

## 1. The asks of the owner (in order)

1. His word on the Concierge page of the canvas → build 03's face on
   the Door's grammar (web/src/features/project-room/door/ is the
   pattern) to the artboards; rig at 640 + 393 asserting the boards;
   walk on his desk (his real engines: llama.cpp on 192.168.1.43, the
   keys in his keychain, his local files).
2. His word on the four faces AND on the N (four; the census ranking
   names the next in line) → build 04 face by face; each with its rig;
   the arrival retires the Chair hero (the `Develop a thought` button in
   a void, `PEOPLE NOT SET UP`, `No calendar connected.`, `CREW 0`).
3. His attended walk of the 169 Door + Room — STILL OWED.
4. **Phase 171 The Heartbeat is CHARTERED as PLANNED** (10 stories,
   pm/roadmap/holdspeak/phase-171-the-heartbeat/); it activates when 170
   merges. Its five open questions for him: the cadence row's home
   (Settings → Rhythm or another name); the notification body (count
   only by default — offer the content opt-in at launch or on ask); the
   Monday brief cadence (daily or every N hours); whether the
   transcription warm-up is one of the conductor's loops; 171 ∥ 172 or
   strictly sequential. 172 + 173 are CHARTERED as PLANNED the same way
   (pm/roadmap/holdspeak/phase-172-the-loop-closes/ 10 stories L;
   phase-173-the-stewards-hand-and-voice/ 9 stories M–L). Recon facts
   that bind them: NO People↔Watch join exists today (the owner_alias
   mechanism at people_service.py:637 is uncalled from the Watch path);
   intelligence has NO trigger after capture (stop_capture never
   enqueues; the run verb is manual); the model drafter
   (_draft_with_model) is real code that has never run for lack of an
   assignment; steward effects are all internal, `gh` read-only. His
   questions for 172: trigger on stop_capture only or import too; which
   plugin extracts decisions/actions or a new extractor; resolver on
   display_name too; Confirm one-step through the kernel; People as a
   section or as needs-you rows. For 173: nudge wording (named or
   steward-anonymous); 48 h latency default; the readiness signal set;
   nudge per-PR or per-person; `github.comment` as a sixth effect kind.
   **174 Reach is CHARTERED as PLANNED** (11 stories, L). Recon that
   binds it: the MCP server is stdio-only but `handle_message()`
   (holdspeak/mcp/server.py:30) is transport-agnostic — the Streamable
   HTTP route calls it behind the existing `_web_auth_gate`;
   AgentCredentialStore mints TTL tokens but has NO palette scope yet;
   the only CLI-backed third-connector candidate installed is `acli
   confluence`. His questions: can .43 reach the Mac's hub over the
   tailnet (unverified); Confluence as the third connector or install
   another CLI; the `remote` egress badge as a fourth chip state;
   credential scope = PROJECT_PALETTE or finer; polling-only V0 for
   long runs or SSE per the current spec.
   **175–177 CHARTERED as PLANNED**: 175 Calendar and the Clock (9; on
   171 — calendar_events exists but is empty on his desk; no
   MeetingWatchSource; the brief has no week window), 176 The Speak
   Loop (8; on 170 — 0 corrections; ring buffer of 20; MicButton on 7
   of ~92 inputs), 177 The Thread at Work (8; on 172 — story 01 is a
   MEASURED DECISION with the kill criterion 0 work threads + 0 runs in
   a week = CUT; project.* tools are in no thread palette today). His
   questions: 175 the week boundary; event-born recordings for all
   meetings or Room-linked only; decisions as entities or rolled up.
   176 MicButton on every input or a size threshold; 20 corrections
   enough; the journal in the shade too. 177 when the measured week
   starts; project.* into Chase/Plan or a Room mode; a softer CUT.
   **178–180 CHARTERED as PLANNED** — the arc to 180 is chartered end
   to end: 178 The Portfolio (10; on 173 + 177 — no cross-Room read
   exists, the needs-you aggregate is flat), 179 The Companion (11; on
   174 + the web spec finished through 178 — apple/App/ holds
   pre-Constitution Swift; mesh.py advertises, never pushes), 180 The
   Proof (10; the measured week, the census at the ratchet floor, the
   Constitution audit article by article, the suite + live legs, the
   performance ledger, the positioning re-read, the retrospective, the
   release candidate). His questions: 178 portfolio as a window or the
   shade's PROJECTS deepened; cross-source dependency alerts; the
   brief's portfolio row. 179 iPad-only or universal; off-LAN honest
   disconnect or cached; QR pairing. 180 Gate B advisory or blocking;
   the week's journal structured; 1.0.0 or 0.x.

## 2. Laws learned this sitting (add to the canon of habit)

- **Count = rows.** A caption `FOUND 5` over three rows is a lie; a
  board never abbreviates — it shows every row the count claims.
- **No dead verbs on a board.** A verb whose precondition the row says
  is unmet (`NO TRANSCRIPT` beside `Run intelligence`) is a design bug,
  not a build bug. Counsel hunts for it; so should the first read.
- **One egress vocabulary.** `THIS DEVICE` · `LAN` · a host. Never a
  synonym on one face.
- **The scanner lies until it is taught.** Property access is not a
  raw id; a JSX comment is not a raw button; TypeScript is not a
  sentence; `!rows.length` is not a counter. Fix the scanner before
  fixing a face it accuses.
- **Commit before dispatching; the tree is a snapshot.** A PMO commit
  may catch another worker's half-drawn board; that is fine — the next
  commit finishes it. What is never fine is a worker restoring files.
- **Publish once, right.** The canvas went to the owner only after
  counsel's conditions were paid on both pages.

---

# HANDOVER: MUAD'DIB VIII — addendum after the merge (2026-09-05)

- **Phase 169 MERGED**: PR #551 → main `27eabf0c` (carries Phase 168,
  closed as superseded). The owner's word: "I will trust you on this
  one" → "LET'S MERGE AND DEVISE ADDITIONAL PLANS…". The Fedaykin are
  BOOSTED to `claude-fable-5-1` (his word; ORCHESTRATION.md §model rule).
- **The Tuesday Arc** is written: pm/roadmap/holdspeak/THE-TUESDAY-ARC.md
  (artifact https://claude.ai/code/artifact/2fb168a2-a9c6-454c-ae4a-832962a3e44f):
  170 The Concierge → 171 The Heartbeat → 172 The Loop Closes → 173 The
  Steward's Hand and Voice → 174 Reach. **The first asks of the next
  sitting: his word on the ORDER (charter 170 only on it — no new
  charters without his word) and his own attended walk of the Door and
  the Room, which every phase assumes he owns.**
- **Owed from 169's close** (final-summary.md ledger): re-point three
  rig legs whose live coverage was lost with the retirements (the
  degraded Room; evaluation → delta review via the API + `Review N`;
  auth-degraded mid-setup); the per-source Adjust well; park the old
  wings' faces + setup/ + `configure-setup`.
- **His desk**: the hub on 127.0.0.1:64035 and the app's own hub on
  63051 both run main; his real project reads `karolswdev/HoldSpeak · 2
  OPEN PRS · 2 CHECKS FAILING`, `KAN · 1 DUE THIS WEEK`, the meeting
  watch `CAN'T CHECK`. Before any real leg: `pgrep -fl 'uv run
  holdspeak'` and restart anything older than the last backend change.

---

# HANDOVER: MUAD'DIB VIII — the orchestrator's mind, serialized an eighth time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-05 at the end of the sitting
that chartered, designed, built and walked Phase 169 The Streamlined
Door on the owner's mandate — verbatim: "I want us to really refine
and really streamline the UX. This is, by far, the biggest obstacle
to me accepting it. It's horrible. And we need this module to be the
first one that we BOTH will be proud of." / "Just make sure the
interface to all of this is absolutely world-freaking-class." / "Just.
Be excellent. Be a powerful UI and UX designer for this." He ratified
the canvas with one word: "word". Muad'Dib VII (below) holds for 168.

## 0. The state of the world (2026-09-05)

- **Phase 169 ACTIVE 5/7 on feat/the-streamlined-door** (off
  feat/connections-door `1f9798f9`; 168 holds at 5/7 unmerged — its
  door is superseded by 169's; when 169 merges, 168's story 05 flips
  on the same walk verdict or is closed as superseded — the owner's
  call). DONE: 01 design (11 artboards, counsel paid, "word"), 04 the
  wire, 02 the Door, 03 the Room, 06 docs. IN PROGRESS: 05 the walk —
  the runner green on the isolated leg AND the real leg on his desk
  (5 clicks, both widths, projects archived, watches paused, baselines
  established); **HIS attended walk and verdict flip it** (evidence
  ships only with the flip); 07 the close — counsel RATIFY-W-C paid;
  the unit fast lane running at the time of writing; still to run: the
  non-unit half (`tests/ --ignore=tests/unit --ignore=tests/e2e/test_metal.py
  -n auto`, isolated HOME, NEVER beside a live walk), the web baseline
  (last: zero branch-new, 2426), the four rigs alone (door, room, the
  168 connections, the isolated walk), the sweep of branch-new names
  against main-failed-names.txt (26 at ce629cc2; previous session's
  scratchpad 199f52c6-…), final-summary.md (draft written: the ledger),
  then PR feat/the-streamlined-door → main on the local gates; merge
  on his word (create and merge are SEPARATE gh calls).
- **His hub runs the final build on 127.0.0.1:64035** (URL + token in
  the scratchpad's hub-url.txt); the `holdspeak` APP process (restarted
  today — it had run since 08-31 on stale code and kept failing his
  watches hourly) also serves its own hub on 63051. His real project
  proj-10b35905777c now reads: `karolswdev/HoldSpeak · 2 OPEN PRS · 2
  CHECKS FAILING`, `KAN · 1 DUE THIS WEEK`, the meeting watch
  `CAN'T CHECK · Remove`; health ON TRACK; nothing needs him.
- **The canvas:** https://claude.ai/code/artifact/aa41070b-9a9e-4946-824c-29f2578c8383
  (working files assets/mockups/*.dc.html + canvas.json; re-seed with
  the design skill's helper; republish the same path with contract
  0.1.31).

## 1. What remains (in order)

1. **His walk.** Hand him the URL; New Project → the outcome line →
   pick a repo → pick KAN → Create → the Room. Record his words
   verbatim in story-05 §THE OWNER'S VERDICT; on PASS `dw story status
   holdspeak 169 05 done`, cadence, commit (evidence-story-05.md exists
   and is tracked? — check `git status`; 05's capture = the isolated leg
   + real leg transcripts; recapture the isolated leg through `dw
   evidence capture` if the file is missing).
2. **07:** run the gates above alone; the sweep = comm -13 of branch
   failures vs the 26 inherited names, candidates re-run serially;
   counsel's S-3 (Fix withheld with Adjust) documented; final-summary
   gates filled; PR; merge on his word; then memory (Phase 169 merged;
   168 disposition).
3. **The debt ledger** (final-summary.md §ledger): the per-source
   Adjust well (extract the Door's AdjustWell; route exists); steward
   settings under sources; park the 167 wings' faces + setup/ + the
   `configure-setup` manifest entry; the door window hugging its
   content (DeskWindow fitContent not exposed to surface windows);
   MCP twins for the door routes; `next_evaluation_at` null on old
   watches; whether the owner's OWN red PRs should call him (needs-you
   rule); the native meeting adapter or its removal from his project.

## 2. The laws this sitting added

- **Build what was ratified — and read the shot beside the artboard
  every round.** 02 took four rounds, 03 five; the probes had to
  assert the artboard (type step, token position, no intersections,
  the well in frame), not presence.
- **The persisted watch snapshot is not the source's return shape**
  (dict entities keyed by id, snake_case fields) — unwrap through one
  helper; fixtures use the PERSISTED shape (memory: reference_watch_
  snapshot_persisted_shape).
- **A green rig on fixtures is not the desk**: the real project showed
  empty rows, the wrong host, a dead CI kind — read the REAL rows
  through the new wire before the owner does.
- **Check the age of every `holdspeak` process before a real leg**
  (the stale app ticked old code for days).
- **The footer is portaled** into the frame's foot slot — a core's
  descendant selectors never reach it; SurfaceFooter now takes a
  className hook.
- **The desk's container query is named `surface`** — `surface-window`
  never matched (three rounds of 393 failures).
- **Workers run scoped suites only; a full `-n auto` left running
  starves live rigs** (two orphans killed; three 393 "hangs" were CPU).
- **Workers restore ONLY rig-shot churn; the orchestrator commits its
  records before dispatching** (a handover was reverted once).
- **A section-level verb is an honest interim; a dead row verb is
  not** (Adjust withheld; Steward / Review N named as 07 candidates).

## 3. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries the
whole picture; never claim what you didn't verify; the owner's bounces
are gifts — answer the exact words, record them verbatim, fix the root;
scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Streamlined Door sitting)

---

# HANDOVER: MUAD'DIB VII — the orchestrator's mind, serialized a seventh time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-04 at the end of the sitting
that PAID the owner's bounce on the Connections Door (Muad'Dib VI below
names the bounce verbatim; this edition carries what was paid, what the
re-walk found, and the exact ask that remains). NO NEW CHARTERS. Show
him, ask again, flip 05 on his word, close 07, PR.

## 0. What this sitting did (commits 2e5b2429, 1cd03962 on feat/connections-door)

- **Root 1 paid at the species** (window chrome, never a face):
  pullout.css — the title `min-width: 0` (its `min-width: auto` had
  blocked the ellipsis EVERYWHERE, not only with wings), the has-wings
  title `flex: 0 1 auto`, `.desk-wings { flex-shrink: 0 }`; DeskWindow
  wraps `{actions}` in `.desk-window-actions` (flex-shrink 0). Pinned by
  tests/e2e/test_hs168_window_wings_glass.py (a 70-char Room name at
  1440 + 393; wings' box inside head and window; title scrollWidth >
  clientWidth) — before: `Wings right edge (898) exceeds head right
  edge (392)`; after: 2 passed — and windowWings.test.ts. Nine `wings=`
  callers, all covered. Rider paid: the Room said the name FOUR times —
  name, outcomeText and purpose all come from ONE interview answer
  (project_setup_service.py:689-710: name = outcome[:80], purpose = the
  original text); the band shows it once when they coincide
  (RoomIdentityBand; 3 vitests). The derivation itself is ledgered.
- **Root 2 paid to the RATIFIED artboard** (the first build had left
  it): SetupRoot returns the wizard (GitHub / Jira / Clarify) ALONE
  while open (answered rows, TOOLS, brief, setup footer UNMOUNT; Back /
  Use this Watch return to the cards); cards carry ONE verb by species
  — connected+untested `Set up` (primary), tested `Tested · N` +
  `Remove` (ghost), disconnected `Connect` (ghost → the same
  openConnectionsInPlace the TOOLS card uses; the scroll-to-TOOLS hunt
  is gone), native unchanged; `SUGGESTIONS N`; in the proposals state
  the answered rows span the full window above the columns; the brief's
  watches block is `SOURCES N` = chosen only (`NONE YET` token). Mockups
  amended FIRST (D7c card verbs; Sources.dc.html + SourcesPhone) and the
  canvas republished at the same URL (version "D7c amendment: card
  verbs"). Pinned: ProviderWizardMounted "wizard owns the body",
  SuggestionCardVerbs (9), the sources rig asserts TOOLS/cards count 0
  while the wizard is open (4 passed); the walk runner + walk-script
  rows 12/16/20 click `setup-card-setup-<id>`.
- **Re-walked HIS desk** (`HS168_WALK=1 HS168_WALK_DB=real`): 1440 + 393
  passed (17 steps each); real-connected-{desktop,phone}/ shots; step 17
  shows the wings inside the window on his real desk. Gallery for his
  verdict (mockup · rigs · his desk):
  https://claude.ai/code/artifact/2c8add39-781a-4e18-8f23-cfc1cfc0ee98
- **The re-walk found three PRE-EXISTING defects on his desk — PAID
  @1cd03962:** (1) every Jira Watch was born with `issue_types: [""]`
  (JiraWizard fired `onToggleType("")` 100 ms after the first project
  pick; finalize wrote it; `_compile_jql` emitted `issuetype in ('')`;
  Jira: `the value '' does not exist for the field 'issuetype'`;
  baseline `pending` on EVERY walk project and on the owner's own
  proj-10b35905777c — while Test said passed, because the test path
  merged scope.projects but never scope.issue_types). Paid at three
  seams: the wizard injects nothing; the compile drops blanks in every
  list clause (his saved watches heal on the next tick, no migration);
  Test merges scope.issue_types (Test compiles what evaluation
  compiles). tests/unit/test_hs168_walk_fixes.py. Live: his stored
  query compiled through the fix ran via acli → KAN-2; re-walk after
  the fix → jira rows baseline `established`. (2) The automation
  conductor's LEGACY pump (`refresh_due_watches`) evaluated paused
  watches on ARCHIVED projects hourly (acli egress since 06:16; the 165
  "legacy-side watch guard" debt) — guarded once at the repo seam,
  `list_enabled_legacy_watches`. (3) The Jira scope step showed a blank
  PROJECT while discovering — `LOADING PROJECTS` token.
- **NOT paid (ledger for 07's final-summary):** the owner's own project
  carries a native `meeting` Watch failing every tick — `native can
  accept pushed snapshots but has no local query adapter yet`
  (watch_980edbb89697) — a Watch the face let him activate cannot
  evaluate. Also: the Room's stats row clips "Changes" at 640 px and the
  footer PROJECT token truncates (167 face; seen in the wings shots).
- **The hub runs the FIXED code on 127.0.0.1:63725** (URL + token in
  the scratchpad's hub-url.txt; 53379 and 55565 were killed). His live
  Jira watch heals on its next tick.

## 1. What remains (in order)

1. Sit at 127.0.0.1:63725 COLD and narrate New Project → Sources as a
   stranger (Muad'Dib VI §3). Hand him the gallery + the URL and ask for
   his walk. Record his words verbatim in story-05.
2. On his PASS: `dw story status holdspeak 168 05 done` (evidence-story-05
   is untracked and holds the isolated leg + this sitting's rig capture;
   recapture the walk if he asks), cadence, commit — evidence ships ONLY
   in that commit.
3. 07: the tree changed (css, setup, SetupBrief, DeskWindow,
   ProjectRoomCore, the Jira compile, the legacy pump). Already green on
   this tree: unit fast lane 7960 passed / 10 failed — all in main's
   baseline at ce629cc2 (main-failed-names.txt, 26 names, previous
   session's scratchpad 199f52c6-…; the two comm-new candidates re-ran
   green serially); web vitest baseline zero branch-new; the sources +
   wings rigs 6 passed (captured); the real walk both widths. Still to
   run at the close: the connections glass rig, the isolated walk, the
   `tests/` remainder (the non-unit half, `-n auto`), a short counsel
   pass over this sitting's diff (judgment: face recomposition + two
   backend seams). Update final-summary.md with the ledger above. Then
   PR feat/connections-door → main on the local gates; merge on his
   word (create and merge are SEPARATE gh calls).

## 2. Laws this sitting adds

- **Build what was ratified** — the wizard artboard already owned the
  window; the build deviated and the owner paid for it. Before a face
  flips, put the artboard and the shot side by side.
- **`min-width: 0` is part of every nowrap-ellipsis flex title.**
- **The Test path and the evaluation path compile the SAME query** — a
  passing Test that a first fetch contradicts is a lie to the owner.
- **A walk's finally is not a proof of health** — read the watch rows
  it left behind (state, baseline_state, last_error) before calling a
  real leg green. That read found three defects the green walk hid.
- **A live desk walk never shares the machine with the `-n auto`
  suite** — three 393 legs "hung" at LOADING PROJECTS >27 s beside the
  12-minute fast lane; idle, discovery took 2.2 s. The runner now
  prints every provider request's duration on failure — read the wire
  before blaming the face.
- **Workers restore ONLY rig-shot churn under pm/**/assets — never
  docs, never the orchestrator's uncommitted edits.** A worker's
  "restore churn outside your files" reverted the first Muad'Dib VII
  handover. Commit the orchestrator's records BEFORE dispatching the
  next worker.
- **Worker attribution of a failure to "the other worker" is a claim**
  — re-run the test yourself (StewardPosture: 49/49).

## 3. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries the
whole picture; never claim what you didn't verify; the owner's bounces
are gifts — answer the exact words, record them verbatim, fix the root;
scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Connections Door, the bounce paid)

---

# HANDOVER: MUAD'DIB VI — the orchestrator's mind, serialized a sixth time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-04 at the END of the
Connections Door sitting — after the owner WALKED THE BRANCH ON HIS
DESK AND BOUNCED. Muad'Dib V (below) describes the phase's build and
close gates and still holds; this edition carries the bounce and the
exact work the next sitting opens with. NO NEW CHARTERS. Pay the
bounce, re-walk his desk, ask again.

## 0. His words, verbatim (2026-09-04, on http://127.0.0.1:53379)

"unacceptable UI work..., see how the TIMELINE, DECISIONS, SEARCH, ASK
are just completely off to the side of the window, as on this
screenshot... second to this..., I really don't understand why
everything's still so complicated. The tool suggestions are still not
obvious AT ALL, it's not obvious I have to click them to then scroll
within that same dialog to test them, validate them, and so on. I'm
telling you - this stuff is still not streamlined at all..." — "so
prepare another Muad'Dib."

## 1. The two roots (anchored this sitting; NOT paid)

1. **Wings escape the Room window on a long title.**
   web/src/desk/components/pullout.css:284 —
   `.desk-pullout-head.has-wings .desk-pullout-title { flex: none }`
   (HS-100-07). The title never shrinks when wings are present; a
   long project name pushes TIMELINE · DECISIONS · SEARCH · ASK past
   the window's edge. Species fix in the window chrome: the title
   `flex: 0 1 auto; min-width: 0` (its ellipsis rule at :130-134
   already exists), the wings `flex-shrink: 0`. Pin it with a vitest
   on DeskWindow (long title + wings → the wings' box inside the
   head's box) and a glass shot of a Room with a 70-char name at 1440
   and 393. Check every OTHER head with wings (grep `has-wings`).
   While there: the Room repeats the project name FOUR times
   (title bar · h1 · the target token row · the purpose line) — the
   167 identity band's purpose/outcome fold; he did not name it, but
   he will.
2. **The Sources step is not legible.** SetupRoot.tsx:167-283 renders
   `SurfaceColumns main=[SetupInterview (answered rows), ToolsRow,
   wizard-or-SuggestionCards] side=SetupBrief` — a provider's wizard
   appears INLINE below the answered rows, beside the brief, so a card
   click leads to scrolling the same dialog to find it; nothing on a
   card says it is the entry. This broke the ratified law (167 D0,
   inherited by 168 D2): "wizards own the whole body while open". The
   amendment is recorded in assets/settled-design-connections.md D7c:
   (a) every provider suggestion card carries ONE verb — `Set up`
   (primary on the card; `Tested · N` after) — the click target NAMED;
   (b) an open wizard OWNS the body: the answered rows, the TOOLS row
   and THE BRIEF unmount; the wizard's ProgressPlan sits under the
   window's plan; the footer carries only `Back · Test this Watch /
   Use this Watch`; closing returns to the cards with the chip
   flipped; (c) consider the ProgressPlan step label carrying what the
   step asks (`Sources` alone told him nothing) — a token, not a
   sentence; (d) re-shoot both widths (the 04 rig + the walk) and
   RE-WALK HIS DESK (`HS168_WALK=1 HS168_WALK_DB=real uv run pytest -q
   tests/e2e/live168_walk.py`) before asking him again.
   Design first? The amendment is small and inside the ratified
   grammar; a one-artboard mockup (Sources with the verb; the wizard
   owning the body) on the existing canvas (artifact e3a6776b-…; the
   sources are assets/mockups/*.dc.html) is cheap insurance — do it,
   show him, then build. His bounce says the last build was not what
   he pictured; do not guess twice.

## 2. The state of the world

- Branch feat/connections-door, HEAD = this handover's commit. 01-04
  + 06 DONE; 05 IN PROGRESS (his bounce recorded in story-05; its
  evidence-story-05.md sits UNTRACKED — the isolated leg; re-capture
  after the fixes); 07 IN PROGRESS with every gate green at the
  pre-bounce tree (suite 7946+1350 passed, sweep zero unexplained,
  counsel RATIFY-W-C paid, final-summary.md written) — the tree will
  change, so the close re-runs the affected suites + the sweep on the
  candidates, not necessarily the whole 24-minute suite (judgment:
  css + SetupRoot + rigs → vitest setup/surface/desk, the four rigs,
  the baseline, the null-read/product-copy guards).
- The hub from this sitting may still be running in the background
  on 127.0.0.1:53379 (real desk, token in his config); kill it before
  re-building (`pgrep -fl "holdspeak web"`), rebuild `cd web && npm
  run build`, restart, hand him the URL with `?token=` again.
- His desk: three archived projects (167's + two from the 168 real
  leg), watches paused; DB backup holdspeak.db.bak-hs168-005512.
- Post-phase menu unchanged (Muad'Dib V §1).

## 3. Laws this bounce adds

- **"Owns the body" means UNMOUNT the rest** — an inline wizard under
  other content is a scroll hunt, not a step.
- **A card that is an entry carries its verb** — a chip row is not an
  affordance.
- **A window's wings never leave the window** — titles shrink first.
- **Walk it with HIM in mind, not the rig**: the rig proved every step
  reachable; it did not ask whether a human would find the next step.
  Before asking him again, sit at the face cold and narrate each step
  as a stranger — if a step needs the narration, the face is wrong.

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim, fix
the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Connections Door sitting, second close)

---

# HANDOVER: MUAD'DIB V — the orchestrator's mind, serialized a fifth time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-04 at the close of the
session that chartered, designed, built, walked and closed Phase 168
The Connections Door — the front door for connectors, born from the
owner's bounce on his own walk of the Room. Muad'Dib IV, III and II
(below, verbatim) still hold; this edition carries what changed.

## 0. The soul, re-proven again

Four worker rounds on one story (04) because "all green" was said
over shots that showed a washed-out column, a footer on the desk
below the window, a heading with no name, an emoji emblem, sixty-
seven vitest skips called "selector edits", and Jira shots skipped
and called "acceptable". Every one caught by reading the PNGs at
true size and probing the live face. Paranoia is WHY you move fast.

## 1. The state of the world (2026-09-04)

- **Phase 168 ACTIVE 5/7 on feat/connections-door** (HEAD after the
  close commits: the sweep paid, final-summary.md written). Stories
  01-04 + 06 DONE; **05 (the walk) flips on the OWNER'S ATTENDED WALK
  and verdict** — its evidence-story-05.md sits UNTRACKED in the tree
  (the gate law: evidence ships only with the flip); 07 (the close)
  flips after 05: full suite 7946+1350 passed, sweep zero unexplained,
  counsel RATIFY-W-C paid. Then PR from feat/connections-door → main
  on the local gates; merge on his word (create and merge are SEPARATE
  gh calls).
- **The owner's words this phase, verbatim:** the charter — "charter
  it"; the canvas — "Okay." (read as PASS, said so to him); the live
  face — "dude. Why is the edit button such a generic HTML button, but
  not a button of our design component library...? — and also, why is
  the checkmark on one line and then the content on another..." (both
  paid: library Buttons everywhere in setup; the ledger-row wrap fixed
  at the species).
- **His desk:** the real leg of the walk ran on it (two projects
  archived with watches paused: proj-4ed6be467d96, proj-81fa4a0532a5;
  the 167 one untouched; DB backup holdspeak.db.bak-hs168-005512
  beside the DB). For HIS walk: `cd web && npm run build`, restart the
  hub, Settings → Connections, New Project; assets/walk-script.md.
- **Post-phase menu (NO NEW CHARTERS WITHOUT HIS WORD):** MCP-008
  remote (§1b of Muad'Dib IV — still the prepared charter); the debt
  ledger (final-summary.md of 168: the Jira accounts step on the old
  route; the emojiGuard blind to pages/cores + features; the fifth
  template per provider never surfacing under the cap of 4; the
  three composers of ConnectionsService); Gate B; the model-era
  collapse; 155 The Crew.

## 2. The laws this session added (append to §7 of the old canon)

- **The connectors' front door**: a tool is connected ONCE in Settings
  → Connections (one row, one state, one verb; the command in a well
  with COPY; no token ever crosses the face); the interview asks
  scope only; the TOOLS row lists every connector provider FROM THE
  WIRE (`GET /api/connections`) — on a cold desk the suggest step
  yields zero provider proposals, so the row is the only place a user
  learns GitHub exists.
- **Every verb is the library Button** (the owner's ruling; in memory
  as feedback_every_verb_is_library_button). `grep '<button'` before a
  face flips.
- **Rigs settle animations before every shot** (glass_infra._settle):
  `surface-rise-in` fades sections in on mount; a "washed-out" column
  is a rig artifact until a probe of computed opacity says otherwise.
- **A setup walk drives the FACE and shoots the WINDOW**; identical
  consecutive step shots fail the walk; the real leg writes `real-`
  prefixed directories (it overwrote the isolated shots once).
- **Re-suggest is idempotent at the seam**: existing rows returned,
  new candidates added (dedup by provider+template; native by
  kind+name); random ids per call had orphaned every selection.
- **The cap is per provider** (`_MAX_PROPOSALS_PER_PROVIDER = 4`); the
  eight-total cut after native → GitHub → Jira starved Jira on any
  three-fact desk.
- **The footer never truncates a host** (egress slot wraps) **and an
  empty slot never moves the receipt** (explicit grid areas) — the
  species that clipped `KAROLSANE` and `OF 4`.
- **A chip the wire lacks is retired from the design** (the 167 ITEMS
  / LABELS / BRANCH counts) — and a "quiet tone" is never an
  explanation for a pixel you have not measured.
- **Skips are theater**: a worker's `describe.skip("interface
  changed")` is a bounce, never a selector edit.
- **Docs must not lie about the face**: three sentences in the guide
  described things the built face does not do — check every claim
  against the code before the flip.
- **git pathspec `phase-1[0-6]*` also matches phase-168** — restore
  churn with explicit ranges (`phase-1[0-5][0-9]-|phase-16[0-7]-`).

## 3. The toolbox (session-scoped; recreate freely)

shot_artboards.py (per-.dc.html shots at true width via Playwright);
build_canvas.py (canvas.json from measured heights); the seeded
canvas at scratchpad/connections-door.html (artifact e3a6776b-…);
probe scripts run from INSIDE tests/e2e (relative imports) and
deleted after; close-unit.txt / close-rest.txt; main-failed-names.txt
from `gh run view 33826811669 --log-failed` (26 names at ce629cc2);
branch-new.txt = comm -13; candidates re-run serially.

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim, fix
the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Connections Door sitting)

---

# HANDOVER: MUAD'DIB IV — the orchestrator's mind, serialized a fourth time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-04 at the close of the
session that chartered, built, owner-verdicted (three words), counsel-
ratified and PR'd Phase 167 The Room in Use — the phase that made the
eight Project Rooms faces ONE Room on the surface library and put the
FIRST real project on the owner's desk. Muad'Dib III and II (below,
verbatim) still hold; this edition carries what changed.

## 0. The soul, re-proven again

Eight faces from eight sittings had drifted from the library; the
owner's real desk had ZERO projects. This session's proof of the soul:
every worker report re-verified by hand, and the catches that only
hands find — a build helper that trusted a stale marker (the 163
theater reborn TWICE: first the marker, then a build RACE leaving two
chunks with a marker newer than stale chunks); a species-level `6ch`
grid column overprinting every date cell on every recomposed face; a
submit inside a React state updater; a trigger route lying about
project scope; a local import making a name unbound on nine MCP
tool paths; a walk that archived a real project and left its watches
evaluating the owner's real providers on the tick (mitigated on his
desk within minutes; paid at the root). Speed and paranoia: paranoia
is WHY you move fast.

## 1. The state of the world (2026-09-04)

- **Phase 167 COMPLETE 8/8**; PR opened from
  feat/project-rooms-the-room-in-use → main on the local gates (full
  suite 24f/9220p, sweep zero unexplained; web 789 + baseline zero
  branch-new; the eight glass rigs 46 green; counsel RATIFY-W-C, all
  M+S paid). MERGE ON THE OWNER'S WORD. If he says merge: `gh pr merge
  <n> --merge` (create and merge are SEPARATE gh calls), then memory
  (the TWELFTH Project Rooms phase merged).
- **The owner's words this phase, verbatim:** the design canvas —
  "PASS — build it."; the whole-Room gallery — "PASS"; the attended
  walk — "Walk it later — close on the dry run." His attended walk is
  LEDGERED PENDING: his desk is set up (restart the hub on the branch
  build; walk the eight steps of assets/walk-script.md; the Tuesday
  question). The runner: tests/e2e/live167_walk.py (HS167_WALK=1,
  HS167_WALK_DB=isolated|real; real HOME; skip-guarded on gh + acli).
- **His desk after the walk:** one project (archived) `proj-102233e71c47`
  "The first real project through the whole Room, attended"; its two
  watches PAUSED and unattended OFF (the mitigation + the root fix);
  the DB backup `holdspeak.db.bak-hs167-163032` beside the DB.
- **Post-phase menu (NO NEW CHARTERS WITHOUT HIS WORD):** the attended
  walk; Gate B partner feedback; MCP-008 remote; the model-era collapse
  (backend); 155 The Crew; the debt ledger (final-summary.md of 167).

## 1b. THE NEXT SITTING: MCP-008 remote — charter it FIRST thing

**The owner's word (2026-09-04), verbatim:** "I want you to prepare
Muad'Dib IV for working on MCP-008, via a handover." That is his word
lifting the SRS deferral — MCP-008 is LATER/V2 "until after product
validation" (SRS_DOMAIN_DRIVER.md:512; Gate B in
SRS_PRODUCT_VALIDATION.md:249-258). Record in the charter that the
owner lifted the gate consciously; do not re-litigate it.

**The row, verbatim:** "MCP-008 | LATER/V2 | Current remote
transport/protocol, scoped remote identity, Tasks integration, and
ecosystem publication are deferred until after product validation."
MCP-001..007 are DONE (Phase 165, PR #531). This is the last MCP row.

**What exists (recon 2026-09-04, anchors re-verified):**
- The sidecar is stdio ONLY (holdspeak/mcp/server.py:116-151, protocol
  `2024-11-05` at :14; MCP_SIDECAR.md:945 "no network listener"). Its
  `handle_message()` is transport-agnostic (dict in, dict out).
- The sidecar ALWAYS runs as OWNER (holdspeak/mcp/auth.py:32); the
  HOLDSPEAK_TOKEN there is an identity LABEL, not a credential
  (MCP_SIDECAR.md:674-676). It opens the DB directly and composes its
  own bare services (the 165 fetcher-seam debt).
- The hub ALREADY serves authenticated HTTP off loopback for
  companions (iPad, AIPI-Lite) on LAN/Tailscale, no hosted relay
  (USER_GUIDE.md:1178-1179): bearer token = `config.meeting.
  web_auth_token` (holdspeak/web_auth.py:27-114 — header
  `X-HoldSpeak-Token`, `Authorization: Bearer`, or `?token=`); the
  middleware derives the principal from the credential
  (holdspeak/web_server.py:560-590; owner → agent credentials → node
  tokens → UNAUTHENTICATED); a non-loopback bind is REFUSED without a
  token (web_auth.py:73-89). `HOLDSPEAK_WEB_PORT` pins the port.
- `AgentCredentialStore` (holdspeak/principals.py:89-172) already
  mints per-identity tokens with TTL + revocation — the substrate for
  scoped remote identity. PROJECT_PALETTE (45 tools) is the palette
  mechanism (MCP-007).
- No SSE plumbing exists in the MCP layer (the hub's real-time channel
  is the WebSocket at /api/ws). Streamable HTTP (the current remote
  transport) arrived in spec revision `2025-03-26` — a protocol bump.
- "Tasks": the recon could not confirm a ratified MCP Tasks feature;
  MCP-003's run_id + explicit polling is the contract that exists.
  Verify against the current spec before designing; never build to a
  draft.

**The charter-ready chain (six stories; the 165 liturgy):**
01 The transport — a Streamable HTTP route ON THE HUB (FastAPI), behind
the existing `_web_auth_gate`, calling `handle_message()`; the remote
handler composes on the WEB runtime's live services (the conductor's
`set_scheduler_services` seam, the wired fetcher) — never the sidecar's
bare instances (this pays the 165 fetcher-seam debt); the protocol
version bumped honestly with its census.
02 Scoped remote identity — a non-OWNER principal per remote client
minted from AgentCredentialStore (TTL, revocation, owner-issued from
the desk), palette-restricted (PROJECT_PALETTE or a configured subset);
the kernel derives authority from the credential (Article XI:3); a
typed capability error for anything outside the palette (MCP-005).
03 Egress + receipts — every remote call kernel-admitted with a
terminal receipt (Article XI:2) and an EGRESS badge at the point of
decision (Article III:2) — reads included, since they cross the
network; the pipeline observer shows them; local stdio stays badgeless.
04 The long-running contract — MCP-003's run_id + polling over HTTP;
SSE push for run state ONLY if the spec's mechanism is ratified and
the Streamable HTTP notification channel fits; documented, tested.
05 The live proof — a second machine on the tailnet (the .43 Linux box
is the natural one; sandboxed Bash cannot reach the LAN — run the
client from a real shell) drives the SS15 scenario the 165 walk proved
over stdio, measured, with a transcript; the OWNER VERDICT. His hub:
`HOLDSPEAK_WEB_PORT=<port> holdspeak web` bound off loopback with the
config token (never paste the token into the repo).
06 The docs + the close — MCP_SIDECAR.md (generated — extend the
generator, never hand-edit counts), the companions section of the
guide, "ecosystem publication" named honestly as self-hosted
discoverability (the no-hosted-relay law), the debt ledger.

**Laws that bind it:** Article III (nothing leaves by default — the
listener is opt-in, disclosed by badge; no hosted relay); Article XI
(admission, receipts, the caller supplies neither principal nor
authority; custody — remote agents get bounded delegation, never
OWNER); MCP-001 parity (one implementation: remote = web = stdio);
ledger-not-gate (a flight recorder, not ceremony); the yolo rigor bar.

**Counsel's hunts to name in the charter:** a remote path composing
bare services (the 164/165 scar); a palette that leaks a tool through
an alias; an egress badge missing on a remote READ; a protocol bump
that silently changes a wire shape the 165 walk pinned; a credential
that never expires.

## 2. The laws this session added (append to §7 of the old canon)

- **Design the whole Room, not a face**: one design doc with a shared
  spine (identity band · ledger grammar · chip vocabulary · a plan
  species for anything that runs · ScrollHint · the footer), counsel
  reads it BEFORE the owner (18 findings paid: never retire a wing;
  never fabricate a chip the wire lacks; name real props).
- **A test that pins dead DOM shape gets a SELECTOR edit** — element
  types, class names, moved testids included. "Kept for test compat" is
  never a reason to keep hand-rolled markup. Say it in the brief.
- **Overprints are species bugs first**: when every recomposed row
  overprints, look at the grid template, not the faces (the `room`
  ledger template was born from a fixed `6ch` column).
- **The build-first helper compares the OLDEST built chunk against the
  newest source and never touches the marker**; two hashed chunks under
  the bundle = a build race = stale pixels. Grep the chunk for a new
  string before believing a shot.
- **Pixel-identical round N+1 shots = the bundle did not change.** Read
  timestamps AND content, never the worker's word.
- **Archive stops the watches** (list_due_watches excludes archived
  projects; archive pauses + unattended off; restore never auto-
  resumes). Any real-desk walk's finally disables unattended BEFORE
  archiving.
- **A local `from x import y` inside one branch makes `y` local to the
  whole function** — nine tool paths died of one worker's import. Hoist.
- **Version pins hide under lying names** (again): `is_44` → `is_45`;
  the project family 34 → 35; classify every new MCP tool in
  thread_tools._TOOL_CLASSES; regenerate the schema snapshot in the
  same commit as a column.
- **Thread-local side channels must clear on entry AND on the except
  path** (a failed fetch's calls count leaked into the next watch).
- **Candidates lists are branch-NEW names only** (comm -13 main branch),
  never the whole branch failure list — the sweep count lied by 8 once.
- **zsh gotchas**: `echo ===X===` dies on `=`-prefixed words; unquoted
  `$VAR` is NOT word-split (use arrays); `uv run` must run from the
  repo cwd; the rigs REWRITE older phases' shot PNGs — restore before
  staging (`git checkout -- pm/.../phase-1[0-6]*/assets`).

## 3. The toolbox (session-scoped; recreate freely)

shot-artboards.py (per-artboard shots of a design canvas at true size
via a one-artboard seed launched focused); measure.py (true rendered
heights of .dc.html roots); build-canvas.py (canvas.json + notes);
build-gallery.py (the verdict gallery: sheets + key pairs, ≤4 MB);
regen_schema.py (the canonical schema snapshot); close-unit.txt /
close-rest.txt (the two suite halves); main-failed-names.txt from `gh
run view <id> --log-failed | grep -oE 'FAILED tests/[^ ]+'` at the
branch BASE; branch-new.txt = comm -13 of the names.

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim, fix
the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Room in Use sitting)

---

# HANDOVER: MUAD'DIB III — the orchestrator's mind, serialized a third time

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-03 at the close of the
session that chartered, built, owner-verdicted, counsel-ratified and
PR'd Phase 166 The Jira Parity (P7) — the LAST §14 slice. Muad'Dib II
(below, kept verbatim) still holds; this edition carries what changed.

## 0. The soul, re-proven harder

OWNER TRUST is the only currency — and this session SPENT it once:
the first Jira face was assembled by a worker from label:value rows
and prose, I bounced pixels twice, and the owner said "I absolutely
hate the UX of this thing ... Walls of text..., complete disregard to
our component". The repair: HALT, write a settled design on the
surface library, publish MOCKUPS (the `design` canvas skill, real
token values, both widths), get his word ("HECK YES, a BIG YES to
this."), THEN rebuild — and read every PNG every round. LAW (in
memory as face-design-before-build): no new face is built before the
owner has ratified its design on the library.

## 1. The state of the world (2026-09-03)

- **PR #532 MERGED** → main `31c072f5` on the owner's word (2026-09-03,
  "yes the PR is fine, I gave my word..., you know?"); the next
  session chartered Phase 167 The Room in Use (his pick over the
  model-era collapse, 155 The Crew, Gate B). What follows was true
  at the close of the 166 sitting: PR #532 was OPEN
  on the local gates (suite 19f/9201p, sweep zero unexplained; web
  2358 zero branch-new; counsel RATIFY-W-C paid). **MERGE WAITS FOR
  THE OWNER'S WORD** on the two galleries (the face on the rig
  ba57d6bd-…; the live walk on his site da7d9db9-…). The design
  canvas he ratified: 85d15031-…. If he says merge: `gh pr merge 532
  --merge` (create and merge are SEPARATE gh calls — the classifier
  blocks a chained create+merge), then main = the merge commit, then
  update memory (arc: ELEVENTH phase merged; the SRS V0 slices
  P0..P7 all merged).
- **The arc after P7:** V0 COMPLETE. Post-arc menu (NO NEW CHARTERS
  WITHOUT HIS WORD): Gate B partner feedback; MCP-008 remote
  (deferred by design); the debt ledger (final-summary.md of 166 —
  incl. the second-target proof: the owner holds ONE acli account,
  multi-site was fixture-tested only; MCP_SIDECAR's stale
  per-family counts; the population toggles are visual state; the
  per-process acli lock); the parked backlog (155 The Crew, the
  model-era collapse).
- **The owner's practice site:** karolsaneapple.atlassian.net,
  project KAN (3 issues; KAN-1 due 2026-09-10). acli 1.3.36 at
  /opt/homebrew/bin/acli, OAuth; auth lives with HOME (an isolated
  HOME = unauthorized). The walk (tests/e2e/test_hs166_jira_walk.py)
  is LIVE: it transitions KAN-1 and reverts in a finally; it skips
  honestly (a collectable skipif) without acli auth.

## 2. The laws this session added (append to §7 of the old canon)

- **Design the face before building it** (above). Workers compose
  library species; the mockup sources (.dc.html) are the reference;
  zero sentences; the egress chip names the real host.
- **A rig that can skip a step is theater**: every step asserted,
  scrolled into view, shot at both widths; "no visual changes
  needed" from a worker means READ THE PNGS YOURSELF.
- **The live site is the only judge of some lies**: the URL-form
  identity split, `calls` dropped by a decoder whitelist, an empty
  test that was a fixture answering no JQL, a day-early date — none
  visible with fakes. Every provider story gets a live proof script.
- **The 163 same-watermark law (§9.3)**: a second MANUAL run at the
  same watermark IS created and RECONCILES at the act step; Gate 4's
  existing-run dedup belongs to the conductor DRAIN only. The walk's
  route-level dedup broke the 163 glass — counsel ratified it and
  the sweep caught it; never assert "replay → same id" on the route.
- **The false baseline**: finalize claimed baseline_state=established
  with no snapshot — a provider-agnostic inherited lie that made the
  first unattended tick a false discovery. Now finalize baselines
  for real; a failed fetch leaves `pending`.
- **Composition seams hide `if None` skips**: the Delta service was
  composed without project_service so item creation silently
  skipped — characterization-test the WEB context's composition, not
  a unit fixture's.
- **dw's row flip**: `dw story status … done` flips the phase table
  row too; python cadence edits must not assert the row's old state
  (two repair commits on 166-06).
- **acli truths**: `workitem search --fields` refuses duedate/
  resolution/updated (view accepts all → N+1 enrichment, calls
  reported); Jira Cloud search is eventually consistent (~3-6 s);
  team-managed Done issues carry no resolution (status_category is
  the completion signal); `acli` cannot set due dates.
- **Sweep collection**: a module-level pytest.skip breaks collection
  by node id ("found no collectors") and aborts the whole candidates
  run — use a skipif marker.
- **The main baseline** must be refreshed from the branch BASE
  commit's CI run (`gh run view <id> --log-failed | grep FAILED`);
  a dead scratchpad list is not a baseline.

## 3. The toolbox (session-scoped; recreate freely)

story166-NN-verify.sh wrappers (pipefail; scoped suites in isolated
HOME + a LIVE proof script with real HOME); live166-NN.py; the
close: close-suite-166.sh in two halves (unit / the rest, each
`-n auto`, ~13 + 8 min) + story166-07-verify.sh (totals from the
saved halves, `comm` vs main-failed-names.txt, the candidates re-run
with ids read into a bash ARRAY — unquoted `[1440]` is a glob —, the
live walk, web, the flake x2); the galleries are python-built HTML
with base64 PNGs published as NEW artifacts per phase (the old
stable-URL rule needs a full read of the prior page first).

## 4. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never claim what you didn't verify; the owner's
bounces are gifts — answer the exact words, record them verbatim,
fix the root; scars become laws in memory.

— Muad'Dib, session 016siGSBgZph9EhEdGMoyWcu (the Jira Parity sitting)

---

# HANDOVER: MUAD'DIB II — the orchestrator's mind, serialized again

Read this once, fully, before your first tool call. When you finish,
you ARE the orchestrator. Written 2026-09-02/03 at the close of the
session that merged THREE phases (163 The Steward's Hand #529, 164
The Unattended Desk #530, 165 The MCP Family #531) — the eighth,
ninth, and tenth Project Rooms phases — each chartered, built,
owner-verdicted, counsel-ratified, and merged inside one sitting.

---

## 0. The one-paragraph soul (unchanged, re-proven)

OWNER TRUST is the only currency. Every claim is backed by output
you personally read; every face passes your eyes before his; every
worker report is re-verified with your own hands before anything
flips. Speed and paranoia are not in tension: paranoia is WHY you
move fast. This session's proof: eleven orchestrator catches on
worker output, every one real (see §5).

## 1. The cast (unchanged)

- **The owner**: karolswdev. Verdicts close every face story; his
  words recorded VERBATIM, bounces and passes alike. This session:
  163 PASS (one round); 164 round-1 Bounce (scroll affordance + his
  model-wiring question — a question IS a finding) then PASS; 165
  PASS (Gate B ready, one round). He asked the arc's remaining
  length and ordered the WIND-DOWN: finish 165, hand over, zero
  context. NO NEW CHARTERS without his word.
- **The Fedaykin (opus-worker)**: all delegated work,
  claude-opus-4-6[1m], never Fable subagents. Workers run SCOPED
  tests only; you own every full gate.
- **You**: commit, verify, judge pixels AND wire transcripts, talk
  to the owner, write the PMO records, carry the memory.

## 2. The state of the world (2026-09-03)

- **The arc**: §14's slices P0..P6 are MERGED (#521 #522 #523 #524
  #525 #527 #529 #530 #531 — ten phases; 165's merge = main
  ddd4b050). **P7 The Jira Parity is the LAST slice and the owner
  RATIFIED it, verbatim: "Yes, I will want Jira parity."** Charter
  it FIRST thing next session (phase-166, branch
  feat/project-rooms-p7-the-jira-parity): §14 P7 — a real Jira
  provider adapter for site/Project/type/status discovery and issue
  search; compile/test/baseline/poll semantic issue Watches; exit =
  Jira readiness backed by LIVE discovery/search and the same
  no-duplicate Delta/action behavior, never pushed fixtures alone.
  Natural riders from the 165 ledger: the sidecar fetcher-seam fix
  (a provider-injection shape serves both gh and Jira), the
  legacy-side watch guard, the scheduled-path trigger wire. After
  P7 the SRS arc's V0 is COMPLETE; post-arc: Gate B partner
  feedback, MCP-008 remote (deferred by design), the debt ledger,
  the parked backlog (155 The Crew, the model-era collapse).
- **main**: ddd4b050 (the 165 merge, PR #531). Branch hygiene: phase branches merge via PR + merge
  commit; local gates are the substance (the owner's standing
  posture — record the basis on the PR, never wait the serial CI
  Unit job).
- **The verdict gallery artifact**: ONE stable URL
  (2e2e5683-e617-4f73-8ca9-5fee04ba78b7), republished per phase
  from the scratchpad's update-room-shots.html (same file path =
  same URL within a session; from a NEW session pass url= and READ
  it first). 165's round proved a gallery can be a WIRE TRANSCRIPT
  (no pixels — the face is the wire) when the phase is driver-side.
- **The debt ledger** (re-list at every close; the 165
  final-summary carries the full set): 165's eight counsel N + the
  legacy-side watch guard + the sidecar fetcher seam + per-watch
  cadence write wire + the scheduled-path trigger route; 164's
  five N + others; 163 S-4/N-1/N-3; 160 N-5/N-1/N-2; 158
  S-1/N-1/N-3; 159 seeding walls; 161 N-1.

## 3. The turn discipline (unchanged, one addition)

Privately enumerate needs with dependencies; request EVERYTHING
independent in one response; end the turn when all remaining items
depend on pending results; never poll (background tasks notify);
never predict a pending agent's result. ADDITION: the wrapper's
`echo SUITE_EXIT=$?` after a piped tail LIES (pipe exit) — the
totals line is the only truth; and a `; echo ===X===` chain in zsh
dies on `=`-prefixed words (equals-expansion) — use plain markers.

## 4. The story loop + the close liturgy (unchanged from Muad'Dib I)

Brief hard (verbatim intent, READ-FIRST file:line anchors, laws,
scoped commands, STOP CONDITIONS, REPORT BACK ending in SURPRISES);
re-verify with your own hands; evidence wrappers through dw capture
with the tail READ; flip; cadence by anchored python (assert-in;
a failed assert means READ, never force); stamped contract read
before every flip; msg files always python-written. Close: owner's
PASS -> flip 05 -> full suite background + counsel parallel ->
sweep (isolation x2 + git-log = the protocol; mid-run artifacts
re-run on the settled tree) -> churn restored BEFORE staging ->
final-summary -> COMPLETE 7/7 -> PR (create and merge as SEPARATE
gh calls — the classifier blocks chained create+merge) -> merge.
GATE LAW learned twice: evidence-story-NN ships ONLY in the commit
that flips its story done — a functional commit carrying evidence
is refused.

## 5. The scars that became laws THIS session (append to §7 of the old canon)

- **Production seams prove themselves**: 163's door idem key was a
  phantom held up by a unit fixture that hand-seeded the very key it
  asserted (the 161 scar reborn). When a fixture writes what only
  production should write, the test lies.
- **Rigs BUILD FIRST**: the 163 rig had no npm build step — stale
  pixels with fresh timestamps, caught live. Every shot/walk wrapper
  builds before it runs.
- **Version pins hide under lying names**: two v-pin tests asserting
  ==70 were named _is_69. On every schema bump: grep EVERY
  `SCHEMA_VERSION ==` in tests/ and rename honestly.
- **Crippled-service construction**: 164's conductor blocks built
  bare services (no fetcher, None collaborators) — green in
  fake-injected tests, dead in production. The cure is the
  set_scheduler_services injection seam (mirror set_broadcast);
  unwired = honest skip. The MCP twin: the sidecar's
  _watch_service() still composes no fetcher (ledgered).
- **Theater tests**: 164's block-isolation tests simulated try/
  except inline and touched nothing real — rewritten against the
  REAL _tick. If a test can pass with the product deleted, it is
  theater.
- **SurfaceLedgerRow's 52px time column**: primary lands in the
  time slot when no time= is passed — always pass time= (or lead=).
  And a wrapped token inside a ledger row clips its siblings —
  tokens nowrap.
- **Attention outranks configuration**: a broken source renders
  FIRST (the 164 circuit section move). Scrollable wells announce
  themselves (the Door scroll-hint species, ported vertical — reuse
  it for any scrolling well).
- **Egress badges exactly where egress happens**: the MODEL chip on
  create_proposals over-claimed (the Delta is deterministic,
  DEL-007). The owner's questions expose these — answer them
  plainly AND treat them as findings.
- **Copies drift; delegate**: serializers, provider lists — import
  from the one source (the resources.py precedent). Copied route
  glue goes in a REGISTER for counsel.
- **Docs must not promote**: 165's docs upgraded 'conceptual
  ownership' to 'enforced both directions' without code. The doc
  drift guard + the roadmap-vocabulary guard are allies; run them.
- **The watermark contract is caller-carried**: same-watermark
  dedup keys live ON the act step (project:watermark scoped; empty
  watermark = run-scoped, no contract); manual presses are governed
  by the follow-through read-back (only ever the NEXT uncovered
  item).
- **Wake dormant machinery as designed, never bypass**: 165-03's
  STOP found the 161 effect tables with zero callers; the ruling
  wired them properly (rules match, effects record, run_due
  drains). Trace-first briefs with STOP CONDITIONS are where these
  are caught.

## 6. The toolbox (scratchpad is session-scoped — recreate freely)

orch-scoped.sh (cd repo; HOME=$(mktemp -d); PLAYWRIGHT_BROWSERS_PATH
=$REAL_HOME/Library/Caches/ms-playwright; pytest "$@") — THE way.
story<phase>-<n>-verify.sh wrappers; msg-*.txt; pr-*-body.md;
main-failed-names.txt (27 names @ run 33459107466 — STILL VALID
through the 165 close by reasoning: only branch-new fixes merged;
refresh from a fresh main run if candidates smell like drift);
close-suite-<phase>.txt; update-room-shots.html (the gallery).

## 7. The voice (unchanged)

Terse, concrete, numbers over adjectives; the last message carries
the whole picture; never hedge about what you verified; never claim
what you didn't; the owner's bounces are gifts — answer the exact
words, record them, fix the root; scars become laws in memory.

— Muad'Dib, session 015wvZJuEHkmosZR349Mv9J8 (the three-phase sitting)
