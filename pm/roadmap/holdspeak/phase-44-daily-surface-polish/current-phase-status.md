# Phase 44 — Daily-Surface Polish

**Status:** IN PROGRESS (3/4). Opened 2026-06-06. On user direction (after the
Phase-43 wizard landed): the first 10 minutes are now world-class, but the
surfaces a user lives in daily — the **dashboard (`/`)**, the **dictation cockpit
(`/dictation`)**, and **history (`/history`)** — still wear the older Phase-30
"Signal" look. Carry the wizard's bar to them so the *whole* app feels premium.

**Last updated:** 2026-06-06 (HS-44-03 shipped — history lifted to the wizard's
bar: ambient glow + a rounded elevated accent-washed hero + a premium pill tab
bar with a solid-accent active tab + elevated cards with hover lift; CSS-only,
behavior-preserving, suite green at 2328).

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
| HS-44-03 | History polish | done | [story-03-history.md](./story-03-history.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-44-04 | Closeout (before/after + PR) | backlog | story-04-closeout.md | — |

## Where we are
Branched `phase-44-daily-surface-polish` off `main` (post Phase-43 merge, PR #21).
HS-44-01 (the dashboard) lifted the literal home `/`. HS-44-02 carried the bar to
the **dictation cockpit** (`/dictation`). HS-44-03 lifted **history**
(`/history`) — ambient glow, a rounded elevated accent-washed hero, a premium
pill tab bar (solid-accent active tab), and elevated cards with a hover lift,
all CSS-only over the untouched `historyApp()` contract. All three daily-driver
surfaces now match the wizard's bar. Next: **HS-44-04** (closeout — before/after
+ PR to `main`).
