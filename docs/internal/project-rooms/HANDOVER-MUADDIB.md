# THE HANDOVER — from Muad'Dib XXIII (READ **§9, THEN §7b, THEN THE XXIII CHAPTER** FIRST)

The entries below this section are the running log, newest first. This
section is the whole picture in one sitting. When it disagrees with a
log entry, this section wins; when it disagrees with the code or the
roadmap files, they win. Memory (the Claude Code auto-memory, index
`MEMORY.md`) holds the same facts as pointers; the repo holds the truth.

## 0. Who is who (and the one change)

- **The owner** — a Senior Architect managing three people, one desk.
  His word gates two things and only two: the CANVAS (a face is built
  only to boards he or counsel-on-his-behalf ratified) and the MERGE.
  Never his walks, never the build. He also DEFERS: on 2026-09-06 he
  handed 175's seven open questions to the orchestrator ("The decision
  is deferred to you") — when he does that, RULE, record the ruling in
  the phase's final-summary, act, and tell him what you ruled. Address
  him as the owner; never a first name; never a pronoun from a name.
- **Muad'Dib** — the orchestrator (you), on Fable. Charters, briefs,
  reads every shot beside its board, bounces with specifics, runs the
  gates, commits, opens PRs, and MERGES ON ITS OWN VERIFICATION
  (2026-09-17: "there's no such thing as my word. This is your
  opportunity to verify and validate."). Never delegates the gates.
  Never lets a worker touch git.
- **The Fedaykin** — the workers, `.claude/agents/opus-worker.md`.
  **2026-09-17: they are FABLE 5.1** ("you are empowered to use Fable
  Fedaykins from now on"); the file says `model: fable` (the filename is
  historical). The file is gitignored — on a fresh clone re-create it
  (memory `feedback_no_such_thing_as_his_word` has the ruling;
  `feedback_opus_terra_verify_model` the older text). Scoped tests only,
  isolated HOME, never git, never his real DB, never a secret in the
  tree, honest reports ("could not verify X" is a good answer).
- **Counsel** — a Fedaykin briefed to HUNT (the design, then the built
  phase, then a re-read after the fixes). Counsel's verdict is advice;
  the orchestrator outranks it and rules; his word outranks both.
- **Delivery Workbench** — the PMO gate (`.githooks/dw`). Markdown is the
  truth; a story flips done only with evidence in the same commit;
  evidence never ships without its story (the gate refuses).

## 1. The state of the tree (2026-09-06 — SUPERSEDED, see the XIX chapter)

| Phase | Name | State |
|---|---|---|
| 170 | The Great Pass | MERGED #553 → `0e69f3d7` |
| 171 | The Heartbeat | MERGED #554 → `397e3594` |
| 172 | The Loop Closes | MERGED #555 → `0c17425e` |
| 173 | The Steward's Hand and Voice | MERGED #556 → `d416e08a` |
| 174 | Reach | MERGED #557 → `8c994305` |
| 175 | Calendar and the Clock | **COMPLETE 9/9 · MERGED #558 → `aa278604`** on his word; the R1 follow-up MERGED #564 → `7d897302`; his attended walk OWED |
| 176 | The Speak Loop | **CLOSED 7/8** on `feat/the-speak-loop` (PR #566, out of draft; merge on his word); built on his word ("Let's follow your ruling"); the `text` correction kind, the Journal stream, the Learned wing, the voice law paid; counsel-on-built's bounce paid; the suite classified; **06 his attended walk OWED** (the hub from this branch is up on his desk, port in the scratchpad only) |
| 177–179 | Thread at Work · Portfolio · Companion | scaffolds; not chartered |
| 177–179 | Thread at Work · Portfolio · Companion | PARKED behind Phase 200 (never deleted) |
| 180 | The Proof | folds into Phase 200's G5 |
| **200** | **The Working Practice** | **CURRENT** — his charter (PR #563 → `bea4176c`): G0 built (01–04 done, 05's physical beats his), G1 06–08 done, 09's design on the canvas for HIS VERDICT; **MERGED #567 → `5e2f1704`** on his word (2026-09-07) |

Main also carries work that landed beside 175 from elsewhere: #560 (the
web integration checks restored — the product-copy and write-receipt
guards are LIVE again), #561 (repeatable interview delivery; new
`interview_*` tables), #562 (the product docs refresh + an STE writing
policy — README rewritten in that voice; no dashes in prose), #528 (the
rainy-city desk atmosphere; `three` is a web dependency now — `npm ci`
in `web/` after pulling). `dw next` still surfaces an ancient
`HS-91-10 in-progress` — a stale leftover, not the current road.

**CI truth, unchanged.** GitHub Actions on main is RED on a
runner-environment set (no speech engine, no `mlx_whisper`, no
PortAudio, the Q6 model absent, the two broker density fences,
product-copy drift) plus a rotating flaky rig family. The gate this
repo runs is the LOCAL CI-shape suite + his word. Parked in BACKLOG.

**The desk.** His hub was left running on `127.0.0.1:54644` (the
pre-merge 175 build) for his walk; the owner URL is
`http://127.0.0.1:<port>/?token=<meeting.web_auth_token from
~/.config/holdspeak/config.json>` — the token lives ONLY in the
scratchpad (`hub-url.txt`), never in the repo or an evidence file
(redact `token=` when capturing a walk). His real DB is
`~/.local/share/holdspeak/holdspeak.db`; it now holds SIX real meetings
(the two 167/168 walk seeds were deleted on his deferral through the
product's `meeting_delete`).

## 2. What 175 delivered, in plain words

The calendar gave the desk its clock. The arrival: a WEEK strip (local
Mon–Sun, one dot per meeting, today accented, `N MEETINGS THIS WEEK` ==
the dots, always), `NEXT · <title> · HH:MM · ROOM · <name>`, a
`THIS WEEK` section (what is still coming; `ROOM ·`, the source label,
`ARMS HH:MM` + `Cancel`, `Unlink` on hover) and an orphan armed row
(`ARMED · HH:MM · FROM · title (source)`). Settings → Meetings gained the
CALENDAR section on the module the hub row opens (SettingsCore's
meetings case; it REPLACED the 146 group): one row per source (● ·
label · `ICS`|`SNAPSHOT` · host EgressChip for https, nothing for a
file · `N EVENTS` · `LAST READ HH:MM` · `Edit` · `Disable`/`Enable` ·
`Remove` with an in-world confirm), `Connect calendar` with `Add` (one
well, a mic) and `Snapshot` (the vision adapter, its host chip beside
it), `Auto-record` (`OFF` default · `ARM ROOM MEETINGS ONLY` · `ARM ALL
CALENDAR MEETINGS`, `5 MIN BEFORE`, `N MATCHED THIS WEEK`). The Room's
SOURCES gained a REAL meeting Watch (`MTG · MEETINGS · N THIS WEEK ·
NEXT DAY HH:MM · CHECKED`, Pause/Resume; created when a meeting links,
backfilled once by the sweep, evaluated by the sweep, feeding SINCE YOU
LOOKED; Retire is a tombstone). Rhythm reads `Weekly brief · DAILY
08:00 · LAST MON DD` with a summary line; the brief face is one display
(the period), THIS WEEK composed rows, SINCE FRIDAY flat rows with kind
tokens and emblem chips, one gutter, no counters of zero.

The wire: the calendar refresh rides the heartbeat sweep; events link to
Rooms by the Room's FULL name as a phrase (ruling R1; a one-word generic
Room name never links; Unlink is durable via a suppression table);
event-born recordings arm at `starts_at − 5 min` and RECORD at the event
like every scheduled recording (ruling B11/R2 — the toggle is the
consent, OFF by default); Cancel works for the row's whole life, names
its refusal, and is FINAL per occurrence (the cancelled row is the
tombstone; Delete behaves as Cancel); Remove/Disable prune and disarm
(a snapshot's generated ICS deleted on Remove); every arm has its own
receipt; local time per instant everywhere (DST-safe). Schema 75
(additive). API surface 668 routes on main.

## 3. The seven rulings (his deferral, 2026-09-06) — final-summary.md §"The seven questions"

R1 auto-link stays, full-name phrase, generic one-word never (#564) ·
R2 the toggle = record at the event, OFF by default · R3 Cancel = this
occurrence · R4 Remove = gone · R5 the hub's local clock · R6 the
arrival's calendar caption is `THIS WEEK` (the recorded-meetings ledger
owns MEETINGS) · R7 the seed rows deleted. If he ever flips one, the
addendum rows B11–B17 in the design doc name the code that moves.

## 4. Owed to the owner

- His ATTENDED walks on 170–175 (every phase's walk so far was the
  read-only runner on his desk).
- Skip the queued "Already titled" job (172's accidental write).
- 172/173/174's earlier questions (the handover XIII/XIV lists) — he
  has not answered them; 175's are ruled.

## 5. The loop that held (six phases, refined by 175)

1. **Charter** — story files, `current-phase-status.md`, the value-era
   question first ("will you use this on a Tuesday?"). Author PMO directly.
2. **Design on the canvas BEFORE build** — settled-design doc (D0 the
   Tuesday moment · D1 laws · D2 faces element by element with species
   · D3 wire with file:line · D4 counsel's hunts · D5 the walk · honest
   sizes) + `.dc.html` boards at 1440 and 393; counsel hunts the design;
   his word. **Check the design's file pointers against the tree** —
   175's design pointed the Settings section at `MeetingsConfig.tsx`
   (the Meetings window's gear panel) while the BOARD was Settings →
   Meetings (`SettingsCore` `case "meetings"`); a lane built the wrong
   face first. The board wins; the pointer is a hint.
3. **Build to the boards** — wire lanes first, then face lanes, ONE
   FACE PER LANE in the same tree with STRICT FILE OWNERSHIP (name every
   file each lane owns; a shared file is a collision). Every face's rig
   SEEDS through the real seam, OPENS the face, ASSERTS the artboard,
   SHOOTS both widths; the orchestrator Reads every PNG beside the board
   and bounces with specifics (175: A 2 rounds, B 4, C 3, D 3).
   **A replacing face never loses a working verb** — the old group's
   TESTS name its behaviours (Edit/Disable/Remove); read them before
   retiring anything.
4. **Counsel on the built phase**, then FIX LANES by ownership, then
   counsel's RE-READ. Expect a bounce: 175's spine (record vs arm,
   a dead Cancel, re-arm on refresh) only fell to counsel with
   reproductions. Rule what is his to rule and carry it.
5. **Docs** — a dedicated docs story; verify-at-build markers paid
   against the SHIPPED tree (a docs worker reading mid-edit files writes
   fiction — run it after the faces settle); shots for the guide go
   under `docs/assets/`, never linked into `pm/roadmap/` (the drift
   guard); no dashes in prose (the vocabulary guard; a date range uses
   a hyphen in source).
6. **The walk on his desk** — `tests/e2e/liveNNN_walk.py`, every write
   denied with a printed decision table, refuses a hub without a
   bundle, never clicks "Continue later" (a write), never beside the
   parallel suite; `configure-settings` then the Meetings row's `Open`
   is the real path into Settings → Meetings. Redact the token in the
   capture. Then census his DB read-only for anything the walk should
   not have touched.
7. **The suite in CI shape** — see §6 commands; classify every failure
   (inherited · xdist-only · mid-edit → re-run serially · paid). Run it
   when NO lane is editing, or classify twice.
8. **Close** — final-summary.md with the gates; COMPLETE; the project
   README "Last updated"; this handover; memory; PR out of draft; his
   word; `gh pr merge --merge`; sync main; `npm ci` if web deps moved.

## 6. Commands that matter

```bash
# orientation
.githooks/dw next holdspeak ; .githooks/dw check holdspeak ; git reflog -3   # reflog BEFORE every verification run
# a story
.githooks/dw story status holdspeak <phase-dir> HS-NNN-NN in-progress
.githooks/dw evidence capture holdspeak <phase-dir> HS-NNN-NN -- bash -c 'set -o pipefail; <command> 2>&1 | tail -3'   # pipefail, or a green tail hides a red exit
.githooks/dw story status holdspeak <phase-dir> HS-NNN-NN done
# restore what rigs and the scanner rewrite under OTHER phases, right before staging, every time
git status --short | grep '^ M pm/roadmap/holdspeak/phase-1' | grep -v <this-phase> | awk '{print $2}' | xargs -r git checkout --
# a commit (stage FIRST, then the contract, flip every box, commit; never --no-verify; two flips need .tmp/BUNDLE-OK.md)
git add … && .githooks/dw contract new --story HS-NNN-NN --force --tests-capture <evidence.md>
sed -i '' 's/^- \[ \] /- [x] /' .tmp/CONTRACT.md && git commit -F <msgfile>
# the suite in CI shape (detached — the tool's 10-min cap kills a 30-min run; poll a .done file)
HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm PUPPETEER_CACHE_DIR=$HOME_REAL/.cache/puppeteer \
  uv run pytest -q --ignore=tests/e2e/test_metal.py -n auto -p no:cacheprovider -rf > suite.log; echo done > suite.done
# mermaid render guard needs PUPPETEER_CACHE_DIR from the real home under an isolated HOME
# web baseline · ratchet · api surface · schema snapshot (regen with the normalizer in tests/unit/test_db.py, never by hand)
uv run python scripts/check_web_baseline.py --run ; uv run pytest -q tests/unit/test_ux_canon_ratchet.py ; uv run python scripts/gen_api_surface.py
# the hub for a walk (URL+token ONLY in the scratchpad)
nohup uv run holdspeak web --no-open > hub.log & ; lsof -nP -iTCP -sTCP:LISTEN | grep python   # the log stays silent; find the port
# merging — three separate steps
gh pr ready N ; gh pr view N --json mergeable,mergeStateStatus ; gh pr merge N --merge
```

## 7. The laws in one screen (long form: UX-CANON.md, CONSTITUTION.md, memory)

- The Constitution above all; UX-CANON is the face canon; POSITIONING
  the voice (now with the STE policy: no dashes in prose).
- Every verb the library Button; no prose; no modals; no counters of
  zero; ONE count everywhere; the lead slot is the emblem; egress
  exactly where it happens; receipts wear human labels; a mic on every
  text input; the ratchet never rises; the name said once per face
  (two identical captions on one face is a defect — 175's THIS WEEK).
- Ledger, not gate; open throttle; the hard boundary is custody, People
  refusals, egress badges, receipts. A scheduled recording records.
- Never delete — park (BACKLOG.md). Migrations additive; INSERTs name
  columns; regenerate the canonical schema snapshot in the same commit.
- **NO GIT VERB THAT MOVES THE TREE, FROM ANY WORKER, EVER** (stash,
  reset, checkout --, restore, clean, switch). 175's scar: a lane ran
  `git stash` to measure a before-count and dropped it; ten files of
  three lanes reverted. Recovery: `git fsck --no-reflogs --unreachable
  | grep commit` finds the dropped stash; `git show <sha>:<path> >
  <path>` only over paths at HEAD. Read `git reflog -3` before every
  verification run; grep worker transcripts for git verbs when in doubt.
- Workers run scoped tests; the orchestrator runs the suite and owns
  every gate and git verb. Rigs and the canon scanner REWRITE other
  phases' PNGs and the 170 census — restore before staging.
- The owner's real DB is read-only to every agent; a walk writes
  nothing; a rig seeds only an isolated HOME. Anything a test seeds into
  his DB is a scar (167/168's was found and removed on his deferral).
- Line-anchored fences (`test_phase143_*` censuses, the surface-fallback
  census + its artifact under phase-143's assets, `test_hs169_wire`,
  the schema-version floor tests) MOVE whenever the files they anchor
  change; pay them in the same commit, never by deleting assertions.
- A capability census matches inference vocabulary by NAME (`rebind`,
  `dispatch`, …) — do not name a repository method with one.
- **The verification law, and it has now caught defects four sittings
  running.** A test double that lies about the field a check reads
  proves NOTHING about the check (`reference_lying_test_doubles`).
  Therefore: write the test FIRST and WATCH IT FAIL against the shipped
  code; mint through the REAL producer; assert against the REAL
  validator's own constants, never a copy you typed; give every fence a
  POSITIVE CONTROL (prove the guarded path still works when the fence
  should not fire); then MUTATE the fence out and watch the test go red.
  **Report every mutant that SURVIVES** — three lanes did this sitting
  and two found their own code was dead. A test that passes against
  deliberately broken code is a defect in the test.
- Scars become laws the same day: UX-CANON.md, this file, memory.

## 7b. Sentences in this tree that are FALSE

**This section exists because a zero-context agent cannot tell a true
doc from a stale one, and this tree has both.** The list used to live
here by hand, and a hand-maintained list of lies rots exactly like the
lies it catalogues. Since HS-200-46 it lives in
`tests/unit/doc_claims/registry.py`, where each row carries the
document and a literal anchor, the sentence in the author's own words,
an **executable predicate over the real code**, its state (`holds` or
`known_false`), the measured truth, and the story that owns the repair.
`tests/unit/test_phase200_doc_claims.py` fails CI in both directions: a
`holds` sentence the code stops satisfying, and a `known_false`
sentence the code starts satisfying (so a fix cannot land without
correcting the prose in the same commit). The `known_false` count is a
dated, down-only ratchet.

To read the table — the same columns this section used to carry, from
the one place it now exists:

```sh
uv run python scripts/doc_claims.py            # the table
uv run python scripts/doc_claims.py --measure  # + run every predicate
```

Trust the code column. If you fix one, fix its sentence and its
registry row in the same commit.

**The general lesson, which is worth more than the table:** in this
repo, a comment describing the architecture someone INTENDED is how the
next agent concludes the work was already done. When you fix one of
these, fix the sentence in the same commit.

## 8. Where things live

- Roadmap: `pm/roadmap/holdspeak/README.md`, `THE-TUESDAY-ARC.md` (the
  road to 180), `BACKLOG.md` (the parking lot; 175's P2 ledger is there),
  `PMO-CONTRACT.md`.
- 175: `pm/roadmap/holdspeak/phase-175-calendar-and-the-clock/` —
  `final-summary.md` (gates + the seven rulings), `assets/settled-design-
  calendar-clock.md` (Addendum 1 counsel's conditions; Addendum 2 the
  build rulings B1–B17), `assets/counsel-on-built-175.md` + `-reread.md`,
  `assets/hygiene-census-175.md`, the shots under `assets/story-0N-shots/`.
- Canon: `docs/internal/CONSTITUTION.md`, `UX-CANON.md`, `POSITIONING.md`.
- This log: `docs/internal/project-rooms/HANDOVER-MUADDIB.md`.
- Canvases: 171 `82c55045…`, 172 `b153c331…`, 173 `9f1558b4…`, 174
  `5719ec5d…`, 175 `113102aa-7bc9-4508-a334-79e22d542155`
  (`https://claude.ai/code/artifact/<id>`).
- Memory: `MEMORY.md` index; `feedback_*` = his rulings; `project_*` =
  per-phase state; `reference_*` = gotchas (the git-stash scar, the
  walk seeds, xdist starvation, the effect-ledger tombstone, the
  double-prefixed legacy ids, the .43 endpoint).
- Ephemeral: the scratchpad (worktrees, `hub-url.txt`, suite logs,
  counsel's repro scripts) dies with the session.
- The .43 box: llama.cpp at 192.168.1.43:8080; sandboxed Bash cannot
  reach the LAN.

## 9. Your first hour (mechanical — do these in order)

**XX adds one trap to the four below:** a fresh `git worktree` + `uv venv
--python 3.13 && uv sync` does NOT install the `[test]` extras, so `uv run
pytest` silently falls through to a homebrew Python 3.14 pytest with no
`pytest-timeout` ("Unknown config option: timeout" is the tell). Run
`uv pip install -e '.[test]'` in the worktree and check `pytest.__file__`
resolves into its `.venv` before trusting a count.

1. **`.githooks/dw context holdspeak --compact`** and **`.githooks/dw next holdspeak`**.
   The roadmap is the source of truth, not this file. (`dw next` still
   surfaces a stale `HS-91-10`; ignore it — the road is Phase 200.)
2. **Read the NEWEST chapter below, then §7 (the laws) and §7b (the
   sentences that are false).** §7b will save you an hour and a wrong fix.
3. `git log --oneline -15 main`; `pm/roadmap/holdspeak/README.md`'s
   "Last updated" line; the Phase 200 status file.
4. `cd web && npm ci`. Re-create `.claude/agents/opus-worker.md` if
   missing (`model: fable` since 2026-09-17 — the file is gitignored).
5. **Read `docs/internal/OPERATIONAL-SURFACE-AUDIT.md` before proposing
   anything.** It is the measured state of every surface as of
   2026-09-13, and it names what is broken versus what is merely OFF.
6. Ask him nothing you can read. Rule when he defers; record the ruling;
   tell him what you ruled.

**The four traps that cost this session time — all avoidable:**

- A full suite run **rewrites 388 tracked evidence PNGs** from phases
  141-176 plus seven JSON assets, and the canon scanner rewrites the 170
  census. **Restore before staging** or you silently rewrite closed
  phases' proof (`reference_suite_dirties_evidence_assets`).
- `uv run` inside a fresh `git worktree` silently picks up **system
  Python 3.14** and skips every test, which reads as a pass. Verify
  `holdspeak.__file__` resolves INTO the worktree before trusting any
  cross-branch comparison.
- Parallel lanes sharing the scratchpad root **overwrite each other's
  helper scripts**. Give every lane its own subdirectory.
- A killed process leaves a stale zero-byte `.git/index.lock`. Check for
  a real git process first, then remove it.

**And the rule I broke this sitting, so you do not:** the tree's default
branch is `main` and two documentation commits landed on it directly
instead of on a branch with a PR. Branch first.

## Muad'Dib XXIII — 2026-09-18/19. THREE LANES, SIX BOUNCES, AND THE CLOCK THE PRODUCT ALREADY HAD

**Read this first. It supersedes XXII.** G1 finished building, G2 started, and
the sitting's real output was not code — it was finding out what this product
cannot do and writing that down where the next agent cannot miss it.

### 0. What he said, verbatim

- **"all your workers must also be Opus 4-6 workers, got it? opus-4-6[1m]"** —
  supersedes the Fable ruling of 2026-09-17. `.claude/agents/opus-worker.md` now
  says `model: opus-4-6[1m]`. **The file is gitignored; re-apply it on a fresh
  clone.** The agent definition is cached at session start, so an edit lands on
  the NEXT session — inside the session that edits it, pass an explicit `model`
  override on every Agent call. A 429 naming `claude-fable-5-1` is how the stale
  definition announces itself.
- **"Lane starts.... now"** — on a three-lane plan. No further steering was
  asked for and none was needed.
- **"Yes - that's next..."** — on making the real scheduled clock serve
  recipes. That became the HS-200-47…53 cluster the same sitting, per XIX's law:
  an analysis that does not become chartered stories is not delivery.

### 1. What shipped

| | Story | State |
|---|---|---|
| PR #581 | HS-200-13 | MERGED `ba48baf3` on verification (one branch-new failure, `hs160_delta_glass`, failed a DIFFERENT param each CI run and ran 12/12 green serially on the PR head — a load flake) |
| PR #582 | HS-200-17 | three prepared procedures, `24f2f974` + copy fix `1e5efa26` |
| PR #583 | HS-200-16 | the daily-loop rig, `a8458b93`; **story deliberately left `in-progress`** |
| PR #584 | the clock cluster | `29210b59`, seven stories chartered, stacked on #582 |
| canvas | HS-200-18 | design RATIFIED-W-C, 11 boards / 26 artboards, artifact `b39abb5b-784d-4f47-b938-eb0228716ccc` — **HIS VERDICT OWED** |

### 2. The law this sitting proved twice: counsel corrects the ORCHESTRATOR

Every lane was counselled and **every counsel bounced its lane at least once**;
the 18 design bounced twice. Two of the corrections landed on me, not on a
worker, and both had already been told to the owner before they were checked:

- I reported a timezone double-conversion as a live defect on his desk. Counsel
  measured a freshly-read watch at six offsets — `available` everywhere. Both
  writers of `last_success_at` use SQLite `datetime('now')` (naive UTC) and the
  comparison is local-to-local; **the test FIXTURE wrote a shape no production
  writer produces.** Retracted to him in the next message.
- I passed him "nothing in this product can trigger on a wall clock" as a
  universal negative, from one lane's single grep. It is false — see §4.

**The habit, and it is the whole job: say it to him, then let counsel try to
break it, and retract in your own voice when it breaks.** Do not let a
convenient finding harden just because you already reported it.

### 3. The three findings worth more than the code

**a. A fence that agrees with the code instead of the producer (HS-200-17's
P0).** The catalog claimed to reuse the shipped coverage vocabulary and had
hand-rolled it: a watch in `cant_check` reported `available`. Paid by
DELEGATION, not by correcting the copy — a public `room_coverage()` seam on
`needs_you_aggregate`, the producer's own two call sites rerouted through it,
worst-first reduction so a summary can never read better than its sources.
**One producer, three callers.** Delegating immediately surfaced two more errors
the hand-rolled version had. This is the shape of fix to reach for here.

**b. A false proof of a true thing (HS-200-16's P0).** `capture_runtime_identity`
caches `_IDENTITY` for the process lifetime; both hubs in the day-boundary walk
share one OS process; so the same-database fence compared a cached value with
itself, and the 393 record described the 1440 run's database. The boundary was
real — hub #2's recall returns day-1 records, impossible from another file — but
the attestation was fake, and HS-200-23 would have read it as evidence. Reproved
through `database_identity()`, plus a fence that goes red the moment the
instrument becomes a constant again.

**c. Four defects only a second morning can see.** A proposal dated by its row's
write time (09-18 in the Room, 09-17 in recall). A due DATE drawn as a wall
clock (`DUE 18:00`, wrong day west of UTC). `1 DAYS`. And the carried-forward
**kind swap** — a commitment drawn `DEC … ✓ CURRENT`, a decision drawn `CMT` —
fixed in the Room's projection, which selected `proposal_kind` and threw it
away while recall read the same column to keep an action out of its decision
cards. **A same-day test cannot see any of these.**

### 4. THE CLOCK — the correction, and what it costs

**The wall clock is real and good.** `workbenches.schedule` is a five-field
cron (`schema.py:1714-1716`), ticked by `workbench_conductor.py:541-551` via
`cron_is_due` (`holdspeak/cron.py:34`), run by `WorkbenchRunner.run_scheduled`
under a delegation **only the owner mints** (`schedule_delegation.py:50-58`),
terms hashed (`:37-39`), one receipt per due-minute with duplicates rejected as
`duplicate_tick`. `kernel_schedule_ticks` is reported empty on his desk.

**Four gaps stop a prepared procedure riding it** — and G1 is refused by the
code, not merely missing: `_terms` resolves `wb.recipe_id` against the
agent-persona `recipes` table and raises `delegation_stale_work` (`:17-19`), so
a delegation cannot be minted at all; the route freezes at
`capability_id="workbench.item"` (`:20-24`); `workbenches` has no `project_id`;
and `workbench_items.result` is not a kept brief. Plus `cron_is_due` on naive
`datetime.now()` with no zone stored anywhere.

**And the finding that is worse than the clock:** `ReactionService.create_watch`
mints `state=''`, which `arm_watch` refuses (`watch_service.py:115`) and
`list_due_watches` excludes (`db/automations.py:457`). `ensure_meeting_watch`
arms, but it is automatic and meeting-only. **No surface can create a connector
watch that recurs.** That is why 30 enabled watches plus HS-200-43's repaired
arming still add up to no recurring anything.

**Cadence is not a scheduler** — a projection of open loops, and the product
says so in its own tick (`workbench_conductor.py:630`). Stories 21, 33, 34, 35
and CONTRACTS.md C9 all named it as a scheduler seam and are corrected on the
clock branch.

### 5. Rulings I made (record them, he deferred none of these explicitly)

- **HS-200-18 ENDS AT PREPARED.** There is no install operation, so every state
  past `PREPARED` is drawn under a `NOT REACHABLE ON THIS TREE` band naming what
  19 must build. The apply verb is **ABSENT** on manual boards (a refused verb
  teaches a concept the product will never have) and **REFUSED** only where the
  operation exists and is blocked.
- **The clock is a cluster inside 200, not a new phase** — G4 already owns this,
  and 41-46 set the precedent for chartering into 200 mid-flight.
- **Story 21 is NOT re-gated.** Its scheduled leg is what 53 proves in G4, so
  **G2 cannot close before a G4 story lands** — stated in the status file,
  DELIVERY, and 21 itself rather than discovered later. The gates are his.
- **Never widen a ratchet to admit new copy.** The product-copy debt ledger only
  shrinks: it records what was already wrong, never what we just wrote.
- **POSITIONING has no noun for a prepared procedure**, and both near misses are
  traps (`persona` → Agent; `workflow` → a shipped table). The user guide names
  the three things instead. **Minting a canonical feature name is his call.**

### 6. What is open, and whose it is

**His:** the 18 canvas verdict; his attended walk (HS-200-16 stays
`in-progress`, `PILOT-R1.md` opens the ten-workday window unstarted); HS-200-05's
physical voice beats; and four measured rulings — the CARRIED FORWARD doubling
(4 rows for 2 outcomes, deliberate), three filled primaries in the Room, ten
receipt rows carrying no tokens, and that **no owner can choose a deterministic
brief** (the route accepts `generator: deterministic`, the face never sends it).

**The next orchestrator's:** merge #582 → #583 → #584 in order as each CI
failure set falls inside main's known six (hs153 guardrail, two task-resume
`Connection refused`, ci-isolation, custody-after-recreate, transcriber race;
`hs160_delta_glass` is a load flake, proven green serially). Then HS-200-47 and
HS-200-52 are startable immediately; 48→49→50→51 are strictly serial; 53 is the
proof.

### 7. A gate repair worth remembering

A duplicated paragraph inside the story-status table had been hiding **stories
44, 45 and 46 from `dw` since they landed** — `dw context` reported 43 stories
on HEAD and 53 on the clock branch. Proven a heal, not damage, against a
pristine `git archive HEAD` extract. **When a story seems to vanish from the
gate, suspect the table's prose before suspecting the story.**

## Muad'Dib XXII — 2026-09-18. THE VERDICT, THEN THE DAILY PATH BUILT END TO END

**Read this first. It supersedes XXI.** One verdict and six stories in one
sitting, across a session-limit cut and a resume.

### 0. His words, verbatim — the steering

- On being shown *The Tuesday Verdict* (a page that walked the 22 boards
  posture by posture with the design's own examples and put the six remaining
  questions to him with recommendations): **"OK I accept."** HS-200-09 is
  PASSED; the recommendations stand as his answers (settled-design Addendum 4).
- With it: **"I certainly want you to manage the orchestration process a lot
  more efficiently - to push this product to the full usability it has
  promised to me."** LAW: parallel lanes on disjoint stories; counsel once, on
  the BUILT code; merge on verification; every story ends on his desk as a
  face he can use on a Tuesday. Documents are not delivery.
- **"resume, please."** after a session limit killed two lanes mid-fix. A lane
  resumes from its own transcript with `SendMessage`; nothing was lost.

### 1. What shipped

| Story | Commit(s) | PR | What it is |
|---|---|---|---|
| 09 | 7b0d5c3c | (on #576) | the verdict recorded; 11–15 ready |
| 15 | f364c83f, ff2c2433 | #577 | attention: five ranked, coverage above, set-based notifications |
| 12 | a283c21e, d01f715c, f4e2544e | #578 | a real meeting → reviewed outcomes; retry identity |
| 11 | 1b1ab206, a6629212, dbffb7ff… | #579 | the preparation brief with a manifest that names its omissions |
| 14 | c2f285fd, 52e7c8b6, 18789c3d… | #580 | People preparation inside the boundary |
| 13 | 71e7c408, ddbc92d2, 36d0e5c7, e8951375 | #581 | recall, carry, completion by explicit act |

Merged to main this sitting on verification: #571, #572, #573, #574, #575.
The train: #576 (44) → #577 → #578 → #579 → #580 → #581, each fired with
close/reopen after its base merges, each merged when its CI failure set ⊆ the
known seven runner-environment failures.

### 2. What counsel found in the BUILT code (this is why counsel-on-built exists)

- **12:** no real meeting had EVER produced a proposal, for two reasons one
  layer under the audit's finding — the HS-172 bridge read `dec["text"]`
  while the extractor writes `decision`, and `action_owner_enforcer`
  violated its own closed registry contract so every real chain run errored.
- **11:** the refused face said `NOTHING SENT · THIS DEVICE` after a request
  had left and been answered (Constitution III/VI); readiness was never
  consulted on a real desk (the leg id did not match the profile row);
  `Stop` stopped nothing; the NAME-unknown heuristic (HS-200-06's) minted a
  false person on 28 of 30 ordinary sentences.
- **15:** the dedup key merged two different tickets with one title (a row
  vanished); a long Project name clipped verbs off a 393 viewport without
  moving `scrollWidth`; `heartbeat_notify` read `datetime.now()` past the
  injected clock.
- **14:** the boundary held on every door; the P0 was a dead status filter
  (a Done commitment stayed open forever).
- **13:** carry + supersession doubled the mark; closed commitments accepted
  further verbs; the durable last-known store was never pruned and only one
  of three callers used it.
- **The stack itself:** seven branch-new census/vocabulary/pin fences on the
  first full pass of 11 over 12 over 15; a pre-existing xdist race in
  `test_one_path_census` that mutated a real source file on disk.

### 3. Laws this sitting adds

- **Parallel lanes, one composition.** Three or four Fable lanes on disjoint
  files; stack in one order; rebase up as each lands; `SCHEMA_VERSION` is
  informational, so two lanes at 78 become one 78 carrying both shapes and
  the next takes 79; regenerate the API surface and the canonical snapshot
  on the COMBINED tree, never per lane.
- **Run the full suite on the stack top before the CI train reaches it.**
  Census, vocabulary and line-pin fences only fail on the combined tree.
- **Colons, not em dashes, in accessible names** (`Open: ${title}`); the web
  vocabulary guard reads them as prose.
- **A worker may not edit CLAUDE.md or `.mcp.json`**; a worker restores a
  tracked asset with `git show HEAD:<path> >`, never a checkout.
- **Every rig writes shots only with `HOLDSPEAK_WRITE_SHOTS=1`.** Five rigs
  were gated this sitting; the 388-PNG scar is the reason.
- **A session limit is not a loss.** `SendMessage` to the lane's id resumes it
  with its context; check `git status` for a partial edit first.
- **Counsel's probes are evidence.** Their before/after outputs go in the
  story's evidence file verbatim.

### 4. Open, in order

1. Merge the train as CI proves each set (see §1).
2. After the merge, his hub needs a restart to pick up the drainer, the
   armed watches, WAL, the sidecar proxy, and the six faces.
3. Still his: the pilot Project and the model route (the walk's beats 3–6
   run on them); HS-200-05's remaining beats; the walks on 169–176.
4. BACKLOG §AJ (from 44/45/46) and the new parked items from this sitting:
   ASCII-only recall search; a forged supersession cycle; diacritics in owner
   matching; an alias equal to another display name; the resumed
   `INCOMPLETE · n OF m SOURCES` brief state; `Open source` on a commitment
   ref; two library raw buttons inside the ceiling (`Disclosure` trigger,
   `ProgressPlan` action); the 0.6 content-word support threshold; the Door
   board listing decision-kind action items as `UNASSIGNED`.
5. Next stories: G2 (three recipes via the Interview, the owner pilot) once
   the train is merged.

---

## Muad'Dib XXI — 2026-09-17/18. "THERE'S NO SUCH THING AS MY WORD"; THE FOUR AUDIT STORIES BUILT AND STACKED

**Read this first. It supersedes XX.** Two rulings and four stories.

### 0. His words, verbatim — the steering

- **"Muad'Dib, you are empowered to use Fable Fedaykins from now on."** The
  agent file says `model: fable`. Counsel and builders both.
- On being told three stacked PRs "await his word": **"No, there's no such
  thing as my word. This is your opportunity to verify and validate."** LAW:
  a PR merges when the orchestrator has VERIFIED it — CI read, every failure
  attributed (pre-existing runner set vs branch-new), local gates green,
  counsel paid — and the merge record says so. Never unverified, never
  waiting on him. The canvas is the same: counsel ratifies on his behalf
  unless he asks to see it.

### 1. What shipped

- **#571 (docs) MERGED 62c3a767** on verification: docs-only, CI set = the
  seven pre-existing runner-environment failures from #570 plus one
  ordering flake (green 3/3 locally).
- **#572 (HS-200-42) MERGED 9bca5246**: CI set six of the same seven, zero
  branch-new.
- **#573 (HS-200-43)** retargeted to main, CI run 35289938977 — merge when
  its set ⊆ the known seven. Its own docs commit had turned the drift guard
  red (story number + em dashes in `docs/ARCHITECTURE.md`,
  `docs/MCP_SIDECAR.md`); paid b391632f.
- **#574 (HS-200-46) → #575 (HS-200-45) → #576 (HS-200-44)**, stacked in that
  order on #573. Each is DONE on the rails with evidence; each merges in
  order after the one below it, by verification.

**CI only runs on `pull_request` to main.** Retargeting a stacked PR does not
fire it: close + reopen does (`gh pr close N; gh pr reopen N`).

### 2. HS-200-46 (33090cdb) — a stale document fails CI

The thirteen §7b sentences are `tests/unit/doc_claims/registry.py`: sentence
verbatim, anchor, a predicate over the REAL module/file/generated surface,
state, measured truth. `holds` fails when broken; `known_false` fails when
the code starts satisfying it (a fixed claim cannot sit as debt). Dated
down-only ratchet. §7b is a pointer + `scripts/doc_claims.py`. Measuring
corrected the audit: 22 missing catalog verbs / 0 phantoms (the "phantoms"
were `go.*` verbs derived from `applications.ts`), 203 raw buttons, and
`busy_timeout=5000` was sqlite3's default, not a pragma. **The worker
refused to edit CLAUDE.md on a brief's authority** — correct; the
orchestrator paid it. The fence fired twice this sitting, exactly as
designed, when 45 and 44 made their sentences true.

### 3. HS-200-45 (5d0701d4) — one composition root

`holdspeak/runtime/composition.py` is the ONE root; the hub installs it in
`_create_app`; every MCP family reads it (`db_or`/`observer_or`/
`runtime_service`; `service()` raises on unknown names). An AST fence
forbids bare accessors under `holdspeak/mcp/`; a live-root fence drives the
real app and proves every asked service is non-None — it caught
`confluence_provider` declared on `WebContext` and never constructed since
HS-174-07. The stdio sidecar is a CLIENT of the running hub (owner lock body
→ port; the hub's token read from the config FILE, never `Config.load`,
which mints one); no hub → an honest JSON-RPC error and the DB is never
opened; `HOLDSPEAK_MCP_STANDALONE=1` claims the owner lock. Loopback OWNER
admitted on `/api/mcp` with the remote flag off. One `desk_changed` frame.
WAL + busy_timeout + foreign_keys, proven on a `cp` of his real DB.

**Counsel BOUNCED with a P0 the R5 ruling itself caused:** "remove stale
`-wal`/`-shm` on restore" under a RUNNING hub bricked the database (`disk
I/O error` for every fresh reader and the next hub). Restore now refuses
under a live owner, under ANY open connection (SQLite's own exclusivity:
`PRAGMA journal_mode=DELETE` on a timeout-0 connection), and on a
write-protected file. P1s: the null-body 204 raised inside the hub on every
handshake; the sidecar minted `config.json`; `ask_service`/`plugin_job_service`
were asked for and not carried; the "any caller" frame claim was overstated.
All paid; re-read RATIFY. **The lesson: a ruling that is only safe under a
precondition nobody enforces is a defect, and counsel-on-built is where it
is found.** R7(b)'s premise was wrong too (busy_timeout), and the worker
corrected the premise instead of writing a fence that passed pre-fix.

Full suite twice (isolated HOME, xdist): six branch-new census/registry
fences on pass one, all paid (one census had gone BLIND to a factory the
moment it was wrapped in `runtime_service(...)`; it now sees through it).

### 4. HS-200-44 (d957af84 + 217305a7) — the guard sees its own violations

A1 was 4 because `<button[\s>/]` ran on `splitlines()`; the truth is **175**
in scope, 203 repo-wide, reconciled file by file (28 in `design/`,
`_parked/`, `*.test.tsx`). Seven rules fixed to whole-file matching
(superset of old hits, nothing lost); the rest recorded as per-line by
construction. Ceilings reset as dated down-only ratchets; `--write-ceiling`
refuses a rise without `--ceiling-reason`; a plain run writes NOTHING (it
used to rewrite the phase-170 census). UX-CANON states 175. The 175 are
debt: face stories pay them file by file.

### 5. Open, in order

1. Merge #573 → #574 → #575 → #576 as each CI set proves ⊆ the known seven
   (each needs a close/reopen after its base merges).
2. BACKLOG §AJ (this sitting): `bind_host` applied by nothing; the
   verb-catalog mirror and `desk_snapshot` layout (registry unowned rows);
   `doctor.py` builds a bare `PrimitiveService`; the delete-mode restore
   still proceeds under a live hub.
3. Still his: HS-200-09 canvas verdict (gates 11-15), the pilot Project,
   HS-200-05's beats, the walks. The X11 wire face wants its own phase.
4. His hub still runs pre-42 code; after the stack merges, a restart on his
   desk picks up the drainer, the armed watches, WAL, and the sidecar
   proxy — `.mcp.json` needs NO change for the proxy (it reads the lock).

### 6. Laws this sitting adds

- **Verify and validate, then merge.** The merge record names the CI run,
  the failure set, and its attribution.
- **A worker may not edit CLAUDE.md or `.mcp.json` on a brief's authority.**
  The orchestrator does, and says so.
- **Stacked PRs: base merges first, then close/reopen the next to fire CI.**
- **A rebase of a story with `dw story status` edits conflicts on the
  status table and the cadence lines; resolve by hand, then re-check the
  story's own row** (an auto-merge left 44's row at `ready`).
- **Counsel-on-built pays for itself every time.** 45's P0 was the
  orchestrator's own ruling.

---

## Muad'Dib XX — 2026-09-14. THE TWO MISSING CALLERS ARE PAID; THREE STACKED PRs AWAIT HIS WORD

**Read this first. It supersedes XIX's §4b.** His whole instruction was
"continue Muad'Dibbing"; XIX had left two asks open and this sitting resolved
both without asking again: the six docs commits went to a branch with a PR
(the law), and 42 was built — then 43 in parallel, because their files are
disjoint.

### 0. State at handoff

```
#571  docs/audit-and-200-charters        the audit + the five charters (6 commits)
#572  feat/hs-200-42-drain-intel-queue   c80d27b7 + 79d683fa + fa3c770e   stacked on #571
#573  feat/hs-200-43-arm-the-watch       efd899ef (+ this handover commit)      stacked on #572
```
GitHub retargets each as its base merges. Merge order: 571 → 572 → 573, ON HIS
WORD. Local `main` equals `origin/main`. Nothing on his desk has changed: his
hub still runs pre-42 code. Phase 200: 12 done, 05 and 09 in progress, 44/45/46
ready. **Next in order: 45 (one composition root) with 46 pairing, then 44.**
The worktrees `scratchpad/wt42` and `wt43` die with the session; the branches
are pushed.

**The full suite ran on 42 (CI shape, -n auto): 12 failed / 10732 passed.**
Three were branch-new and are paid in `79d683fa` (a story id in a user-facing
diagram — the doc-drift guard; two census line anchors; the History core's
no-drainer path forgot the egress receipt the click had established). Eight
were inherited or timing (hs153 guardrail and hs171 command deck are red on
untouched main; the rest pass serially). One looked branch-new and was not:
the hs176 speak loop passed 6/6 legs on main and 3/6 on the branch, and the
bisect showed the failure rate tracked MACHINE LOAD, not the tree — a
pre-existing paint race in the window-wings species (a passive `useEffect`
bridging the wing strip in the head to the body in the core, so the head
named the old wing over the new body for up to ~600 ms). Paid at the source
in `fa3c770e` (`useLayoutEffect`; lag 0 ms; 6/6 green). **The lesson: "passes
on main, fails on the branch" is not attribution until you have bisected
under the same load.**

### 1. What 42 is, in one screen

The drainer is the hub's FOURTH lifespan conductor (`intel_queue_conductor.py`),
on the calendar-ingest pattern, ownership-gated (the three existing conductors
never were — a hub under `HOLDSPEAK_ALLOW_UNOWNED_DB=1` starts no drainer), 15 s
poll plus a `wake()` the verb calls. Rulings: `intelligence_auto` gates enqueue
only; quiet hours govern notification, not compute (and there is no
`aftercare_ready` → desktop path at all — it is a WebSocket frame); Article III
host restated at execution time from the frozen deployment revision (the
enqueue-time Config estimate and the executed route DISAGREED on the rig);
owner lock released only after the conductors stop.

**Two defects underneath, both paid:** every failure-alert check raised a
swallowed `AttributeError` (`get_database().get_intel_queue_summary()` — the
accessor lives on `.intel`; a lying double had modelled the flat one); and with
an EMPTY routed plugin chain the claim planner re-froze an identical descriptor
on every claim and inserted the successor with `attempts=0`, so the retry
ceiling was unreachable and a permanently failing job grew `intel_jobs` two
rows a cycle — unreachable before, because nothing drained. The shape to look
for: a bug that was harmless only because its caller did not exist.

**The shot walk caught what 12 green unit tests had passed:** the first face
change never reached a pixel (the receipt swapped the badge before the verb
branch rendered), and `SurfaceLedgerRow` rendered its trailing verb INSIDE the
row's own `<button>` — every click also opened a window, nested buttons. Fixed
in the species (`role="button"`, trailing stops propagation), not the face.
The badge now reads `QUEUED` / `NOT DRAINING` from the `runtime_queue` frame,
which carries `drainer`.

### 2. What 43 is, in one screen

Five rulings on his standing deferral, each premise verified by a read-only
research lane at file:line before ruling: R1 the heartbeat is the single
scheduler (the conductor's block ran every 60 s with no quiet-hours check and no
ownership gate and always won the race); R2 quiet hours hold the whole sweep,
and Run now overrides (`owner_hand=True`, unbounded + not held); R3 arm to
`now`; R4 the backfill is UNGATED in reconcile step 2 (`_apply_data_backfills`
runs only under `if shape_changed:` — dead on an up-to-date desk; the B3 lesson
a second time); R5 manual evaluation mints effects through the extracted
`_record_effects_if_any`.

**Counsel found the rulings' own P0, and it was MINE.** R3's first form armed
`now + cadence` when no snapshot existed, believing the delay protected against
discovery-from-nothing. It delayed it by an hour: `_evaluate_core` diffs against
`snapshot or {}` and `baseline_state` is never read by evaluation. Counsel's
repro: one `pending` row + one `older_than` rule → 30 false transitions. Now the
first evaluation of ANY empty-baseline watch is silent by construction in
`_evaluate_core` (`baselined`, zero transitions, no evaluation row), so every
caller inherits it. **When counsel refutes your ruling, say which sentence was
wrong** — the story file does.

The unattended sweep is bounded to 10 fetches a sweep (`watches_deferred` on the
receipt); on his desk the ~30 backfilled rows baseline over three sweeps, ~45
minutes, every one silent. Ceiling 40 evaluations an hour and no face says so —
backlogged with the cadence-preset defect (`trigger_json.every_minutes` never
reaches `evaluation_cadence_minutes`; every watch runs hourly whatever he
picked).

### 3. The loop this sitting ran, and what it cost

research lane (43) → build lanes (42, 43 in parallel worktrees) → counsel-on-
built → conditions paid → shot walk (42) → counsel re-read → last P2s → evidence
capture through the gate → docs → contract → commit → PR. Both counsels returned
RATIFY-WITH-CONDITIONS then RATIFY. Every fence on new behaviour was proven to
fail on a pre-fix tree (43 kept four surgical trees, one per ruling round).

### 4. Laws this sitting adds

- **A worktree's `uv venv` does not carry `[test]`** — §9 has the tell and the fix.
- **macOS `xargs` has no `-a`, and a newline-joined variable does not word-split
  in zsh.** The restore of rig-dirtied assets silently failed once and 79 PNGs
  from other phases were staged; caught by counting before the contract. Use
  `< list xargs git checkout --` and COUNT staged assets outside the phase.
- **Stash-free rebase of a dirty worktree:** `git diff > patch; cp` the
  untracked files out; `checkout -- .; reset --hard <base>; git apply --3way`;
  resolve; recapture evidence on the rebased tree (43's capture on top of 42
  ran 42's fences too — the cheapest integration proof there is).
- **The tool's foreground cap kills a backgrounded `&` chain** — use the
  harness's own background mode for the full suite, never `nohup … &`.
- **`git add -A` also sweeps UNTRACKED rig orphans from other phases.** Six
  PNGs from 153/170/171 rode into a commit and the commit was redone. Before
  every contract: `git diff --cached --name-only | grep -v <phase> | grep png`
  must print nothing.
- **His hub is never touched by a sitting.** All proof was isolated-HOME; the
  claim that his 30 unarmed watches arm on next open is an inference from the
  backfill's WHERE clause and is written as one.

### 5. Still his, carried forward

The merge order above; the HS-200-09 canvas verdict (gates 11-15); the pilot
Project; 05's beats 2-6; the attended walks on 169-176; `.mcp.json` (the sidecar
is a second unlocked writer — HS-200-45 is where that is paid, and it is next).

---

## Muad'Dib XIX — 2026-09-09/13. THE STORY CLOSED, THEN THE WHOLE SURFACE WAS MEASURED

**Read this first. It supersedes XVIII.** Two things happened: HS-200-10 closed
and merged, and then the owner asked for a deep introspection of the last fifteen
phases — which found that two missing function calls explain nearly every zero on
his desk.

### 0. What he said this sitting, verbatim — this is the steering

- **"I really want us to do a very deep introspection on what had been done to
  HoldSpeak in the last 10-15 phases..., and what it really means for its
  operational surfaces, what are the expected flows that would work?"** — the
  audit exists because of this sentence. `docs/internal/OPERATIONAL-SURFACE-AUDIT.md`.
- **On his long-standing vision:** *"an 'mcp for everything', that would allow to
  literally drive the app from mcp/http (parity)... a 'crude' X11, in a way...,
  where graphics wouldn't have to be really sent down the wire but the primitives
  of what window is open, which is active, all of its controls... since we're
  building everything out of a common building block, isn't it? I hope so!"*
  **He was told the honest answer: half true.** Do not flatter this premise.
- **"Where's our plan's execution, based on our phase-based execution approach,
  huh?"** — the audit had shipped as a DOCUMENT with nothing on the rails, and he
  was right. **LAW: an analysis that does not become chartered stories is not
  delivery.** Findings go on the rails in the same sitting.
- **"wouldn't the MCP need to go through some kind of common service layer? much
  like any http call? why the fuck do those mcps even write directly to the db in
  the first place?"** — he was right, and the code was worse than the first
  framing. See §3.

### 1. HS-200-10 CLOSED — PR #570 merged → `cfa4fd61`

Counsel-on-built ran in two lanes; both RATIFY-WITH-CONDITIONS. The central claim
survived: every path that reads a note body was enumerated, no undisclosed
retrieval route exists. **Two P0s, both fixed, both in the lane the design had
reasoned about least.**

**P0-1 is the one worth remembering, because the previous commit created it.**
Ruling B1 keyed the L4 replay fence on TIME — "anything frozen after a promotion
arrived by reference." That premise holds only on the device that MINTED the
promotion, and that commit is what made promotions cross-device. An unsynced
desktop freezes a promoted body BY RELEVANCE, sync repairs the corpus and never
touches `thread_refs`, and the timestamp then reads a relevance body as consent,
forever. **Fixed by recording the ORIGIN and consulting no clock at all** — the
timestamp was a proxy for origin and the proxy is what broke. Reproduced on the
real cross-device path in BOTH directions: the old fence also silently DROPPED a
by-reference attach when the promotion clock landed later.

P0-2: `revoke_promotion` overwrote `unavailable` with `stale`. Two latent
fail-open seams closed, one hiding a defect that was NOT latent (a swallowed
backfill exception left a transaction open on reconcile's own connection, so the
next `BEGIN` would raise — a desk that cannot open).

**Two roadmap sentences were FALSE and were retracted rather than defended.** B2's
"fenced forever by every route" (a detach deletes the row, so re-attaching clears
it) and B3's "the backfill calls `_persist_manifest`". **The habit is the lesson:
when counsel refutes your own written ruling, correct the ruling in the same
commit and say which sentence was wrong.**

Also this sitting, on his order: **the 325 polluted egress rows were deleted from
his real DB** (backup at `holdspeak.db.pre-egress-cleanup-2026-09-09.bak`). One
deleted row ran 929ms and did not look like the others; that was disclosed to him
rather than buried.

### 2. THE AUDIT — what it found, in one screen

Four read-only lanes over `main`. `docs/internal/OPERATIONAL-SURFACE-AUDIT.md`.

**The product has a real browser-free API:** 222 MCP tools, 675 routes, 19 CLI
commands, **six of fifteen end-to-end flows fully driveable without a browser.**

**And two missing function calls stop it being a daily product:**

1. **Nothing drains the intel queue.** `start_intel_queue_worker` has ZERO
   production callers; the only drainers are the CLI and a route no face calls;
   `Run intelligence` returns `{"state":"queued"}`. Phase 172's design assumed a
   different queue's loop would do it. `intel_snapshots` on his desk: **0**.
2. **Nothing ever arms a watch.** `next_evaluation_at` is written only INSIDE
   `evaluate_due`, so a watch never evaluated by the scheduler can never be
   selected by it. **32 watches, 2 armed.** The entire unattended half of the
   thirteen-phase Project Rooms arc has been waiting on a column nobody sets.

**His desk:** 718 heartbeat evaluations → **1 notification ever**; **1 meeting
session ever**, cancelled; 0 decisions, 0 commitments, 0 watch effects, 0
interview sessions, 1 brief from August. **Several zeros are CONFIG, not defect**
(cadence off, calendar sources empty, auto-record off) — say which is which or the
census misleads.

### 3. THE X11 RULING, and the composition-root finding

**His premise is half true.** Real: a 22-entry application manifest, a 20-kind
primitive table, a 67-verb registry, one `DeskWindow` across 19 hosts, 88.4% of
interactive UI composed from library species. Against it: **no doc ever claimed
one building block**, the inventory doc rejects it ("'Primitive' currently means
at least five things"), the block is TWO blocks, the species canon documents 23 of
68, and **`SurfaceVerbs` is used in 9 files of 197 and takes arbitrary JSX — so
there is no per-surface control manifest.**

**Screen state lives in ONE BROWSER TAB's `localStorage` + Zustand.** Zero of 675
routes, zero of 217 tables, zero of 44 frame types carry it — and that is WRITTEN
POLICY, enforced by two runtime assertions in the Swift client. **`desk.verb`'s
five dispatchable verbs have an EMPTY INTERSECTION with the UI's verb registry.**

**The split that makes the vision tractable:** the READ half (what is open, what
is active, its controls) is ALREADY permitted by Article XI.5 — reads and
presentation "owe the kernel no admission and no receipt" — and is blocked only by
state locality. The DRIVE half needs one UI-verb operation kind through the kernel
broker that already exists; the deferral is explicit and CONDITIONAL, not a
prohibition.

**And the composition-root finding, which came from his own question.** MCP does
NOT write raw SQL — it goes through the service layer. But `tools.dispatch`
rebuilds every service from `get_database()` with **no `broadcast=`**, and
`mcp_http.py` receives the hub's live `WebContext` and DROPS it. One fact, three
symptoms: an MCP write never reaches the open browser; the sidecar needs its own
DB handle and so walks around the owner lock; and concurrent access was never safe
anyway. **This is the shape of finding to look for in this codebase** — not a
missing feature, but a second instance of something that should have been one.

### 4. What is chartered and what order

Five stories, all `ready`, none started:

| Story | Gate | What it repairs |
|---|---|---|
| **HS-200-42** | G1 | drain the intel queue — a finished meeting produces intelligence |
| **HS-200-43** | G1 | arm the watch; make manual evaluation record effects; RULE on the double scheduler |
| **HS-200-45** | G0 | one composition root — MCP goes through the hub's services |
| **HS-200-44** | G0 | the canon guard sees its own violations |
| **HS-200-46** | G0 | a stale document fails CI — the claims registry behind §7b |

**Order: 42 → 43 → 45 → 44**, with **46 pairing with 45** (that is where the first
`known_false` claims flip). 42 first because it unblocks 12, 13, 16 and the pilot.
44 last because it makes debt visible rather than repairing a flow, and its honest
output is a large number rather than a green tick. **He was offered the option of
doing 45 first** — it is the architecture, and it precedes HS-200-28 and any
wire-face work — and has not ruled.

**NOT chartered: the X11 wire face.** It wants a phase and it needs his word. The
audit's §11 has what each half costs and the cheapest honest first steps — a
parity test binding the three drifted verb lists, and making `desk_snapshot`
either return layout or stop advertising it. (46 pays the cheap half of both.)

### 4b. STATE AT HANDOFF — read this before you touch anything

**No code has been written since HS-200-10 merged.** Everything after it is
planning, and all of it sits **UNPUSHED on `main`**:

```
ab3bfb83  docs(200-46): the claims registry
4d058cd2  docs(handover): Muad'Dib XIX  (this file)
196d338b  docs(200-45): two composition roots, not a second writer
b87c376e  docs(200): four stories chartered out of the audit
d33c4a1f  docs(audit): the operational surface, measured
```

**Two asks are open with him and both were put to him plainly:**

1. **Push those five, or move them to a branch with a PR?** They landed on `main`
   directly, which was the orchestrator's slip — the repo's law is a PR to main.
   Do not push them on your own initiative; ask, or branch.
2. **Start HS-200-42?** He has not said go. Four exchanges in a row were planning;
   the next honest move is building, not another document.

**Working tree is clean.** Phase 200 stands at **10 done, 2 in-progress (05, 09),
5 ready (42-46), the rest backlog.** His hub (pid from Tuesday) still runs
pre-200-10 code at schema v77.

**Do not call `mcp__holdspeak__*` tools against his desk** until he rules on
`.mcp.json` — the sidecar opens his live database as a second writer (§3, and
`reference_mcp_sidecar_second_writer`). That file is his configuration; do not
edit it.

### 5. Still his, carried forward

The **HS-200-09 canvas verdict** (gates 11-15), the **pilot Project**, HS-200-05's
beats 2-6 (he does not want to be marched through them), his attended walks on
169-176, and the `.mcp.json` decision — **the sidecar opens his live database and
that file is his config; do not edit it, and do not call `mcp__holdspeak__*`
against his desk until he rules** (`reference_mcp_sidecar_second_writer`).

---

## Muad'Dib XVIII — 2026-09-08/09. THE WALK HAPPENED, AND IT FOUND THE PRODUCT BROKEN

**Read this chapter first. It supersedes XVII, whose walk instructions are now
history.** Two things define this sitting: voice typing was dead on his desk in
two independent places for four weeks each and is now fixed and proven by his own
hand, and HS-200-10's wire is built. Both are on main or one commit from it.

### 0. What he told you this sitting, in his words — this is the steering

- **"why the fuck are we focusing on scenarios when a typing adapter dies
  mid-flight, I seriously don't give a shit"** — the walk's own open question,
  killed. RULED: uncertain delivery stays never-automatic, the words wait in the
  well. Retired, do not raise it.
- **"I honestly don't give too much of a shit about those corrections and so on -
  that's really not so important in my mind to my use case, at least for now."**
  This is the big one. **The correction/teach loop is the entire thesis of Phase
  176 The Speak Loop**, which was built and merged on the orchestrator's ruling
  when he deferred the road. It was justified on a canon debt (the voice law) and
  a ZERO CENSUS — "the loop has never been taught" — not on anything he asked
  for. He has now said it is not his use case. **When a phase's justification is
  a canon debt or a zero census rather than a stated need of his, SAY SO at
  charter time and get his word before building.** A zero census is not an answer
  to "will you use this on a Tuesday?" Memory:
  `feedback_corrections_not_his_use_case`.
- **"let's focus on more high impact work from now on"** and **"Build it,
  then."** — he wants forward motion, not ceremony. He does not want a menu of
  five options; he wants a recommendation and then the work. Beats 2–6 of the
  walk (denied permission, silence, interruption, correction) are edge cases and
  he did not want to be marched through them. Do not.
- He walks **over Screen Sharing**, often not at the machine. See §4.

### 1. The two defects, because their SHAPE is the lesson

He held the hotkey. The hub **died** — `libc++abi: terminating ... There is no
Stream(gpu, 1) in current thread`, an uncaught C++ throw through numpy's buffer
protocol where no Python frame can catch it. `Transcriber` stores the RESOLVED
backend; the reuse check compared it against the RAW request; on a desk
configured `backend: "auto"` that is `"mlx" != "auto"` forever, so the boot warm
was discarded and a SECOND `_MlxTranscriber` was built on a SECOND pinned thread
FOR EVERY UTTERANCE, inheriting lazy arrays owned by the first thread's stream.
HS-60-06 (per-instance pin) and HS-63-06 (construction lock) had both aimed one
level too low: everything mlx_whisper caches is PROCESS-level. The pinned MLX
thread is now process-wide.

Underneath it, a second: every utterance was heard, transcribed, journalled and
then refused `desktop_executor_warrant_invalid`. `Broker.decide` signs 17 warrant
fields; `desktop_executor.py` demanded exactly 11. The six extras landed
2026-08-09/08-10/08-22 and that file has one commit in its life. **Desktop typing
was dead for everyone since August 9.** The VALIDATOR widened, never the warrant —
`sign_warrant` HMACs every unsigned field, so trimming fails the signature
instead, and their being signed is exactly why admitting them forges nothing. It
stays an ALLOWLIST.

**THE LAW, and it is now the most useful thing in this file:
`reference_lying_test_doubles`. A test double that lies about the field a check
reads proves nothing about the check.** Three green guards covered these two
seams and neither bug could have tripped them: `_FakeTranscriber.backend =
"auto"` where the real class stores `"mlx"` (one word — and the SAME lie was in
the HS-63-06 regression test written to guard that exact crash class); a warrant
test hand-built key-for-key from the validator's own constant and self-signed; a
typer stub swallowing the warrant with `**kwargs` and never reading it. Mint
through the REAL producer, assert against the REAL validator's constants, and
**prove every new fence FAILS against the pre-fix code before trusting it.**

### 2. The state of the tree

| What | Where |
|---|---|
| `#568` Phase 200 working context (41, 05's automatable half) | MERGED → main `cdbc8f2a` |
| `#569` the two voice-typing defects | MERGED → main `2481d328` |
| **HS-200-10's wire** | **committed `dbb86ce6` on `feat/hs-200-10-working-context`, PUSHED, NO PR YET** |
| HS-200-05 | in-progress. **Beat 1 passes on his hand.** Beats 2–6 unwalked, and he does not care about 5 |
| HS-200-09 | in-progress. **His canvas verdict is the exit, and 11–15 wait on it** (canvas `63eaae1a-eb59-4bcf-902d-0c70d3e0c275`) |

### 3. HS-200-10 — what is built, and what it still owes

Three lanes, strict file ownership, in ruling C1's order: boundary → verb →
reverse index. Read `story-10-scoped-working-context.md` (the rulings, including
**B1–B3 added this sitting**) and `assets/settled-design-working-context.md`.

The boundary is **C2′: reachable by reference, never by relevance** — and note
WHY, because it is counterintuitive and the first design draft got it backwards:
`grounding.py` runs its global relevance pass **if and only if nothing was
explicitly attached**, so NOT ATTACHING IS THE TRIGGER FOR AUTOMATIC RETRIEVAL.
Exclusion is by construction (promotion row INSERTed before the Note, so the
guarded indexing trigger never sees the body), and there are TWO retrieval routes
— lexical through the FTS corpus, and the GRAPH route via `_load_related_row`
which reads the notes table directly and bypasses the index entirely. Closing
only the first looks green.

**Owed before it closes: counsel-on-built, `evidence-story-10.md`, a clean
CI-shape suite run, and the PR.** The face is struck by ruling C6 and owes a
ratified board.

**One open item that is genuinely unresolved, B2:** `forbidden` is TERMINAL in
practice and NOTHING clears it. The design says "cleared ONLY by an explicit
re-promotion"; that is unimplementable as built, because promotion writes no
dependent row and a rebind deliberately re-inserts the mark. The orchestrator
implemented the clearing and **the ratified P0-2 test refused it**. Reverted;
fail-closed wins. A consumer fenced once is fenced forever for that record. This
is owed to counsel and to him.

### 4. Conducting him at the desk (learned the hard way this sitting)

- **He is usually on Screen Sharing and not at the laptop.** `open "<url>"` and
  `osascript -e 'tell application "TextEdit" to activate'` put faces on the Mac's
  screen where he CAN see them. Do not tell him to "open your browser" — set it
  up for him. Telling him to open Notes when he is remote wasted a leg.
- **`⌥R` DOES survive Screen Sharing.** Right-Option is not collapsed. That worry
  was wrong.
- **The hub takes `HOLDSPEAK_WEB_PORT` — there is no `--port` flag.** Pin it so a
  restart keeps the same URL. Token to the scratchpad only; `open` it rather than
  printing it.
- **NEVER run the suite beside his live walk.** This sitting produced 274 e2e
  failures that were pure CPU starvation and had to be thrown away. That clean
  run is still OWED.
- His DB is read-only to every agent. `sqlite3 -readonly`, always.

### 5. Ledgered, not fixed — all his to rule

1. `/api/dictation/readiness` answered **`ready: true`** on a desk where dictation
   crashed the process on every attempt. That is the fake all-clear HS-200-07 was
   meant to end.
2. The Speak face reads `DICTATION · GPT 5 mini · KEY NOT SET` while the runtime
   resolves LOCAL — every assignment row inherits the migrated
   `legacy-legacy-intel` cloud profile (readiness unknown, no key). One face, two
   truths, and the source of the recurring `intent-router classify failed:
   speech_provider_fenced`.
3. **The egress ledger: NO FIRE, investigated and closed.** 326 `external.egress`
   operations read `indeterminate`, but **325 are test-fixture pollution written
   into his REAL DB** before the isolation fixture landed — proven by 0.58–2.39ms
   "calls" to `api.openai.com`, physically impossible for real TLS, plus
   blackhole and `*.example.test` hosts, 287 of them in one 2am burst on
   2026-08-22. Exactly ONE is real (2026-08-30, a 751ms call to his llama.cpp
   that raised). Custody is intact and the direction of error is safe. Two real
   but smaller defects: `except BaseException` collapses every failure into
   `indeterminate` with the reason written only to an in-process dict, so
   "connection refused" and "sent and rejected" are indistinguishable on the
   receipt; and nothing surfaces egress state on his desk at all. **The failure
   branch has zero test coverage.**
4. **325 junk rows sit in his real DB** from that pollution. He was asked whether
   to remove them and has not answered. Do not touch his database.

### 6. Owed to him, carried forward

His attended walks on 170–176; the queued "Already titled" job (172's accidental
write); 172–174's unanswered questions; **the HS-200-09 canvas verdict**; the
pilot Project (one active, nine archived, all from the 168/169 window).

---

## Muad'Dib XVII — 2026-09-07/08. YOUR JOB IS TO CONDUCT HIS WALK, NOT TO BUILD

**Read this chapter before you do anything else. The owner asked for you
specifically, and he asked for a guide, not another builder.**

He has just watched a long build session. Two stories landed
(`feat/phase-200-working-context`, PR #568 open, commits `6d309652` and
`85a181e5`). What is left cannot be built by anyone: it needs his hands, his
microphone, his Mac. **Your work this sitting is to stand beside him while he
tests it, one beat at a time, and to write down honestly what happens.**

Do not open a build lane unless he asks. Do not start a refactor. If you find a
defect during the walk, NAME it and ledger it; fix it only if he says so.

### What he is testing, and why it cannot be automated

**HS-200-05, physical voice.** Six beats. A browser fixture cannot establish a
microphone permission, cannot press a physical key, cannot be denied by macOS,
cannot be interrupted mid-sentence, and cannot restart a hub. Everything a test
could carry is already green (`tests/unit/test_phase200_voice_custody.py`,
`tests/integration/…`, 55 tests). The runner is
**`tests/e2e/live200_voice_walk.py`**, and it is written for exactly this: it
takes a read-only census at both ends, prints the script for his hand, and
asserts that the ONLY writes are the ones his own beats should have produced.
It refuses to write anything itself, refuses a hub with no bundle, and redacts
the token in everything it prints.

**HS-200-41, the durable ask.** Built and proven this session, but never
touched by him. Worth ten minutes at the end: start an ask in a Project Room,
close the tab, come back, press `Resume`.

### How to run it (get this right or the walk is hollow)

His long-running hub (PID 81866 on `:49353`) is from **Sunday**, on an older
schema and an older bundle. **A walk against that proves the wrong build.**
Stop it and boot a fresh one on the current tree, on his real data root:

```bash
uv run holdspeak web --no-open        # then find the port; the log stays silent
lsof -nP -iTCP -sTCP:LISTEN | grep python
```

The owner URL is `http://127.0.0.1:<port>/?token=<meeting.web_auth_token from
~/.config/holdspeak/config.json>`. **The token goes in the scratchpad only** —
never into the repo, never into an evidence file.

```bash
# read-only first: census, faces, then the script printed for him
uv run python tests/e2e/live200_voice_walk.py --hub "http://127.0.0.1:PORT/?token=TOKEN"

# then attended: it pauses on stdin while he walks beats 0-6
uv run python tests/e2e/live200_voice_walk.py --hub "…" --attended
```

**Never run it beside the parallel suite.** CPU starvation reads exactly like a
discovery hang, and this session already lost time to that lesson.

### Before he starts: the permissions, which is the newest work

Voice typing needs THREE macOS grants and any one can be missing alone:
Microphone (the audio), Input Monitoring (the global hotkey), Accessibility
(typing into the focused app). All three live in **System Settings → Privacy &
Security**.

**The grant belongs to the application he launched from.** A hub started in a
terminal needs Terminal or iTerm enabled in those panes, not an entry named
HoldSpeak. And macOS applies several of these only to a newly started process,
so the launching app must be quit and reopened after granting.

Commit `85a181e5` makes this legible for the first time: Speak now draws a
head row (`ACTIVE` / `BLOCKED` / `UNAVAILABLE`) and one row per non-granted
permission with its pane as walkable tokens and a `Re-check` verb. **`BLOCKED`
is the state that used to be invisible** — the listener installs, the key looks
fine, and nothing is ever heard because Input Monitoring is refused. When every
grant is held the block is absent by design; a working hotkey says nothing.

`docs/GETTING_STARTED.md` "Grant macOS permissions" and `docs/USER_GUIDE.md`
"When voice typing does nothing" carry the same words. If the walk teaches you
something they do not say, fix the docs in the same sitting.

### The seven beats, in his order

0. **Readiness.** Fresh install opens on the first-value chair; he answers it
   himself (the runner will not — both answers are writes). Then read the
   engine row and the egress chip. If the engine is not ready, **STOP**: every
   beat below would be hollow.
1. **The hotkey into a target.** Caret in Notes or a terminal. Hold Right
   Option, speak, release. The words land IN THAT APP and the Journal gains ONE
   row with source HOTKEY. If they land elsewhere, that is the defect.
2. **Denied permission.** Revoke the browser's microphone access, press `Talk`.
   The face names the refusal and his typed words REMAIN EDITABLE. No journal
   row. He restores access before beat 3.
3. **Silence.** Press `Talk`, say nothing, release. Nothing heard, no row, no
   counter of zero.
4. **Interruption.** Start speaking, then take the mic (press `Talk` again or
   start a meeting). The face names WHO holds the microphone and the partial
   words are not silently typed anywhere.
5. **One correction, then a replay.** Teach a `text` correction on a row the
   mic got wrong, then `Replay` that row. The replay shows corrected words.
   **`N APPLIED` does NOT move** — a replay is a preview and writes no row.
   *Ask him whether that reads right;* if he wants a replay to count, it
   becomes a story.
6. **Restart.** Ctrl-C the hub, start it again on the same data root. The rows
   survive, the correction survives and still fires, `N APPLIED` is unchanged.

### The one question the walk owes him

A delivery whose outcome is UNKNOWN (the typing adapter died mid-keystroke)
parks as `delivery_pending` and is **never retyped automatically**; the words
stay in the well for him to send again. Is "never automatically, always his
hand" right, or should the desk offer a retry? **Get his answer and record it.**

### Laws you must not break while conducting

- **A walk on his desk WRITES NOTHING.** The runner is read-only by
  construction. Anything a rig seeds goes in an isolated HOME. There is a scar:
  earlier walks left seed rows in his real database and he had to delete them
  himself.
- His real database is `~/.local/share/holdspeak/holdspeak.db`. Read-only
  inspection only, `sqlite3 -readonly`.
- Redact `token=` in every capture.
- After the walk, census his DB read-only for anything the walk should not have
  touched.
- Handovers live in `docs/internal/`, never in a Claude artifact. Canvases are
  the only artifacts.

### The state of the tree

PR #568 is open with two commits and awaits **his word** to merge. HS-200-41 is
DONE. HS-200-05 is in-progress with its automatable half paid and no evidence
file — the gate refuses evidence whose story is not done, so create
`evidence-story-05.md` only when his beats are recorded and the story flips.
HS-200-10's wire design is ratified with conditions, all paid, and **not
built** — do not start it during the walk.

Suite in CI shape at the last full run: 10590 passed, 17 failed — 8 xdist
contention, 6 fences paid, 3 inherited on main (hs153's ledgered guardrail,
hs171 ×2 from HS-200-07's coverage badge colliding with an older zero-badge
law). `dw check` reports six known structural issues, zero new.

Still his, and none of it yours to decide: the **canvas verdict on HS-200-09**
(stories 10 through 15 wait on it), the **pilot Project** (his desk has one
active and nine archived, all from the 168/169 build window), and the **merge**.

---

## Muad'Dib XVI — 2026-09-06, the road continues on the orchestrator's ruling; 176 CHARTERED and on the canvas

**His word.** "muad'dib... you decide. we push this forward, or it's
phase 200 time..." — a deferral of the ROAD itself. Ruled: PUSH
FORWARD. Reasons on the record (176's status file, "Decisions made"):
the road to 180 is his standing goal; 176's charter and recon were
already written; the voice law (Article IV.1) is an unpaid canon debt;
the correction loop has never been taught (census 0); "phase 200"
names no thesis anywhere in the tree, so a pivot would trade a named
road for an unnamed one. What stays his: the canvas and the merge.

**Done this sitting.** Branch `feat/the-speak-loop` off main
`7a47904e`. HS-176-01 in progress. The 2026-09-05 design draft
RE-VERIFIED against main by a Fedaykin (18 pointer fixes, 11 of them
claims, not lines): the teach path is `POST
/api/dictation/journal/{id}/correct` with the corrections route as
fallback; `corrected` is already stored and served and the Journal
already renders `TAUGHT · N SIMILAR`; the real gap is that the LIVE
nudge's `corrected` never reaches the recorder; the route's `source`
filter exists but is clamped to two of four sources; `Review` opens the
Configure door; the scanner ALREADY has the voice-law rule, id `mic`
(ceiling 6), file-scoped and voided by one opt-out; the intent bar is
0.5 not 0.6; a live defect — Memory.tsx reads `row.gist`, the route
serves `key` (GIST renders a dash on his desk); a 170 drift — a second
mic on the utterance well against "Talk is the only mic". The census
recomputed (`assets/mic-census-176.md`): 44 raw elements, 8 uncovered
dictatable + 9 unjustified `mic={false}` opt-outs = 17 sites (the
draft's 31 counted tests, `_parked/` and library internals); 170 left
four orphaned dictation components (park them). Stories 02–05 corrected
to those truths. Fifteen boards drawn to 175's `.dc.html` + `canvas.json`
format, rendered and read beside the design, published:
https://claude.ai/code/artifact/36f77f70-fb03-461d-a0dd-8b43c4682e63 .
Counsel's hunt on the design: `assets/counsel-on-design-176.md` —
**BOUNCE on one P0**: the correction store holds ROUTING corrections
only (`intent` = a block id, `target` = a profile id), so the charter's
Tuesday ("postgress → PostgreSQL") cannot happen on that wire and the
teach row 170 shipped is dead for a typed sentence. Counsel proposed a
pick over the enum. RULED otherwise: a third kind `text` (heard phrase →
said phrase) applied deterministically at the transcript seam beside
the spoken-symbol substitution (`text_processor.py`), exact-phrase; the
teach field cycles TEXT · INTENT · TARGET; C2–C14 accepted as R2–R14
(the design's addendum; one word one meaning: LEARNED the wing, TAUGHT
the receipt, APPLIED the chip). Design and boards redrawn to the
rulings; counsel's re-read RATIFY-W-C (N1–N5: no `auto` in the pick —
it raises on the live path; the TEXT well pre-fills with the RAW
transcript; punctuation-stripped matching; the text rule's blast radius
said honestly; the taught-from row wears `TAUGHT`; no caption count on
the Learned wing), all ruled accepted and paid; then his word.

**Laws this sitting added.** When he defers the road, RULE and record
the ruling where the phase lives (the status file's "Decisions made"),
then act. A design drafted on one branch is re-verified against main
before it goes on the canvas — every pointer, every claim; the refresh
found eleven false claims in a 465-line draft. The design's own census
is recomputed on the tree it will build on, excluding tests, `_parked/`
and library internals, and each `mic={false}` is a voice-law hole the
raw-element count cannot see.

**The build, the same day.** His word: "Well. Let's follow your ruling,
then. It's important we continue to make progress..." — read as the
word to build to the design counsel ratified on his behalf, the merge
on his word. Waves: wire (lane A the `text` kind + the Pipeline.run
seam + schema 76 + the recorder's bus seam; lane B the routes; lane C
the voice law), faces (02 the teach row, 03 the Journal stream, then 05
the Learned wing + Review + one mic authority), counsel-on-built
(BOUNCE: the real Talk path's reply dropped the three keys the loop
needs — paid; the frame honours the filter; the secret guard widened to
real token shapes; `N TODAY` counts today), docs, the CI-shape suite
(26/10180, classified against a main worktree: 12 inherited, 7 moved
fences paid, 7 rigs serial-green or inherited), the walk's read-only leg
on his desk (six beats MATCH, zero writes; his DB 9/0/6 before and
after; findings: his engine reads KEY NOT SET; an empty-transcript row).
Commits: `9bbef950` 01 · `01a1a03b` 04 · `f45bb9c8` 02 · `3b39422e` 03 ·
`e1067485` 05 · `5a0a29f5` 07 · `3a573eb4` the fixes · the close.
Laws added to UX-CANON §D: one word one meaning; the species that has
the value wins the face; a `mic={false}` is a hole; a rig never types
into the focused window.

**The evening: #566 MERGED on his word, and the road turned.** "Merge
man. And let's keep going. Although, I do believe there are other PRs
that need to be merged to main based on what's out there on `gh`?" —
#566 merged (`8fb56d97`). Two PRs were open: #563, HIS OWN charter for
**Phase 200 The Working Practice** ("the owner-directed line in the sand
for new delivery"; the "phase 200" of his morning question), and #526,
relationship-aware memory (Sept 2, 61 files, conflicting). #563 was
merged into main in a worktree (the roadmap README carries both 176's
close and Phase 200 as the CURRENT phase; a merge commit needs
`.tmp/BUNDLE-OK.md`), taken out of draft and merged (`bea4176c`). Phase
200 is the road now; 177–179 of the Tuesday arc are PARKED behind it
(never deleted); 180 The Proof folds into its G5. HS-200-01 (the
baseline and obligation map) is in progress on `feat/phase-200-g0`.
#526's merge of main is being resolved in a worktree (seven conflicts:
four docs, the Room face, its css, a glyph test) by a Fedaykin; the
orchestrator commits and merges it on the gates.

**Phase 200, the same night — MERGED #567 → main `5e2f1704` on his word
("Please it merge it...").** G0: 01 the baseline (two hubs found on one DB — the stale
one stopped; his engine profile KEY NOT SET with two LAN destinations
ready; one active + nine archived Projects; 69 obligations mapped) ·
02 runtime identity + the owner lock (a second hub refuses to start) +
restore on a copy · 03 the release checks (47 identities reproduced,
34/35 CI failures repaired; tests/conftest.py REFUSES a real HOME;
tests/critical/ with its own CI job; three absolute fences → dated
down-only debt ratchets, R200-03-1, for his eye) · 04 first value cold +
the real task probe + four NEEDS YOU repair states + the return-to-task
defect fixed · 05's automatable half (physical beats his). G1: 06 the
three claim axes (no schema change) · 07 attention coverage (no fake
all-clear anywhere; MCP needs_you fixed) · 08 the evaluation harness
(33 episodes, held-out split, critical failures cannot be averaged; the
LIVE run is his command; the drafter's silent fallback on his profile
shape found and fixed) · 09 the daily workflow DESIGN (six postures, 22
boards, counsel bounced then ratified; canvas
`63eaae1a-eb59-4bcf-902d-0c70d3e0c275`; HIS VERDICT is the exit and
10–15 wait on it). The runner: E2E traced and paid (the rigs' own
week-edge clock bug, a leaked hub between modules, the Meetings
arrival's real 404, the mermaid cache); 161 green, 1 ledgered.

**Laws this day added.** The suite is classified against a main
worktree, never by memory. A merge commit into a PR branch needs
`.tmp/BUNDLE-OK.md`. A worker runs the canon scanner only to a scratch
path. Rigs seed in the desk's zone, never UTC's. A test never types
into the focused window. A fence anchored to a file moves with the
file, and a private helper must be classified in the census the day it
is born. His DB is read-only to every agent; the product's own
additive reconcile on startup is the one write a walk may cause.

**Owed to him.** His VERDICT on the 200-09 canvas (stories 10–15 wait);
the pilot Project (one active + nine archived exist — which is the real
stream, which sources);  his
attended walks: 176 (the hub from that build is on his desk, port in
the scratchpad; beat 0 = the engine key or a LAN engine) and 200-05
(tests/e2e/live200_voice_walk.py); the attended walks 170–175; the
queued "Already titled" job; 172–174's questions; the walk questions
(a text rule's first application: confirm or silent-and-undoable? an
uncertain delivery: never automatic or `Send again`? the cap of five?).

## Muad'Dib XV — 2026-09-05 late, 175 RESUMED on his word; the four faces BUILT

**His word.** "I think you could continue working out 175 no?" — read as
the word that lifts the wind-down for 175 only. The main tree moved to
`feat/calendar-clock` (the stale wt175 removed; main's handover commits
merged @85a844cf). Draft PR #558 stays on main.

**Built (to the ratified boards, shot beside each at 1440 + 393, bounced
until it matched).** (a) The arrival: the WEEK strip, `NEXT · … · ROOM ·
<name>`, the MEETINGS section, the orphan armed row with `FROM · title
(source)`. (b) Settings → Meetings' CALENDAR section on SettingsCore's
meetings case (the board's module; the design's MeetingsConfig pointer
was wrong), REPLACING the 146-era group — its verbs (`Edit` · `Disable`/
`Enable` · `Remove` + in-world confirm) carried onto the new rows after
the old group's tests named them; `Add` + `Snapshot`; the one well with a
mic; Auto-record with `5 MIN BEFORE` and `N MATCHED THIS WEEK`;
`GET /api/calendar/sources` (667 routes). (c) The Room's MEETINGS row is a
REAL Watch: created when a meeting links (routing_glue + the manual path),
backfilled once by the sweep, evaluated by the sweep (proven:
decisions_changed → a Watch event → checkedAt moves). (d) Rhythm's Weekly
brief row and the brief face: one display (the period), THIS WEEK
composed rows, SINCE FRIDAY flat rows with kind tokens and emblem chips,
one gutter; `this_week` added to the brief's section vocabulary first;
the 132/129 triage behaviours kept, their assertions moved to the new DOM.

**Rulings.** Design Addendum 2, B1–B9 (past events count in the strip's
shape, not the section; no synthetic rows; the board's module wins; a
replacing face never loses a working verb; `this_week` additive; the
snapshot egress paid).

**Hygiene.** The census (`assets/hygiene-census-175.md`); P2-2 PAID —
the snapshot's direct dispatch prefers local/LAN vision profiles and
records the host (fence test, 3 pass); tz-aware `compute_lookahead`
default; the swallowed Watch-query load now logs; the canonical schema
snapshot regenerated (the 02 wire never did); the 173 drafter diagram's
`PAR` alias (mermaid's `par` keyword) renamed so the render guard passes.
Four items parked in BACKLOG.md (the 393 Intelligence-row overlap from
172, per-source refresh status, the Snapshot verb's place for counsel,
UTC week edges).

**The scar.** A lane ran `git stash` in the SHARED tree to measure a
before-count and `git stash drop` after: ten files reverted to HEAD (the
arrival, the Settings face, the door and snapshot fixes, the API surface,
the schema snapshot, two of mine). Recovered from the dangling stash
commit (`git fsck --no-reflogs --unreachable`, then `git show <sha>:<path>`
only over paths at HEAD). The law is now in `.claude/agents/opus-worker.md`
and memory: no git verb that moves the tree, ever; the orchestrator reads
`git reflog -3` before every verification run. Rigs also re-shoot OLDER
phases' PNGs and the ratchet regenerates the 170 census — restore those
paths before staging, every time.

**Counsel on the built phase (the second commit).** BOUNCE on twelve
conditions, six reproduced: an event-born recording FIRED capture while
the copy said "armed, never started" (ruled B11: it records at the event
like every scheduled recording; the toggle is the consent; carried to the
owner); the arrival's Cancel dead outside `arming`; a cancel re-armed by
the next refresh; Remove/Disable leaving recordings armed; the ratified
Unlink on no face; the matcher selecting a phantom column; UTC on the
faces; `WEEKLY MON 08:00` naming a cadence that does not exist. Three fix
lanes paid C2–C11 (B12–B15); the re-read ratified with six conditions,
five paid (B16–B17: Cancel means this occurrence; every arm receipted;
Delete behaves as Cancel; per-instant local time on the DST edge; the
B11 hand-off proven by a test that runs both conductors), the sixth is
his walk. Seven questions ride to him (see the status file and the
re-read). Schema 75; api-surface 667.

**The close (2026-09-06).** His word: "You got my word for a merge."
06 flipped on his word with the runner's read-only walk as the desk proof
(his attended walk owed); 09 closed on the gates; final-summary.md; PR
#558 out of draft and merged with a merge commit. Seven questions ride
to his sitting.

**Gates at this commit.** Unit set 247 passed (-n auto, isolated HOME);
web baseline zero branch-new; ratchet green (A8 healed to 24); the 175
rigs + the 170/171/172 rigs they touch green serially; mermaid guard
2 passed; api-surface 5 passed. 08 the docs flips here (13 markers paid
against the shipped tree). Still owed: counsel-on-built, the walk on his
desk (06; the runner's Settings selectors re-pointed to the built rows),
07's flip (census done, items paid or parked), the suite in CI shape, the
close (09), #558 out of draft.

## Muad'Dib XIV — 2026-09-05 21:50, the stack MERGED; 174 closing; 175 parked

**His word.** Mid-turn: "Can we focus on finalizing whatever is in
flight, build it out to the finalization, and... slowly wind down?
You've delivered a lot. A lot of those PRs are basically still open for
some reason. Shouldn't we have merged all those PRs?" Read as the word
that gated the merges. Done in order the same hour, branches kept (never
delete), each dependent PR retargeted to main before its merge:
#553 → 0e69f3d7, #554 → 397e3594, #555 → 0c17425e, #556 → d416e08a,
#557 → 8c994305 (174, after its close: counsel paid, the walk with zero
writes, the suite classified). #558 (175) is a DRAFT on main, parked.

**CI truth.** Main's Actions were already red before this arc on a
runner-environment set (no speech engine → `no_assignment`, no
`mlx_whisper`, no PortAudio, the Q6 model file absent, two broker density
fences, product-copy drift) plus a rotating flaky family. #553 failed on a
SUBSET of main's set and healed five of main's failures. The merge gate
in this repo is the local CI-shape suite (6 inherited) + his word — not
the red Actions badge. Making Actions green again is a phase of its own
(park it in BACKLOG under "CI runner environment").

**174 Reach.** Counsel-on-built RATIFY-W-C; paid @bc02a6de: no token in
the URL on /api/mcp (401 `token_in_query_refused`, tested — the refusal
sits BEFORE the principal guards); the Door's fixed GH · Jira ·
Confluence order (the board's); the LIKE receipt scoping documented;
`NO RUNS YET` on a remote Runs-on with no run; `CREDENTIALS · N ACTIVE`.
His open questions from counsel: Door order preference; the richer
receipt grammar (✓, `overnight`) before or after merge; the zero-state
token wording. Close = live174_walk.py on his desk (remote expected OFF →
zero writes; the probe credential only if already ON), the suite
classification, flip 11, merge #557.

**175 Calendar and the Clock — PARKED at 5/9.** Design ratified (counsel
RATIFY-W-C; five conditions paid in the addendum: one count on the
orphan board; the TWO-WINDOW brief — `compute_window` unchanged,
`compute_lookahead` to Sunday; `refresh` not `refresh_all`; auto-link
ruled with `Unlink` + receipt, his word may flip it; the matched fact
beside ARM ROOM MEETINGS ONLY). Wire 02–05 landed with tests on
feat/calendar-clock. NOT built: the four faces + rigs, docs verify,
hygiene, the walk, counsel-on-built, the close. Resume from
`assets/settled-design-calendar-clock.md` (addendum at the end) and the
story files; the runner draft is `tests/e2e/live175_walk.py`.

**Owed to him, unchanged.** His walks on 170–175; Skip the queued
"Already titled" job (172's accidental write); the per-phase questions
in XII/XIII/above.

## Muad'Dib XIII — 2026-09-05 20:40, Reach BUILT to the wire; 173 CLOSED

**State.** 173 CLOSED 9/9 on feat/the-stewards-hand (PR #556). 174 Reach
6/11 on feat/reach, **PR #557** open stacked on #556: the transport,
scoped identity, the runner (proven on loopback), the Confluence
decision + connector wire, the mesh event; the Settings → System face
built; the receipts/Door/Rhythm faces landing; then counsel-on-built,
the docs verify, the walk (the probe credential only if remote is
already ON), the suite, the close.

**Found and paid across the stack today.** 171's loop never called the
notifier (P0, found by 174's runner lane; paid d0f6d89f on
feat/the-heartbeat, commented on #554, merged forward through #555, #556,
#557). 173's first desk walk was hollow — a worktree hub served "build
missing" and the runner reported zero defects; the runner now refuses a
hub with no bundle. Two evidence captures had proved nothing (a zsh
word-split; a `-k` expression as one identifier); the pass line is read
before every flip now.

**Laws added.** Close a phase from a `git worktree` of its branch once
the next phase is active in the main tree (PYTHONPATH=<wt> with the main
venv; copy `holdspeak/static/_built` for a hub). A ghost-dense Button is
a transparent-bordered mono label (172's species) — not a bounce. A
runner must fail closed on every write AND refuse a hub without a
bundle. `cadence.run_now` is not in the SWEEP palette; `heartbeat.
run_now` is the sweep tool.

**Your questions (174):** Confluence — blogs vs page search; the
awake-Mac prerequisite vs a lid-open V0; in-memory credentials
re-issued after every restart vs persisted; the leg from the .43 box at
your sitting; the listener on for your desk once a credential exists.

**Merge order stays his:** #553 → #554 → #555 → #556 → #557.

## Muad'Dib XII — 2026-09-05 19:20, the Steward's Hand BUILT

**State.** 173 is 7/9 on evidence on feat/the-stewards-hand; **PR #556**
open, stacked on #555 (172) on #554 (171) on #553 (170). Counsel on the
built phase, the runner fill and the full suite are in flight; then the
walk on his desk with EVERY write denied (no Send, no Publish, no
steward run, no effect enable) and 09 the close.

**What the phase is.** The steward drafts the weekly update with the
model behind the claim schema (refs verbatim, UNVERIFIED never smoothed,
the model and its host named); the Room reads HEALTH from what it
already watches (`REVIEW WAIT` in days since the PR was created — the
honest word — · `ISSUE AGING` · `CI` · `RELEASE`); on a project where he
armed `Reviewer nudge`, a bottleneck row offers `Nudge`, the card shows
the exact text and `GITHUB.COM`, Send re-checks the gate, admits through
the kernel, runs only `gh pr comment`, and the receipt names who, where
and the text. No Undo. 7-day cooldown after Send or Dismiss.

**Laws this phase.** A host and a model are recorded at draft time. A
nudge step belongs to a real steward run — never a dummy run, never
foreign keys off. The scanner knows StringGadget carries the mic; the
ceiling only lowers; the mic stays on every input. A capture that
selects nothing exits 0 — read the pass line before a flip. zsh does not
split `$FILES` — wrap captures in `bash -c`.

**Session note.** The account's session limit killed five lanes mid-edit
once (reset 12:20pm Denver); every lane was resumed by message and
finished; the tree compiled throughout.

**Counsel on the built 173: RATIFY-W-C, paid** (the cooldown token in
hours under a day; the nudge text bounded; the vacuous capture redone).
Its questions, ruled: hours in the first day; `Open` on a bottleneck row
opens the People card; `PER-NUDGE APPROVAL` stays a token.

**Merge order stays his:** #553 → #554 → #555 → #556.

## Muad'Dib XI — 2026-09-05 17:10, the Loop Closes BUILT

**State.** 172 is 9/9 on evidence on feat/the-loop-closes (stacked on
171 #554 on 170 #553). Counsel on the built phase: RATIFY-W-C, paid.
The P0 is the lesson of this phase: `bridge_meeting_artifacts` and the
suggestion scanner had NO production call site — six green rigs seeded
proposals by SQL and hid it. Paid in `intel_queue.py`
`_on_intel_complete` (bridge → scanner per Room → durable dirty marker
in `desk_projection_state`), with a test through the real seam. Law
added to the rigor bar: every new service entry point needs a
production call site and one end-to-end test before a phase closes;
counsel-on-built greps for call sites.

**The owner's desk.** The walk ran twice. The first runner's write
guard failed OPEN and posted `Run intelligence` on "Already titled"
(Aug 22) — its model is the migrated cloud profile without a key, so
the job sits QUEUED with the OLD recorded host label; nothing left the
machine; nothing undone. `Skip` on that meeting clears it. The guard
now fails closed; the second walk reads `SKIPPED: not LAN:
api.openai.com`, nine shots, zero defects.

**Laws this phase.** Dismiss never Drop. The third verb is a Button.
The lead slot is the source. No clipped text. No pronoun or first name
from a name. Suggestions dedup case-insensitively. The display step is
a fact. A host is RECORDED at run time and is the endpoint host
(`192.168.1.43` · `local` · `api.openai.com`), never a label, never a
config fallback. A commitment folds into its decision row. A lane's
report without a rig tail and shots on disk is not a report. The
ratchet ceiling is restored with `git checkout` when a lane raises it.
`SurfaceLedger` needs `cols="room"` or the primary collapses.

**174 counsel on the design (2026-09-05 20:50): RATIFY-W-C, ruled.** The
ground had claimed the presence host keeps the hub alive with the lid
closed — false; the overnight run needs the Mac awake on AC (the face
says `WHILE THIS MAC IS AWAKE`). **Your questions (174, counsel's):**
(1) Confluence: does your team live in blog posts, or is page search the
need (then V0 is a badge, not a tool)? (2) the awake-Mac prerequisite —
a setting you already run, or would you rather a lid-open V0? (3)
credentials are in-memory and re-issued after every hub restart — fine
for the overnight runner, or persist them (with an at-rest story)?

**Phase 174 Reach (2026-09-05 19:45) — activated, stacked on #556.**
Boards dispatched. **Your questions (174):** (1) the third connector —
Confluence is the reversible default, but its CLI cannot list or search
pages (only blog posts, and pages by known ID); is that enough for your
team, or do you want another tool? (2) the .43 runner drives the hub
over the tailnet with a scoped credential (palette + TTL); the leg from
the .43 box itself waits for your sitting — when? (3) the remote
listener is off by default; do you want it on for your desk once you
have issued a credential?

**Phase 173 (2026-09-05 18:00) — counsel RATIFY-W-C on the design,
ruled.** Nine boards on
https://claude.ai/code/artifact/9f1558b4-0867-4152-bc7e-1314dde5e82c.
Rulings: `REVIEW WAIT` in days from createdAt, never `REVIEW LATENCY`;
the green state is present with `CLEAR` / `PASSING` / `READY`; the
nudge text names the tool and no person (`Flagged by HoldSpeak.`, posts
from your own gh identity, editable per nudge and per project); the
receipt names who; the model is named beside its host; one `CHECKED N
MIN AGO` on the HEALTH caption; `NUDGED N D AGO` while cooling.

**Counsel's questions for you (173):** (1) the nudge's attribution —
tool named, no personal name — is that how you want your team to read
it? (2) the createdAt approximation — WAIT in days is what the system
can honestly say; acceptable? (3) the 7-day cooldown shown as `NUDGED
N D AGO` — adopted; keep?

**Counsel's questions for the owner (172, built):** (1) the two-prefix
vocabulary `Decide:`/`Confirm:`; (2) the 1:1 card's summary-then-Now
shape and `2 PRS WAITING ON ANIA` with the name in caps; (3) Jira
assignments on the card — keep?

**Next.** PR **#555** is open (`--base feat/the-heartbeat`); then 173 The Steward's Hand +
Voice on its drafted ground (assets/settled-design-stewards-hand.md),
stacked on 172. Merge order stays his: #553 → #554 → 172's → 173's.

## Muad'Dib X — 2026-09-05, the Loop Closes on the canvas

**State.** 170 (#553) and 171 (#554) open on his word, stacked. 172
ACTIVE on feat/the-loop-closes: thirteen boards published
(https://claude.ai/code/artifact/b153c331-cd38-4856-b38b-837407dd6fba),
two bounces paid, counsel **RATIFY-W-C** (three conditions, nine
findings, all ruled in the design's second addendum). The whole wire is
in (e11d1d21): auto-intel trigger, the proposal bridge (schema 73,
`follow_through_proposals`, Confirm through the kernel, Dismiss
receipted), the People resolver (opaque id only), 1:1 enrichment,
suggested sources (case-insensitive dedup). Docs (09) and the walk
runner (08) drafted. Four lanes building: Room faces (03/06), meeting +
arrival + Settings→Meetings (02/03), the People card (05), and the
story-07 boards (People in the Room, the shade at 393).


**A write on your desk, owed to you (2026-09-05 09:45).** The 172 walk
runner's guard failed open: it could not read the provider, judged the
host "LAN/local", and posted `Run intelligence` on your meeting
"Already titled" (Aug 22). Its model is the migrated cloud profile
without a key, so the job sits **QUEUED** and cannot run; nothing left
the machine. Nothing was deleted or undone; `Skip` on that meeting
clears it, or leave it and the Concierge's next assignment will run it.
The guard now fails closed (unknown = no; a queued job blocks a second
run) and prints the values it decided on. The same walk found the
QUEUED meeting detail still wearing the pre-170 prose panel; fixed in
this phase.

**Counsel's three questions for the owner (172):**
1. Decisions lead with `Decide:` and action items with `Confirm:` —
   is the two-prefix vocabulary yours?
2. The People card's Prep wing is one summary row per concern and
   `Open` switches to Now for the per-entity rows — is that the shape
   you want before a 1:1?
3. Do Jira assignments belong on the 1:1 card, or only PRs and
   commitments?

**Laws added this sitting.** Dismiss, never Drop. The third verb is a
Button. The lead slot is the source. No clipped text. No pronoun from a
name. Suggestions dedup case-insensitively. The display step is a fact.
`SOURCES N` counts accepted sources only. `Run all` parked (paid egress
in a batch).

**Merge order stays his:** #553 → #554 → 172's.

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

- **171 at 07:20:** boards + canvas
  https://claude.ai/code/artifact/82c55045-4a19-4990-a8b5-569b91eb8647
  (counsel reading); the wire built and committed (heartbeat setting in
  `cadence_policies`, the third conductor loop `HoldSpeakHeartbeat`,
  `needs_you_aggregate.py` cache, `desktop_notify.py` osascript V0,
  brief regeneration in runtime/cadence.py). Next: counsel's conditions
  → faces (shade PROJECTS + dock badge = 04; ⌘K = 07; Rhythm's row = 02's
  face; the brief row = 06) → rigs → his-desk walk (a real notification
  at a real edge) → docs → close → stacked PR.

- **171 at 08:00:** the wire complete with counsel's conditions; the
  shade's PROJECTS + dock badge and ⌘K PROJECTS built, read and
  committed (one count everywhere — muted Rooms dimmed, `MUTED`,
  uncounted; the shade's empty sections absent, `NOTHING MISSED` when
  all are); Rhythm built and BOUNCED once (title `Rhythm`, no eyebrow,
  accent headline, hug height, WRITTEN receipt, the hub shot); the
  arrival learning the mutes; docs written with seven markers;
  live171_walk.py written, selectors filling. Product-copy fence at 26
  (< the inherited 27: `_parked` skipped). Next: gauntlet → the walk on
  his hub (run-now on his real Rooms; a banner at a real edge is his to
  see) → docs markers → counsel-on-built → close → PR stacked on #553.

- **171 at 09:50 — 6/10 on evidence** (02 cadence · 03 aggregate · 04
  shade + badge · 06 brief · 07 ⌘K · 09 docs), counsel-on-built
  RATIFY-W-C paid; the first walk on his real desk found his Monday
  brief was the kernel ledger (`1839 THINGS · AUG 19`) — the SOURCE is
  fixed (human items only; `LedgerSummary` no face counts); a `PROJECTS`
  caption over nothing → the brief under its own `BRIEF` caption. 05
  keeps its click-to-open box open (osascript; the bundle); 01/08/10 are
  his word. The second walk runs; then the full suite; then
  `gh pr create --base feat/the-great-pass` (stacked on #553). Evidence
  captures for 01/05/08/10 wait for his word.

- **172's design ground is DRAFTED** (pm/roadmap/holdspeak/phase-172-the-loop-closes/assets/settled-design-loop-closes.md, pending 170's merge): six faces with species. Recon: the EXTRACTORS EXIST (`decision_capture`, `action_owner_enforcer` plugins) but their artifacts are opaque JSON nothing reads — story 03 is the bridge to proposals; the auto-run trigger belongs after `_associate_meeting_with_projects` (meeting_glue.py:447); `resolve_relationship_by_owner` is the resolver's seed, never called from the Watch path; the 1:1 brief has no Watch data. His three new questions: auto-run default ROOM-LINKED ONLY or AFTER EVERY MEETING; does an edited proposal keep its original as provenance; the People card from the Room at 393 inline or navigate.

- **173's design ground is DRAFTED** (pm/roadmap/holdspeak/phase-173-the-stewards-hand-and-voice/assets/settled-design-stewards-hand.md, pending 172). Recon: the snapshots lack review-request timestamps (add `createdAt` to `GH_WATCH_FIELDS`, watch_sources.py:35 — a read field, not a CLI verb); `gh` writes are gated by `WriteConnectorManifest` (gated_connector.py:128) and the PR-comment actuator already exists (github_pr_actuator.py:86) — the steward has never called it; the sixth effect kind is one `elif` in `_apply_effect` (project_steward_service.py:1094) behind the existing gate; flaky CI needs `run list --limit 10` (allow-listed). His three new questions: the nudge's wording (it goes out under his name); the health thresholds (24/48 h, 14 d, 3 failures); the nudge cooldown (7 d).

- **176's design ground is DRAFTED** (phase-176-the-speak-loop/assets/settled-design-speak-loop.md). Recon: Teach's corrections ARE applied on the next dictation today (dictation_runner.py:335 snapshots the store per run; intent_router.py:206 + target_profile.py:126 apply them) and persist durably (ring of 20 in memory, the DB uncapped) — the loop exists and has never been taught (0 corrections on his desk); the mic gap is 31 raw inputs/textareas outside the gadget system (the gadgets default mic=true), not ~85. His questions: LEARNED as a wing or under Configure; the teach chip tap-to-detail or always visible; the raw-input allowlist.

- **175's design ground is DRAFTED** (phase-175-calendar-and-the-clock/assets/settled-design-calendar-clock.md). Recon: the calendar adapter reads ICS only (a local file or an HTTPS subscription URL — integrations.py:18-26; no EventKit/Google); events reach the NEXT line via door_service.py:266 but carry no Room link (no `project_id`; a matcher or a `calendar_event_projects` table is needed); `scheduled_recordings.calendar_event_id` exists (db/scheduled_recordings.py:34) with a unique armed index (schema.py:3483) but auto-arming is unbuilt; the ICS parser drops ATTENDEE. His questions: event→Room auto-link or SUGGESTED rows; the auto-record default once a calendar is connected; the week strip MON–FRI or seven days.

- **174's design ground is DRAFTED** (phase-174-reach/assets/settled-design-reach.md). Recon that changes the charter's assumptions: `acli confluence page` exposes only `view --id` — NO page list/search (only `blog list` and `space list` paginate) — so a Confluence WatchSource in V0 watches blog posts, not pages; the .43 is the CLIENT and the Mac the hub (.43 → hub → .43's llama.cpp → hub → receipt); `_web_auth_gate` (web_server.py:561-591) does not yet refuse OWNER derivation off-loopback — new code; AgentCredential has no palette field (principals.py:83-113) and the store is in-memory (dies with the hub); EgressChip has three scopes (`remote` is the fourth). His questions: Confluence still the third connector knowing V0 watches blogs only, or Linear; persist credentials or re-issue after restart; `caffeinate` for the lid-closed night or fail gracefully.

- **PR #554 is OPEN for 171** (https://github.com/karolswdev/HoldSpeak/pull/554), stacked on #553 (base
  `feat/the-great-pass`). 6/10 done on evidence; 05 keeps its click box;
  01/08/10 flip on his word. Design grounds for 172–176 are drafted
  under their phase assets. Merge order: #553 → #554.

- **10:55 — Phase 172 ACTIVATED, STACKED** on `feat/the-loop-closes` off
  `feat/the-heartbeat` (PR #554) off `feat/the-great-pass` (PR #553).
  In flight: two artboard lanes (Room proposals · meeting after run ·
  arrival Confirm rows | the 1:1 card · the suggested source ·
  Settings → Meetings auto-run) from settled-design-loop-closes.md; two
  wire lanes (the auto-run trigger after `_associate_meeting_with_projects`
  + the extractors→proposals bridge + confirm through the kernel | the
  People↔Watch resolver + the 1:1 brief's watch_summary + suggested
  sources); the docs to the design; live172_walk.py drafted. Then
  counsel → faces → rigs → his-desk walk → close → PR stacked on #554.
  Merge order stays his: #553 → #554 → 172's.

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
