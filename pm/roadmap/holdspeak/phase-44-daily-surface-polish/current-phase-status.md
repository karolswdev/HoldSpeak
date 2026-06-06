# Phase 44 — Daily-Surface Polish

**Status:** IN PROGRESS (2/4). Opened 2026-06-06. On user direction (after the
Phase-43 wizard landed): the first 10 minutes are now world-class, but the
surfaces a user lives in daily — the **dashboard (`/`)**, the **dictation cockpit
(`/dictation`)**, and **history (`/history`)** — still wear the older Phase-30
"Signal" look. Carry the wizard's bar to them so the *whole* app feels premium.

**Last updated:** 2026-06-06 (HS-44-02 shipped — the dictation cockpit lifted to
the wizard's bar: a cockpit hero + ambient glow + a premium contained section
nav with a solid-accent active tab + card depth/motion; behavior-preserving,
suite green at 2325).

## Goal

Bring the daily-driver web surfaces up to the Phase-43 wizard's standard —
richer hierarchy, depth + motion, warm idle/empty states, distinct treatments —
without changing behavior (same Alpine apps, same APIs).

## Invariants
- **Behavior-preserving** — the meeting/dictation/history logic is untouched; this
  is presentation. Default suite green; 0 `_built/` tracked.
- **Accessible** — visible focus, reduced-motion, SVG glyphs, contrast.

## Scope
- Dashboard (`/`) — a premium idle "command center" home + elevated hero/presence
  (HS-44-01).
- Dictation cockpit (`/dictation`) — premium pass (HS-44-02).
- History (`/history`) — premium pass (HS-44-03).
- Closeout — before/after + PR (HS-44-04).

## Story status
| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-44-01 | Dashboard idle home + hero polish | done | [story-01-dashboard.md](./story-01-dashboard.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-44-02 | Dictation cockpit polish | done | [story-02-dictation.md](./story-02-dictation.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-44-03 | History polish | backlog | story-03-history.md | — |
| HS-44-04 | Closeout (before/after + PR) | backlog | story-04-closeout.md | — |

## Where we are
Branched `phase-44-daily-surface-polish` off `main` (post Phase-43 merge, PR #21).
HS-44-01 (the dashboard) lifted the literal home `/`. HS-44-02 carried the bar to
the **dictation cockpit** (`/dictation`) — cockpit hero, ambient glow, a premium
contained section nav (solid-accent active tab), and card depth/motion, all
presentation-only over the untouched Alpine-free app. Next: **HS-44-03**
(history `/history`) then **HS-44-04** (closeout — before/after + PR to `main`).
