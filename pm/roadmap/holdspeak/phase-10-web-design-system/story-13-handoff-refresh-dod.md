# HS-10-13 - Designer handoff refresh + phase exit

- **Project:** holdspeak
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HS-10-01 through HS-10-12
- **Unblocks:** phase 11 work
- **Owner:** unassigned

## Problem

The phase ships only when the artifact a designer would judge — the
`designer-handoff/` package — reflects the new state. Today the
package describes the legacy UI; if we land the rebuild without
refreshing handoff, future designers get a misleading snapshot and the
open style questions never get closed.

## Scope

- **In:**
  - Re-run `designer-handoff/capture-screenshots.py` against the
    rebuilt runtime; commit the new screenshots.
  - Update `designer-handoff/style-handoff.md`:
    - Replace "Current Visual Language" with the actual rebuilt one.
    - Resolve every "Open Style Question" with one of: a documented
      answer, a deliberate deferral with reasoning, or a follow-up
      pointer.
  - Update `designer-handoff/ux-inventory.md`:
    - Reflect the unified TopNav, the component library, and the
      consistent empty-state grammar.
    - Replace "Current Gaps For Designer Review" with a much shorter
      list of remaining (genuinely small) gaps.
  - Update `designer-handoff/functional-handoff.md` only where behavior
    changed; this rebuild was intentionally presentation-only, so most
    workflow text stays.
  - Update `designer-handoff/screenshot-index.md` with the new captures.
  - Phase DoD checklist (this story is the canonical phase-exit story):
    - All HS-10-01..12 stories `done` with evidence files.
    - `current-phase-status.md` story table fully updated.
    - `pm/roadmap/holdspeak/README.md` "Last updated" line bumped.
    - No `<style>` block remains inline in any served page (post-build
      grep is clean).
    - The legacy `holdspeak/static/{dashboard,activity,history,
      dictation,dictation-runtime-setup}.html` files no longer ship
      from source — only the Astro-built equivalents do.
- **Out:**
  - Any new design work — this is exit-gate documentation.
  - Phase 11 prep beyond noting that connector packs will use the new
    component grammar.

## Acceptance Criteria

- [ ] Fresh screenshots committed for every route in
  `designer-handoff/screenshots/`.
- [ ] All open style questions in `style-handoff.md` resolved or
  explicitly deferred.
- [ ] `ux-inventory.md` "Current Gaps For Designer Review" pruned to
  what remains.
- [ ] Inline `<style>` grep returns zero matches in served output.
- [ ] No legacy hand-authored HTML remains in `holdspeak/static/`
  source ownership.
- [ ] Roadmap README updated with phase-10 completion.

## Test Plan

- Manual screenshot recapture run.
- `grep -r '<style>' holdspeak/static/` is empty (or only matches
  Astro-emitted scoped styles, which use a different mechanism — the
  evidence file documents what the grep should look like in the new
  pipeline).
- Full regression sweep: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes

This story is pure discipline — it is what makes the next person
(human or agent) trust that "phase 10 done" actually means the design
system is real and documented. Do not skip the question-resolution
step in `style-handoff.md`; that document's open-questions section is
the lighthouse for whether the system is coherent.
