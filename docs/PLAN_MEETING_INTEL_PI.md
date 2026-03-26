# PI Plan: Meeting Intelligence & Web Dashboard

**Program Increment:** Meeting Mode v2.0
**Duration:** 2-3 weeks estimated
**Goal:** Real-time meeting intelligence with modern web dashboard

---

## Executive Summary

Transform HoldSpeak's meeting mode from basic transcription into an intelligent meeting assistant with:
- Real-time AI-powered extraction (action items, topics, summaries)
- Modern web dashboard per meeting instance
- Dual-model strategy (fast 7B for real-time, large model for end-summary)

---

## Epic 1: LLM Infrastructure

**Goal:** Establish local LLM inference capability using llama-cpp-python

### Story 1.1: Install and Configure llama-cpp-python
**Points:** 2
**Description:** Set up llama-cpp-python with Metal backend for Apple Silicon optimization.

**Acceptance Criteria:**
- [ ] `llama-cpp-python` installed with Metal support
- [ ] Can load Mistral-7B GGUF from ~/Models/gguf/
- [ ] Basic inference works with <2s first-token latency
- [ ] Added to pyproject.toml dependencies

**Tasks:**
- Install with `CMAKE_ARGS="-DGGML_METAL=ON"`
- Verify Metal GPU offloading works
- Test with simple prompt
- Document install in README

---

### Story 1.2: Create MeetingIntel Module
**Points:** 3
**Description:** Build the core intelligence extraction module.

**Acceptance Criteria:**
- [ ] `holdspeak/intel.py` created
- [ ] `MeetingIntel` class with lazy model loading
- [ ] Streaming `analyze()` method
- [ ] Configurable model path in config

**Tasks:**
- Create `MeetingIntel` class
- Implement structured JSON extraction prompt
- Add streaming token generator
- Handle JSON parsing with error recovery
- Add to MeetingConfig: `intel_model_path`, `intel_enabled`

**Schema:**
```python
@dataclass
class IntelResult:
    topics: list[str]
    action_items: list[ActionItem]
    summary: str
    raw_response: str

@dataclass
class ActionItem:
    task: str
    owner: Optional[str]  # "Me" or "Remote" or None
    due: Optional[str]
```

---

### Story 1.3: Integrate Intel with MeetingSession
**Points:** 2
**Description:** Wire MeetingIntel into the existing MeetingSession for automatic analysis.

**Acceptance Criteria:**
- [ ] Intel runs after each transcription batch
- [ ] Results stored in MeetingState
- [ ] Callback `on_intel` fires when new intel available
- [ ] Can disable via config

**Tasks:**
- Add `MeetingIntel` instance to `MeetingSession`
- Call analyze after `_transcribe_chunks()`
- Accumulate intel results in state
- Add `on_intel` callback parameter

---

### Story 1.4: Dual-Model Strategy
**Points:** 2
**Description:** Support fast model for real-time + large model for end-of-meeting summary.

**Acceptance Criteria:**
- [ ] Config supports `intel_realtime_model` and `intel_summary_model`
- [ ] Real-time uses Mistral-7B (or configured fast model)
- [ ] End-of-meeting triggers comprehensive summary with larger model
- [ ] Graceful fallback if large model unavailable

**Tasks:**
- Add dual model paths to config
- Implement `generate_final_summary()` method
- Call on meeting stop
- Handle model switching/unloading for memory

---

## Epic 2: Web Server Infrastructure

**Goal:** Per-meeting web server with WebSocket real-time updates

### Story 2.1: Create Web Server Module
**Points:** 3
**Description:** Build FastAPI-based web server that spins up per meeting.

**Acceptance Criteria:**
- [ ] `holdspeak/web_server.py` created
- [ ] `MeetingWebServer` class
- [ ] Starts on random available port
- [ ] Stops gracefully when meeting ends
- [ ] Health endpoint `/health`

**Tasks:**
- Create FastAPI app factory
- Implement start/stop lifecycle
- Port selection (find available)
- Background uvicorn runner
- Graceful shutdown handling

**API Endpoints:**
```
GET  /                  - Dashboard HTML
GET  /health            - Health check
GET  /api/state         - Current meeting state (JSON)
POST /api/bookmark      - Add bookmark
POST /api/stop          - Stop meeting
WS   /ws                - Real-time updates
```

---

### Story 2.2: WebSocket Real-Time Updates
**Points:** 3
**Description:** Implement WebSocket handler for pushing live updates to browser.

**Acceptance Criteria:**
- [ ] WebSocket endpoint at `/ws`
- [ ] Pushes new transcript segments
- [ ] Pushes intel updates
- [ ] Pushes duration updates (every second)
- [ ] Handles multiple connected clients
- [ ] Reconnection support

**Message Types:**
```json
{"type": "segment", "data": {...}}
{"type": "intel", "data": {...}}
{"type": "duration", "data": "00:12:34"}
{"type": "bookmark", "data": {...}}
{"type": "stopped", "data": {...}}
```

**Tasks:**
- Create WebSocket manager class
- Implement broadcast to all clients
- Wire up MeetingSession callbacks to WebSocket
- Handle client connect/disconnect
- Add heartbeat/ping

---

### Story 2.3: Integrate Web Server with MeetingSession
**Points:** 2
**Description:** Wire web server lifecycle to meeting start/stop.

**Acceptance Criteria:**
- [ ] Web server starts when meeting starts
- [ ] URL shown in TUI meeting bar
- [ ] Server stops shortly after meeting ends (grace period for export)
- [ ] Multiple meetings don't conflict (different ports)

**Tasks:**
- Add `MeetingWebServer` to `MeetingSession`
- Start server in `start()` method
- Pass callbacks for real-time updates
- Update TUI to show URL
- Stop server in `stop()` method (with delay)

---

## Epic 3: Web Dashboard Frontend

**Goal:** Modern, responsive meeting dashboard in browser

### Story 3.1: Dashboard HTML Shell
**Points:** 2
**Description:** Create single-file HTML dashboard with Tailwind + Alpine.js.

**Acceptance Criteria:**
- [ ] `holdspeak/static/dashboard.html` created
- [ ] Dark mode, modern aesthetic
- [ ] Responsive layout (works on mobile too)
- [ ] No build step required (CDN imports)

**Layout:**
```
┌─────────────────────────────────────────────────┐
│  HoldSpeak Meeting          00:12:34    [Stop]  │
├─────────────────────────────────────────────────┤
│  ┌─ Transcript ──────┐  ┌─ Intelligence ──────┐ │
│  │                   │  │ Topics: ...         │ │
│  │                   │  │ Action Items: ...   │ │
│  │                   │  │ Summary: ...        │ │
│  └───────────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────┤
│  [Bookmark]  [Copy]  [Export]                   │
└─────────────────────────────────────────────────┘
```

**Tasks:**
- Create HTML structure
- Add Tailwind CSS (CDN)
- Add Alpine.js (CDN)
- Style dark mode theme
- Make responsive

---

### Story 3.2: Live Transcript Panel
**Points:** 2
**Description:** Real-time scrolling transcript with speaker labels.

**Acceptance Criteria:**
- [ ] Shows all transcript segments
- [ ] Color-coded by speaker (Me vs Remote)
- [ ] Auto-scrolls to bottom on new segments
- [ ] Timestamps shown
- [ ] Click to copy individual segment

**Tasks:**
- Create transcript container component
- Wire to WebSocket segment events
- Implement auto-scroll
- Add speaker color coding
- Add click-to-copy

---

### Story 3.3: Intelligence Panel
**Points:** 3
**Description:** Live-updating intelligence display with streaming tokens.

**Acceptance Criteria:**
- [ ] Topics list updates in real-time
- [ ] Action items list with checkboxes
- [ ] Rolling summary section
- [ ] Shows "thinking" indicator when LLM processing
- [ ] Streaming token display (optional, cool factor)

**Tasks:**
- Create intel panel component
- Wire to WebSocket intel events
- Implement streaming text display
- Style action items as checklist
- Add loading/thinking states

---

### Story 3.4: Meeting Controls
**Points:** 2
**Description:** Control buttons and actions in dashboard.

**Acceptance Criteria:**
- [ ] Stop Meeting button (with confirmation)
- [ ] Add Bookmark button
- [ ] Copy All (transcript) button
- [ ] Export dropdown (Markdown, JSON, TXT)
- [ ] Keyboard shortcuts (b=bookmark, etc.)

**Tasks:**
- Create control bar component
- Implement API calls for each action
- Add confirmation dialogs
- Implement export formats
- Add keyboard shortcut handling

---

### Story 3.5: Connection Status & Reconnection
**Points:** 1
**Description:** Handle WebSocket disconnection gracefully.

**Acceptance Criteria:**
- [ ] Shows connection status indicator
- [ ] Auto-reconnects on disconnect
- [ ] Shows "reconnecting..." message
- [ ] Fetches missed state on reconnect

**Tasks:**
- Add connection status UI
- Implement reconnection logic
- Fetch `/api/state` on reconnect
- Merge with existing data

---

## Epic 4: TUI Integration

**Goal:** Seamless meeting experience from TUI

### Story 4.1: Show Web URL in Meeting Bar
**Points:** 1
**Description:** Display the meeting dashboard URL in TUI.

**Acceptance Criteria:**
- [ ] URL shown in meeting bar when active
- [ ] Clickable (opens browser) if terminal supports
- [ ] Copy URL shortcut

**Tasks:**
- Update MeetingBarWidget to show URL
- Add URL to meeting state
- Implement click handler (if possible)
- Add 'u' key to copy URL

---

### Story 4.2: Intel Preview in TUI
**Points:** 2
**Description:** Show basic intel summary in TUI (optional, for non-browser use).

**Acceptance Criteria:**
- [ ] Action item count in meeting bar
- [ ] Press 'i' to see intel summary modal
- [ ] Shows topics + action items

**Tasks:**
- Add intel count to meeting bar
- Create IntelPreviewScreen modal
- Wire to meeting session intel callback
- Add 'i' keybinding

---

## Epic 5: Configuration & Polish

### Story 5.1: Meeting Config Expansion
**Points:** 1
**Description:** Add all new config options.

**New Config Fields:**
```python
@dataclass
class MeetingConfig:
    # Existing
    system_audio_device: Optional[str] = None
    mic_label: str = "Me"
    remote_label: str = "Remote"
    auto_export: bool = False
    export_format: str = "markdown"

    # New - Intel
    intel_enabled: bool = True
    intel_realtime_model: str = "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf"
    intel_summary_model: Optional[str] = None  # Falls back to realtime if None

    # New - Web
    web_enabled: bool = True
    web_auto_open: bool = False  # Auto-open browser on meeting start
```

---

### Story 5.2: Meeting Export Enhancements
**Points:** 2
**Description:** Enhanced export with intel data.

**Acceptance Criteria:**
- [ ] Export includes intel (action items, summary)
- [ ] Markdown export is well-formatted
- [ ] JSON export includes all data
- [ ] SRT/VTT export for subtitles

**Tasks:**
- Update export to include intel
- Format markdown nicely
- Add SRT/VTT format
- Test all formats

---

### Story 5.3: Error Handling & Edge Cases
**Points:** 2
**Description:** Robust error handling throughout.

**Acceptance Criteria:**
- [ ] LLM load failure doesn't crash app
- [ ] Web server port conflict handled
- [ ] Graceful degradation if no models available
- [ ] Clear error messages to user

**Tasks:**
- Add try/except around LLM operations
- Handle port conflicts
- Add fallback modes
- Improve error notifications

---

## Dependencies Graph

```
Epic 1 (LLM) ──────────────────────┐
  1.1 Install                       │
   └─► 1.2 Intel Module             │
        └─► 1.3 Session Integration │
             └─► 1.4 Dual Model     │
                                    │
Epic 2 (Web Server) ◄───────────────┤
  2.1 Server Module                 │
   └─► 2.2 WebSocket                │
        └─► 2.3 Integration ◄───────┘
                    │
Epic 3 (Frontend) ◄─┘
  3.1 HTML Shell
   ├─► 3.2 Transcript
   ├─► 3.3 Intel Panel
   ├─► 3.4 Controls
   └─► 3.5 Connection

Epic 4 (TUI) ◄── depends on 2.3
  4.1 URL in Bar
  4.2 Intel Preview

Epic 5 (Polish) ◄── after all above
  5.1 Config
  5.2 Export
  5.3 Error Handling
```

---

## Sprint Breakdown (Suggested)

### Sprint 1: Foundation (Stories: 13 points)
- 1.1 Install llama-cpp-python (2)
- 1.2 MeetingIntel Module (3)
- 2.1 Web Server Module (3)
- 2.2 WebSocket Updates (3)
- 5.1 Config Expansion (1)

### Sprint 2: Integration (Stories: 11 points)
- 1.3 Intel + Session Integration (2)
- 2.3 Web + Session Integration (2)
- 3.1 Dashboard HTML (2)
- 3.2 Transcript Panel (2)
- 3.3 Intel Panel (3)

### Sprint 3: Polish (Stories: 10 points)
- 1.4 Dual Model Strategy (2)
- 3.4 Meeting Controls (2)
- 3.5 Connection Status (1)
- 4.1 URL in TUI (1)
- 4.2 Intel Preview TUI (2)
- 5.2 Export Enhancements (2)

### Sprint 4: Hardening (Stories: 2 points)
- 5.3 Error Handling (2)
- Bug fixes, testing, documentation

---

## Total Points: ~34 story points

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM inference too slow for real-time | High | Use smaller quant, reduce context, batch segments |
| Memory pressure (Whisper + LLM) | Medium | Lazy loading, model unloading between uses |
| WebSocket complexity | Medium | Start simple, add features incrementally |
| Port conflicts | Low | Random port selection, clear error messages |

---

## Definition of Done

- [ ] Feature works in TUI + Web dashboard
- [ ] No regressions in basic voice typing
- [ ] Tested with real meeting (Zoom/Meet)
- [ ] Config documented
- [ ] Logs are helpful for debugging
