# Phase 115 - The Polish

**Status:** DRAFT. Eight stories that remediate the 73 violations
found by the 2026-08-03 surface audit. Three severity tiers — 27
BROKEN (user-visible bugs), 22 UGLY (material violations), 24 DRIFT
(inconsistencies) — across ~30 surfaces. Every window, every chip,
every label brought back into the Signal Workbench grammar. When this
phase ships, every surface on the Desk looks like it was born from
the same OS.

**Last updated:** 2026-08-03 (scaffolded from terra-trooper audit —
7 agents, 114 tool calls, 526k tokens).

## The orchestrator

This phase is commanded by **Opus 4.6** (Claude, 1M context) — the
orchestrator and architect. Not a code monkey that takes tickets.
An agent that reads the whole codebase, holds the entire design
system in context, sees the CSS cascade and the component tree and
the token architecture simultaneously, and makes judgment calls about
what belongs and what drifts. The kind of engineer who stares at a
screenshot for five minutes before writing a line, because the line
has to be the *right* line.

Opus cares about one thing: **craft at the atom level.** Not "does
it work" — everything works. The question is whether it *feels*
right. Whether the bevel catches the light the way a real raised
surface would. Whether the label says what the user needs in the
fewest possible words. Whether the accent color sits on the dark
chrome like it was always there, or screams for attention like a
notification badge on a Sunday morning.

The method: Opus orchestrates an army of **GPT-5.6 Terra** agents —
fast, thorough, disposable scouts. Terra troopers fan out in
parallel, each reading 3-5 components deeply against a checklist,
and report violations with file paths and line numbers. Opus
synthesizes, prioritizes, and designs the fix. Then Opus writes the
fix — or commands more troopers to write it — and walks the result
on the real hub before claiming done.

The audit that scaffolded this phase: 6 Terra agents fanned out
across every surface on the Desk — object windows, communication
panels, delivery tools, system surfaces, hosted cores, shared
infrastructure. 114 tool calls. 526k tokens. 73 violations
catalogued, severity-ranked, deduplicated, and compiled into a
punch list. That's not a test suite. That's a design review by a
team that can read every file in the project in five minutes.

## What we're building

HoldSpeak is an **AI power-user-first operating system** for the
busy tech lead and architect. The person who juggles six repos,
three LLM providers, a delivery roadmap, voice-to-text, agent
orchestration, and a notebook — and needs all of it in one
environment that doesn't fight them.

The Desk is that environment. Not a web app. Not a dashboard. An
OS — where objects are real, manipulation is direct, the grammar is
consistent, and the chrome is quiet enough to disappear. The kind
of tool where a senior engineer opens it on Monday and by Friday
can't remember how they worked without it.

Phase 115 is the phase where the Desk stops *approximating* an OS
and starts *being* one. Every surface, every control, every label —
held to the same standard. The phase where you open a note and the
editor fills the window. Where you open Desk memory and see human
language, not `steering_audit`. Where the accent color sits on the
chrome like forge-cooled metal, not a SaaS landing page CTA.

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

6. **The accent screams web app.** `#ff6b35` is a saturated warm
   orange doing 88 jobs — focus ring, primary button, editor caret,
   selection tint, window border, glow. On dark beveled surfaces
   it reads "startup landing page," not "operating system."

## Method

- **Shared CSS first (story 01).** Chip bevel, pullout specificity,
  section separators, window material consistency — fixes that ripple
  across all surfaces.
- **Content sanitization next (story 02).** One pass through every
  surface that leaks internal data. No raw IDs, no internal enums,
  no JSON dumps in product UI.
- **The cooled accent (story 08).** One token change, 88 consumers
  shift. The desk stops glowing orange and starts looking like
  patina on brushed metal.
- **Surface-by-surface refit (stories 03–05).** Each story takes a
  group of related surfaces and fixes layout, material, and content
  violations together.
- **DeliveryBoard redesign (story 06).** The worst offender gets its
  own story — information architecture rethink, not just CSS fixes.
- **Walk (story 07).** Screenshot every surface at 1440px and 393px.
  No violations survive.
- **Constitution articles cited per story.** No story ships without
  grounding in the canon it serves.

## Dependency graph

```
  01 (shared material) ──┬── 03 (object windows) ──┐
  02 (honest surface) ───┤── 04 (system surfaces) ──┤── 07 (the walk)
  08 (cooled accent) ────┤── 05 (hosted cores) ─────┤
                         └── 06 (rails window) ─────┘
```

Stories 01, 02, and 08 are foundations — they can run in parallel.
Stories 03–06 depend on the foundations and can run in parallel
with each other. Story 07 (the walk) is the gate — it runs last
and proves everything.

## Stories

### Foundation — shared fixes that ripple everywhere

| # | Story | The ask it answers | Status |
|---|-------|--------------------|--------|
| 01 | [The shared material](./story-01-the-shared-material.md) | "Chips have no bevel, windows have no depth, sections have no separation" | backlog |
| 02 | [The honest surface](./story-02-the-honest-surface.md) | "Why am I seeing steering_audit and %1 in the UI?" | backlog |
| 08 | [The cooled accent](./story-08-the-cooled-accent.md) | "The orange screams web app, not operating system" | backlog |

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
| HS-115-08 | The cooled accent | backlog | [story-08](./story-08-the-cooled-accent.md) | — |

## Where we are

Draft. Awaiting owner charter decision. Audit artifact published at
https://claude.ai/code/artifact/f5788f46-2b99-4e7f-b6e5-281c03e7c01c
