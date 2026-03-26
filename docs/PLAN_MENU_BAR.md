# Initiative: Menu Bar Mode

**Goal:** Transform HoldSpeak from terminal-bound to always-available via macOS menu bar integration.

**Branch:** `feature/menu-bar`

---

## Overview

Currently HoldSpeak requires a terminal window to be open. Menu bar mode will:
- Run as a background service
- Show status in the macOS menu bar
- Provide quick access to all features
- Make HoldSpeak a true "always on" assistant

---

## Architecture Decision

### Recommended: rumps + Existing Core

```
┌─────────────────────────────────────────────────────────┐
│                    Menu Bar App (rumps)                  │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Status Icon: ● Recording / ○ Idle / ◐ Processing│    │
│  └─────────────────────────────────────────────────┘    │
│                          │                               │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │  Menu Items                                        │  │
│  │  ├─ Status: Idle                                   │  │
│  │  ├─ ─────────────────                              │  │
│  │  ├─ Start Recording (⌥R)                           │  │
│  │  ├─ Recent ▶ [last 5 transcriptions]               │  │
│  │  ├─ ─────────────────                              │  │
│  │  ├─ Meeting Mode ▶                                 │  │
│  │  │   ├─ Start Meeting                              │  │
│  │  │   ├─ Open Dashboard                             │  │
│  │  │   └─ Stop Meeting                               │  │
│  │  ├─ ─────────────────                              │  │
│  │  ├─ Settings...                                    │  │
│  │  ├─ Open TUI                                       │  │
│  │  └─ Quit                                           │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              HoldSpeak Core (existing)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │  Hotkey  │  │  Audio   │  │  Transcriber         │   │
│  │ Listener │  │ Recorder │  │  (mlx-whisper)       │   │
│  └──────────┘  └──────────┘  └──────────────────────┘   │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Meeting Session (optional)                       │   │
│  │  ├─ Dual-stream recording                         │   │
│  │  ├─ Web server                                    │   │
│  │  └─ Intel extraction                              │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Why rumps?

| Option | Effort | Native Feel | Maintenance |
|--------|--------|-------------|-------------|
| **rumps** | Low | Good enough | Simple |
| PyObjC | High | Excellent | Complex |
| Tauri | Very High | Excellent | Heavy deps |

rumps gives us 80% of the UX with 20% of the effort. Can upgrade later if needed.

---

## Implementation Plan

### Phase 1: Core Menu Bar Shell

**File:** `holdspeak/menubar.py`

```python
import rumps
from holdspeak.config import Config
from holdspeak.hotkey import HotkeyListener
from holdspeak.audio import AudioRecorder
from holdspeak.transcribe import Transcriber

class HoldSpeakMenuBar(rumps.App):
    def __init__(self):
        super().__init__("HoldSpeak", icon="mic_idle.png")
        self.config = Config.load()
        self.transcriber = Transcriber(model_name=self.config.model.name)
        # ... setup hotkey listener, etc.

    @rumps.clicked("Start Recording")
    def start_recording(self, _):
        # Manual trigger (hotkey still works too)
        pass

    @rumps.clicked("Settings...")
    def open_settings(self, _):
        # Could open TUI settings or a native dialog
        pass
```

**Tasks:**
- [ ] Create `menubar.py` with basic rumps app
- [ ] Wire up existing hotkey listener
- [ ] Wire up audio recorder + transcriber
- [ ] Status icon changes (idle/recording/processing)
- [ ] Basic menu structure

### Phase 2: Transcription Output

**Decision needed:** Where does output go?

Options:
1. **Clipboard only** (current behavior) - simplest
2. **Notification + clipboard** - user sees result
3. **Recent menu** - access last N transcriptions
4. **All of the above** - configurable

**Tasks:**
- [ ] Add macOS notification on transcription complete
- [ ] Implement "Recent" submenu with last 5-10 transcriptions
- [ ] Click to copy from Recent menu
- [ ] Add output preference to config

### Phase 3: Meeting Mode Integration

**Tasks:**
- [ ] "Meeting Mode" submenu
- [ ] Start/Stop meeting from menu
- [ ] "Open Dashboard" launches browser
- [ ] Status shows when meeting active
- [ ] Meeting duration in menu

### Phase 4: Settings & Polish

**Tasks:**
- [ ] Settings dialog (or launch TUI settings)
- [ ] "Open TUI" option for power users
- [ ] Launch at login option
- [ ] Proper app icon set (multiple sizes)
- [ ] Handle permissions gracefully

---

## CLI Changes

```bash
# New default - menu bar mode
holdspeak

# Explicit modes
holdspeak --menubar    # Menu bar (same as default)
holdspeak --tui        # Full TUI mode
holdspeak meeting      # Meeting CLI (unchanged)
```

Or keep TUI as default for now, add menubar explicitly:
```bash
holdspeak              # TUI (current default)
holdspeak --menubar    # Menu bar mode
holdspeak menubar      # Alternative syntax
```

**Decision:** Start with `holdspeak menubar` as explicit command, graduate to default later.

---

## Dependencies

```toml
[project.optional-dependencies]
menubar = ["rumps>=0.4.0"]
```

Install: `uv pip install -e ".[menubar]"`

---

## Config Additions

```python
@dataclass
class MenuBarConfig:
    enabled: bool = True
    show_notifications: bool = True
    recent_count: int = 5
    launch_at_login: bool = False
```

---

## File Structure

```
holdspeak/
├── menubar.py          # NEW - Menu bar app
├── resources/          # NEW - Icons and assets
│   ├── icon_idle.png
│   ├── icon_recording.png
│   ├── icon_processing.png
│   └── icon_meeting.png
├── main.py             # Add menubar entry point
└── ...
```

---

## Testing Strategy

1. **Manual testing** - Menu bar apps are hard to unit test
2. **Core logic tests** - Ensure hotkey/audio/transcribe still work
3. **Integration test** - Script that launches menubar, triggers recording, verifies output

---

## Success Criteria

- [ ] Can launch HoldSpeak without terminal window
- [ ] Hotkey recording works from menu bar
- [ ] Status icon reflects current state
- [ ] Recent transcriptions accessible
- [ ] Meeting mode accessible from menu
- [ ] Clean quit without orphan processes

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| rumps limitations | Start simple, can rewrite in PyObjC if needed |
| Hotkey conflicts | Same as TUI - user configurable |
| Memory usage | Lazy load models, unload after idle |
| Permissions | Guide user through accessibility/mic permissions |

---

## Quick Start for Implementation

```bash
# Create branch
git checkout -b feature/menu-bar

# Install rumps
uv pip install rumps

# Start with basic shell
cat > holdspeak/menubar.py << 'EOF'
import rumps

class HoldSpeakMenuBar(rumps.App):
    def __init__(self):
        super().__init__("HoldSpeak", title="🎤")
        self.menu = ["Status: Idle", None, "Start Recording", None, "Quit"]

    @rumps.clicked("Start Recording")
    def start_recording(self, _):
        rumps.notification("HoldSpeak", "Recording", "Started recording...")

if __name__ == "__main__":
    HoldSpeakMenuBar().run()
EOF

# Test it
python holdspeak/menubar.py
```

---

## References

- [rumps documentation](https://github.com/jaredks/rumps)
- [Apple Human Interface Guidelines - Menu Bar](https://developer.apple.com/design/human-interface-guidelines/menu-bar-extras)
