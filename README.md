# HoldSpeak

Voice typing for macOS and Linux - hold a hotkey, speak, release.

**Local-first. Private by default. Cloud optional. Fast.**

New to HoldSpeak?

- Start with [Getting Started](docs/GETTING_STARTED.md) for install, diagnostics, first launch, and basic voice typing.
- Use [Intelligent Typing Setup](docs/INTELLIGENT_TYPING_GUIDE.md) for project-aware dictation, `.hs/` context, target overrides, OpenAI-compatible endpoints, and Claude/Codex hooks.
- Keep [User Guide](docs/USER_GUIDE.md) open as the product map and workflow reference.

## Features

- **Voice Typing**: Hold your configured hotkey, speak, release
- **Punctuation Commands**: Say "period", "comma", "question mark" etc. - they become punctuation
- **Clipboard Insertion**: Say "clipboard" to insert your clipboard contents
- **Meeting Mode**: Record meetings with dual-stream capture (mic + system audio)
- **Live Transcription**: Real-time transcript with speaker labels
- **Meeting Intelligence**: AI-powered topics, action items, and summaries via local or cloud models
- **Deferred Intel Queue**: If no compatible local model is available, queue meeting intelligence for later processing
- **Deferred MIR Plugin Queue**: Queue heavy MIR plugin runs and process/retry/cancel them from web controls
- **Web Interfaces**: Live meeting dashboard plus browser-based archive/settings hub

## Platform Support

| Capability | macOS 14+ (Apple Silicon) | Linux X11 | Linux Wayland |
|------------|----------------------------|-----------|---------------|
| TUI voice typing | ✅ | ✅ | ✅ |
| Global hotkey (cross-app) | ✅ | ✅ | ⚠️ Best effort |
| Cross-app auto paste/type | ✅ | ✅ | ⚠️ Best effort |
| Focused hold-to-talk fallback | ✅ | ✅ | ✅ |
| Meeting mode (mic capture) | ✅ | ✅ | ✅ |
| Meeting mode (system audio capture) | ✅ (BlackHole) | ✅ (Pulse/PipeWire monitor) | ✅ (Pulse/PipeWire monitor) |
| `menubar` mode | ✅ | ❌ | ❌ |

## Known Limitations

- Wayland sessions often block global hooks and synthetic typing; HoldSpeak falls back to focused hold-to-talk + clipboard/manual paste.
- `menubar` command is macOS-only (TUI/CLI flows are cross-platform).
- Linux system audio capture requires an available Pulse/PipeWire monitor source.

## Quick Install (Linux/macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/scripts/install.sh | bash
```

Then run:

```bash
holdspeak doctor
holdspeak
```

Optional meeting extras:

```bash
curl -fsSL https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/scripts/install.sh | bash -s -- --with-meeting
```

## Installation

For local installs from this checkout:

```bash
uv pip install -e .
```

### Linux

OS deps (Debian/Ubuntu):

```bash
sudo apt-get install portaudio19-dev ffmpeg xclip pulseaudio-utils
```

Install HoldSpeak + faster-whisper:

```bash
uv pip install -e '.[linux]'
```

### macOS

Optional system-audio capture dependency:

```bash
brew install blackhole-2ch
```

### Optional: Meeting Mode Dependencies

For meeting mode with AI intelligence:

```bash
uv pip install -e '.[meeting]'

# Optional: accelerate llama-cpp on macOS
CMAKE_ARGS="-DGGML_METAL=on" uv pip install llama-cpp-python
```

### Optional: Dictation LLM Backend

The DIR-01 dictation pipeline routes utterances against a user-defined block taxonomy and enriches them with project-KB context. It supports local in-process backends and OpenAI-compatible endpoints; pick one based on platform and latency needs.

**Apple Silicon (primary on the reference Mac):**

```bash
uv pip install -e '.[dictation-mlx]'

# Default model: ~/Models/mlx/Qwen3-8B-MLX-4bit
# Download via huggingface-cli once you have HF auth configured:
huggingface-cli download mlx-community/Qwen3-8B-MLX-4bit --local-dir ~/Models/mlx/Qwen3-8B-MLX-4bit
```

**Cross-platform (Linux x86_64, or macOS fallback):**

```bash
# IMPORTANT on macOS arm64: rebuild llama-cpp-python with Metal flags
# or it falls back to CPU-only and misses latency targets dramatically.
CMAKE_ARGS="-DGGML_METAL=on" uv pip install -e '.[dictation-llama]'

# Default model: ~/Models/gguf/Qwen2.5-3B-Instruct-Q4_K_M.gguf
mkdir -p ~/Models/gguf
huggingface-cli download bartowski/Qwen2.5-3B-Instruct-GGUF \
  Qwen2.5-3B-Instruct-Q4_K_M.gguf --local-dir ~/Models/gguf --local-dir-use-symlinks False
```

**OpenAI-compatible endpoint (local server or hosted API):**

```bash
uv pip install -e '.[dictation-openai]'
```

Then point HoldSpeak at any `/v1/chat/completions` compatible server, for example LM Studio, Ollama's OpenAI bridge, vLLM, llama.cpp server, LiteLLM, or OpenAI:

```json
{
  "dictation": {
    "pipeline": { "enabled": true },
    "runtime": {
      "backend": "openai_compatible",
      "openai_compatible_base_url": "http://127.0.0.1:8000/v1",
      "openai_compatible_model": "qwen2.5-7b-instruct",
      "openai_compatible_api_key_env": "OPENAI_API_KEY",
      "openai_compatible_timeout_seconds": 8
    }
  }
}
```

For local llama.cpp server, LM Studio, Ollama's OpenAI bridge, vLLM, and LiteLLM, use the server's `/v1` base URL and model name. HoldSpeak reads the API key from the named environment variable and never stores the key in `.hs/` project context. If the endpoint times out, returns malformed output, or cannot rewrite safely, dictation falls back to the original transcript instead of blocking typing.

After install, opt the dictation pipeline in via `~/.config/holdspeak/config.json`:

```json
{
  "dictation": {
    "pipeline": { "enabled": true },
    "runtime": { "backend": "auto" }
  }
}
```

`backend: "auto"` resolves to `mlx` on `darwin/arm64` when `mlx-lm` is importable, else `llama_cpp`. Override with `"mlx"`, `"llama_cpp"`, or `"openai_compatible"` to force a backend.

Verify with:

```bash
holdspeak doctor                          # reports resolved backend + model + project context
holdspeak dictation runtime status        # reports backend resolution + model availability
holdspeak dictation dry-run "your text"   # runs the full pipeline once
```

User-defined blocks live at `~/.config/holdspeak/blocks.yaml`; per-project overrides at `<project_root>/.holdspeak/blocks.yaml`. See `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` §8 for the schema.

## Usage

### Web Runtime (Default)

```bash
holdspeak
```

This starts the local web runtime (loopback only, `127.0.0.1`).
Use this when you want browser-first access to `/history` and `/settings`.
Voice typing is also active in web mode via the configured global hotkey.

Explicit web command (same runtime):

```bash
holdspeak web
holdspeak web --no-open
```

`--no-open` keeps web mode headless (no browser auto-open).  
`--no-tui` is deprecated and currently aliases to `holdspeak web --no-open`.

### Voice Typing (Explicit TUI Mode)

```bash
holdspeak tui
```

Hold your configured hotkey (default: **Right Alt/Option**) and speak.
If global hooks are unavailable (common on Wayland), keep HoldSpeak focused and hold **v** to record.

### Diagnostics

```bash
holdspeak doctor
```

Use this to verify microphone/hotkey/text-injection/transcription prerequisites and get platform-specific fixes.
When `meeting.intel_provider` is `cloud` or `auto`, doctor also runs a cloud preflight (`/models`) and reports DNS, TLS, auth, and model-id mismatches.

### MIR CLI Routing Tools

Use `intel` for deterministic route simulation and manual profile-override reroute on saved meetings:

```bash
holdspeak intel --route-dry-run <MEETING_ID> --profile architect
holdspeak intel --reroute <MEETING_ID> --profile incident --override-intents incident,comms
```

### Homelab Cloud Intel (OpenAI-Compatible)

Point HoldSpeak at your LAN endpoint to keep transcription local while offloading meeting intel:

```json
{
  "meeting": {
    "intel_provider": "cloud",
    "intel_cloud_model": "qwen2.5-32b-instruct",
    "intel_cloud_api_key_env": "HOMELAB_INTEL_API_KEY",
    "intel_cloud_base_url": "http://homelab.local:8000/v1",
    "intel_deferred_enabled": true,
    "intel_queue_poll_seconds": 30
  }
}
```

Then validate from the same shell environment:

```bash
export HOMELAB_INTEL_API_KEY=...
holdspeak doctor
```

#### Punctuation Commands

Speak these words and they become punctuation:

| Say | Get |
|-----|-----|
| "period" or "full stop" | `.` |
| "comma" | `,` |
| "question mark" | `?` |
| "exclamation mark" | `!` |
| "colon" | `:` |
| "semicolon" | `;` |
| "open quote" / "close quote" | `"` |
| "open paren" / "close paren" | `()` |
| "dash" or "hyphen" | `-` |
| "new line" | line break |
| "new paragraph" | double line break |

**Example:** "Hello comma how are you question mark" → "Hello, how are you?"

#### Clipboard Insertion

Say **"clipboard"** to insert whatever text is currently on your clipboard.

**Example:** Copy "example.com" then say "visit clipboard for details" → "visit example.com for details"

### Meeting Mode

Run setup checks first:

```bash
# Check system-audio setup (BlackHole on macOS, Pulse monitor on Linux)
holdspeak meeting --setup

# List audio devices
holdspeak meeting --list-devices
```

Meeting start/stop is available from the web runtime dashboard (`holdspeak` or `holdspeak web`).
TUI meeting controls remain available as a compatibility path (`holdspeak tui`, then press `m`).

#### TUI Navigation

| Key | Action |
|-----|--------|
| `Tab` | Cycle between Voice Typing / Meetings tabs |
| `1` | Voice Typing tab |
| `2` | Meetings Hub (browse saved meetings) |
| `?` | Help screen |
| `s` | Settings |
| `q` | Quit |

#### Meeting Controls (TUI)

| Key | Action |
|-----|--------|
| `m` | Toggle meeting on/off |
| `b` | Add bookmark (auto-labeled from context) |
| `t` | Show transcript |
| `e` | Edit meeting title/tags |
| `w` | Open web dashboard in browser |

When a meeting starts, a web dashboard URL appears. Open it in your browser to see:
- Live transcript with speaker labels (Me / Remote)
- AI-extracted topics and action items
- Action-item review workflow (`Needs review`/`Accepted`) with accept and edit controls
- Meeting summary
- MIR routing controls (profile, intent override, deterministic route preview)
- Bookmark, per-segment copy, and export controls
- Clear intel status when analysis is live, queued, unavailable, or complete

The same local web server also exposes:
- `/history` for meeting search, action tracking, action-item review/edit, speaker tracking, and intel queue management
- `/settings` for browser-based config updates (including cloud `intel_provider` and optional `intel_cloud_base_url`)
- MIR control-plane APIs: `/api/intents/control`, `/api/intents/profile`, `/api/intents/override`, `/api/intents/preview`
- MIR history APIs: `/api/meetings/{meeting_id}/intent-timeline`, `/api/meetings/{meeting_id}/plugin-runs`, `/api/meetings/{meeting_id}/artifacts`
- Local handoff export API: `/api/meetings/{meeting_id}/export?format=markdown|json`
- Deferred plugin-job APIs: `/api/plugin-jobs`, `/api/plugin-jobs/summary`, `/api/plugin-jobs/process`, `/api/plugin-jobs/{job_id}/retry-now`, `/api/plugin-jobs/{job_id}/cancel`
- Local-only access (`127.0.0.1` loopback) by default

Saved meeting detail in `/history` can download local Markdown or JSON handoff files.
Those exports include transcript, summary/topics, reviewed action-item state,
source timestamps when available, and synthesized artifacts. They are local
downloads only; HoldSpeak does not create Jira, Linear, GitHub Issues, Slack, or
other external records from this workflow.

**For complete setup instructions and troubleshooting, see the [Meeting Mode Guide](docs/MEETING_MODE_GUIDE.md).**
Before shipping broadly, run through the [Release Hardening Checklist](docs/RELEASE_HARDENING_CHECKLIST.md).

## Testing

```bash
# Base integration subset (no optional meeting/web deps required)
uv pip install -e '.[test]'
uv run pytest -q tests/integration

# Optional meeting/web integration subset
uv pip install -e '.[meeting]'
uv run pytest -q tests/integration -m requires_meeting

# Strict release gate (fails if checklist items are unchecked)
uv run python scripts/release_gate.py
```

## Configuration

Config file: `~/.config/holdspeak/config.json`

```json
{
  "hotkey": {
    "key": "alt_r",
    "display": "Right Option"
  },
  "model": {
    "name": "base",
    "warm_on_start": true
  },
  "meeting": {
    "system_audio_device": null,
    "mic_label": "Me",
    "remote_label": "Remote",
    "intel_enabled": true,
    "intel_provider": "local",
    "intel_realtime_model": "~/Models/gguf/Mistral-7B-Instruct-v0.3-Q6_K.gguf",
    "intel_queue_poll_seconds": 120,
    "intel_retry_base_seconds": 30,
    "intel_retry_max_seconds": 900,
    "intel_retry_max_attempts": 6,
    "intel_retry_failure_alert_percent": 50.0,
    "intel_retry_failure_hysteresis_minutes": 5.0,
    "intel_retry_failure_webhook_url": null,
    "intel_retry_failure_webhook_header_name": null,
    "intel_retry_failure_webhook_header_value": null,
    "intel_cloud_model": "gpt-5-mini",
    "intel_cloud_api_key_env": "OPENAI_API_KEY",
    "intel_cloud_base_url": null,
    "intel_deferred_enabled": true,
    "web_enabled": true,
    "web_auto_open": false,
    "mir_enabled": true,
    "mir_profile": "balanced",
    "similarity_threshold": 0.75
  }
}
```

## Project-Aware Dictation

HoldSpeak can use repo-local context when dictating into coding-agent tools.
Add a `.hs/` directory at the project root:

```text
.hs/
  instructions.md  # how HoldSpeak should rewrite/inject prompts for this repo
  context.md       # architecture, important paths, setup notes
  memory.md        # durable user-approved facts
  workflows.md     # test/build/review commands
  issues.md        # active local scratchpad
  terms.md         # project vocabulary and preferred spellings
  targets.md       # per-target style notes for Codex, Claude, terminal, browser, etc.
  ignore           # paths/topics HoldSpeak should not inject
```

Flat compatibility files are also read automatically when present:
`.hs_context`, `.hs_issues`, `.hs_memory`, `.hs_instructions`,
`.hs_workflows`, `.hs_terms`, `.hs_targets`, and `.hs_ignore`. These flat
files are read-only inputs; the web UI writes only the canonical `.hs/`
layout after user action. If both forms exist, `.hs/<name>.md` wins. HoldSpeak
skips binary files, very large files, and obvious secret-looking content
instead of injecting them.

Claude Code and Codex hooks can report high-confidence session `cwd` directly
to HoldSpeak, which is more reliable than guessing from the active terminal.
For a reproducible install and verification path, see
[Claude/Codex Agent Hook Install](docs/AGENT_HOOK_INSTALL.md).
Generate hook config with:

```bash
holdspeak agent-hook templates --agent claude
holdspeak agent-hook templates --agent codex
```

The generated hooks call `holdspeak agent-hook ingest --agent ...` silently.
When possible, the template emits the absolute path to the current
`holdspeak` executable. If it falls back to plain `holdspeak`, install it in a
globally visible PATH via `uv tool`, `pipx`, a system package, or a stable
symlink before enabling the hook.
HoldSpeak stores recent agent sessions locally in
`~/.config/holdspeak/agent_sessions.json`; dictation project detection prefers
that recent hook-reported cwd when no explicit project path is supplied.

Assistant-message capture is available but opt-in because it stores bounded
conversation text locally. Generate capture-enabled hooks only after reviewing
the privacy tradeoff:

```bash
holdspeak agent-hook templates --agent claude --capture-messages
holdspeak agent-hook templates --agent codex --capture-messages
```

When enabled, `Stop` hooks read the latest assistant text from the transcript
JSONL, retain at most 4 KB, mark likely questions as `awaiting_response`, and
clear that text on the next submitted user prompt.

The Dictation page also includes a **Project Context** tab for maintaining
these `.hs/` files without leaving the web UI. If assistant-message capture is
enabled, the same page shows a project-scoped banner when Claude or Codex is
waiting for your reply; **Clear** removes the captured assistant text from the
local session registry. The **Agent Hooks** tab shows recent Claude/Codex hook
status and copy-ready hook templates, including the optional
`--capture-messages` variant. The **Runtime** tab has an opt-in
`project-rewriter` stage. When enabled, HoldSpeak asks the configured
local/OpenAI-compatible dictation runtime to rewrite the dictated text using
the repo-local `.hs/` context, the detected target profile, and any captured
awaiting agent question before normal block/template enrichment. If the runtime
is unavailable or the repo has no `.hs/` context, the stage preserves the
original text and records a warning instead of blocking dictation.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        HoldSpeak TUI                        │
├─────────────────────────────────────────────────────────────┤
│  [1 Voice Typing]  [2 Meetings Hub]     ← Tab Navigation    │
├─────────────────────────────────────────────────────────────┤
│  Voice Typing Tab           │  Meetings Hub Tab             │
│  ─────────────────          │  ─────────────────            │
│  Hotkey → Record → Type     │  Browse saved meetings        │
│  Transcription history      │  Search & filter              │
│                             │  View/Edit/Export/Delete      │
├─────────────────────────────┴───────────────────────────────┤
│  Meeting Mode (shared bar visible in both tabs)             │
│  ───────────────────────────────────────────────────────── │
│  Dual-stream recording: Mic → "Me", System → "Remote"       │
│  Every 10s: Transcribe chunks                               │
│  Every 5 segments: Run intel (topics, actions, summary)     │
│  Bookmarks: Auto-labeled from context (±10s window)         │
├─────────────────────────────────────────────────────────────┤
│                     Per-Meeting Web Server                  │
│  GET  /          → Live dashboard (meeting in progress)     │
│  GET  /history   → Meeting archive + actions + speakers     │
│  GET  /settings  → Browser settings UI                      │
│  GET  /api/state → Current meeting state                    │
│  WS   /ws        → Real-time segment/intel broadcast        │
└─────────────────────────────────────────────────────────────┘
```

## Screenshots

### TUI (Terminal UI)
![TUI Meeting Cockpit](docs/screenshots/tui_meeting.svg)

### Voice Typing
![TUI Recording](docs/screenshots/tui_recording.svg)

### Meeting Dashboard
![Meeting Dashboard](docs/screenshots/dashboard_intel.png)

See [docs/screenshots/](docs/screenshots/) for more examples.

## Requirements

- macOS 14+ (Apple Silicon) or Linux x86_64 (Ubuntu/Debian-family)
- Python 3.10+
- Accessibility/input permissions for global hotkey/text injection (platform-dependent)
- Microphone permissions
- BlackHole 2ch (optional, macOS system audio capture)
- Pulse/PipeWire monitor source (optional, Linux system audio capture)
- GGUF model (optional, for meeting intelligence)

## License

MIT
