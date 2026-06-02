# HS-30-01 — UX audit + IA redesign

- **Project:** holdspeak
- **Phase:** 30
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-30-02, HS-30-04
- **Owner:** unassigned

## Problem

The Workbench UI was built look-first (Phase 12), not flow-first. Before we
recolour anything we need to know what's actually wrong with the *experience*:
what the five routes are for, where the information architecture and navigation
fail, and what the redesigned surface should be. Skipping this turns a "full UX
overhaul" into a re-skin.

## Scope

### In

- A **UX audit** (`evidence/ux-audit.md`) of all five routes — `index`
  (dashboard / live meeting runtime), `dictation`, `history`, `activity`,
  `companion` — captured from the running app: what each screen does, the user's
  primary task on it, and concrete IA/usability problems (nav model, hierarchy,
  density, discoverability, empty/loading/error states, cross-route consistency).
- An **IA spec** (`evidence/ia-spec.md`): the redesigned navigation model, the
  per-route layout intention (regions, primary action, what's promoted/demoted),
  and the global patterns every page must share (page header, side rail, status,
  toolbar). This is the contract the page stories (HS-30-06/07/08) build to.
- Use the `ui-ux-pro-max` skill's `ux` / `product` domains to ground the audit in
  established UX guidelines (navigation ≤ items, hierarchy, feedback, empty states).
- Before/after framing only at the IA level — visual language is HS-30-02.

### Out

- Any colour, font, or token decisions (HS-30-02).
- New product features or new routes — IA covers the existing five surfaces.
- Code changes — this story produces docs only.

## Acceptance criteria

- [x] `evidence/ux-audit.md` exists and names, per route, the primary user task
      and at least the top concrete IA/usability problems with the current design.
- [x] `evidence/ia-spec.md` exists and defines: the new nav model, the shared
      global page patterns, and a per-route layout intention for all five routes.
- [x] The audit cites specific `ui-ux-pro-max` `ux`/`product` guidelines (search
      output captured) rather than asserting from taste alone.
- [x] Captured from the **running** app (`astro preview` build), not from reading
      source alone — `evidence/before/before-*.png`.

## Test plan

- Unit / backend: n/a — docs-only story.
- Visual: run `cd web && npm run dev`, walk all five routes, capture current-state
  screenshots into `evidence/` for the audit.
- Build: n/a (no code change).

## Notes / open questions

- Canon: `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` (web-first runtime),
  `README.md` (public usage). If the IA disagrees with canon, canon wins — record
  the conflict here.
- Park the command-palette question for HS-30-04; just flag in the IA whether the
  nav model wants one.
