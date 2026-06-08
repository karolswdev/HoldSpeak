# HS-53-04 — The nudge UI (dictation surface)

- **Project:** holdspeak
- **Phase:** 53
- **Status:** not started
- **Depends on:** HS-53-02, HS-53-03
- **Unblocks:** HS-53-05
- **Owner:** unassigned

## Problem
The nudges exist over HTTP (HS-53-02) and the context action exists (HS-53-03); now they
have to show up where the user is, quietly and citably, so the activity becomes useful
instead of buried on `/activity`.

## Scope
- **In:**
  - A dismissible, source-cited **nudge card** on the dictation surface
    (`web/src/pages/dictation.astro` + `dictation-app.js`), cloning the `#kn-nudge`
    pattern (`dictation.astro:42`): `role="note"`, hidden until there is a nudge, never
    steals focus.
  - Each card **names its source** (browser/profile, the entity or page title, when it
    was last seen) so it is verifiable, and offers two actions: **"Dictate with this"**
    (HS-53-03) and **"Dismiss"** (HS-53-02).
  - Fetches from `GET /api/activity/nudges`; renders nothing when the list is empty or
    activity is off. JS-injected DOM uses `<style is:global>`.
  - **Optional:** the "since last meeting" windowed nudge on the home briefing
    (`index.astro`), if it fits cleanly.
  - **Screenshot evidence:** a `scripts/screenshot_activity_nudges.py` (mirror the
    existing `screenshot_*.py`: boot a real server over a seeded DB, no mic/LLM, drive
    Playwright) capturing the nudge card (with a source citation) and the empty/off state.
    PNGs committed to this phase's `screenshots/` folder.
- **Out:** the docs (HS-53-05); the engine/API (HS-53-01/02).

## Acceptance criteria
- [ ] A dismissible, source-cited nudge card renders on the dictation surface; it names
      the source and offers "Dictate with this" + "Dismiss".
- [ ] Dismiss persists (the card does not return on reload); nothing renders when the
      nudge list is empty or activity is off.
- [ ] Quiet + focus-safe (`role="note"`, never steals focus).
- [ ] `cd web && npm run build` clean; JS-injected DOM uses `<style is:global>`;
      screenshot-verified.
- [ ] `scripts/screenshot_activity_nudges.py` captures the nudge card + the empty state;
      PNGs committed to `screenshots/`. Source committed; 0 `_built/` tracked.

## Test plan
- `cd web && npm run build`; run the screenshot script and review the PNGs; a page-content
  test for the nudge markup if the surface has one.

## Notes / open questions
- UI/UX bar via `ui-ux-pro-max`: an inviting, quiet card, the Signal styling, a clear
  citation line, never a banner.
- Density invariant: if the card lands in `dictation.astro` (~2.7k lines), factor as you
  go.
