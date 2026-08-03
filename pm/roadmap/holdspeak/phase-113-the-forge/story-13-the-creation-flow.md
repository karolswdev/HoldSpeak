# HS-113-13 - The creation flow

- **Project:** holdspeak
- **Phase:** 113
- **Status:** backlog
- **Depends on:** HS-113-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Creating things on the Desk must be as natural as it is in any
real OS. Cmd+N creates a new note. The empty desk has a visible
Create button. The command palette shows create verbs without
requiring the user to already know what to search for. The
decision creation flow must actually work — InlineEditor must
render decision fields. Every primitive kind must have a
consistent, complete creation-to-editing flow.

**Articles served:** I (the Desk is the front door — it must be
immediately productive), VII (the interface serves — affordances
are visible), VIII (native-grade craft — OS-level keyboard
shortcuts).

## Ground (from the behavioral audit)

- `web/src/desk/verbRegistry.ts` — the `desk.new-note` verb has
  no `key` binding. There is no Cmd+N shortcut for any create
  action. The most common OS shortcut is absent.
- `web/src/desk/DeskApp.tsx` — the empty desk shows only
  "Dictate · Record · Create" and "Seed the desk". No visible
  "New Note" button. No hint about right-click or Cmd+K.
- `web/src/desk/components/DeskCommandPalette.tsx` (or equivalent)
  — the command palette's cold state filters out create verbs
  unless they're in recents: `if (!normalized &&
  !recents.includes(v.id)) continue;`. A new user opening Cmd+K
  sees Programs and Settings but NOT the "New Note" verbs.
- `web/src/desk/components/InlineEditor.tsx` — handles note, kb,
  workflow, and recipe kinds but NOT decision. When a decision is
  created, `openEditor(id)` opens InlineEditor with no decision
  rendering branch — the editor opens empty. Broken flow: 5
  gestures to reach an editable state.
- `web/src/desk/store.ts` — `createPrimitive` always places new
  objects at stage center (0.5, 0.55). No way to create objects
  inside a zone window.

## Method

1. **Cmd+N for new note** — add `key: "Mod-n"` to the
   `desk.new-note` verb in `verbRegistry.ts`.

2. **Empty desk affordance** — in `DeskApp.tsx` / EmptyDesk, add
   a prominent "+ New Note" button that calls
   `createPrimitive("note")`. Below the start actions, add a
   quiet hint: "or right-click · Cmd+K". No prose — just the
   affordances.

3. **Cold Cmd+K shows create verbs** — find the command palette
   filter and exempt `group === "new"` verbs from the recency
   gate. Create verbs appear in the cold palette's VERBS section
   without requiring a search query.

4. **Decision InlineEditor branch** — add a decision rendering
   path to `InlineEditor.tsx`:
   - Title input
   - Status cycle (proposed/accepted/superseded/deprecated) as
     `desk-chip` buttons
   - Context field (DeskEditor with label "Context")
   - Decision field (DeskEditor with label "Decision")
   - Consequences field (DeskEditor with label "Consequences")
   - Deciders input (comma-separated text)
   - Tags input
   - Debounced PUT to `/api/decisions/{id}`

5. **Create inside zone windows** — add a "+ New" button to the
   ZoneWindow footer (using DeskWindowFooter). Clicking it opens
   a small picker (Note / Knowledge / Agent) and creates the
   primitive filed directly into that zone.

## Test plan

- Unit: Cmd+N creates a note and opens the editor.
- Unit: empty desk renders a "+ New Note" button that creates
  and opens a note.
- Unit: cold Cmd+K palette shows "New Note", "New Decision",
  etc. without typing.
- Unit: InlineEditor renders decision fields (status cycle,
  context/decision/consequences editors, deciders input).
- Unit: decision creation → InlineEditor opens with all fields
  editable.
- Unit: "+ New" in ZoneWindow creates a note filed into that
  zone.
- Screenshot walk: 1440px — empty desk with Create button,
  decision InlineEditor with all fields visible.
