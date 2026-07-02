# HS-73-03 — Create in-world (no modals, ever)

- **Status:** todo
- **Priority:** HIGH (the no-modals rule, finally enforced on the web)
- **Depends on:** HS-73-01

## Goal

"New Note" spawns a real note object on the stage **instantly** and you
edit it in place — the object IS the editor. The iPad's
`DioInlineNoteCard`/`DioInlineKBCard` grammar, now in React (owner rules
from the 2026-06-27 device-gap punch-list: no dim-scrim modals; New Note
must create a card instantly).

## Scope

- **In:** in-world create + edit for **note, KB, agent, zone**; the create
  beat; escape/click-outside behavior; autosave.
- **Out:** meetings/artifacts (created by recording/intel, not by hand);
  chains/workflows (their authoring home is decided by the HS-73-08
  inventory); the pull-out (HS-73-04 — but the inline editor built here
  must be embeddable there).

## Tasks

- [ ] **Create instantly:** the `+ Note` chip fires `POST /api/notes` with
      a default title immediately; the object appears at stage center with
      a `motion` materialize spring + the NEW beat (port `markNew/isNew`,
      `desk-app.js:393/398` — accent glow, pulse ring, short NEW badge);
      the inline editor opens focused. Same for KB (`POST /api/kbs`),
      agent (`POST /api/agents`, default avatar + name), zone
      (`POST /api/directories`, rename-in-place on the tray).
- [ ] **`InlineEditor` component**, anchored to the object's stage
      position (the object scales up; the world dims around it via a
      radial vignette — never a flat scrim, never `aria-modal`):
      - Note: title input + markdown body + tags; autosave on
        blur/debounce via the notes update route — **verify the exact
        update route/verb in `holdspeak/web/routes/primitives.py` before
        writing the client** (the legacy list's edit path is the
        reference).
      - KB: title + content, same pattern.
      - Agent: essentials visible (name, role, system prompt); "More"
        expands template/tools/KB/profile **inside the same card**.
- [ ] Escape / click-outside closes; saves are on-change so nothing can be
      lost; the float freezes while editing, resumes on close.
- [ ] State: an `editing: id | null` slot in the store; only one editor
      open at a time; opening another closes the first (saving).

## Proof required

A capture: chip → materialize + NEW beat → type in place → reload → content
persisted (real API round-trip). Same for agent and zone rename. Grep: zero
`role="dialog"` / `aria-modal` under `web/src/desk/`. Keyboard walk
(create, type, Escape, reopen). Route pre-flight + full suite +
`npm run build` green.
