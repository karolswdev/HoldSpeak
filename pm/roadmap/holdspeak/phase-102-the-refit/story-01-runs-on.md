# HS-102-01 — Runs on: destinations easy as heck

- **Project:** holdspeak
- **Phase:** 102
- **Status:** done
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

## Design direction (grounded in a live drive, 2026-07-21)

Driven headed against a fresh staged instance: `New destination` is a
literal `Name` / `Kind`-as-`<Select>` / `Base URL` / `Model` /
"Requires its own key on the hub" checkbox / `Context window` stack —
the exact composition canon rule 1 outlaws. Do not invent a new
component for the fix; one already exists and already solves this
shape:

1. **Reuse `RuntimeDestination` verbatim, don't reinvent it.**
   `web/src/pages/cores/settingsBespoke.tsx` (round 5) already turns
   "where does voice typing run" into choice bays that reveal only
   the chosen path's fields ("these things are complicated enough
   that they can't just be dumbed down to a bunch of input boxes" —
   the owner's bar that built it). Lift its choice-bay pattern
   (kind-as-bay-picker, not kind-as-`<Select>`) into `ProfilesCore.tsx`
   directly, or factor it into one shared piece both call — never a
   second hand-rolled version of the same idea.
2. **`SurfaceBay` (`Surface.tsx:544`) needs an expand slot.** It has
   no in-place-edit affordance today — this story is the one that
   adds it (an `expanded`/`onToggle` prop, or an `EditInPlace`-style
   swap of the bay's body for the create/edit form), so editing opens
   ON the bay's own `<li>`, not in a `NEW RUNS ON DESTINATION` section
   bolted below the `DESTINATIONS` list. Ship the prop as a `SurfaceBay`
   kit addition, not a `ProfilesCore`-local fork.
3. **Bays by kind, named exactly:** Endpoint (OpenAI-compatible) / This
   device / Paired device / Mesh node. Each bay's expanded body shows
   ONLY that kind's fields (an endpoint needs Base URL + Model + key
   toggle; "this device" needs none of those).
4. **Honest validation inline, before Save exists as a concept.** A
   malformed URL refuses by name as it's typed (not on submit); a
   "Check" verb pings the real endpoint for a reachable kind and the
   bay's `state`/`lamp` (already wired for liveness — see
   `04-settings.png`'s Settings groups for the same honest-toggle
   language) reflects it live while editing, before commit.
5. **No `New destination` button floating as a lone CTA above an
   empty list.** The empty state's own affordance IS a bay-shaped
   "add" row at the switchboard's foot (consistent with rule 2 —
   creation and editing are the same in-place mechanism, not two
   different UI idioms for the same act).

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
