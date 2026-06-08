# HS-52-05 — Inspect/edit UI: the voice-commands editor

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-02, HS-52-04
- **Unblocks:** HS-52-06
- **Owner:** unassigned

## Problem
Voice commands run real system actions, so the user must see and control exactly what each
keyword does, and add or remove them, without hand-editing JSON. The editing surface is
where the user grants the consent the dispatcher acts on.

## Scope
- **In:**
  - A "Voice commands" section in the settings cockpit (`web/src/pages/settings.astro` +
    `web/src/scripts/settings-app.js`): the master enable switch plus a visible, editable
    list of macros, each row showing the keyword, the action kind, and its payload
    (the URL / app / command / snippet), with add / edit / remove.
  - Reuse the memory-corrections list-editor pattern (`dictation.astro:290-356` +
    `dictation-app.js:1477-1621`): add form, JS-rendered rows, delete via click
    delegation, refresh from `/api/settings`.
  - Make the action plain to read: a `shell` macro shows the exact command it will run, so
    "what you see is what fires" is literally true. An inviting empty state.
  - Persisted through `PUT /api/settings` (HS-52-02). No LLM anywhere in this surface.
- **Out:** the matcher/dispatcher (HS-52-04); the docs (HS-52-06).

## Acceptance criteria
- [ ] A "Voice commands" settings section: enable switch + an editable list (keyword +
      action kind + payload) with add/edit/remove, persisted via `/api/settings`.
- [ ] Each row shows exactly what will run; a `shell` macro's command is visible.
- [ ] `cd web && npm run build` clean; JS-injected rows use `<style is:global>` CSS;
      screenshot-verified that styles apply and the list does not overflow.
- [ ] Source committed; 0 `holdspeak/static/_built/` tracked.

## Test plan
- `cd web && npm run build` succeeds; manual + screenshots (empty state, a few macros of
  different kinds, an overflow check). Page-content test if the surface has one.

## Notes / open questions
- UI/UX bar via `ui-ux-pro-max`: a real editing surface with affordances and the Signal
  styling, plus a plain-language note that these run real actions and are off by default.
- Prefer the lighter `settings.astro` cockpit over the ~2.7k-line `dictation.astro`; if it
  must land in `dictation.astro`, factor as you go (the standing density invariant).
