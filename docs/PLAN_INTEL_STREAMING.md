# Initiative: Meeting Intelligence 2.0

**Goal:** Enhance meeting intelligence with streaming display, better action item management, and meeting persistence.

**Branch:** `feature/intel-streaming`

---

## Overview

Current state:
- Intel extraction works (topics, action items, summary)
- Results appear all at once in dashboard
- No persistence between sessions
- No action item management

Target state:
- Streaming token display (see LLM "thinking")
- Persistent action items with status tracking
- Meeting history with search
- Smarter triggering (content-aware, not time-based)

---

## Architecture

### Current Flow

```
Audio → Transcribe → Intel (batch) → Dashboard (all at once)
                         │
                         └─ analyze() returns IntelResult
```

### Enhanced Flow

```
Audio → Transcribe → Intel (streaming) → Dashboard (token by token)
                         │                      │
                         │                      ├─ "intel_token" messages
                         │                      └─ "intel_complete" message
                         │
                         └─ analyze(stream=True) yields str | IntelResult
                                    │
                                    └─ Already implemented! Just need to wire it.
```

---

## Implementation Plan

### Phase 1: Wire Streaming to WebSocket

**The code exists** - `MeetingIntel.analyze(stream=True)` already yields tokens.

Just need to connect it to the WebSocket broadcast.

**File:** `holdspeak/meeting_session.py`

```python
# Current (batch)
def _run_intel(self, transcript: str) -> None:
    result = self._intel.analyze(transcript)
    self._state.intel = result
    if self._web_server:
        self._web_server.broadcast("intel", result.to_dict())

# Streaming
def _run_intel(self, transcript: str) -> None:
    for chunk in self._intel.analyze(transcript, stream=True):
        if isinstance(chunk, str):
            # Stream token to dashboard
            if self._web_server:
                self._web_server.broadcast("intel_token", chunk)
        else:
            # Final result
            self._state.intel = chunk
            if self._web_server:
                self._web_server.broadcast("intel_complete", chunk.to_dict())
```

**File:** `holdspeak/static/dashboard.html`

Add streaming display in Alpine.js:
```javascript
// Handle streaming tokens
case 'intel_token':
    this.intelBuffer += data;
    this.intelStreaming = true;
    break;
case 'intel_complete':
    this.intel = data;
    this.intelBuffer = '';
    this.intelStreaming = false;
    break;
```

**Tasks:**
- [ ] Modify `_run_intel()` to use streaming
- [ ] Add `intel_token` and `intel_complete` message types
- [ ] Update dashboard to show streaming text
- [ ] Add "thinking" indicator animation
- [ ] Handle interruption (new intel starts before old finishes)

---

### Phase 2: Enhanced Action Items

**Current ActionItem:**
```python
@dataclass
class ActionItem:
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None
```

**Enhanced ActionItem:**
```python
@dataclass
class ActionItem:
    id: str                          # Unique ID for tracking
    task: str
    owner: Optional[str] = None
    due: Optional[str] = None
    status: str = "pending"          # pending, done, dismissed
    source_timestamp: Optional[float] = None  # Link to transcript
    created_at: str = ""             # ISO timestamp
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

    def mark_done(self) -> None:
        self.status = "done"
        self.completed_at = datetime.now().isoformat()

    def dismiss(self) -> None:
        self.status = "dismissed"
```

**API additions:**

```
PATCH /api/action-items/{id}
Body: {"status": "done"} or {"status": "dismissed"}

GET /api/action-items
Returns: [ActionItem, ...]
```

**Dashboard updates:**
- Checkbox to mark done
- "X" to dismiss
- Visual distinction for completed/dismissed
- Filter: All / Pending / Completed

**Tasks:**
- [ ] Extend ActionItem dataclass
- [ ] Generate unique IDs for action items
- [ ] Add PATCH endpoint for status updates
- [ ] Update dashboard with checkboxes
- [ ] Persist action item state in meeting state

---

### Phase 3: Meeting Persistence

**Storage structure:**
```
~/.local/share/holdspeak/meetings/
├── index.json                    # Meeting index for quick search
├── 2024-01-15T10-30-00_standup/
│   ├── meeting.json              # Full meeting state
│   ├── transcript.md             # Human-readable transcript
│   └── audio/                    # Optional: raw audio chunks
│       ├── mic_000.wav
│       └── system_000.wav
└── 2024-01-16T14-00-00_planning/
    ├── meeting.json
    └── transcript.md
```

**meeting.json schema:**
```json
{
  "id": "2024-01-15T10-30-00_standup",
  "started_at": "2024-01-15T10:30:00",
  "ended_at": "2024-01-15T11:15:00",
  "duration": 2700,
  "segments": [...],
  "intel": {
    "topics": [...],
    "action_items": [...],
    "summary": "..."
  },
  "bookmarks": [...],
  "title": "Daily Standup",  // User can rename
  "tags": ["standup", "team"]  // User can tag
}
```

**index.json for search:**
```json
{
  "meetings": [
    {
      "id": "2024-01-15T10-30-00_standup",
      "title": "Daily Standup",
      "started_at": "2024-01-15T10:30:00",
      "duration": 2700,
      "topics": ["sprint progress", "blockers"],
      "action_item_count": 3,
      "tags": ["standup"]
    }
  ]
}
```

**Tasks:**
- [ ] Create `MeetingStorage` class
- [ ] Auto-save meeting on stop
- [ ] Load past meetings
- [ ] Add meeting list endpoint `/api/meetings`
- [ ] Add meeting detail endpoint `/api/meetings/{id}`

---

### Phase 4: Smarter Intel Triggering

**Current:** Fixed interval (every N segments)

**Improved options:**

1. **Content-based:** Trigger when transcript grows by X words
   ```python
   if len(new_words) >= 100:  # Every ~100 new words
       run_intel()
   ```

2. **Silence-based:** Trigger during conversation pauses
   ```python
   if silence_duration > 3.0:  # 3 second pause
       run_intel()
   ```

3. **Incremental context:** Only analyze new content, merge results
   ```python
   # Instead of full transcript each time
   new_intel = analyze(new_segments_only)
   merged_intel = merge(existing_intel, new_intel)
   ```

**Tasks:**
- [ ] Add `intel_trigger_mode` config option
- [ ] Implement word-count trigger
- [ ] Implement silence-based trigger
- [ ] Consider incremental analysis (more complex)

---

### Phase 5: Meeting Search (Future)

**Simple search:**
```
GET /api/search?q=API+decision
```

Returns meetings containing the search term in transcript or intel.

**Semantic search (future):**
Use embeddings for "What did we decide about authentication?"

---

## Config Additions

```python
@dataclass
class MeetingConfig:
    # ... existing ...

    # Intel streaming
    intel_streaming: bool = True

    # Intel triggering
    intel_trigger_mode: str = "segments"  # segments, words, silence
    intel_trigger_segments: int = 5
    intel_trigger_words: int = 100
    intel_trigger_silence: float = 3.0

    # Persistence
    save_meetings: bool = True
    save_audio: bool = False  # Large files, optional
    meetings_dir: str = "~/.local/share/holdspeak/meetings"
```

---

## WebSocket Message Types (Updated)

```typescript
// Existing
{ type: "segment", data: TranscriptSegment }
{ type: "intel", data: IntelResult }  // Keep for non-streaming
{ type: "duration", data: "12:34" }
{ type: "bookmark", data: Bookmark }
{ type: "stopped", data: {...} }

// New
{ type: "intel_token", data: "The main" }  // Streaming token
{ type: "intel_complete", data: IntelResult }  // Final structured result
{ type: "action_item_updated", data: ActionItem }  // Status change
```

---

## Dashboard UI Changes

### Intel Panel (Streaming)

```
┌─ Intelligence ─────────────────────────────┐
│                                            │
│  ● Analyzing...                            │  <- Thinking indicator
│  {"topics": ["project timeline",█          │  <- Streaming text
│                                            │
│  ─────────────────────────────────────     │
│                                            │
│  Topics:                                   │
│  • Project timeline                        │
│  • Budget review                           │
│                                            │
│  Action Items:                             │
│  ☑ Send proposal to client - Me (Done)     │  <- Checkbox
│  ☐ Review budget numbers - Remote          │
│  ✕ Old task (dismissed)                    │  <- Strikethrough
│                                            │
│  Summary:                                  │
│  Discussed project timeline and budget...  │
│                                            │
└────────────────────────────────────────────┘
```

---

## Testing Strategy

1. **Unit tests:**
   - ActionItem status transitions
   - MeetingStorage save/load
   - Intel trigger conditions

2. **Integration tests:**
   - Streaming through WebSocket
   - Action item updates via API
   - Meeting persistence

3. **E2E tests:**
   - Full meeting → save → load → verify

---

## Success Criteria

- [ ] Intel tokens stream to dashboard in real-time
- [ ] "Thinking" indicator shows when LLM processing
- [ ] Action items have checkboxes, can mark done
- [ ] Meetings persist to disk
- [ ] Can list and view past meetings
- [ ] Intel triggers based on content, not just time

---

## Quick Start for Implementation

```bash
# Create branch
git checkout -b feature/intel-streaming

# Phase 1: Wire streaming (fastest win)
# Edit holdspeak/meeting_session.py - change _run_intel to stream
# Edit holdspeak/static/dashboard.html - add streaming display

# Test with:
holdspeak
# Press 'm' to start meeting
# Open dashboard, watch intel stream
```

---

## Dependencies

No new dependencies required. All functionality uses existing:
- `llama-cpp-python` (streaming already supported)
- `FastAPI` (WebSocket already implemented)
- Standard library for file I/O

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Streaming adds complexity | Phase 1 is minimal change, can revert |
| Action item dedup | Use task text hash for ID generation |
| Storage grows large | Configurable, audio optional |
| Search performance | Index file for quick lookups |
