# HS-73-02 — Create in-world (kill the modals)

- **Status:** todo
- **Priority:** HIGH (the no-modals rule, finally enforced on the web)
- **Depends on:** HS-73-01

## Goal

"New Note" spawns a real note object on the stage **instantly** and you edit
it in place — the object IS the editor. Port the iPad's
`DioInlineNoteCard`/`DioInlineKBCard` grammar (owner rules from the
2026-06-27 device-gap punch-list: no dim-scrim modals; New Note must create
a card instantly). The `role="dialog" aria-modal="true"` form drawers at
`desk.astro:488+` are deleted.

## Scope

- **In:** in-world create + edit for **note, KB, agent, zone**; the create
  beat; the drawer deletion; keyboard + escape behavior.
- **Out:** meetings/artifacts (created by recording/intel, not by hand);
  chains/workflows (their authoring stays where it is until the HS-73-04
  inventory decides their home); a browser-mic voice-fill (Out for the
  phase — see the phase status doc); the pull-out (HS-73-03 — but build the
  inline editor so the pull-out can embed it).

## Tasks

- [ ] **Create instantly:** the `+ Note` chip calls `POST /api/notes` with
      a default title (`"New note"`) immediately, then `markNew(id)`
      (`desk-app.js:393`) + the `hs-materialize` motion play as the object
      appears at stage center, and the inline editor opens on it. Same
      pattern for KB (`POST /api/kbs`) and zone (`POST /api/directories`).
      Agents create with the default avatar + name `"New agent"` via
      `POST /api/agents`.
- [ ] **Edit in place:** an Alpine-rendered editor card anchored to the
      object's stage position (the object scales up slightly; the world
      dims *around* it via a radial vignette, never a flat scrim):
      - Note: title input + markdown body textarea + tags — autosaving on
        blur/debounce via `PUT /api/notes/{id}` (verify the PUT route
        exists in `holdspeak/web/routes/primitives.py`; it is the same
        route the list's edit used).
      - KB: title + content, same pattern.
      - Agent: the essential trio (name, role, system prompt) visible;
        "More" expands the remaining fields (template, tools, KB id,
        profile) **inside the same card** — expansion, not a second
        surface.
      - Zone: name only, edited on the tray itself (HS-73-05 restyles the
        tray; the inline rename ships here).
- [ ] Escape/click-outside closes the editor (the object settles back with
      its saved state); unsaved-input loss is impossible because saves are
      on-change.
- [ ] Delete the create drawers (`desk.astro:488+`), their `creating`
      state, `openCreate`/`closeCreate`, and every "Saves to `POST …`"
      microcopy string. The empty-state "Create the first …" links in the
      appendix rewire to the in-world create until HS-73-04 removes them.
- [ ] All new DOM is factory-rendered → all CSS `<style is:global>`; new
      logic lands in `web/src/scripts/desk/create.js` +
      `desk/inline-editor.js`, imported and composed into the `DeskApp()`
      factory (the `?raw` load pattern stays).

## Proof required

A capture (or screenshot sequence) of: chip tap → object materializes with
the NEW beat → typing in place → reload → the content persisted (real
`/api/notes` round-trip, not local state). The same for agent and zone.
Zero `role="dialog"` / `aria-modal` occurrences left in `desk.astro` (grep
in evidence). Keyboard walk: create, type, Escape, reopen. Route pre-flight
+ full suite + `npm run build` green.
