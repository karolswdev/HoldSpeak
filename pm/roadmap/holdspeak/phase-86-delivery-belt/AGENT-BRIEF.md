# AGENT-BRIEF — Phase 86: The Delivery Belt (read-only)

Read this before touching anything. It pins the decisions that were
expensive to reach so the stories don't re-litigate them.

## What this is

The first shipped slice (B1) of the Delivery Belt RFC
([proposals/delivery-belt.md](../proposals/delivery-belt.md), backlog
candidate U): the delivery pipeline as a desk-native surface. Owner
direction, verbatim (2026-07-07): *"incredibly well integrated into
the UI/UX philosophy of Desk OS on iOS, and of course, its Web
Equivalent… it's almost like a conveyor belt builder with rich
interaction affordances."* And, the same day, the wider frame: *"this
is meant to be my 'AI Headquarters' where I build out projects, steer
projects, finalize projects."*

That second sentence is load-bearing: **the Belt is never
single-project.** B1 ships a projects REGISTRY (rails repos by path)
and renders a belt per registered repo — the read-only portfolio
view. It launches with two real belts: this repo and
delivery-workbench itself. Steering (B2) and "New Project" (B3) land
on a surface that was never shaped around one repo.

## The substrate (do not rebuild it)

Delivery-workbench v1.12+ (`~/dev/reusable-processes`) already ships
the machine layer the RFC called B0 — richer than the RFC guessed:

- `dw state --json` — the versioned mission-control state feed
  (`feed_schema: 1`; docs/mission-control.md §1): projects, phases
  (the belt segments), stories, current phase, next story.
- `dw sessions --json` (§2) — live agent sessions correlated to
  stories by `repo_root` (it reads HoldSpeak's own
  `~/.config/holdspeak/agent_sessions.json`); five honest outcomes
  (`on_story`, `ambiguous`, `idle_on_rails`, `off_rails`,
  `unreadable`).
- `dw events` (§3) — the append-only rail event log
  (`.git/pmo-events.jsonl`): story flips, evidence captures, gate
  passes and refusals (refusals carry their rule).
- `dw check` / `dw context` — the desync linter + machine context.
- The stamped-contract gate + PMO trailers + archived contracts.

Upstream phase 16 ("the flagship tree", delivery-workbench PR #2)
taught the reader this repo's legacy dialects: receipts-first
evidence pairing, decorated-status normalization, pointer-driven
current phase. HoldSpeak parses honestly now: 397 spurious errors →
31 real desyncs (triaged in that phase's evidence-story-04). Story
HS-86-01 consumes that triage list.

## The two non-negotiables (RFC canon)

1. **Receipts, never a parallel truth.** The belt renders from
   `dw state`/`sessions`/`events` + git + `gh` conclusions + the
   evidence tree. No belt-side database of claimed progress. If the
   desk and a repo could disagree, the design is wrong.
2. **Every consequential act is an actuator** — but B1 has NONE. This
   phase is read-only end to end; a fitness test proves no mutation
   path is reachable from the belt route (the upstream workbench's
   read-only guard is the precedent). Approve/dispatch/merge are B2.

## The interop decision (owner-steered)

The hub speaks the same telegram grammar it already uses: one pull
snapshot (`GET /api/belt/state`) plus **`scope: "belt"` frames on the
one `/ws` bus** (the Phase-72 canon; the `_run_frame` vocabulary —
`{state, scope, capability}` — is the shape to mirror). Any surface
(web desk, iPad, Qlippy) renders belt motion from the same frames; no
bespoke polling per consumer. The Telegram interface upstream
(absorption-ccgram) is the reference consumer for how third parties
steer via this substrate — read it before designing B2.

## Correction (2026-07-07, mid-phase)

Phase 82 (Mission Control Conveyor) already shipped the hub bridge
(`missioncontrol_bridge.py`, `/api/missioncontrol/state|sessions|
events`), the registry (the operator's project map at
`~/.holdspeak/delivery_workbench.json`), the desk conveyor
(`MissionControlConveyor`, 15 s single-flight poll), and the gated
story-verb approval leg. Read `docs/internal/MISSION_CONTROL_DESK.md`
and phase-82's final summary before touching anything. HS-86-03/04
are re-scoped to the true gaps: gh receipts, `scope:"belt"` frames,
station lights, evidence in place. The section below describes the
architecture Phase 82 chose; it stands.

## How the hub reads the substrate

Shell out to the repo-embedded CLI (`.githooks/dw`, per registered
repo root) with `asyncio.to_thread` — never import `dw_pmo` into the
hub (version skew per repo is a feature: each repo's rails answer for
themselves). Registry lives in hub config (`belt.projects`: list of
absolute paths; default seeds this repo). A registered path without
`.githooks/dw` renders an honest `no rails` belt, never an error 500.

## UI canon (unchanged, binding)

Web = React+Vite islands, desk-first (`web/src/desk/`); Astro is a
document shell. Signal tokens (`web/src/styles/tokens.css`). No
prose in the UI (labels state WHAT); no modals (open in place);
`tests/unit/test_desk_locks.py` patterns apply. The web bundle is
gitignored — edit `web/src`, `npm run build` to verify, commit source
only. Evidence files open in place (filed objects stay openable —
the owner's standing video-review rule). Screenshot-verify every
surface state you claim.

## Gotchas from the trenches

- HoldSpeak's `.githooks` is a fossil (April): HS-86-02 refreshes it
  via delivery-workbench `update.sh` AFTER upstream PR #2 merges.
  From that commit on, contracts are stamped by
  `.githooks/dw contract new` (staging first, then contract; restage
  invalidates). The CLAUDE.md managed block replaces the hand-written
  flow — keep the HoldSpeak-specific sections outside the block.
- `dw story status` (the transactional verb) requires the canonical
  5-column story table. THIS phase's status doc uses it; older
  phases stay as they are (the reader tolerates them now).
- The api-surface manifest regenerates AFTER call sites exist
  (`uv run python scripts/gen_api_surface.py`); route-count guard
  will fail CI otherwise.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
