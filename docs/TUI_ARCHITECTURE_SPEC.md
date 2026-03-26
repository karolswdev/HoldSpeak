# HoldSpeak TUI Architecture Spec (Stability-First)

This spec describes the target architecture for the HoldSpeak TUI so it is *predictable*, *testable*, and *hard to break* as the UI evolves.
It complements `docs/TUI_INVENTORY.md` (what exists today) with “how it should work”.

## Design Principles (Non‑Negotiables)

1. **Screens own widget trees**
   - Only the Screen that composes a widget should query/update it.
   - The App must not `query_one` into the “current screen” for IDs that may not exist.

2. **Navigation is centralized**
   - Components and Screens do not decide navigation flows (“push this screen”) except for purely local modal UX within that screen.
   - Everything that crosses feature boundaries becomes an **intent** handled by the App.

3. **Persistence is centralized**
   - Components and Screens do not import `holdspeak.db` or write to SQLite directly.
   - They post intents like “update speaker avatar” or “delete meeting”.

4. **Threads never touch the UI**
   - Any background work is run via `run_worker(..., thread=True)` (or async worker) and UI updates happen via `call_from_thread`.

5. **Single source of truth is real**
   - The state model (`AppUIState` / `MeetingUIState`) is authoritative.
   - UI is either fully reactive to state, or state is updated alongside imperative view updates (but never “UI-only” changes).

## Layers

### 1) UI Layer (Screens + Components)

**Responsibilities**
- Render UI and local interaction handling (buttons, inputs, selection).
- Post intent messages upward to request actions.

**Constraints**
- No DB access.
- No meeting/session orchestration.
- Avoid cross-screen widget lookups.
- Minimal business logic: format strings, basic validation, view-level state.

**Modules**
- `holdspeak/tui/screens/*`
- `holdspeak/tui/components/*`

### 2) Orchestration Layer (App + Controller adapters)

**Responsibilities**
- Handle intents, call services, and coordinate navigation.
- Marshal results back to screens safely.
- Own “what happens next” decisions.

**Modules**
- `holdspeak/tui/app.py` (central router)
- `holdspeak/main.py` (controller wires audio/meeting pipelines)

### 3) Domain Services (Pure-ish)

**Responsibilities**
- Encapsulate DB operations and side-effects behind stable APIs.
- Provide “use case” functions that the App can call from workers.

**Recommended structure (future)**
- `holdspeak/tui/services/meetings.py`
- `holdspeak/tui/services/speakers.py`
- `holdspeak/tui/services/export.py`

Services may call:
- `holdspeak/db.py`
- `holdspeak/meeting_session.py`
- `holdspeak/web_server.py`

UI never does.

## Messaging / Intents

### Message taxonomy

- **UI intents** (UI → App): “do something”
  - Example: `SavedMeetingOpenDetail(meeting_id)`
- **Domain events** (App/Controller → UI): “something happened”
  - Example: `MeetingSaved(meeting_id)` (optional)

### Rules

- UI emits intents only; it does not assume success.
- App handles intents and:
  - calls a service in a worker thread,
  - then updates state and/or opens screens in the UI thread.
- Domain events are optional but preferred over direct screen poking when multiple views need updates.

## Navigation Contract

### Screen stack model

- `MainScreen` is the default/root screen and owns `#status/#meter/#history/#meeting_bar/#tab_bar/#footer`.
- `MeetingScreen` (cockpit) is a separate screen pushed on top during recording.
- Feature modals (settings, meeting detail, speaker profile) are pushed on top of whichever screen is active.

### Keybinding ownership

- `MainScreen` owns navigation/search/list actions relevant to the tab UI.
- `MeetingScreen` owns meeting-only actions.
- The App owns no UI bindings besides ultra-global “emergency” actions (ideally none).

## State Model Contract

### Authoritative state

- `HoldSpeakApp.ui_state` is authoritative.
- Any service completion updates `ui_state` first, then drives UI refresh.

### View updates

Two acceptable patterns:

1) **Reactive**: widgets observe state and update themselves.
2) **Imperative but consistent**: App updates state + calls screen methods (e.g. `MainScreen.set_state(...)`).

Current code uses (2); the target is to migrate toward (1) where it reduces glue code.

## Async / Worker Contract

### Worker usage

- All DB operations and filesystem export run in background workers:
  - `run_worker(func, thread=True, exclusive=True, group="...")`
- Screen pushes / toasts / widget updates are done via `call_from_thread`.

### Exclusivity

- Use `exclusive=True` for:
  - meetings list render
  - export operations
  - delete/update operations on the same entity

This prevents overlapping operations from corrupting the UI or causing racey refreshes.

## Canonical Flows (Reference)

### Open saved meeting detail

1. `MeetingRow.ViewRequested` → `SavedMeetingOpenDetail(meeting_id)`
2. App worker loads meeting from DB
3. App pushes `MeetingDetailScreen(meeting)` on UI thread

### Edit saved meeting metadata

1. `SavedMeetingEditMetadata(meeting_id)`
2. App worker loads meeting
3. App sets “metadata context = saved meeting id”
4. App pushes `MeetingMetadataScreen(...)`
5. On save, app updates SQLite and refreshes MeetingsHub list + open detail screen (if present)

### Meeting in progress

- Controller posts meeting updates via App methods; App routes updates to `MainScreen` and `MeetingScreen` (if mounted).
- No component queries widgets across screens.

## Testing Targets (Minimum)

Add integration tests that assert:
- Starting meeting pushes cockpit and does not break tab actions.
- “Play” in Meetings Hub opens MeetingDetail reliably.
- Editing metadata from saved meeting updates DB and refreshes list.
- Background updates don’t crash when a modal is open (screen stack safety).

## Migration Strategy

1. Convert the biggest crash sources first:
   - eliminate App-level widget `query_one` into non-owned trees
   - move bindings to screens
2. Convert persistence touch points:
   - meetings hub, meeting detail, speaker profile → intents
3. Extract services (thin wrappers) to stabilize APIs and simplify tests
4. Optionally migrate view updates to reactive state (reduce glue)

