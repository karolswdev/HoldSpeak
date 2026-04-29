# HS-10-09 - `/dictation` rebuild

- **Project:** holdspeak
- **Phase:** 10
- **Status:** backlog
- **Depends on:** HS-10-03, HS-10-04, HS-10-05, HS-10-10
- **Unblocks:** HS-10-13
- **Owner:** unassigned

## Problem

`/dictation` is the technical configuration surface (blocks, KB,
runtime settings, dry-run). Density is acceptable here, but the current
implementation is small-card-soup: nested cards, inconsistent button
treatments across tabs, dry-run output shown in an ad-hoc preview
block. Power users use this screen repeatedly and feel every rough
edge.

## Scope

- **In:**
  - Replace `holdspeak/static/dictation.html` with `web/src/pages/
    dictation.astro` and any sub-pages.
  - Tab structure: Readiness, Blocks, Project KB, Runtime, Dry-run.
  - Form input components introduced as needed (`TextInput`,
    `Textarea`, `Select`, `Toggle`) following the same token-driven,
    focus-ring-consistent style — added to `web/src/components/`.
  - Block editor: list on the left (using `ListRow`), editor on the
    right; no nested cards inside cards.
  - Project KB editor: same pattern.
  - Dry-run trace rendered through the standardized `CommandPreview`
    from HS-10-10 (this story explicitly depends on it).
  - Readiness panel: each check is a `ListRow` with status pill and a
    single primary action when remediation is possible.
  - Replace `holdspeak/static/dictation-runtime-setup.html` with an
    Astro version too — it's only 95 lines, but it lives under
    `/docs/dictation-runtime` and should match the system.
- **Out:**
  - Changes to dictation block schema or KB schema.
  - Changes to readiness check logic.
  - New dry-run capabilities.

## Acceptance Criteria

- [ ] All five tabs render on the new system.
- [ ] Block editor supports the existing create/edit/delete flows with
  no regressions.
- [ ] Readiness checks display consistently and remediation actions
  still work.
- [ ] Dry-run output uses `CommandPreview` from HS-10-10.
- [ ] `/docs/dictation-runtime` rebuilt on the new system.

## Test Plan

- Static surface integration test for `/dictation` tabs.
- Manual block CRUD round-trip.
- Manual dry-run trigger and output review.
- Manual narrow-viewport pass; confirm form labels and inputs do not
  overflow at 420px.

## Notes

Form components (`TextInput`, `Textarea`, `Select`, `Toggle`) live in
this story rather than HS-10-03 because their requirements only become
concrete when the dictation editors land. Add them to the gallery at
the same time so the artifact stays complete.
