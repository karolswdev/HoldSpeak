# Evidence — HS-36-03: Per-artifact-type body polish

**Date:** 2026-06-04. **Branch:** `phase-36/hs-36-01-artifact-card-shell`.

## What shipped

A Signal polish pass over **every** artifact body inside the HS-36-01 card shell, in
`web/src/pages/history.astro` (CSS only — no markup/selector changes, so the spoken-e2e
inner selectors are untouched). Two themes:

### 1. Off-palette → Signal tokens (the root cause of the "flat" look)

The HS-27–29 bodies referenced tokens that **don't exist** in the Signal set
(`--color-danger-soft`, `--color-warning`, `--color-success*`, `--font-weight-bold`,
`--text-default`) — so they rendered via their hardcoded `rgba()/hex` *fallbacks*,
off the brand palette. All migrated to the real Signal status tokens:

| was (fallback) | now (Signal) |
|---|---|
| `--color-danger[-soft]` | `--danger-signal` / `--danger-soft` |
| `--color-warning[-soft]` | `--warn-signal` / `--warn-soft` |
| `--color-success[-soft]` | `--ok` / `--ok-soft` |
| `--font-weight-bold` | `600` |
| `--text-default` | `--text` |

Audit (post-edit): `grep -nE '--color-(danger|warning|success)|--font-weight-bold|--text-default' web/src/pages/history.astro` → **NONE**.

### 2. Flat bodies → designed blocks

- **incident_timeline** — a real **timeline rail**: a vertical line (`--danger-soft`)
  with per-event **node dots** (`--danger-signal`, ringed) and the event time as a
  red mono chip — was a bare `<ol>`. (`<ol class="incident-timeline"> > <li>` structure
  preserved; e2e asserts `.incident-timeline li`.)
- **risk_register** — severity pills on the Signal palette (red/amber/green, now
  bordered) + a row-hover; header rule uses `--border`.
- **runbook_delta** — added/modified/removed as bordered typed badges (ok/warn/danger).
- **requirements** — `.req-type` is now a **typed badge** (functional→ok,
  non_functional→info, constraint→warn, acceptance→accent), was plain mono text.
- **scope_review / customer_signals** — verdict/type chips → bordered Signal badges
  (in_scope→ok, scope_creep/pain→warn, request→info, out_of_scope→muted); customer
  quote italicized.
- **decisions / open-questions** — custom accent `▸` markers (was raw `disc`).
- **stakeholder_update** — accent headline + accent `•` section markers.
- **decision_announcement** — each announcement is an **accent-edged comms sub-card**.
- **action_items / adr / milestone_plan** — each record is a left-accented sub-card
  (ok / info / info) with a surface fill, so stacks read as discrete blocks.
- **dependency_map** — from/to rendered as mono node **chips** with an accent flow arrow.

## Verification

### Visual — all 13 body types rendered

A standalone harness (`.tmp/hs3603_harness/`, not committed) inlines the **real**
`web/src/styles/tokens.css` + the page `<style>` block and renders static markup
(the exact resolved class structure Alpine produces) for every artifact type inside
the `.artifact-card` shell, screenshotted via Playwright/Chromium:

- `evidence/artifact_bodies_polished.png` — wide (2 columns, all 13 types). Every body
  shows typed Signal color, iconography, and sub-card/rail/badge structure — no
  remaining flat/default body.

### Narrow viewport — no overflow regression

Same harness at a **420px** viewport: `document.scrollWidth == clientWidth == 420`
→ **no horizontal overflow** (the risk table scrolls within its `.table-scroll`,
not the page). `evidence/artifact_bodies_narrow.png`.

### Bundle + suite

```
$ cd web && npm run build          # ✓ 8 pages built in 4.29s
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2020 passed, 15 skipped in 54.69s
```

Unchanged count vs HS-36-02 (2020/15). Pure CSS restyle — every asserted inner
selector (`.risk-table tbody tr`, `.incident-timeline li`, `.requirement-list
.requirement-item`, `.runbook-list .runbook-change`, `.scope-list .scope-finding`,
`.signal-list .signal-item`, `.decisions-artifact .decision-list li`,
`.dependency-list li`, `.adr-artifact .adr-record`, `.milestone-artifact
.milestone-record`, `.announcement-artifact .announcement`, `.stakeholder-update`,
`.action-item-list .action-item`, `.mermaid-artifact svg`) is preserved.

## Notes

- The on-`.43` re-capture in the live cards (the before/after money shot) is the
  HS-36-06 closeout deliverable; this story's gate is the per-type restyle + selector
  preservation + the harness render above.
