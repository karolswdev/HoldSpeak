# HS-102-01 — Runs on: destinations easy as heck

- **Project:** holdspeak
- **Phase:** 102
- **Status:** ready
- **Depends on:** —
- **Unblocks:** HS-102-07

## The owner's words (the bar)

> "'Runs On' window — an absolute overhaul to use OS-like guides,
> styles, and generally improve the usability of this component so
> that managing and creating destinations is easy as heck."

## Problem

The switchboard half (HS-101-03 B5) reads right: bays, lamps, the
route. But CREATING or EDITING a destination
(`web/src/pages/cores/ProfilesCore.tsx`, the `editing` branch) drops
back into a label-over-input form stack — Name / Kind-as-a-Select /
Base URL / Model / Context window / a "Save destination" button — the
exact composition canon rule 1 outlaws outside a configuring face,
and a Kind SELECT that gates which fields appear is a guide the
person has to simulate in their head. Round 5 already built the
answer once: `RuntimeDestination` in `settingsBespoke.tsx` turned
"where does voice typing run" into CHOICE BAYS that reveal only the
chosen path's needs. Destinations deserve the same guided grammar,
plus honest validation (a bad URL or unreachable endpoint should say
so BEFORE Save, by name).

## Scope

- In: `ProfilesCore.tsx` — the create/edit path becomes a guided,
  OS-grade flow: kind as choice bays (endpoint / this device /
  paired device / mesh node) with only the chosen bay's fields;
  editing happens ON the bay (the switchboard row expands in place —
  no separate form section below the list); reachability/validation
  surfaced honestly at the point of entry (URL shape; a "Check"
  verb against the real wire where one exists); Make default /
  Delete stay on the bay. The mockup-grade before/after for this
  recomposition is part of THIS story's eyes-first step.
- Out: the `/api/profiles` wire contract (byte-identical); the
  switchboard bay composition itself (B5, keep); Settings'
  RuntimeDestination (already bespoke).

## Acceptance criteria

- [ ] Hands-first ledger recorded in the evidence file (headed, 1440
      + 393) BEFORE the first code change.
- [ ] Creating a destination never shows a bare label+input stack:
      kind is chosen by bay, and only that path's fields render,
      inline on the switchboard.
- [ ] Editing opens IN PLACE on the destination's bay; Escape
      reverts, the commit rides the existing PUT/POST unchanged.
- [ ] Dishonest states impossible: an invalid URL refuses by name
      before save; a mesh node's liveness shows on the bay while
      editing.
- [ ] Driven live on a staged hub: create → appears as a bay; edit →
      changed on the wire; delete two-step; Make default flips the
      route lamp. Screenshots at 1440 + 393, all read.
- [ ] A named guard: the interior-canon guard (or a vitest) refuses
      a `Field`-stack regression inside ProfilesCore's edit path.

## Test plan

- Web vitest (ProfilesCore tests updated); token gate; vocabulary +
  interior-canon guards; geometry walk (the Runs on window is one of
  the measured 12); live create/edit/delete walk on the staged hub,
  headed, both viewports.

## Evidence required

- The ledger; before/after screenshots; the live-drive record; guard
  output.
