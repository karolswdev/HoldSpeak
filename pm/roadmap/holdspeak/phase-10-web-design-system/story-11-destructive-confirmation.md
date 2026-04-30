# HS-10-11 - Destructive-action confirmation pattern

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-10-03, HS-10-05
- **Unblocks:** HS-10-13
- **Owner:** unassigned

## Problem

The product has several destructive actions: delete a meeting, clear
connector output, remove a candidate, delete a dictation block, delete
a project rule, drop activity records. Today the confirmation language
and visual treatment differ per surface — sometimes a native
`confirm()`, sometimes a custom overlay, sometimes none at all. This is
inconsistent at best and dangerous at worst (the gh/jira deletion in
particular needs to make clear it touches *connector output*, not
source data).

## Scope

- **In:**
  - `web/src/components/ConfirmDialog.astro` — modal with title,
    descriptive body, `LocalPill` for "this affects local data only"
    where applicable, primary destructive button (red), secondary
    cancel button.
  - Standard copy patterns: "Delete X?", "Clear Y?", with explicit
    scope language ("This removes the local annotations written by
    this connector. It does not touch the source data on GitHub.").
  - Focus management: focus the cancel button on open; trap focus
    inside the modal; restore focus to the originating button on
    close.
  - Keyboard: Esc closes; Enter triggers cancel by default (destructive
    actions never default-confirm on Enter).
  - Adoption in every destructive action site:
    - `/activity` connector output deletion (gh, jira).
    - `/activity` candidate clearing.
    - `/activity` activity-records deletion (if exposed).
    - `/history` meeting deletion.
    - `/dictation` block deletion.
    - `/dictation` KB-entry deletion.
- **Out:**
  - Async/long-running operation progress UI inside the dialog (those
    use the existing `Button loading` state).
  - Bulk-delete UX — if needed, that's a future product story.

## Acceptance Criteria

- [x] Every destructive site listed above uses `ConfirmDialog`. Greps
  for `window.confirm(` in `web/` return zero matches.
- [x] Cancel is the default focus and the default Enter target.
- [x] Focus is trapped while the dialog is open and restored on close.
- [x] Esc closes without confirming.
- [x] Connector-output deletions explicitly state that source data is
  untouched.

## Test Plan

- Manual keyboard-only walk through every destructive site.
- Manual Esc/Enter behavior verification.
- Visual check of the destructive button's red treatment vs the rest
  of the system.

## Notes

The copy is half the value here. Resist generic "Are you sure?" — every
destructive action gets specific scope language.
