# UX Inventory

## Routes

| Route | Purpose | Main User |
|---|---|---|
| `/` | Runtime dashboard for active/idle meeting state | Meeting user |
| `/activity` | Local activity ledger, candidates, project rules, connectors | Power user / operator |
| `/history` | Saved meetings, detail review, exports | Meeting reviewer |
| `/history` (Settings tab) | Settings surface served as a tab inside `/history` | Operator |
| `/dictation` | Dictation blocks, readiness, KB, runtime, dry-run | Power user / admin |
| `/docs/dictation-runtime` | Runtime setup guidance | Installer / troubleshooter |
| `/design/components` | Component gallery (dev-facing, not a product surface) | Frontend / designer |

Every route now composes `web/src/layouts/AppLayout.astro`, which
mounts the unified `TopNav`, the skip-to-content target, the
optional secondary toolbar slot, and the global `ConfirmDialog`
host. There is no per-route navigation or per-route confirmation
markup anymore.

## Important UI Surfaces

### Runtime Dashboard (`/`)

- Hero with idle / active / stopping state transition (HS-10-12).
- Meeting start/stop with a `ConfirmDialog` on stop.
- Live transcript stream + bookmark + copy + export.
- Side rail: live intel, topics, summary, action items, deferred
  plugin jobs.
- Live status pulses on the dot of `recording`, `stopping`,
  `analyzing`, and `connecting` pills (HS-10-12) — only the dot
  animates so surrounding text never reflows.

### Activity (`/activity`)

- Ingestion status, retention, browser source availability.
- Domain exclusions with `ConfirmDialog`-gated removal.
- Project mapping rules with preview, save, and delete.
- Meeting candidates: preview, save, dismiss, and bulk-clear.
- Recent activity records with a destructive bulk-clear gated by
  `ConfirmDialog`.

### History (`/history`)

- Tabbed: Meetings, Action items, Projects, Settings, Intel jobs.
- Meeting list, search, detail panel, transcript, artifacts,
  export.
- Project archive gated by `ConfirmDialog`.

### Dictation (`/dictation`)

- Readiness checks, block list + editor, project KB editor.
- Runtime model settings, dry-run trace rendered through
  `CommandPreview`.
- Block delete + KB-file delete gated by `ConfirmDialog`.

## Current Gaps For Designer Review

What's left after phase 10:

- First-party connector packs (`gh`, `jira`) still need the in-
  panel UI controls that the new `Pill` + `Panel` + `ListRow`
  grammar makes possible. Tracked in **phase 11** (Local Connector
  Ecosystem).
- The dictation editor is functional but visually denser than the
  rest of the product; a follow-up polish pass would tighten the
  rhythm. Not blocking.

## What was closed in phase 10

- Navigation style is consistent across activity, history,
  dictation, and runtime — `AppLayout` + `TopNav`.
- Empty-state grammar is one component (`EmptyState`) shared
  across surfaces.
- Command previews use one component (`CommandPreview`).
- Destructive-deletion language and visuals are one component
  (`ConfirmDialog`) with explicit "this is local-only" scope copy
  on the prompts that touch connector output.
- Visual hierarchy of dense panels uses `Panel density="dense"`.
- Token-driven colour, type, spacing, radius, motion.

## Suggested Design Deliverables (for next iteration, optional)

- A connector-control composition (panel + list rows + status
  pills + command preview) — informational only; the components
  exist, this would be a wireframe of how they assemble for `gh`
  and `jira`.
- A light-theme token map proposal (deferred from phase 10).
- A prioritized polish backlog for the dictation editor's
  density.
