# Phase 70 — The Legible Product (Out-of-the-Box): final summary

**Status:** CLOSED (9/9) — 2026-06-30. Branch `phase-70-legible-product`,
PR [#205](https://github.com/karolswdev/HoldSpeak/pull/205).

## Why this phase existed

Opened on the owner's own words: *"I literally am confused myself about the
product, and IMO, that's a VERY, very bad sign."* Phase 69 brought the web to
the iPad's felt craft; this phase fixed what craft cannot. The story was settled
(POSITIONING: *one copilot, two modes*) but the web surface had sprawled to
**16 pages** shown as ~14 co-equal doors with triple redundancy (three first-run
surfaces, three canvas surfaces, two ambient surfaces). The confusion was the
information architecture diverging from the story. Phase 70 reconciled them.

Two owner-confirmed calls at scaffold shaped every story: **(A)** bold reorg +
consolidate (not an additive front-door); **(B)** tuck the power features into a
collapsed **Studio** tier (not a third pillar, not hidden).

## The result: four doors, not fourteen

```
HoldSpeak
├─ Home        what is this + your next action
├─ Dictation   voice typing + the journal + learning + pre-briefing
├─ Meetings    capture / import + the archive + aftercare
└─ Studio ▾    (collapsed, advanced) Workbench · Desk · Agent Desk · Cadence · Commands · Profiles
   Settings
```

The acceptance bar was behavioral (AGENT-BRIEF §1): within ten seconds of the
screen a person can say what HoldSpeak is, name the two modes, and take a first
action, with the power features present but never confronting them. The closeout
proof and the Home screenshots meet it.

## The nine stories

1. **The IA spine** — `TopNav` from Live/Review/Configure groups to `Home ·
   Dictation · Meetings · Studio▾`; Studio is a native `<details>` disclosure
   that auto-opens on an active route.
2. **Home** — `/` reframed from the 1378-line live-meeting dashboard (moved to
   `/live`) into orientation: identity + a `/api/setup/status` next-action band +
   the two modes as co-equal cards + a quiet Studio link + a first-run guard.
3. **One arrival** — `/welcome` is the single first-run surface (guard + CLI
   nudge route there; it teaches both modes and lands on Home); `/setup` demoted
   from a second "Welcome" to the "Setup & health" surface, surfaced from Settings.
4. **Dictation made whole** — the pre-briefing nudges were already in the
   cockpit; Activity removed from the Studio nav and `/activity` reframed as a
   Dictation sub-view ("Activity ledger", a back link), nothing lost.
5. **Meetings made whole** — `/history` retitled "Meetings" with the entry
   actions (Start a meeting → `/live`, Import) promoted to the hero; `/meetings`
   redirects to `/history`.
6. **The Studio tier** — a new `/studio` index frames the six power tools as
   clearly-secondary cards (one-line purpose + an honest "Off by default" on
   Cadence); the dropdown "ADVANCED" eyebrow links to it.
7. **Guiding empty states** — a shared `.empty-state` primitive; the Meetings
   archive rebuilt on it in two guiding variants, fixing the stale "Runtime"
   copy; the other primaries already guided.
8. **Naming + positioning** (docs) — POSITIONING records the web IA + Home/
   Meetings/Studio canonical names; Getting Started's surface map and the docs
   index reflect the new front door; voice guard green.
9. **Closeout** — this.

## Closeout proof

- **No dead doors:** `scripts/phase70_closeout.py` sweeps all 18 routes → **18/18
  resolve 200** (following redirects: `/meetings`→`/history`, and the new
  `/live` / `/studio`, and `/setup` / `/activity` reframed but reachable). The
  route pre-flight (`tests/e2e/test_route_preflight.py`) sweeps every page for
  zero page errors and guards that every `pages.py` route is listed.
- **One clean arrival:** first-run `/` → `/welcome` (the guard); a set-up user
  stays on **Home** with nav primaries `['Home', 'Dictation', 'Meetings',
  'Studio']` (`screenshots/closeout-home-nav.png`).
- **Legibility read-test (recorded):** against `home-empty.png`, a fresh viewer
  gets, in order: the identity ("One copilot, two modes."), the two modes (two
  co-equal cards with a one-line what-it-does each), and a first action ("Open
  Dictation" / "Start a meeting") — plus a single "Next" band pointing at the one
  setup step. Studio is a quiet dashed link, never competing. This clears the
  ten-second bar.
- **Suite:** `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **3045 passed,
  37 skipped** (unchanged across the phase; every story's ripple was retargeted,
  never silenced). Build green (18 pages). `_built/` never committed.

## What moved (route map)

| Was | Now |
|---|---|
| `/` (live-meeting dashboard) | **Home** (orientation); the dashboard moved to `/live` |
| `/welcome` + `/setup` + the `/` guard | one arrival (`/welcome`); `/setup` demoted to "Setup & health" |
| `/history` (History archive) | **Meetings** (`/meetings` redirects here) |
| `/activity` (top-level) | a **Dictation** sub-view ("Activity ledger") |
| the six power tools (flat/ungrouped) | the **Studio** tier + a `/studio` index |

## Honest follow-ups (not blockers)

- The `/activity` ledger and the `/live` dashboard are reframed, not ported into
  their parent mode's page. Folding them into `/dictation` and a unified Meetings
  page is a future refinement (the ledger is 825 lines of `?raw`-loaded Alpine;
  porting it now would risk a paradigm-mixing rewrite for no user-visible gain).
- The Studio index shows static per-tool state (Cadence "Off by default"); wiring
  live on/off/configured state per tool is a nice-to-have.
- The first-dictation leg of the arrival play-walk is mic-bound (covered by the
  excluded metal test); the closeout proves the guard + Home landing, not the
  physical hotkey.

## For the next agent

The web is now legible: four doors, one arrival, a framed advanced tier, guiding
empty states, and canon that records it. The standing rule (POSITIONING) is that
a new capability joins a mode or the Studio tier, not a new top-level door. PR
#205 is the owner's to merge on green CI.
