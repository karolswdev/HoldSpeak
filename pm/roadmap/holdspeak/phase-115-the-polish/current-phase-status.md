# Phase 115 - The Polish

**Status:** DRAFT. Seven stories that remediate the 73 violations
found by the 2026-08-03 surface audit. Three severity tiers — 27
BROKEN (user-visible bugs), 22 UGLY (material violations), 24 DRIFT
(inconsistencies) — across ~30 surfaces. Every window, every chip,
every label brought back into the Signal Workbench grammar. When this
phase ships, every surface on the Desk looks like it was born from
the same OS.

**Last updated:** 2026-08-03 (scaffolded from terra-trooper audit —
7 agents, 114 tool calls, 526k tokens).

## Why this phase exists

Phase 113 built the shared kit, the real editor, the voice router,
git drawers, AI editor, decision primitives, and refitted every
surface onto the shared kit. But the refit was structural — it moved
surfaces onto shared components without fixing the material and
content violations inside them. The 2026-08-03 audit found:

1. **Editors don't fill their windows.** The DeskEditor and
   InlineEditor shared a CSS class name, capping the editor to 340px
   inside Pullout windows. (Fixed in `125b53e9` — but the audit
   found more layout violations.)

2. **Windows are invisible.** The Signal Workbench tokens
   (`--desk-window-bevel`, `--desk-window-keyline`) were defined but
   never wired to the window shell CSS. Windows had no visible depth
   against the desk background.

3. **Raw internal data bleeds through.** 18 of 73 findings are C1
   violations — steering audit labels, raw `source_kind` enums,
   `%1` placeholders, complete API JSON responses, hex invocation
   IDs all appearing in product-facing UI.

4. **Bespoke controls everywhere.** 14 findings are M3 violations —
   buttons that should be shared `.desk-chip` with bevel treatment
   are instead one-off bare buttons with custom styling.

5. **The DeliveryBoard is unusable.** Broken scroll containment
   (title bar scrolls away), information overload (everything
   renders concurrently in one 560px window), raw operational
   identifiers, and nonconforming window material.

## Method

- **Shared CSS first (story 01).** Chip bevel, pullout specificity,
  section separators, window material consistency — fixes that ripple
  across all surfaces.
- **Content sanitization next (story 02).** One pass through every
  surface that leaks internal data. No raw IDs, no internal enums,
  no JSON dumps in product UI.
- **Surface-by-surface refit (stories 03–05).** Each story takes a
  group of related surfaces and fixes layout, material, and content
  violations together.
- **DeliveryBoard redesign (story 06).** The worst offender gets its
  own story — information architecture rethink, not just CSS fixes.
- **Walk (story 07).** Screenshot every surface at 1440px and 393px.
  No violations survive.
- **Constitution articles cited per story.** No story ships without
  grounding in the canon it serves.

## Stories

### Foundation — shared fixes that ripple everywhere

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | [The shared material](./story-01-the-shared-material.md) | "Chips have no bevel, windows have no depth, sections have no separation" | backlog |
| 02 | [The honest surface](./story-02-the-honest-surface.md) | "Why am I seeing steering_audit and %1 in the UI?" | backlog |

### Surface groups — layout, material, and content per group

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 03 | [Object windows](./story-03-object-windows.md) | "The editor doesn't resize, the inspector shows raw IDs" | backlog |
| 04 | [System surfaces](./story-04-system-surfaces.md) | "Desk memory shows internal data, shade has wrong chrome" | backlog |
| 05 | [Hosted cores](./story-05-hosted-cores.md) | "Workbench can't resize, cores dump JSON, typography drifts" | backlog |

### The hardest problem

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 06 | [The rails window](./story-06-the-rails-window.md) | "Delivery Workbench is overcomplicated and unusable" | backlog |

### Proof

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 07 | [The walk](./story-07-the-walk.md) | "Prove every surface passes the audit" | backlog |

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-115-01 | The shared material | backlog | [story-01](./story-01-the-shared-material.md) | — |
| HS-115-02 | The honest surface | backlog | [story-02](./story-02-the-honest-surface.md) | — |
| HS-115-03 | Object windows | backlog | [story-03](./story-03-object-windows.md) | — |
| HS-115-04 | System surfaces | backlog | [story-04](./story-04-system-surfaces.md) | — |
| HS-115-05 | Hosted cores | backlog | [story-05](./story-05-hosted-cores.md) | — |
| HS-115-06 | The rails window | backlog | [story-06](./story-06-the-rails-window.md) | — |
| HS-115-07 | The walk | backlog | [story-07](./story-07-the-walk.md) | — |

## Where we are

Draft. Awaiting owner charter decision. Audit artifact published at
https://claude.ai/code/artifact/f5788f46-2b99-4e7f-b6e5-281c03e7c01c
