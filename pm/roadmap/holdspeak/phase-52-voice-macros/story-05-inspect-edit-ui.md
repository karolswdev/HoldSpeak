# HS-52-05 — The Voice Commands board (the centerpiece surface)

> **Placement decided (user, 2026-06-08): a dedicated command board, not a settings
> section.** Its own route (e.g. `/commands`) with a card-per-command grid, room to
> breathe, a big add CTA, and inline Test. Designed UI-first via `ui-ux-pro-max`
> before the model is finalized (see `design-voice-commands-board.md`).

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-02, HS-52-04
- **Unblocks:** HS-52-06
- **Owner:** unassigned

## Problem
Voice commands run real system actions, so the user must see and control exactly what each
keyword does, and add or remove them, without hand-editing JSON. The editing surface is
where the user grants the consent the dispatcher acts on. **This is the centerpiece of the
phase**, not a tail-end chore: the execution plumbing is mostly reused (the actuator
framework), so the feature lives or dies on whether this surface is beautiful, meaningful,
and easy. It is designed UI-first (the macro model in HS-52-02 serves this surface, not the
other way around).

## Scope
- **In:**
  - A dedicated "Voice Commands" board at its own route (e.g. `/commands`): the master
    enable switch plus a card-per-command grid with add / edit / remove. Build it to the
    `ui-ux-pro-max` design (`design-voice-commands-board.md`); reuse the memory-corrections
    render/persist mechanics (`dictation-app.js:1477-1621`) as the plumbing base, but the
    bar is a real tool, not a settings list. Add a discoverable entry point from the daily
    surfaces (dashboard / settings) that links to the board.
  - **A live preview line per row.** Every row reads back exactly what fires in plain
    language ("opens Terminal.app", "runs: git push origin HEAD", the snippet text). What
    you see is literally what fires.
  - **A Test button per row.** Fire the macro from the UI without speaking it, so the user
    can trust it before relying on it mid-dictation. (Runs through the same dispatch path.)
  - **A per-kind adaptive editor.** Choosing the action kind (Open URL / Launch app / Shell
    / Type text) morphs the form to fit it (URL field, app picker, monospace command box,
    snippet textarea). Never a raw payload field.
  - **Honest danger treatment for `shell`.** The command shows in monospace with a quiet
    "runs code on your machine" badge. Not a nag (the user owns the risk), never disguised
    as harmless.
  - **A match hint + conflict warning.** Show the normalized keyword the matcher actually
    listens for; warn if two macros share a keyword.
  - **An inviting empty state** with one-tap starter examples so the first command takes
    seconds.
  - Persisted through `PUT /api/settings` (HS-52-02). No LLM anywhere in this surface.
  - **Screenshot evidence (required).** A `scripts/screenshot_voice_commands.py` (mirror
    `scripts/screenshot_learning_digest.py`: boot a real server over a temp DB seeded with
    fixtures, no mic/LLM, drive Playwright) that captures the board's states:
    the **populated grid with all four macro kinds** (open_url, launch_app, shell,
    type_text), the **empty state**, the **per-kind adaptive editor** for each kind, and
    the **shell danger treatment**. PNGs committed to this phase's `screenshots/` folder.
    The new `/commands` route is also picked up by the `screenshots.yml` route-screenshot
    CI on this web-touching PR.
- **Out:** the matcher/dispatcher (HS-52-04); the docs (HS-52-06).

## Acceptance criteria
- [ ] A "Voice commands" settings section: enable switch + an editable list with
      add/edit/remove, persisted via `/api/settings`.
- [ ] Every row has a plain-language live preview of exactly what fires; a `shell` macro's
      command is shown in monospace with the "runs code" treatment.
- [ ] A per-row Test button fires the macro through the dispatch path without speaking it.
- [ ] The add/edit editor is per-kind adaptive (no raw payload field); shows the normalized
      match and warns on a keyword conflict; an inviting empty state with starters.
- [ ] `cd web && npm run build` clean; JS-injected rows use `<style is:global>` CSS.
- [ ] `scripts/screenshot_voice_commands.py` captures the populated board (all four macro
      kinds), the empty state, each per-kind editor, and the shell danger treatment; the
      PNGs are committed to this phase's `screenshots/` folder and reviewed (styles apply,
      no overflow, each state renders well).
- [ ] Source committed; 0 `holdspeak/static/_built/` tracked.

## Test plan
- `cd web && npm run build` succeeds; run `scripts/screenshot_voice_commands.py` and review
  the captured states (populated grid with all four kinds, empty state, each per-kind
  editor, shell danger). A page-content test for the `/commands` route if it has one.

## Notes / open questions
- UI/UX bar via `ui-ux-pro-max`: a real editing surface with affordances and the Signal
  styling, plus a plain-language note that these run real actions and are off by default.
- Prefer the lighter `settings.astro` cockpit over the ~2.7k-line `dictation.astro`; if it
  must land in `dictation.astro`, factor as you go (the standing density invariant).
