# HANDOVER — many calendars, one honest rail (written 2026-08-28, late)

For the next agent. This file supersedes the "Door is open" handover
of earlier the same day (historical now). Read this whole file, then
orient (`.githooks/dw context holdspeak --compact` — ignore `dw
next`'s stale phase-91 pointer; the README "Current phase" line is
truth), then go. The owner's verb is "gooo": run whole arcs without
asking permission at each step; put a short menu in front of the
owner only where a decision is genuinely theirs (next-phase picks,
scope fold-ins, merges, shot verdicts).

## 1. What the world looks like now

- **Three phases shipped in ONE day, all merged.** Phase 144 (The
  Dashboard Door) + Phase 145 (The Door Polish) went to main as
  PR #499 (`4c08a613`). Phase 146 (Multiple Calendars) closed 7/7 on
  `feat/hs146-multi-calendar` (close `f01ebed6`) and merged on the
  owner's word right after this handover was written — check
  `git log main` for the merge commit; if the PR is somehow still
  open, the owner's merge word is ALREADY GIVEN.
- **The product now:** `/` opens First Sentence, then the Door —
  five-column board, the UPCOMING rail fed by MULTIPLE calendar
  sources (`CalendarSource {id,label,url,enabled}` list; per-source
  last-good projections — a broken calendar never wipes a healthy
  one; orphan cleanup; provenance chips ONLY when >1 source,
  label→hostname→LOCAL, stamped server-side; NO cross-feed dedupe by
  ruling), the joyful Settings calendar list editor (GadgetTable,
  mics, per-source egress chips, + ADD SOURCE / REMOVE? /
  IMPORT SCREENSHOT), and **the Calendar Snapshot adapter**: a
  screenshot of a locked-down O365 week → vision extraction through
  the router (`calendar.snapshot_extract`, vision=True; routed when
  assigned, ask-template direct dispatch when not; no vision model =
  the NAMED refusal `no_vision_model_assigned`) → the anchor-gated
  review SurfaceWindow (week never silently guessed; CANCEL writes
  nothing) → a generated `.ics` under
  `~/.local/share/holdspeak/calendar-snapshots/` registered as the
  "O365 SNAPSHOT" file source through the settings write path → the
  SAME bounded parser as any hostile feed. Inventories: 540 API
  routes (538+2 snapshot endpoints, manifest regen shipped), 135 MCP
  tools (unchanged), one-path execution sites 103 (the vision leaf
  `run_prompt_messages` deliberately admitted).
- **The record:** `phase-146-multiple-calendars/` — charter with the
  seven settled-design rulings + the full decision log (TWO owner
  rulings mid-arc: the dedicated docs story HS-146-06; the adapter
  fold-in HS-146-07 with a required design beat), both archived
  plans, evidence-story-01..07 each with an orchestrator triage
  note, final-summary.md, and the owner-delivered shot exhibit in
  `assets/story-0304-shots/` + `assets/story-07-shots/`.
- **Close counsel: RATIFY-WITH-CONCERNS**, and its should-fix earned
  the pass: it read the delivered shots AGAINST EACH OTHER and
  caught snapshot times stamped UTC (review 09:00, rail 03:00).
  Fixed to local wall-clock; the fix exposed a second latent defect
  (the ICS generator string-mangled ISO offsets) — replaced with
  honest fromisoformat→UTC. The exhibit was re-shot before the owner
  saw it. Lesson made law: **shots are evidence to cross-read, not
  just to admire.**

## 2. The consolidated ledger (owner-visible, carried)

| Item | Class |
|---|---|
| IMPORT SCREENSHOT button swallows 422 upload refusals (bare catch; drop path is honest) | counsel ledger → next polish |
| Snapshot direct-dispatch fallback doesn't pre-filter vision-capable profiles (failure = named refusal + wasted inference, never bad data) | counsel ledger |
| Phase 145 ledger stands: scroll-hint useEffect per-render reattach; `_calendar_configured` silent-except debug breadcrumb | carried |
| Phase 144 ledger stands: conductor shutdown gap (backlog); trust-destinations calendar entry (REAL enforcement only, never data-only); `_active_thoughts` pagination spin | carried |
| No real-vision-model probe has ever run (all proofs use fake engines; `.43` may lack a vision model) | named honestly in story 07's Out-scope; first real capture = a control-vs-treatment moment |

**Flake families (serial ×2 is the protocol; recurrence beyond =
DIAGNOSE):** hs143 assignments s5 leg (glass-under-load, named in two
handovers now), hs141 thought-workbench 1440/393, refinement
recovers-owner family. The calendar-conductor watch item is CLOSED
(diagnosed + fixed in 145: await the receipts, not reader entry).

## 3. What to work on next (present a short menu)

1. **Real-metal snapshot probe** — assign a vision-capable model
   (cloud with badge, or a local llava/qwen-VL if `.43` grows one)
   and run one real screenshot through; control-vs-treatment per the
   real-metal law. Small, high-truth.
2. **Snapshot polish** — the two counsel ledger items (422 refusal
   surfacing; vision-capable pre-filter in the fallback).
3. **Event → one-tap record** — the standing backlog candidate the
   owner deferred twice; the rail's natural next verb.
4. `BACKLOG.md` — the parking lot; don't mega-bundle. AE (the
   adapter) is GRADUATED/shipped — mark it if not already.

Standing charter questions: **"will you use this on a tired
Tuesday?"** and **"does this operate with joy?"**

## 4. The standing laws (same as the last two eras, plus this arc's)

1. YOLO bar + TIE-BREAKER; ceremony budget ([ORCH-CALL]s ruled by
   YOU, one counsel close pass); models law (opus-worker for ALL
   delegated work, Terra only paired, never Fable subagents; author
   PMO/roadmap YOURSELF); CI is dead — local verification, push/merge
   only on the owner's word; shots before merge and LOOK yourself
   first; web is the spec; never delete — park; isolated HOME always
   (`uv run --python 3.13.11`); no modals / no prose / mic on inputs /
   one egress badge / errors in-flow / height-cap grammar.
2. **The stub law (new, story 07):** a worker's "done" with a
   production path that only works when tests inject a fake is NOT
   done — refuse the flip, mandate the wiring, demand the proof fake
   at the ENGINE-FACTORY level, never the route seam.
3. **Cross-read the shots (new):** two shots of one flow must agree
   with each other (times, counts, labels). The counsel caught what
   four eyeballs missed by doing exactly this.
4. **Never string-mangle ISO offsets (new):** convert with
   fromisoformat/astimezone. The mangling version corrupted every
   non-UTC timestamp into garbage DTSTART.
5. **Guard-forced registration is a feature:** the three censuses
   (routing-authority pins, one-path buckets + exact count,
   capability call-sites + runner entrances) each caught the new
   vision seam. Register deliberately WITH attribution comments;
   remap pure line-drift 1:1 (a reusable remap script pattern lives
   in this arc's transcript — pointers+classifications+references,
   keyed (file, attr), order-matched per file); NEVER remap a set
   with unmatched new entries — those are real additions demanding a
   decision.
6. **Baseline-failing guards hide branch-new violations** — stash-
   compare their violation LISTS (HEAD vs dirty), not their
   pass/fail. Caught a real one-path violation and a real factless
   failure string this arc.

## 5. Sweep + walk mechanics (unchanged + additions)

- Baseline: `phase-143-intelligence-router/assets/
  story-08-inherited-failure-baseline.txt`; verdict vocabulary
  "baseline-exact, zero branch-new"; readable run + dw capture are a
  PAIR (capture truncates pre-summary; triage from the readable log,
  note the pairing).
- Recipe + env-ordering gotchas: see the sweep script at the session
  scratchpad pattern — `PLAYWRIGHT_BROWSERS_PATH`/`npm_config_cache`
  resolve from the REAL HOME BEFORE `HOME=$(mktemp -d)`.
- **After every sweep/walk/e2e run:** `git checkout --` the
  phase-141/143/144/145/146 assets — the glass runs clobber ALL of
  them (146's own shot dirs included once committed).
- The cold walk `scripts/door_walk_hs144.py` is current (leg 5 rides
  the sources wire via the settings API; TODO(HS-146-05) markers
  where the list editor's glass could be asserted deeper). Rerun it
  YOURSELF before any flip that touches the Door.
- **Run everything from the repo ROOT** — a `cd web` that leaks cwd
  makes relative shot paths write into `web/pm/...` and pytest
  collect nothing ("no tests ran in 0.00s" = check your cwd).
- Shot rigs: fresh browser CONTEXT per surface (persisted windows
  sit OVER the chair while assertions pass against elements BEHIND —
  the walk-law trap, burned twice); wait for CONTENT, not the window
  frame (lazy Cores photograph as "…").

## 6. Orchestration knowledge (this arc's additions)

- The story pipeline ran two-deep+parallel: disjoint-lane builders
  (03 settings UI ∥ 04 rail/seeds) with explicit do-not-touch lists;
  one commit lane (YOU), explicit-path staging always.
- Retire heavy-context builders (the 3-story agent was retired
  before story 07; the settled design travels in the brief).
- `SendMessage` to a worker's id resumes it with context — used for
  the story-07 round-2 wiring mandate.
- dw specifics: charter story table MUST be the five-column format;
  contract AFTER staging; one flip per commit (BUNDLE-OK with
  rationale for genuinely interleaved stories — 145 did it once);
  all-done demands final-summary.md before the last flip; the known
  phase-101 evidence ERROR in `dw check` is a held item, ignore it.
- Memory: `~/.claude/.../memory/project_phase146_multiple_calendars.md`
  (+ 144/145 files) hold the arc details; MEMORY.md Active list is
  current as of this handover.

Go get the owner's next word. The rail is honest, the calendars are
many, and a locked-down Tuesday morning now fits through the Door.
