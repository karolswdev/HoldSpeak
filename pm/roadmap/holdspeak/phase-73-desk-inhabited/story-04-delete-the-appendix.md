# HS-73-04 — Delete the appendix (one paradigm)

- **Status:** todo
- **Priority:** MED (the deletion is trivial; the zero-loss inventory is the story)
- **Depends on:** HS-73-02, HS-73-03

## Goal

Remove "Browse as a list" (`desk.astro:158–429`) — the entire pre-Phase-71
admin page still stacked under the world — so `/desk` is one paradigm. The
rule: **zero verbs lost.** Every control in the appendix either already has
an in-world home (from 02/03), gets one here, or is relocated to a `/studio`
surface with a decision note. Nothing is silently dropped.

## Scope

- **In:** the verb inventory; the deletion; the small in-world additions the
  inventory demands; relocations.
- **Out:** building new major surfaces for relocated verbs (a relocation is
  a link/placement on an existing `/studio` page, or a deferral recorded in
  the phase status doc with the owner flagged).

## Tasks

- [ ] **Inventory first, in the evidence file:** walk `desk.astro:158–429`
      and table every interactive control with its disposition. Known
      population (verified at scaffold): per-kind `openCreate(kind)` add
      buttons; per-card "Move to…" `openFile(kind, item)` (the
      directory-membership picker drawer); `openRun(item, 'agent'|'chain'|
      'workflow')`; per-kind empty-state "Create the first …" links; card
      title/meta displays; plus whatever field-level edit affordances the
      cards carry — the inventory must be exhaustive from the source, not
      from this list.
- [ ] Expected mappings (validate each): create → HS-73-02 chips; open/
      inspect → HS-73-03 pull-outs; run → pull-out Run (HS-73-03/07);
      "Move to…" → drag-onto-zone already files, **but** add a `Move to…`
      action inside the pull-out reusing `toggleFile`/`openFile` logic
      (`desk-app.js:708/724`) as the no-drag path (keyboard + accessibility
      parity — the iPhone lane learned this same lesson with long-press
      filing, PR #195).
- [ ] Delete: the `<details class="desk-list">` block, the run/file drawers
      that served only the list (keep/adapt the file-picker logic the
      pull-out now uses), dead Alpine state (`tab`, list-only helpers —
      e.g. `worldRows` at `desk-app.js:412` if nothing else consumes it),
      and the orphaned CSS (including the `.desk-list-toggle` rules,
      `desk.astro:~980`).
- [ ] Add a delete affordance if (and only if) the inventory finds one in
      the appendix: destructive actions go through the existing premium
      confirm sheet (Phase 69's `ConfirmDialog`), never `window.confirm`.
- [ ] Re-run the HS-73-01 line-count target: with the appendix gone, no
      desk file over ~600 lines; extend the density guard to cap
      `components/desk/*` and `scripts/desk/*`.

## Proof required

The disposition table in the evidence file with EVERY control accounted
for. Grep: zero references to `desk-list`, `openCreate`, and the deleted
state keys. Screenshots: the page ends where the world ends (no scrollable
appendix). Density guard green with the new caps; route pre-flight + full
suite + `npm run build` green.
