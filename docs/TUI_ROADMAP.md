# HoldSpeak TUI Improvement Roadmap

> **Purpose:** Self-contained starter kit for implementing world-class TUI improvements.
> **Generated:** 2025-01-12 by GPT-5.2 (Codex), polished for agent execution.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Overview](#current-architecture-overview)
3. [Phase 1: Quick Wins](#phase-1-quick-wins-immediate)
4. [Phase 2: Structural Improvements](#phase-2-structural-improvements-medium-term)
5. [Phase 3: Product Vision](#phase-3-product-vision-long-term)
6. [File Structure Proposal](#file-structure-proposal)
7. [Testing Requirements](#testing-requirements)
8. [Appendix: Data Flow Reference](#appendix-data-flow-reference)

---

## Executive Summary

The HoldSpeak TUI is functional but lacks the polish of the web dashboard. Key gaps:

| Area | Current State | Target State |
|------|---------------|--------------|
| Discoverability | Footer shows 4 of 9 keybindings | All bindings visible, contextual |
| Onboarding | Empty list, no guidance | First-run hints, empty states |
| Keyboard Safety | Selection triggers actions | Explicit activation required |
| Architecture | Single 1200-line file | Modular package structure |
| Design System | Inline CSS, no tokens | External `.tcss`, reusable tokens |
| Meeting Experience | Basic bar + modal | Full cockpit with live transcript |

**Effort Estimate:** ~40-60 hours total across all phases.

---

## Current Architecture Overview

### Key Files

| File | Lines | Purpose |
|------|-------|---------|
| `holdspeak/tui.py` | ~1200 | All widgets, screens, CSS, app |
| `holdspeak/main.py` | ~420 | Controller, app lifecycle |
| `holdspeak/meeting_session.py` | ~600 | Meeting state, recording, intel |
| `holdspeak/web_server.py` | ~400 | FastAPI server, WebSocket |
| `holdspeak/static/dashboard.html` | ~1000 | Web UI (reference for patterns) |

### Current Widget Hierarchy

```
HoldSpeakApp
├── Container#chrome
│   ├── Horizontal#header
│   │   ├── Label#title ("HoldSpeak")
│   │   └── Horizontal#header_icons
│   │       ├── IconButton#settings_icon (⚙)
│   │       └── IconButton#help_icon (?)
│   ├── Horizontal#status_bar
│   │   ├── StatusWidget#status
│   │   ├── AudioMeterWidget#audio_meter
│   │   └── Label#hotkey_hint
│   ├── MeetingBarWidget#meeting_bar (conditional)
│   ├── HistoryWidget#history
│   └── FooterHintsWidget#footer
└── Modal Screens (pushed on demand)
    ├── SettingsScreen
    ├── MeetingTranscriptScreen
    ├── MeetingHistoryScreen
    ├── ActionItemsScreen
    └── MeetingMetadataScreen
```

### Current Keybindings (from `HoldSpeakApp.BINDINGS`)

```python
BINDINGS = [
    ("q", "quit", "Quit"),
    ("s", "settings", "Settings"),
    ("c", "copy_last", "Copy last"),
    ("m", "toggle_meeting", "Toggle meeting"),
    ("b", "add_bookmark", "Add bookmark"),
    ("t", "show_transcript", "Show transcript"),
    ("e", "edit_meeting", "Edit meeting"),
    ("h", "show_history", "History"),
    ("a", "show_actions", "Actions"),
]
```

---

## Phase 1: Quick Wins (Immediate)

### 1.1 Fix Footer Hints to Reflect All Keybindings

**Priority:** P0
**File:** `holdspeak/tui.py`
**Location:** `FooterHintsWidget.render()` (line ~270)

**Problem:** Footer only shows `Record | m Meeting | s Settings | q Quit`, hiding 5 bindings.

**Current Code:**
```python
def render(self) -> Text:
    meeting_hint = "m Stop meeting" if self.meeting_active else "m Meeting"
    meeting_extras = "  │  b Bookmark  │  e Edit" if self.meeting_active else ""
    return Text(
        f"{self.hotkey_display} Record   "
        f"│  {meeting_hint}{meeting_extras}  "
        f"│  s Settings  "
        f"│  q Quit"
    )
```

**Target Code:**
```python
def render(self) -> Text:
    parts = [f"{self.hotkey_display} Record"]

    if self.meeting_active:
        parts.extend([
            "m Stop",
            "b Bookmark",
            "e Edit",
            "t Transcript",
        ])
    else:
        parts.extend([
            "m Meeting",
            "h History",
            "a Actions",
        ])

    parts.extend(["c Copy", "s Settings", "q Quit"])

    return Text("  │  ".join(parts))
```

**Acceptance Criteria:**
- [ ] All 9 bindings visible (contextually)
- [ ] Meeting-active shows: m/b/e/t
- [ ] Meeting-inactive shows: m/h/a
- [ ] Always shows: Record/c/s/q

---

### 1.2 Prevent Accidental Actions on Selection

**Priority:** P0
**Files:** `holdspeak/tui.py`
**Locations:**
- `HistoryWidget.on_list_view_selected()` (line ~185)
- `ActionItemsScreen.on_list_view_selected()` (line ~540)

**Problem:** Keyboard navigation triggers copy/toggle immediately.

**Current Code (HistoryWidget):**
```python
def on_list_view_selected(self, event: ListView.Selected) -> None:
    """Copy selected item to clipboard."""
    if event.item:
        label = event.item.query_one(Label)
        text = str(label.renderable)
        self.post_message(self.ItemCopied(text))
```

**Target Code:**
```python
def on_list_view_selected(self, event: ListView.Selected) -> None:
    """Highlight selected item (don't copy yet)."""
    pass  # Selection is visual only

def on_key(self, event: events.Key) -> None:
    """Copy on Enter/Space."""
    if event.key in ("enter", "space"):
        selected = self.query_one(ListView).highlighted_child
        if selected:
            label = selected.query_one(Label)
            text = str(label.renderable)
            self.post_message(self.ItemCopied(text))
            event.prevent_default()
```

**Acceptance Criteria:**
- [ ] Arrow keys navigate without side effects
- [ ] Enter/Space triggers action
- [ ] Mouse click still works (explicit intent)
- [ ] Same pattern in ActionItemsScreen

---

### 1.3 Add Empty States and First-Run Guidance

**Priority:** P0
**File:** `holdspeak/tui.py`
**Location:** `HistoryWidget` (line ~155)

**Problem:** Empty list shows nothing; users don't know what to do.

**Implementation:**

Add reactive property and empty state widget:

```python
class HistoryWidget(Static):
    """Shows transcription history with empty state."""

    is_empty: reactive[bool] = reactive(True)

    def compose(self) -> ComposeResult:
        with Container(id="history_container"):
            yield Static(
                "[dim]Hold [bold]⌥R[/bold] to record, release to transcribe.\n\n"
                "Press [bold]m[/bold] to start meeting mode.\n"
                "Press [bold]s[/bold] for settings.[/dim]",
                id="empty_state",
            )
            yield ListView(id="history_list")

    def watch_is_empty(self, empty: bool) -> None:
        self.query_one("#empty_state").display = empty
        self.query_one("#history_list").display = not empty

    def add_item(self, text: str) -> None:
        self.is_empty = False
        # ... existing add logic
```

**CSS Addition:**
```css
#empty_state {
    padding: 2 4;
    text-align: center;
    color: $muted;
}
```

**Acceptance Criteria:**
- [ ] Empty state visible on fresh start
- [ ] Disappears after first transcription
- [ ] Shows relevant hotkey hints
- [ ] Styled consistently with app theme

---

### 1.4 Show Bookmarks in Transcript Modal

**Priority:** P0
**File:** `holdspeak/tui.py`
**Location:** `MeetingTranscriptScreen` (line ~410)

**Problem:** Bookmarks exist in data but aren't shown in transcript view.

**Current:** Only shows segments.

**Target:** Interleave bookmarks with segments, visually distinct.

**Implementation:**

```python
class MeetingTranscriptScreen(ModalScreen[None]):
    def __init__(
        self,
        segments: list[TranscriptSegment],
        bookmarks: list[Bookmark] = None,  # ADD THIS
    ) -> None:
        super().__init__()
        self._segments = segments
        self._bookmarks = bookmarks or []

    def compose(self) -> ComposeResult:
        # Merge and sort by timestamp
        entries = []
        for seg in self._segments:
            entries.append(("segment", seg.start_time, seg))
        for bm in self._bookmarks:
            entries.append(("bookmark", bm.timestamp, bm))
        entries.sort(key=lambda x: x[1])

        with Container(id="transcript_dialog"):
            yield Label("Meeting Transcript", id="transcript_title")
            with VerticalScroll(id="transcript_scroll"):
                for kind, ts, item in entries:
                    if kind == "bookmark":
                        yield Static(
                            f"[bold yellow]🔖 {item.label or 'Bookmark'}[/] "
                            f"[dim]@ {self._format_time(ts)}[/dim]",
                            classes="bookmark_marker",
                        )
                    else:
                        yield Static(
                            f"[bold]{item.speaker}[/bold] "
                            f"[dim]{item.format_timestamp()}[/dim]\n"
                            f"{item.text}",
                            classes="transcript_segment",
                        )
            # ... buttons
```

**Update caller in main.py:**
```python
def show_meeting_transcript(self) -> None:
    segments = self._meeting_session.get_transcript()
    bookmarks = self._meeting_session.get_bookmarks()  # ADD THIS
    self.app.show_meeting_transcript(segments, bookmarks)
```

**Acceptance Criteria:**
- [ ] Bookmarks appear inline with segments
- [ ] Visually distinct (yellow, icon)
- [ ] Sorted by timestamp
- [ ] Shows bookmark label

---

### 1.5 Unify Clipboard Handling

**Priority:** P0
**File:** `holdspeak/tui.py`
**Locations:**
- `HoldSpeakApp._copy_to_clipboard()` (line ~780)
- `MeetingTranscriptScreen._copy_all()` (line ~460)

**Problem:** Two different clipboard implementations.

**Solution:** Route all clipboard operations through `HoldSpeakApp._copy_to_clipboard()`.

**Current (MeetingTranscriptScreen):**
```python
def _copy_all(self) -> None:
    text = "\n\n".join(str(s) for s in self._segments)
    pyperclip.copy(text)  # Direct call
    self.app.notify("Copied transcript", timeout=1.5)
```

**Target:**
```python
def _copy_all(self) -> None:
    text = "\n\n".join(str(s) for s in self._segments)
    # Use app's unified method
    if hasattr(self.app, '_copy_to_clipboard'):
        self.app._copy_to_clipboard(text)
    self.app.notify("Copied transcript", timeout=1.5)
```

**Better: Add public method to app:**
```python
# In HoldSpeakApp
def copy_to_clipboard(self, text: str) -> bool:
    """Copy text to clipboard. Returns success."""
    return self._copy_to_clipboard(text)
```

**Acceptance Criteria:**
- [ ] Single clipboard method used everywhere
- [ ] Consistent error handling
- [ ] Works on all platforms (pyperclip + pbcopy fallback)

---

### 1.6 Add Escape-to-Close for All Modals

**Priority:** P0
**File:** `holdspeak/tui.py`
**Locations:** All `ModalScreen` subclasses

**Problem:** Some modals close on Escape, some don't.

**Solution:** Add consistent binding to all modal screens.

```python
class SettingsScreen(ModalScreen[None]):
    BINDINGS = [("escape", "cancel", "Close")]

    def action_cancel(self) -> None:
        self.app.pop_screen()
```

**Apply to:**
- [ ] `SettingsScreen`
- [ ] `MeetingTranscriptScreen`
- [ ] `MeetingHistoryScreen`
- [ ] `ActionItemsScreen`
- [ ] `MeetingMetadataScreen`

**Acceptance Criteria:**
- [ ] Escape closes all modals
- [ ] No unsaved data loss (prompt if needed)
- [ ] Focus returns to previous element

---

## Phase 2: Structural Improvements (Medium-term)

### 2.1 Extract TUI to Package Structure

**Priority:** P1
**Current:** Single `holdspeak/tui.py` (~1200 lines)

**Target Structure:**
```
holdspeak/tui/
├── __init__.py          # Exports HoldSpeakApp
├── app.py               # Main app class, bindings, actions
├── controller.py        # HoldSpeakController (move from main.py)
├── components/
│   ├── __init__.py
│   ├── status.py        # StatusWidget
│   ├── audio_meter.py   # AudioMeterWidget
│   ├── history.py       # HistoryWidget
│   ├── meeting_bar.py   # MeetingBarWidget
│   ├── footer.py        # FooterHintsWidget
│   └── icon_button.py   # IconButton
├── screens/
│   ├── __init__.py
│   ├── settings.py      # SettingsScreen
│   ├── transcript.py    # MeetingTranscriptScreen
│   ├── history.py       # MeetingHistoryScreen
│   ├── actions.py       # ActionItemsScreen
│   ├── metadata.py      # MeetingMetadataScreen
│   └── help.py          # HelpScreen (NEW)
├── styles/
│   ├── tokens.tcss      # Color/spacing tokens
│   ├── components.tcss  # Widget styles
│   └── screens.tcss     # Modal styles
└── messages.py          # All Message classes
```

**Migration Steps:**
1. Create package structure
2. Extract `messages.py` first (no dependencies)
3. Extract components one by one
4. Extract screens
5. Move CSS to `.tcss` files
6. Update imports in `main.py`
7. Update tests

**Acceptance Criteria:**
- [ ] No single file > 300 lines
- [ ] All imports work
- [ ] Tests pass
- [ ] CSS loads from `.tcss`

---

### 2.2 Define Design Token System

**Priority:** P1
**File:** `holdspeak/tui/styles/tokens.tcss`

**Current:** Hardcoded colors throughout inline CSS.

**Target Token System:**
```css
/* tokens.tcss */
$bg-base: #0b0f14;
$bg-surface: #0f172a;
$bg-elevated: #1e293b;

$text-primary: #e5e7eb;
$text-secondary: #9ca3af;
$text-muted: #6b7280;

$accent-primary: #a78bfa;    /* violet */
$accent-secondary: #818cf8;  /* indigo */

$status-success: #34d399;    /* emerald */
$status-warning: #fbbf24;    /* amber */
$status-error: #f87171;      /* red */
$status-info: #60a5fa;       /* blue */

$border-subtle: #1f2937;
$border-default: #374151;

$spacing-xs: 1;
$spacing-sm: 2;
$spacing-md: 3;
$spacing-lg: 4;

/* Component tokens */
$meeting-bar-bg: $bg-elevated;
$meeting-bar-active: #7c3aed;  /* violet-600 */
$audio-meter-fill: $accent-primary;
$audio-meter-empty: $border-subtle;
```

**Usage Example:**
```css
/* components.tcss */
StatusWidget {
    background: $bg-surface;
    color: $text-primary;
    padding: 0 $spacing-sm;
}

StatusWidget.recording .status_dot {
    background: $status-error;
}
```

**Acceptance Criteria:**
- [ ] All colors use tokens
- [ ] Consistent spacing scale
- [ ] Easy to create themes
- [ ] High-contrast variant possible

---

### 2.3 Create Dedicated Meeting Screen

**Priority:** P1
**File:** `holdspeak/tui/screens/meeting.py` (NEW)

**Problem:** Meeting mode is just a bar + modal. No live experience.

**Target: Full Meeting Cockpit**

```
┌─────────────────────────────────────────────────────────────┐
│ ● MEETING  "Weekly Standup"  05:23  │  12 segments  │  🌐   │
├─────────────────────────────────────────────────────────────┤
│ ┌─── Live Transcript ──────────────────┐ ┌─── Intel ──────┐ │
│ │ [00:15] Me: Let's discuss the Q1...  │ │ Topics:        │ │
│ │ [00:32] Remote: I think we should... │ │ • Q1 Planning  │ │
│ │ 🔖 Decision point                    │ │ • Auth System  │ │
│ │ [01:45] Me: Agreed, let's go with... │ │                │ │
│ │ [02:10] Remote: I'll draft the...    │ │ Action Items:  │ │
│ │                                      │ │ ☐ Draft OAuth  │ │
│ │                                      │ │ ☐ Schedule mtg │ │
│ │                                      │ │                │ │
│ │                                      │ │ Summary:       │ │
│ │                                      │ │ Team discussed │ │
│ └──────────────────────────────────────┘ └────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│ b Bookmark  e Edit  c Copy  m Stop  │  Escape to minimize  │
└─────────────────────────────────────────────────────────────┘
```

**Implementation Sketch:**
```python
class MeetingScreen(Screen):
    """Full meeting cockpit with live updates."""

    BINDINGS = [
        ("b", "bookmark", "Bookmark"),
        ("e", "edit", "Edit"),
        ("c", "copy", "Copy"),
        ("m", "stop", "Stop"),
        ("escape", "minimize", "Minimize"),
    ]

    def compose(self) -> ComposeResult:
        yield MeetingBarWidget(id="meeting_bar")
        with Horizontal(id="meeting_content"):
            with Container(id="transcript_panel"):
                yield Label("Live Transcript", classes="panel_title")
                yield VerticalScroll(id="live_transcript")
            with Container(id="intel_panel"):
                yield Label("Intelligence", classes="panel_title")
                yield IntelWidget(id="intel")
        yield FooterHintsWidget(id="footer")

    def on_mount(self) -> None:
        # Subscribe to meeting updates
        self.set_interval(0.5, self._refresh)

    def _refresh(self) -> None:
        # Update from meeting session
        pass
```

**Acceptance Criteria:**
- [ ] Live transcript updates in real-time
- [ ] Bookmarks appear inline
- [ ] Intel panel shows topics/actions/summary
- [ ] Keyboard shortcuts work
- [ ] Escape minimizes to bar (returns to main)

---

### 2.4 Create Help Screen

**Priority:** P1
**File:** `holdspeak/tui/screens/help.py` (NEW)

**Problem:** `?` icon shows brief toast. Users need real documentation.

**Implementation:**
```python
class HelpScreen(ModalScreen[None]):
    """Comprehensive help and documentation."""

    BINDINGS = [("escape", "close", "Close")]

    def compose(self) -> ComposeResult:
        with Container(id="help_dialog"):
            yield Label("HoldSpeak Help", id="help_title")
            with TabbedContent():
                with TabPane("Keybindings", id="keys_tab"):
                    yield Static(self._keybindings_content())
                with TabPane("Meeting Mode", id="meeting_tab"):
                    yield Static(self._meeting_content())
                with TabPane("Setup", id="setup_tab"):
                    yield Static(self._setup_content())
                with TabPane("Troubleshooting", id="trouble_tab"):
                    yield Static(self._troubleshooting_content())
            with Horizontal(id="help_actions"):
                yield Button("Close", id="help_close")
                yield Button("Open Logs", id="help_logs")

    def _keybindings_content(self) -> str:
        return """
[bold]Global Hotkey[/]
  ⌥R (Option+R)  Hold to record, release to transcribe

[bold]Navigation[/]
  m   Toggle meeting mode
  s   Open settings
  h   Meeting history
  a   Action items
  q   Quit

[bold]During Meeting[/]
  b   Add bookmark
  e   Edit title/tags
  t   View transcript
  c   Copy last segment
"""

    def _meeting_content(self) -> str:
        return """
[bold]Meeting Mode[/]

Captures both your microphone and system audio
(remote participants) for full meeting transcription.

[bold]Requirements:[/]
• BlackHole audio driver installed
• Multi-Output Device configured in Audio MIDI Setup

[bold]Features:[/]
• Live transcription with speaker labels
• Bookmarks for important moments
• AI-generated topics, action items, summary
• Web dashboard for remote viewing
"""
```

**Acceptance Criteria:**
- [ ] Tabbed interface for organization
- [ ] All keybindings documented
- [ ] Meeting mode explained
- [ ] Setup instructions included
- [ ] "Open Logs" button works

---

### 2.5 Introduce AppState for Unified State Management

**Priority:** P1
**File:** `holdspeak/tui/state.py` (NEW)

**Problem:** State scattered across widgets; hard to reason about.

**Solution:** Central state container with reactive updates.

```python
from dataclasses import dataclass, field
from typing import Optional
from textual.reactive import reactive

@dataclass
class MeetingUIState:
    """Meeting-specific UI state."""
    active: bool = False
    duration: str = "00:00"
    segment_count: int = 0
    has_system_audio: bool = False
    mic_level: float = 0.0
    system_level: float = 0.0
    title: str = ""
    tags: list[str] = field(default_factory=list)
    web_url: str = ""

@dataclass
class AppUIState:
    """Complete app UI state."""
    mode: str = "voice_typing"  # voice_typing | meeting
    status: str = "idle"  # idle | recording | transcribing | loading | error
    hotkey_display: str = "⌥R"
    audio_level: float = 0.0
    meeting: MeetingUIState = field(default_factory=MeetingUIState)
    error_message: Optional[str] = None
```

**Usage in App:**
```python
class HoldSpeakApp(App):
    state: reactive[AppUIState] = reactive(AppUIState())

    def watch_state(self, old: AppUIState, new: AppUIState) -> None:
        """React to state changes."""
        # Update all dependent widgets
        self.query_one(StatusWidget).status = new.status
        self.query_one(AudioMeterWidget).level = new.audio_level
        self.query_one(MeetingBarWidget).active = new.meeting.active
        # etc.
```

**Acceptance Criteria:**
- [ ] Single source of truth
- [ ] Reactive updates to all widgets
- [ ] Easy to serialize for debugging
- [ ] Type-safe

---

## Phase 3: Product Vision (Long-term)

### 3.1 Command Palette

**Priority:** P2

Add `Ctrl+P` or `/` to open command palette with fuzzy search.

```
┌─────────────────────────────────────┐
│ > start meeting                     │
├─────────────────────────────────────┤
│ ▸ Start Meeting Mode          m     │
│   Stop Meeting Mode           m     │
│   View Transcript             t     │
│   Browse History              h     │
│   Manage Action Items         a     │
│   Open Settings               s     │
└─────────────────────────────────────┘
```

### 3.2 Global Search

**Priority:** P2

Search across all transcripts and meetings.

```
┌─────────────────────────────────────┐
│ 🔍 oauth implementation             │
├─────────────────────────────────────┤
│ Meeting: Q1 Planning (Jan 12)       │
│   "...decided on OAuth 2.0..."      │
│                                     │
│ Meeting: Auth Review (Jan 10)       │
│   "...OAuth vs JWT discussion..."   │
└─────────────────────────────────────┘
```

### 3.3 Diagnostics Screen

**Priority:** P2

Real-time system status for troubleshooting.

```
┌─────────────────────────────────────────────────┐
│ Diagnostics                                     │
├─────────────────────────────────────────────────┤
│ Audio Devices                                   │
│   Mic: MacBook Pro Microphone ✓                 │
│   System: BlackHole 2ch ✓                       │
│                                                 │
│ Models                                          │
│   Whisper: base.en (loaded) ✓                   │
│   Intel: Mistral-7B (loaded) ✓                  │
│                                                 │
│ Web Dashboard                                   │
│   URL: http://localhost:8765 ✓                  │
│   Clients: 1 connected                          │
│                                                 │
│ Performance                                     │
│   Last transcription: 0.8s                      │
│   Last intel analysis: 2.3s                     │
│                                                 │
│ [View Logs]  [Copy Debug Info]  [Close]         │
└─────────────────────────────────────────────────┘
```

### 3.4 Unified TUI/Web Design Language

**Priority:** P2

Ensure TUI and web dashboard share:
- Same terminology (segments, bookmarks, intel)
- Same status indicators
- Same color meanings
- Same keyboard shortcuts where possible

---

## File Structure Proposal

After all phases, the codebase should look like:

```
holdspeak/
├── __init__.py
├── main.py                    # CLI entry, minimal
├── config.py
├── db.py
├── intel.py
├── meeting.py
├── meeting_session.py
├── transcribe.py
├── web_server.py
├── tui/
│   ├── __init__.py            # from .app import HoldSpeakApp
│   ├── app.py                 # ~300 lines
│   ├── controller.py          # ~200 lines
│   ├── state.py               # ~50 lines
│   ├── messages.py            # ~50 lines
│   ├── components/
│   │   ├── __init__.py
│   │   ├── status.py          # ~40 lines
│   │   ├── audio_meter.py     # ~50 lines
│   │   ├── history.py         # ~80 lines
│   │   ├── meeting_bar.py     # ~100 lines
│   │   ├── footer.py          # ~40 lines
│   │   ├── intel.py           # ~60 lines (NEW)
│   │   └── icon_button.py     # ~30 lines
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── settings.py        # ~150 lines
│   │   ├── transcript.py      # ~100 lines
│   │   ├── history.py         # ~120 lines
│   │   ├── actions.py         # ~100 lines
│   │   ├── metadata.py        # ~80 lines
│   │   ├── help.py            # ~150 lines (NEW)
│   │   ├── meeting.py         # ~200 lines (NEW)
│   │   └── diagnostics.py     # ~150 lines (NEW, P2)
│   └── styles/
│       ├── tokens.tcss        # ~50 lines
│       ├── components.tcss    # ~150 lines
│       └── screens.tcss       # ~200 lines
└── static/
    ├── dashboard.html
    └── history.html
```

---

## Testing Requirements

### Unit Tests (for each component)

```python
# tests/unit/tui/test_footer.py
class TestFooterHintsWidget:
    def test_shows_all_bindings_when_idle(self):
        """Footer shows m/h/a when no meeting active."""

    def test_shows_meeting_bindings_when_active(self):
        """Footer shows m/b/e/t when meeting active."""

    def test_updates_on_meeting_state_change(self):
        """Footer updates reactively."""
```

### Integration Tests

```python
# tests/integration/test_tui_flows.py
class TestMeetingFlow:
    async def test_start_meeting_shows_bar(self):
        """Pressing m shows meeting bar."""

    async def test_edit_metadata_saves(self):
        """e -> edit -> save updates state."""

    async def test_bookmark_appears_in_transcript(self):
        """b -> bookmark -> t shows bookmark."""
```

### Acceptance Tests

```python
# tests/e2e/test_tui_experience.py
class TestFirstRunExperience:
    async def test_empty_state_shows_guidance(self):
        """New user sees helpful hints."""

    async def test_keyboard_navigation_safe(self):
        """Arrow keys don't trigger actions."""
```

---

## Appendix: Data Flow Reference

### Voice Typing Flow
```
HotkeyListener.on_press()
    → HoldSpeakController._on_hotkey_press()
        → AudioRecorder.start()
        → App.set_state("recording")

HotkeyListener.on_release()
    → HoldSpeakController._on_hotkey_release()
        → AudioRecorder.stop() → audio_data
        → App.set_state("transcribing")
        → Transcriber.transcribe(audio_data) → text
        → TextTyper.type(text)
        → App.add_transcription(text)
        → App.set_state("idle")
```

### Meeting Flow
```
App.action_toggle_meeting()
    → post_message(MeetingToggle)

Controller.on_meeting_toggle()
    → MeetingSession.start()
        → MeetingRecorder.start()
        → MeetingWebServer.start() → url
        → App.set_meeting_active(True)
        → App.set_meeting_web_url(url)

MeetingSession._transcribe_loop()
    → Transcriber.transcribe() → segment
    → App.set_meeting_segment_count(n)
    → WebServer.broadcast("segment", segment)

MeetingSession._intel_analysis()
    → MeetingIntel.analyze(stream=True)
        → yield token → WebServer.broadcast("intel_token", token)
        → yield result → WebServer.broadcast("intel_complete", result)
```

### Message Flow (TUI)
```
User presses 'e'
    → App.action_edit_meeting()
        → post_message(MeetingEditMetadata)

Controller.on_meeting_edit_metadata()
    → App.show_meeting_metadata(title, tags)
        → push_screen(MeetingMetadataScreen)

User clicks Save
    → MeetingMetadataScreen.on_button_pressed()
        → post_message(Saved(title, tags))
        → App.pop_screen()

App.on_meeting_metadata_screen_saved()
    → post_message(MeetingMetadataSaved)

Controller.on_meeting_metadata_saved()
    → MeetingSession.set_title(title)
    → MeetingSession.set_tags(tags)
    → App.set_meeting_title(title)
```

---

## Implementation Checklist

### Phase 1 (Target: 1-2 days)
- [ ] 1.1 Fix footer hints
- [ ] 1.2 Safe keyboard navigation
- [ ] 1.3 Empty states
- [ ] 1.4 Bookmarks in transcript
- [ ] 1.5 Unified clipboard
- [ ] 1.6 Escape-to-close

### Phase 2 (Target: 1-2 weeks)
- [ ] 2.1 Package structure
- [ ] 2.2 Design tokens
- [ ] 2.3 Meeting screen
- [ ] 2.4 Help screen
- [ ] 2.5 AppState

### Phase 3 (Target: Future)
- [ ] 3.1 Command palette
- [ ] 3.2 Global search
- [ ] 3.3 Diagnostics
- [ ] 3.4 Design unification

---

*This roadmap is designed to be executed incrementally. Each item is self-contained with clear acceptance criteria. Start with Phase 1 for immediate impact.*
