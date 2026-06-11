# HS-58-02 — README.md, the front door

- **Project:** holdspeak
- **Phase:** 58
- **Status:** done
- **Depends on:** HS-58-01
- **Unblocks:** HS-58-05
- **Owner:** unassigned

## Problem
The README's hero doesn't lead with the chosen angle, there is no
comparison section, and the feature story stops around the config-cockpit
era — the repo's front door under-sells the product behind it.

## Scope
- **In:** rewrite README.md against the canon: hero + one-liner ("one
  copilot, two modes"), a two-modes tour with equal billing (dictation:
  the pipeline, the journal/learning loop, voice commands, pre-briefing;
  meetings: live capture, import of recordings AND transcripts, the 14
  plugins, aftercare, faceted search), the honest named comparison
  section (date-stamped), quickstart/platform/upgrade-trust retained and
  tightened, the where-next table on canonical names, Qlippy as the
  delight beat. `docs/README.md` aligned to the same narrative. Keep the
  plugin-count claim (lock) and absolute URLs for images.
- **Out:** the deeper guides (03/04); new screenshot production beyond
  reusing existing assets where they fit.

## Acceptance criteria
- [x] The hero pitches both modes in one breath (the canon's one-liner
      verbatim); the "two modes" tour gives them equal billing and carries
      the post-48 surface the old README missed.
- [x] The comparison section names real tools, states trade-offs in both
      directions, and is date-stamped ("as of mid-2026").
- [x] Every claim is backed by a shipped capability; honest limits
      (0.x, Wayland best-effort, ffmpeg, bring-your-own model, no
      Windows) stay, gathered in the trade-offs paragraph.
- [x] Zero em/en dashes in prose; humanizer-clean (one slip caught and
      fixed in the audit); 238 lines vs. 217, with a whole new section.
- [x] All doc locks green (plugin count, links, images, vocab).
      See `evidence-story-02.md`.

## Test plan
- Doc-guard slice + full suite; rendered-preview check at closeout.
