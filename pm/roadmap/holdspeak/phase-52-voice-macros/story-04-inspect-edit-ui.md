# HS-52-04 — User-defined macros + the inspect/edit UI

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-02, HS-52-03
- **Unblocks:** HS-52-06
- **Owner:** unassigned

## Problem
The whole point of voice macros is that they are visible and editable, not LLM magic. A
user needs to see the macro list, add their own phrase to a deterministic action, and
edit or remove one, without hand-editing JSON.

## Scope
- **In:**
  - A "Voice macros" section in the settings cockpit (`web/src/pages/settings.astro` +
    `web/src/scripts/settings-app.js`): an enable toggle plus a visible, editable list
    of macros (phrase to action), with add / edit / remove.
  - Reuse the existing list-editor pattern from the memory-corrections curate UI
    (`web/src/pages/dictation.astro:290-356` + `dictation-app.js:1477-1621`): static add
    form, JS-rendered rows, delete via click delegation, refresh from `/api/settings`.
  - The built-in pack is shown read-only (so a user sees what already fires) and
    distinguished from their own editable macros.
  - Persisted through `PUT /api/settings` (HS-52-02). No LLM anywhere in this surface;
    what is shown is exactly what fires.
- **Out:** the matcher itself (HS-52-03); the runtime-activity signal (HS-52-05).

## Acceptance criteria
- [ ] A "Voice macros" settings section: enable toggle + an editable list with
      add/edit/remove, persisted via `/api/settings`.
- [ ] The built-in pack is visible (read-only); user macros are editable; the two are
      clearly distinguished.
- [ ] No LLM call in this surface; the displayed list is the source of truth for what
      fires.
- [ ] `cd web && npm run build` clean; JS-injected rows use `<style is:global>` CSS;
      screenshot-verified that styles apply and the list does not overflow.
- [ ] Source committed; 0 `holdspeak/static/_built/` tracked.

## Test plan
- `cd web && npm run build` succeeds; manual + screenshot of the section (empty state,
  a few macros, an overflow check). Page-content test if the surface has one.

## Notes / open questions
- UI/UX bar via `ui-ux-pro-max`: a real editing surface with affordances, an inviting
  empty state, and the Signal styling, not a raw textarea.
- If the macro UI lands in `dictation.astro` (~2.7k lines) rather than `settings.astro`,
  factor as you go (the standing density invariant); prefer the lighter `settings.astro`
  cockpit if it fits the journey.
