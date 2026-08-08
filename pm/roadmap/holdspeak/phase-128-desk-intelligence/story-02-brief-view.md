# HS-128-02 — Brief view

- **Project:** holdspeak
- **Phase:** 128
- **Status:** in-progress
- **Depends on:** HS-128-01
- **Unblocks:** HS-128-05, HS-128-07
- **Owner:** unassigned

## The thesis (the bar)

The Monday brief becomes the first thing the Desk shows about today: a compact
operating picture from stored facts, never a dashboard or invented summary.

### What changes

1. Render `MondayBriefService` data with a 32px Space Grotesk headline hero.
2. Group Changed, Broke, Waiting, and Decisions in `FoldGadget` sections.
3. Render each item as a `SurfaceLedgerRow` with its source link.
4. Provide `ACKNOWLEDGE`, `DEFER`, and `SPEAK` footer verbs, including shelf
   state after acknowledgement.
5. Render the exact empty state: `Nothing material changed.`

## Acceptance criteria

1. The view renders each service group and its source-backed rows.
2. Acknowledging a brief item updates the shelf state without hiding history.
3. Every footer verb uses the shared SurfaceFooter contract.
4. Empty service output produces only the named empty state.

## Test plan

- Web: fixture each brief group, source link, and empty response.
- Interaction: acknowledge one row and assert its shelf state and footer verbs.
- Service: exercise the brief read and acknowledgement path through its API.
