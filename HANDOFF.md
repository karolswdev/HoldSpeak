# HoldSpeak - LLM Handoff Document

**Date:** 2026-01-13
**Last Session:** TUI Phase 3 - Tab Navigation & Meetings Hub

---

## Project Overview

**HoldSpeak** is a macOS voice-to-text application with two modes:
1. **Voice Typing** - Hold a hotkey, speak, release -> text appears in any app
2. **Meeting Mode** - Dual-stream recording (mic + system audio) with live transcription and AI intelligence

**Tech Stack:**
- Python 3.13, macOS (Apple Silicon)
- mlx-whisper for transcription
- llama-cpp-python for LLM inference (Metal GPU accelerated)
- Textual for TUI, FastAPI for web dashboard
- rumps for menu bar integration

---

## Just Completed: TUI Phase 3 - Tab Navigation & Meetings Hub

### 3.1 Tab-Based Navigation
Two persistent tabs at the top of the TUI:
- **Voice Typing** (press `1`) - Original voice-to-text interface
- **Meetings** (press `2`) - Browse and manage saved meetings

```
┌─────────────────────────────────────────────────────┐
│ [1 Voice Typing] [2 Meetings]                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  (Tab content here)                                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**New files:**
- `holdspeak/tui/components/tab_bar.py` - TabBarWidget with TabChanged message

### 3.2 Meetings Hub
Compact one-line meeting rows with inline tags:
```
┌─────────────────────────────────────────────────────┐
│ Meetings                          [Search...]       │
├─────────────────────────────────────────────────────┤
│ [All] [This Week] [This Month]         2 meetings   │
├─────────────────────────────────────────────────────┤
│ 01/13 08:17 │ Weekly Standup │ #work   │ 05:32 │ 12seg │ ▶ ✎ ↓ × │
│ 01/12 22:22 │ (Untitled)     │         │ 00:11 │ 0seg  │ ▶ ✎ ↓ × │
└─────────────────────────────────────────────────────┘
```

**Actions per row:**
- `▶` View - Opens Meeting Detail Screen
- `✎` Edit - Opens metadata editor (title/tags)
- `↓` Export - Saves as markdown to ~/Documents
- `×` Delete - Removes meeting from database

**New files:**
- `holdspeak/tui/components/meetings_hub_pane.py` - MeetingsHubPane, MeetingRow

### 3.3 Meeting Detail Screen
Full-screen modal with three tabs:

```
┌─────────────────────────────────────────────────────┐
│              Weekly Standup                         │
│  📅 Monday, January 13, 2026 at 08:17               │
│  ⏱ 05:32  📝 12 segments  #work #standup            │
├─────────────────────────────────────────────────────┤
│ [Overview] [Actions] [Transcript]                   │
├─────────────────────────────────────────────────────┤
│ Summary                                             │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Team discussed Q1 roadmap priorities and...    │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ Topics Discussed                                    │
│ • Q1 Roadmap                                        │
│ • Resource allocation                               │
│                                                     │
│ Action Items                                        │
│ 2 pending, 1 completed                              │
│ ☐ Review budget proposal (@finance)                 │
├─────────────────────────────────────────────────────┤
│              [Close] [Export] [Edit]                │
└─────────────────────────────────────────────────────┘
```

**Tabs:**
- **Overview** - Summary, topics, action items preview
- **Actions** - Full action item list with checkboxes (toggle status)
- **Transcript** - Full transcript with bookmarks

**New files:**
- `holdspeak/tui/screens/meeting_detail.py` - MeetingDetailScreen

### 3.4 Auto-Generated Bookmark Labels
Two-phase intelligent bookmark naming:

**Phase 1: Ad-hoc (during meeting)**
1. Press `b` -> immediate label `"Bookmark @ 05:32"`
2. Background thread gets ±10s context
3. Updates to `"Budget Discussion"` if intel model available

**Phase 2: Post-meeting refinement**
1. Final intel analysis runs when meeting stops
2. All bookmarks re-processed with:
   - Meeting summary for high-level grounding
   - Local ±10s context for specificity
3. Labels refined: `"Budget Discussion"` -> `"Q3 Budget Approval"`

**Modified files:**
- `holdspeak/meeting_session.py` - add_bookmark(), _refine_bookmark_labels()
- `holdspeak/intel.py` - generate_bookmark_label(), generate_bookmark_label_with_context()

---

## Package Structure (Updated)

```
holdspeak/tui/
├── __init__.py
├── __main__.py
├── app.py                   # Main app with tab navigation
├── state.py                 # AppUIState with active_tab
├── messages.py              # MeetingToggle, MeetingOpenWeb, etc.
├── utils.py
├── components/
│   ├── audio_meter.py
│   ├── footer.py            # Tab-aware FooterHintsWidget
│   ├── header.py
│   ├── history.py
│   ├── icon_button.py
│   ├── meeting_bar.py
│   ├── meetings_hub_pane.py # NEW - MeetingsHubPane, MeetingRow
│   ├── status.py
│   ├── tab_bar.py           # NEW - TabBarWidget
│   └── voice_typing_pane.py # NEW - Extracted voice typing content
├── screens/
│   ├── actions.py
│   ├── help.py
│   ├── history.py
│   ├── meeting.py
│   ├── meeting_detail.py    # NEW - MeetingDetailScreen
│   ├── metadata.py
│   ├── settings.py
│   └── transcript.py
└── styles/
    └── app.tcss             # Consolidated with new row/detail styles
```

---

## Key Bindings (Updated)

| Key | Action | Context |
|-----|--------|---------|
| `Tab` | Cycle tabs | Global |
| `1` | Voice Typing tab | Global |
| `2` | Meetings tab | Global |
| `m` | Toggle meeting | Voice tab / Meetings tab |
| `b` | Add bookmark | During meeting |
| `e` | Edit meeting | During meeting |
| `t` | Show transcript | During meeting |
| `w` | Open web UI | During meeting |
| `/` | Focus search | Meetings tab |
| `r` | Refresh list | Meetings tab |
| `c` | Copy last | Voice tab |
| `s` | Settings | Global |
| `?` | Help | Global |
| `q` | Quit | Global |

---

## Database Methods (New)

```python
# Update meeting title and tags
db.update_meeting_metadata(meeting_id, title, tags)

# Update action item status (done/pending/dismissed)
db.update_action_item_status(action_id, status)
```

---

## Running & Testing

```bash
# TUI mode
uv run holdspeak

# Menu bar mode
uv run holdspeak menubar

# Run tests (442 tests)
uv run pytest tests/unit/ -v

# Quick test
uv run pytest tests/unit/ -q
```

---

## Configuration

File: `~/.config/holdspeak/config.json`

```json
{
  "hotkey": {"key": "alt_r", "display": "⌥R"},
  "model": {"name": "base"},
  "meeting": {
    "system_audio_device": null,
    "intel_enabled": true,
    "intel_realtime_model": "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf",
    "web_enabled": true
  }
}
```

---

## Bug Fixes This Session

1. **Meeting toggle not working** - Handler names didn't match message class names after Phase 2 refactoring
2. **UI freeze during meeting** - Audio level callbacks (~100/sec) overwhelming Textual; added throttling (~15 FPS)
3. **Meeting bar not hiding** - `set_meeting_active(False)` called from background thread after blocking stop
4. **Settings crash** - Saved audio device not in available options; added validation
5. **Refresh crash** - `remove_children()` not awaited before mounting new cards; made async

---

## What's Next

From `docs/TUI_ROADMAP.md`:

### Phase 3 Remaining
- Command Palette (`Ctrl+P` or `/` fuzzy search)
- Global Search (across all transcripts)
- Diagnostics Screen (real-time system status)

### Future Ideas
- Meeting templates (recurring meetings with preset tags)
- Export to multiple formats (SRT, JSON, PDF)
- Meeting analytics dashboard
- Keyboard-driven meeting card navigation

---

## User Context

- User is a **Senior Software Architect**
- Prefers parallel development with git worktrees
- Values comprehensive testing
- Uses Opus agents for implementation work
- Working directory: `/Users/karolczajkowski/Tools/HoldSpeak`

---

*Tab-based navigation complete. Meetings Hub with detail view working. Bookmark auto-labeling with two-phase refinement.*
