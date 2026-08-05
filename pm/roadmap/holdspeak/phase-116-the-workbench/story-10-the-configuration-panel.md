# HS-116-10 — The configuration panel

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-02
- **Unblocks:** HS-116-13, HS-116-14, HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

Every workbench setting is editable in-world, from the workbench
window itself. The configuration panel is the first thing a new
workbench shows — the moment you create one, you're already
configuring it, not navigating to a settings page. When a workbench
is configured, the panel collapses to a dense status strip that
tells you everything at a glance: who's working, where, when. Open
it again by clicking the strip. Thirty seconds from "New Workbench"
to "first run."

**Articles served:** VII (no modals — edit in-world, in place), II
(the workbench IS the configuration surface).

**UI/UX direction:** Study DW's Phase 36 workbench: the operator
topbar, comfortable/compact density, progressive disclosure. The
config panel follows the same philosophy: collapsed = one dense
mono strip; expanded = real, labeled controls with enough space to
breathe. No cramming everything into a toolbar. The Signal
Workbench material applies: hairline separators, mono labels,
bevel on actionable chips.

## Deliverables

1. **Collapsible configuration section.** Replaces the current
   inline toolbar. Two states:

   **Collapsed (configured workbench):**
   A single dense strip showing: agent avatar (16px) + agent name,
   egress lamp + target name, schedule in natural language ("7 AM
   weekdays"), skill count badge. Click to expand. The strip uses
   `SurfaceRow` from the surface kit — same as other dense desk
   rows.

   **Expanded (unconfigured or user-opened):**
   Full configuration panel with labeled sections, each on its own
   `SurfaceSection` with a hairline separator:

   - **Agent** — avatar (32px) + name + role, with a "Change"
     chip that opens a searchable list of recipes. Each recipe in
     the list shows avatar + name + role + system prompt preview
     (first 80 chars). The list uses `SurfaceRows`.
   - **Runs on** — `RunsOnPicker` with the target's readiness
     state below: model name, readiness lamp (green/amber/red),
     and if unavailable, the refusal reason as a quiet error line.
   - **Schedule** — preset chips (each a `desk-chip`) in a
     horizontal row: "7 AM daily", "7 AM weekdays", "2 AM nightly",
     "Every hour", "Manual". The active preset is visually selected
     (filled vs outlined). An "Enable/disable" toggle beside the
     presets. Below: the next fire time in natural language ("Next
     run: tomorrow at 7:00 AM").
   - **Skills** — a list of active skills (title + body preview),
     each with a Remove chip. Draft skills show with an Approve /
     Dismiss chip pair. An "Attach skill" chip at the bottom opens
     a search overlay. Skill count in the section header.

2. **Inline name editing.** The window title uses `EditInPlace`
   from the surface kit. Click → type → blur/Enter → saved via
   PUT. The glyph changes to match the agent's avatar family.

3. **Auto-expand on creation.** When a workbench is created from
   "New Workbench" (not from a template), the config panel is
   expanded and the agent picker is focused. When created from a
   template, the panel is collapsed (the template already
   configured everything).

4. **Workspace directory indicator.** At the bottom of the config
   panel, a quiet mono line: the workspace path
   (`~/.holdspeak/workbenches/<id>/`). A "Browse" chip opens the
   workspace wing (story 11).

## Test plan

- `npx vitest run` — config section renders collapsed and expanded,
  agent picker filters, schedule presets apply, skill list renders.
- Visual at 1440: create a blank workbench → config panel expanded
  → pick an agent → pick a target → pick "7 AM weekdays" → see the
  panel collapse to the dense strip. All in-world.
- Visual at 393: the panel stacks vertically, presets wrap, the
  dense strip is still readable.
