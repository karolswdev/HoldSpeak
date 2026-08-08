# HS-128-05 — Dock icon and palette commands

- **Project:** holdspeak
- **Phase:** 128
- **Status:** backlog
- **Depends on:** HS-128-02, HS-128-03, HS-128-04
- **Unblocks:** HS-128-07
- **Owner:** unassigned

## The thesis (the bar)

Intelligence must be reachable from the Desk's two universal entrances: the
dock for presence and the palette for intent.

### What changes

1. Add Intelligence to `DOCK_APPS` with the established launcher and
   `announceLauncher` behavior.
2. Derive its badge from overdue follow-through count or an unread Brief dot.
3. Register palette verbs in `VERBS`: `Show today's brief`, `Show overdue
   follow-through`, `Find receipt…`, and `Review decisions`.
4. Make each verb open the same pullout in its relevant view and filter state.

## Acceptance criteria

1. Dock and palette open one Intelligence pullout, never duplicate windows.
2. Badge state is honest: overdue count wins; unread brief otherwise shows a dot.
3. Every named palette command focuses the promised view or query mode.
4. Registry changes preserve existing keyboard and launcher behavior.

## Test plan

- Web: assert dock registration, launch announcement, and badge precedence.
- Palette: invoke all four verbs and assert target view/filter state.
- State: refresh projections after overdue and read-state changes.
