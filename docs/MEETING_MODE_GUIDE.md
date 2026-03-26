# Meeting Mode - Complete User Guide

HoldSpeak's Meeting Mode transforms your Mac into a powerful meeting assistant. It captures both your microphone and remote participants' audio, transcribes in real-time, and uses local AI to extract actionable intelligence.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [BlackHole Setup](#blackhole-setup)
4. [Using Meeting Mode](#using-meeting-mode)
5. [Web Dashboard](#web-dashboard)
6. [Meeting Intelligence](#meeting-intelligence)
7. [Configuration Reference](#configuration-reference)
8. [Web API Reference](#web-api-reference)
9. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Install BlackHole for system audio capture
brew install blackhole-2ch

# 2. Check setup
holdspeak meeting --setup

# 3. Start HoldSpeak
holdspeak

# 4. Press 'm' to start a meeting
```

---

## Prerequisites

### Required
- **macOS** (Apple Silicon recommended)
- **Python 3.10+**
- **Microphone permissions** granted to Terminal/iTerm

### For System Audio Capture
- **BlackHole 2ch** - Virtual audio device to capture remote participants

### For Meeting Intelligence (AI)
- **GGUF model** - Local LLM for extracting topics, action items, and summaries
- Recommended: Qwen2.5-32B or Mistral-7B

### For Web Dashboard
- **FastAPI + Uvicorn** - Web server dependencies
```bash
uv pip install fastapi uvicorn
```

---

## BlackHole Setup

BlackHole is a free virtual audio device that lets HoldSpeak capture system audio (Zoom, Meet, Teams, etc.).

### Installation

```bash
brew install blackhole-2ch
```

### Audio MIDI Setup

1. Open **Audio MIDI Setup** (Applications > Utilities)
2. Click **+** at bottom left, select **Create Multi-Output Device**
3. Check both:
   - Your speakers/headphones (e.g., "MacBook Pro Speakers")
   - **BlackHole 2ch**
4. Right-click the new Multi-Output Device > **Use This Device For Sound Output**

### Verification

```bash
holdspeak meeting --setup
```

This will check if BlackHole is detected and configured correctly.

### List Audio Devices

```bash
holdspeak meeting --list-devices
```

Shows all available audio input/output devices. Look for "BlackHole 2ch" in the list.

---

## Using Meeting Mode

### Starting a Meeting

From the TUI, press `m` to toggle meeting mode on/off.

When a meeting starts:
1. Recording begins on both mic and system audio
2. A web dashboard URL appears (e.g., `http://127.0.0.1:8234`)
3. Transcription happens automatically every ~10 seconds
4. AI intelligence runs every few segments (if enabled)

### TUI Controls

| Key | Action |
|-----|--------|
| `m` | Toggle meeting on/off |
| `b` | Add bookmark at current time |
| `t` | Show full transcript |
| `i` | Show intelligence summary |
| `u` | Copy dashboard URL |

### Stopping a Meeting

Press `m` again to stop. The meeting data is preserved until you start a new one.

---

## Web Dashboard

When a meeting starts, HoldSpeak launches a local web server with a modern dashboard.

### Accessing the Dashboard

1. Look for the URL in the TUI meeting bar (e.g., `http://127.0.0.1:8234`)
2. Open it in any browser
3. The dashboard updates in real-time via WebSocket

### Dashboard Features

**Transcript Panel**
- Live scrolling transcript
- Speaker labels (Me / Remote) color-coded
- Timestamps for each segment
- Click any segment to copy

**Intelligence Panel**
- Topics discussed
- Action items with owners and due dates
- Rolling summary of the meeting
- Updates automatically as new content arrives

**Controls**
- **Bookmark** - Mark important moments
- **Copy** - Copy full transcript
- **Export** - Download as Markdown, JSON, or TXT
- **Stop Meeting** - End recording from browser

### Multiple Clients

Multiple browsers/tabs can connect to the same meeting dashboard. All receive real-time updates.

---

## Meeting Intelligence

HoldSpeak uses local LLM inference to extract structured intelligence from your meeting transcript.

### What It Extracts

**Topics**
- Key subjects discussed
- Automatically identified from conversation

**Action Items**
```
Task: Document API endpoints
Owner: Me
Due: Friday
```

**Summary**
- Concise overview of the meeting
- Updates as the meeting progresses

### Model Requirements

Intelligence requires a GGUF model. Recommended options:

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| Mistral-7B Q6_K | 5.5GB | ~30s | Good |
| Qwen2.5-32B Q4_K_M | 18GB | ~8s (GPU) | Excellent |
| Llama-3.1-8B Q6_K | 6.5GB | ~5s | Good |

### Installing a Model

Download GGUF models from HuggingFace:

```bash
# Using hf CLI
hf download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
  --include "*Q6_K.gguf" \
  --local-dir ~/Models/gguf/

# Or direct download
curl -L -o ~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf \
  "https://huggingface.co/bartowski/Mistral-7B-Instruct-v0.3-GGUF/resolve/main/Mistral-7B-Instruct-v0.3-Q6_K.gguf"
```

### GPU Acceleration

HoldSpeak automatically uses Metal GPU on Apple Silicon. The `n_gpu_layers=-1` setting offloads all layers to GPU for maximum speed.

With GPU: Qwen 32B processes meeting intel in ~8 seconds
Without GPU: Same model takes 20+ minutes

---

## Configuration Reference

Configuration file: `~/.config/holdspeak/config.json`

### Meeting Settings

```json
{
  "meeting": {
    "system_audio_device": null,
    "mic_label": "Me",
    "remote_label": "Remote",
    "auto_export": false,
    "export_format": "markdown",
    "intel_enabled": true,
    "intel_realtime_model": "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf",
    "intel_summary_model": null,
    "web_enabled": true,
    "web_auto_open": false
  }
}
```

### Option Details

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `system_audio_device` | string | null | System audio device name (e.g., "BlackHole 2ch"). Auto-detected if null. |
| `mic_label` | string | "Me" | Label for your microphone audio in transcript |
| `remote_label` | string | "Remote" | Label for system audio in transcript |
| `auto_export` | bool | false | Automatically export when meeting ends |
| `export_format` | string | "markdown" | Export format: txt, markdown, json, srt |
| `intel_enabled` | bool | true | Enable AI intelligence extraction |
| `intel_realtime_model` | string | (Mistral path) | Path to GGUF model for real-time intel |
| `intel_summary_model` | string | null | Path to larger model for end-of-meeting summary. Falls back to realtime model if null. |
| `web_enabled` | bool | true | Enable web dashboard server |
| `web_auto_open` | bool | false | Auto-open browser when meeting starts |

---

## Web API Reference

The meeting web server exposes these endpoints:

### HTTP Endpoints

#### `GET /`
Returns the dashboard HTML page.

#### `GET /health`
Health check endpoint.

**Response:**
```json
{"status": "ok"}
```

#### `GET /api/state`
Returns current meeting state.

**Response:**
```json
{
  "started_at": "2024-01-15T10:30:00",
  "duration": 1234.5,
  "formatted_duration": "20:34",
  "segments": [
    {
      "speaker": "Me",
      "text": "Let's discuss the project timeline.",
      "timestamp": 0.0
    }
  ],
  "intel": {
    "topics": ["Project timeline", "Budget review"],
    "action_items": [
      {"task": "Send proposal", "owner": "Me", "due": "Friday"}
    ],
    "summary": "Discussed project timeline and budget."
  },
  "bookmarks": [
    {"timestamp": 300.0, "label": "Important decision"}
  ]
}
```

#### `POST /api/bookmark`
Add a bookmark at current timestamp.

**Request:**
```json
{"label": "Important point"}
```

**Response:**
```json
{"success": true}
```

#### `POST /api/stop`
Stop the meeting.

**Response:**
```json
{"success": true}
```

### WebSocket

#### `WS /ws`
Real-time updates via WebSocket connection.

**Message Types:**

```json
// New transcript segment
{"type": "segment", "data": {"speaker": "Me", "text": "...", "timestamp": 123.4}}

// Intel update
{"type": "intel", "data": {"topics": [...], "action_items": [...], "summary": "..."}}

// Duration tick (every second)
{"type": "duration", "data": "12:34"}

// Bookmark added
{"type": "bookmark", "data": {"timestamp": 300.0, "label": "..."}}

// Meeting stopped
{"type": "stopped", "data": {"status": "stopped"}}
```

**Ping/Pong:**
Send `"ping"` text message, receive `"pong"` response.

---

## Troubleshooting

### "BlackHole not found"

1. Install BlackHole: `brew install blackhole-2ch`
2. Restart Audio MIDI Setup
3. Run `holdspeak meeting --list-devices` to verify

### No remote audio captured

1. Ensure Multi-Output Device is set as system output
2. Check that BlackHole is checked in the Multi-Output Device
3. Verify with `holdspeak meeting --setup`

### Intel extraction is slow

1. Check GPU is being used: Look for "Metal" in logs
2. Use a smaller model (Mistral-7B instead of Qwen-32B)
3. Ensure `n_gpu_layers=-1` is set (default)

### Web dashboard not loading

1. Check FastAPI is installed: `uv pip install fastapi uvicorn`
2. Verify URL in TUI is accessible
3. Check firewall isn't blocking localhost

### Transcription quality is poor

1. Check microphone permissions
2. Reduce background noise
3. Try a larger Whisper model in settings (small, medium)

### Memory issues

1. Use smaller quantization (Q4 instead of Q6)
2. Close other applications
3. Disable intel if not needed: `intel_enabled: false`

---

## Best Practices

1. **Test before important meetings** - Run `holdspeak meeting --setup` first
2. **Use headphones** - Prevents echo from speakers
3. **Monitor the dashboard** - Keep it open in a browser tab
4. **Add bookmarks** - Mark important decisions in real-time
5. **Export after meetings** - Save the transcript and intel for reference

---

## Example Workflow

```bash
# Before the meeting
holdspeak meeting --setup    # Verify audio setup
holdspeak                    # Start HoldSpeak

# During the meeting (TUI)
m                            # Start meeting
# Open dashboard URL in browser
b                            # Add bookmark when something important happens

# After the meeting
m                            # Stop meeting
# Export from dashboard or use auto_export
```

---

*For more information, see the [README](../README.md) or open an issue on GitHub.*
