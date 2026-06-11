# HS-56-01 — Assets + the mascot gate

- **Project:** holdspeak
- **Phase:** 56
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-56-02..07
- **Owner:** unassigned

## Problem
The Qlippy pack lives on the Desktop and the presence layer has no mascot
concept: no assets in the repo, no `presence.mascot` flag, no settings
affordance, no way for the presence page to know the mascot is wanted.

## Scope
- **In:**
  - Vendor the pack into `web/public/qlippy/`: the 14 sprite strips
    (`sprites/<state>.png`, 80×80 × 9 frames), the 4 glyphs, the canonical
    avatar; a short `web/public/qlippy/README.md` recording provenance (the
    PixelLab object id + the body-emotes/composited-glyph design rule, per
    the asset-pack README).
  - `PresenceConfig.mascot: bool = False`; round-trips config-version-safe
    through `/api/settings` (the PresenceConfig pattern).
  - The `/settings` presence section gains a "Qlippy, the mascot" sub-toggle
    (visually subordinate to the presence toggle; inert/dimmed when presence
    itself is off), persisted live like the presence toggle.
  - The flag reaches the presence page: extend what `GET /api/state` (or the
    equivalent the page already reads) exposes, without breaking existing
    consumers.
- **Out:** any rendering (HS-56-02+).

## Acceptance criteria
- [x] Assets committed under `web/public/qlippy/` with the provenance README;
      `npm run build` clean; served under the `/_built` base (verified: 14
      sprites in `_built/qlippy/sprites/` post-build).
- [x] `presence.mascot` defaults off, persists via `/api/settings`, coerces
      config-version-safe (test — zero route changes needed; the
      `PresenceConfig(**data)` construction carries it).
- [x] The settings sub-toggle renders, persists, and is subordinate to the
      presence toggle (page-content + integration test; two reviewed
      screenshots: inert + on).
- [x] The presence page can read the flag (via the existing
      `GET /api/settings`); with it unset, nothing else changed — the
      presence page was not touched this story, and the full suite is green
      unmodified (2573 passed, 17 skipped; see `evidence-story-01.md`).

## Test plan
- Unit/integration: config round-trip + coercion; settings API; page-content
  locks. Full suite.

## Notes / open questions
- Public-dir serving keeps 14 strips out of the JS bundle; the page
  references `/_built/qlippy/<state>.png` (base-aware).
