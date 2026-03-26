# HoldSpeak TUI Inventory (Architecture + Interactions)

This document is an inventory of the current TUI architecture: what exists, who owns what, and how components interact.
It is intentionally “mechanical” so we can improve safely without guessing.

## Goals

- Enumerate the moving parts (modules, screens, components).
- Capture interaction contracts (messages, callbacks, threads).
- Identify brittleness classes (common failure modes) with concrete examples.
- Define a short list of “stabilize first” refactors.

## Current Topology (High-Level)

```
┌──────────────────────────────────────────────────────────────────────┐
│ holdspeak/main.py                                                    │
│  - CLI entry + model preload                                         │
│  - HoldSpeakController: hotkey + meeting session orchestration        │
└───────────────┬──────────────────────────────────────────────────────┘
                │ creates
                ▼
┌──────────────────────────────────────────────────────────────────────┐
│ holdspeak/tui/app.py: HoldSpeakAppWithController                      │
│  - Textual App: compose chrome + tabs + meeting bar + footer           │
│  - Thread-safe UI update helper: call_from_thread                      │
│  - Posts/handles Textual Messages for controller requests               │
└───────┬───────────────────────────────────────────┬──────────────────┘
        │                                            │
        ▼                                            ▼
┌───────────────────────────────┐           ┌───────────────────────────┐
│ Voice typing widgets           │           │ Meeting cockpit screen     │
│  - status/meter/history        │           │  - live transcript + intel │
└───────────────────────────────┘           └───────────────────────────┘
        │                                            │
        ▼                                            ▼
┌───────────────────────────────┐           ┌───────────────────────────┐
│ Meetings hub                  │           │ Persistence + web          │
│  - list/search/filter          │           │  - holdspeak/db.py         │
│  - meeting detail modal        │           │  - holdspeak/web_server.py │
└───────────────────────────────┘           └───────────────────────────┘
```

## Inventory: Modules and Responsibilities

### Entry + Controller

- `holdspeak/main.py`
  - CLI parsing, model preload, app lifecycle.
  - `HoldSpeakController`
    - **Voice typing path**
      - `HotkeyListener` (press/release) → `AudioRecorder` → `Transcriber` → `TextProcessor` → `TextTyper`
      - Updates TUI via `HoldSpeakApp.*` methods (thread-safe wrapper).
    - **Meeting path**
      - `MeetingSession.start()` / `.stop()` / `.save()`
      - Passes callbacks: `on_segment`, `on_mic_level`, `on_system_level`, `on_intel`
      - Updates meeting UI (meeting bar + meeting cockpit screen).

### TUI Root

- `holdspeak/tui/app.py`
  - `HoldSpeakApp` (Textual `App`)
    - Composes:
      - `CrtOverlay` (texture)
      - `MeetingBarWidget`
      - `TabBarWidget`
      - `ContentSwitcher` with `VoiceTypingPane` and `MeetingsHubPane`
      - `FooterHintsWidget`
    - Exposes imperative setters:
      - `set_state`, `set_audio_level`, `add_transcription`
      - `set_meeting_*` and cockpit methods
    - Internal helper `_ui()` wraps `call_from_thread` for thread-safe UI updates.
  - `HoldSpeakAppWithController`
    - Starts/stops `HoldSpeakController`.
    - Handles message types and delegates to controller (see `holdspeak/tui/messages.py`).

### TUI State Model (Currently Underused)

- `holdspeak/tui/state.py`
  - `AppUIState` and `MeetingUIState` exist as “single source of truth”.
  - In practice, UI updates are mostly imperative (`query_one(...).update(...)`), so the state model is only partially authoritative.

### TUI Messages (UI → Controller intents)

- `holdspeak/tui/messages.py`
  - `MeetingToggle`
  - `MeetingBookmark`
  - `MeetingShowTranscript`
  - `MeetingEditMetadata`
  - `MeetingMetadataSaved(title, tags)`
  - `MeetingOpenWeb`

### Components (widgets/panes)

- `holdspeak/tui/components/tab_bar.py`: `TabBarWidget`
  - Renders title + rigid tab buttons + HUD buttons (settings/help).
  - Posts `TabChanged(tab_id)` when `active_tab` changes.
- `holdspeak/tui/components/meeting_bar.py`: `MeetingBarWidget`
  - Slim “REC” bar, duration, levels, URL, segment count.
  - Blinking indicator (reactive tick).
- `holdspeak/tui/components/voice_typing_pane.py`: `VoiceTypingPane`
  - `StatusWidget`, `AudioMeterWidget`, `HotkeyHintWidget`, `HistoryWidget`.
- `holdspeak/tui/components/meetings_hub_pane.py`: `MeetingsHubPane`
  - DB-backed meetings list, search, time filters.
  - Opens `MeetingDetailScreen` for a selected meeting.
- `holdspeak/tui/components/footer.py`: `FooterHintsWidget`
  - Contextual key hints (depends on active tab + meeting_active).
- `holdspeak/tui/components/crt_overlay.py`: `CrtOverlay`
  - Subtle scanline/noise overlay (slow refresh).

### Screens (modals / full-screen)

- `holdspeak/tui/screens/meeting.py`: `MeetingScreen` (cockpit)
  - Live transcript + intel panel, meeting header (duration/levels), meeting-specific keybindings.
- `holdspeak/tui/screens/meeting_detail.py`: `MeetingDetailScreen`
  - Modal screen for viewing a *saved* meeting (overview/actions/speakers/transcript).
- `holdspeak/tui/screens/settings.py`: `SettingsScreen` (modal)
- `holdspeak/tui/screens/transcript.py`: `MeetingTranscriptScreen` (modal)
- `holdspeak/tui/screens/history.py`: `MeetingHistoryScreen` (modal)
- `holdspeak/tui/screens/actions.py`: `ActionItemsScreen` (modal)
- `holdspeak/tui/screens/speaker_profile.py`: speaker profile modal
- `holdspeak/tui/screens/help.py`: help modal

### Persistence / Meeting pipeline

- `holdspeak/meeting.py`: `MeetingRecorder`
  - Dual stream audio capture (mic + system), level callbacks.
  - Detects system-stream failure and falls back to mic-only.
- `holdspeak/meeting_session.py`: `MeetingSession`
  - Transcription loop, segment creation, diarization integration, bookmarks.
  - Saves to SQLite via `holdspeak/db.py` and to JSON for compatibility.
- `holdspeak/db.py`: SQLite persistence + FTS search.
- `holdspeak/db_migration.py`: JSON → SQLite migration (auto-run in some commands).
- `holdspeak/web_server.py`: per-meeting FastAPI dashboard, WS broadcasting.

## Interaction Contracts (Sequences)

### Voice typing sequence

1. Hotkey press → `HoldSpeakController._on_hotkey_press()`
2. UI: `app.set_state("recording")`, `app.set_audio_level(0)`
3. `AudioRecorder.start_recording()` begins PortAudio callback
4. Hotkey release → stop recorder → background thread transcribes
5. UI: `app.set_state("transcribing")`, then `app.add_transcription(text)`

Key contract: `app.*` calls may occur from background threads; must be wrapped by `call_from_thread` (already done via `_ui()`).

### Meeting start/stop sequence

1. UI action `m` → `MeetingToggle` message
2. `HoldSpeakAppWithController.on_meeting_toggle` → controller toggles meeting
3. Meeting start:
   - `MeetingSession.start()` spins up `MeetingRecorder` + transcription loop
   - UI: `set_meeting_active(True)`, `set_meeting_has_system_audio(...)`, open `MeetingScreen`
4. Meeting live:
   - audio callbacks → `set_meeting_mic_level`, `set_meeting_system_level`
   - transcribed segments → `set_meeting_segment_count`, `update_meeting_cockpit_segment`
5. Meeting stop:
   - UI hides cockpit, meeting stops in background thread, then `MeetingSession.save()`

### Meetings hub (browse saved)

1. `MeetingsHubPane.on_mount` calls `_load_meetings()`
2. `_load_meetings()` uses `get_database().list_meetings(...)` or `search_transcripts(...)`
3. UI renders `MeetingRow` entries
4. Click “play/view” opens `MeetingDetailScreen(meeting)` by pushing a modal

## Thread / Event Boundaries (Where Things Go Wrong)

- **PortAudio callback threads**
  - `AudioRecorder` (voice typing) and `MeetingRecorder` (meeting) call into UI update callbacks.
  - Any UI updates must be marshaled to the UI thread.
- **Background transcription threads**
  - Voice typing transcription runs in a `threading.Thread` (controller).
  - Meeting transcription runs in `MeetingSession._transcribe_thread`.
- **Web server thread**
  - `MeetingWebServer` runs uvicorn in its own thread + event loop.

## Brittleness Inventory (Observed Failure Modes)

### 1) “Wrong screen” DOM access (imperative `query_one`)

Pattern:
- App code does `self.query_one("#status", StatusWidget) ...` assuming those widgets exist in the active screen.
- When `MeetingScreen` is on top, those IDs may not exist, causing crashes.

Inventory:
- `holdspeak/tui/app.py`: `set_state`, `set_audio_level`, `add_transcription`, tab switching, etc.

Risk:
- Any global action or background update during a modal / cockpit screen can crash.

### 2) Global bindings executed in inappropriate context

Pattern:
- App-level `BINDINGS` fire regardless of which screen is active.
- Some actions call `query_one(...)` for widgets that don’t exist on the current screen.

Inventory:
- `holdspeak/tui/app.py`: `BINDINGS`, `action_switch_tab`, `action_focus_search`, `action_refresh_meetings`.

### 3) State model not authoritative (drift between `AppUIState` and UI)

Pattern:
- `AppUIState` exists but widgets aren’t driven by it; updates are imperative.

Inventory:
- `holdspeak/tui/state.py` vs direct `.query_one(...).update(...)` in `holdspeak/tui/app.py` and components.

### 4) Composition helpers yielded incorrectly (generator mounted as widget)

Pattern:
- Using `yield helper()` instead of `yield from helper()` when helper returns a generator/ComposeResult.

Example (fixed):
- `holdspeak/tui/screens/meeting_detail.py` was mounting generators.

### 5) “Exception: pass” hides root causes

Pattern:
- Broad exceptions swallowed in UI actions make failures invisible.

Inventory:
- `holdspeak/tui/app.py` (`action_refresh_meetings`, `action_focus_search`)
- some screens/components (search this repo for `except Exception: pass`)

## Stabilize-First Refactor Options (Inventory of Possible Moves)

These are listed in increasing scope.

1. **Cache widget references on mount** (low scope)
   - Store references to `StatusWidget`, `AudioMeterWidget`, etc., and update them directly.
   - Avoid `query_one` from app methods that might run while other screens are active.

2. **Move bindings to screens** (medium scope)
   - Main screen owns tab switching/search/refresh.
   - Meeting screen owns meeting-only keys.
   - App has only quit/help and message routing.

3. **Introduce explicit “MainScreen”** (medium scope)
   - Encapsulate the entire main chrome (tabs + panes + footer) as a screen.
   - Then cockpit and modals don’t share DOM expectations.

4. **Go reactive for real (use `AppUIState`)** (higher scope)
   - Widgets observe state; app updates only state.
   - Reduces “update widget that doesn’t exist” failures by centralizing rendering per-screen.

## Test Inventory (What Exists vs What’s Missing)

- Unit tests: strong coverage (fast, deterministic).
- Integration tests: `tests/integration/test_tui.py` exists but is currently stale (references non-existent symbols like `_clamp01`).

Missing (high value):
- “Screen stack safety” tests (start meeting → cockpit open → press tab keys → no crash).
- “Meetings hub open detail” test (press play/view → modal composes successfully).
- “Background update while modal open” test (simulate `set_state` while `MeetingScreen` on stack).

## Suggested Next Inventory Additions

To keep improving, capture these next:
- A list of **widget IDs** that are assumed globally (`#status`, `#meter`, etc.) and which screens actually contain them.
- A list of **App actions** and which screen should own each.
- A list of **threaded callbacks** and their expected UI thread marshaling behavior.

