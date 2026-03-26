# Meeting Mode - Implementation Plan

## Overview
Add a "meeting mode" to HoldSpeak that captures **both microphone input AND system audio output**, enabling full meeting transcription with speaker differentiation.

## Why This Works Well
- **Separate audio streams** = easy speaker identification
  - Stream 1: Microphone (YOU)
  - Stream 2: System audio (THEM - Zoom/Meet/Teams participants)
- No complex diarization needed - channels are pre-separated
- Can label speakers as "Me" vs "Remote" or use app names

## Architecture

### Audio Capture
```
┌─────────────────┐     ┌──────────────────┐
│   Microphone    │────▶│                  │
│   (Input)       │     │                  │
└─────────────────┘     │   AudioMixer     │────▶ Transcriber
                        │   (sync streams) │
┌─────────────────┐     │                  │
│  System Audio   │────▶│                  │
│  (BlackHole/    │     └──────────────────┘
│   Soundflower)  │
└─────────────────┘
```

### macOS System Audio Capture
Requires a **virtual audio device** to tap system output:
1. **BlackHole** (recommended, free, open source) - https://github.com/ExistentialAudio/BlackHole
2. **Soundflower** (older alternative)
3. **Loopback** (paid, more features)

Setup: Create Multi-Output Device in Audio MIDI Setup that sends to both speakers AND BlackHole.

## Implementation Steps

### Phase 1: Core Infrastructure
1. **Create `MeetingRecorder` class** (`holdspeak/meeting.py`)
   - Dual-stream audio capture (mic + system)
   - Synchronized buffers with timestamps
   - Chunk-based processing for continuous recording

2. **Add BlackHole detection**
   - Check if BlackHole is installed (`sounddevice.query_devices()`)
   - Guide user through setup if missing
   - Store preferred system audio device in config

3. **Implement audio mixing/sync**
   - Align timestamps between streams
   - Handle sample rate differences
   - Create interleaved chunks for transcription

### Phase 2: Transcription Pipeline
4. **Extend Transcriber for dual-stream**
   - Process mic chunks → label as "Me:"
   - Process system chunks → label as "Remote:"
   - Merge chronologically with timestamps

5. **Speaker labeling options**
   - Simple: "Me" / "Remote"
   - Advanced: Detect active app (Zoom/Meet/Teams) for context
   - Future: Voice fingerprinting for multiple remote speakers

### Phase 3: Meeting Mode TUI
6. **Add meeting mode toggle**
   - New hotkey or menu option to enter meeting mode
   - Different UI state: continuous recording vs push-to-talk
   - Show both audio levels (mic + system)

7. **Meeting transcript view**
   - Two-column or color-coded speaker display
   - Timestamps for each utterance
   - Running word count / duration

8. **Meeting controls**
   - Start/Stop/Pause meeting recording
   - Mark important moments (bookmarks)
   - Export meeting transcript

### Phase 4: Export & Polish
9. **Export formats**
   - Plain text with speaker labels
   - Markdown with headers
   - SRT/VTT subtitles
   - JSON for programmatic use

10. **Settings additions**
    - System audio device selection
    - Speaker labels customization
    - Auto-start with calendar integration (future)

## File Changes Required

### New Files
- `holdspeak/meeting.py` - MeetingRecorder class
- `holdspeak/audio_devices.py` - Device discovery & BlackHole detection

### Modified Files
- `holdspeak/config.py` - Add meeting mode settings
- `holdspeak/tui.py` - Add meeting mode UI
- `holdspeak/main.py` - Add meeting mode entry point
- `pyproject.toml` - No new deps (sounddevice already supports multi-device)

## Config Additions
```python
@dataclass
class MeetingConfig:
    enabled: bool = False
    system_audio_device: Optional[str] = None  # e.g., "BlackHole 2ch"
    mic_label: str = "Me"
    remote_label: str = "Remote"
    auto_export: bool = False
    export_format: str = "markdown"  # txt, markdown, json, srt
```

## TUI Changes
- New status: "MEETING" (different color, e.g., orange)
- Dual audio meters (mic + system)
- Meeting duration timer
- Speaker-labeled transcript list

## CLI Addition
```bash
holdspeak meeting          # Start in meeting mode
holdspeak meeting --setup  # Guide through BlackHole setup
```

## Dependencies
- **BlackHole** (user must install): `brew install blackhole-2ch`
- No new Python deps - sounddevice handles multiple devices

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| BlackHole not installed | Detect & show setup guide |
| Audio sync drift | Timestamp-based alignment, periodic resync |
| High CPU (dual transcription) | Process in larger chunks, queue-based |
| Privacy concerns | Clear "recording" indicator, easy stop |

## Testing Plan
1. Unit tests for MeetingRecorder
2. Test with Zoom, Google Meet, Teams
3. Test various audio device configurations
4. Stress test long meetings (1hr+)

## Success Criteria
- [ ] Can capture mic + system audio simultaneously
- [ ] Transcripts clearly show who said what
- [ ] Works with major video conferencing apps
- [ ] Export produces useful meeting notes
- [ ] Setup process is user-friendly

---

## Quick Start for Next Agent

```bash
cd ~/Tools/HoldSpeak
source .venv/bin/activate

# Key files to understand:
cat holdspeak/audio.py      # Current audio recording
cat holdspeak/transcribe.py # Whisper transcription
cat holdspeak/tui.py        # TUI implementation
cat holdspeak/main.py       # Entry point & controller

# Run the app:
holdspeak  # or: hs (alias)

# Check logs:
tail -f ~/.local/share/holdspeak/holdspeak.log
```

## Implementation Order
1. Start with `audio_devices.py` - device discovery
2. Then `meeting.py` - dual capture (can test without TUI)
3. Add CLI `holdspeak meeting` for testing
4. Finally integrate into TUI
