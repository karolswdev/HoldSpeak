# HoldSpeak architecture

This is the map a contributor should read first: how HoldSpeak's pieces fit
and how a single utterance flows through them. It is the runtime view. For
how the code is laid out into modules, see the two structure docs in
[`internal/`](internal/): the
[web frontend decomposition](internal/ARCHITECTURE_WEB_FRONTEND.md) and the
[backend runtime decomposition](internal/ARCHITECTURE_BACKEND_RUNTIME.md).

The diagrams are Mermaid and render on GitHub. A guard
(`tests/e2e/test_mermaid_renders.py`) checks that every block in the docs
still renders, so a broken diagram cannot ship.

## The shape of it

HoldSpeak is one process. A web runtime (`WebRuntime`, the
mixin-composed orchestrator in `holdspeak/web_runtime.py`) owns the
hardware-facing pieces and a local FastAPI server (`MeetingWebServer`) that
serves the web UI and the API. Two modes run on top of the same building
blocks:

- **Dictation** turns held-key or wake-word speech into typed text, with an
  optional pipeline that routes and rewrites it before it lands.
- **Meetings** turn captured or imported audio into a transcript, typed
  artifacts, and an aftercare digest, with approval-gated actions out.

Transcription is local (`Transcriber`, MLX or faster-whisper). The LLM is
whichever backend you configure. State lives in one SQLite database behind
a set of repositories. Nothing takes an outbound action without an explicit
approval, and the network crossings are enumerated in the
[trust boundary](#the-trust-boundary) below and in
[`SECURITY.md`](SECURITY.md).

## The components

How the major pieces connect. Boxes are subsystems, not classes; the module
that owns each is named in the label.

```mermaid
flowchart TB
  subgraph entry["Audio entry"]
    HK["Hotkey<br/>(hotkey.py)"]
    WW["Wake word<br/>(wake_word.py)"]
    DEV["Device bridge<br/>(device_audio_ws.py)"]
  end

  subgraph runtime["WebRuntime — the orchestrator (web_runtime.py + runtime/*)"]
    VS["Voice session<br/>(voice_typing.py)"]
    TR["Transcriber<br/>(transcribe.py)"]
    DR["Dictation pipeline<br/>(dictation_runner.py)"]
    MS["Meeting session<br/>(meeting_session/)"]
    PH["Plugin host + router<br/>(plugins/host.py, router.py)"]
    AX["Actuator executor<br/>(plugins/actuator_executor.py)"]
    SRV["Web server + API<br/>(web_server.py, web/routes/*)"]
  end

  subgraph out["Outputs"]
    TY["Keyboard inject<br/>(typer.py)"]
    UI["Web UI + presence<br/>(web/, desktop_presence.py)"]
    CN["Gated connectors<br/>(plugins/gated_connector.py)"]
  end

  DB[("SQLite<br/>(db/*)")]
  LLM(["LLM backend<br/>(local GGUF / MLX / OpenAI-compatible)"])

  HK --> VS
  WW --> VS
  DEV --> VS
  VS --> TR
  TR --> DR
  TR --> MS
  DR --> TY
  DR -. "optional rewrite" .-> LLM
  MS --> PH
  PH -. "intel" .-> LLM
  PH --> AX
  AX --> CN
  CN -. "approved egress" .-> EXT(["GitHub / Slack / webhooks"])
  SRV --> UI
  runtime <--> DB
  SRV -. "WebSocket" .-> DEV
```

The dictation and meeting flows are detailed in their own sections below.

## The dictation pipeline

How held-key or wake-word speech becomes typed text. Capture and
transcription always run; the routing and rewrite stages are opt-in and off
by default, so the plain path is "speak, and it types what you said."

```mermaid
flowchart TD
  HK["Hotkey hold then release<br/>(hotkey.py)"] --> CAP
  WW["Wake word, then the armed window<br/>(wake_word.py)"] --> CAP
  DEV["Device audio over WebSocket<br/>(device_audio_ws.py)"] --> CAP
  CAP["Capture"] --> TR["Transcribe, local Whisper<br/>(transcribe.py)"]
  TR --> PUNC["Punctuation and spoken symbols<br/>(text_processor.py)"]
  PUNC --> VC{"Matches a voice command keyword?"}
  VC -- yes --> FIRE["Fire the bounded connector<br/>open URL, launch app, run command, type a snippet"]
  VC -- no --> PIPE{"Dictation pipeline enabled?"}
  PIPE -- "off, the default" --> FORK
  PIPE -- "on" --> STAGES["Stages, in order:<br/>intent-router, project-rewriter, kb-enricher<br/>(project-rewriter calls your LLM)"]
  STAGES --> FORK{"Entered by wake word?"}
  FORK -- "hotkey or device" --> TYPE["Type into the focused app<br/>(typer.py)"]
  FORK -- "wake, preview by default" --> PREVIEW["Preview card, nothing typed yet"]
  PREVIEW -. "you tap Type it" .-> TYPE
  TYPE --> J[("Journal the run<br/>db/journal.py")]
```

### The learning loop

Every dictation is recorded, so you can correct a wrong result once and
watch the change take effect, rather than trusting that it did.

```mermaid
flowchart LR
  RUN["A dictation runs"] --> J[("Dictation journal:<br/>said, typed, route, latency")]
  J --> REVIEW["Review at /dictation"]
  REVIEW --> FIX["One-tap correction"]
  FIX --> MEM[("Correction memory<br/>db/corrections.py")]
  MEM -. "nudges future routing" .-> RUN
  J --> REPLAY["Replay an utterance through<br/>the updated pipeline"]
  MEM -. "applied" .-> REPLAY
```

### The device path

An AIPI-Lite ESP32-S3 board on the same network (home Wi-Fi or a phone
hotspot) streams audio to the runtime. If a coding agent is waiting on a
reply, the transcribed text goes straight into that session instead of the
focused app.

```mermaid
sequenceDiagram
  participant D as ESP32-S3 device
  participant WS as Device WebSocket
  participant VT as Voice typing
  participant AG as Coding agent session
  D->>WS: 16 kHz audio frames (same LAN)
  WS->>VT: utterance
  VT->>VT: transcribe, then the pipeline
  alt an agent is awaiting a reply
    VT->>AG: type the reply into the selected session
  else
    VT->>VT: type into the focused app
  end
```

## The meeting pipeline

How captured or imported audio becomes a transcript, typed artifacts, and an
aftercare digest. The intelligence work calls the LLM you configured; the
actions out are proposals you approve, never automatic.

```mermaid
flowchart TD
  LIVE["Live capture<br/>mic plus system audio"] --> TRW
  IMP["Import a recording (meeting_import.py)<br/>or a transcript (transcript_parse.py)"] --> TRW
  TRW["Windowed transcribe<br/>(meeting_session/transcribe_loop.py)"] --> ROUTE
  ROUTE["Intent routing, opt-in<br/>(plugins/router.py)"] --> HOST
  HOST["Plugin host runs the chain<br/>(plugins/host.py)"]
  HOST -. "intel" .-> LLM(["LLM backend"])
  HOST --> ART["Typed artifacts:<br/>decisions, action items, ADRs, risk registers, and more"]
  ART --> AFT["Aftercare digest:<br/>open, decided, changed since last time<br/>(meeting_aftercare.py)"]
  AFT --> ISSUE["An accepted action becomes<br/>a GitHub issue proposal"]
  AFT --> SLACK["The digest or draft becomes<br/>a Send to Slack proposal (slack_export.py)"]
  ISSUE --> APV{"Propose, approve, execute<br/>(plugins/actuator_executor.py)"}
  SLACK --> APV
  APV -. "approved only" .-> EXT(["GitHub, Slack"])
```

## The trust boundary

Everything inside the box runs on your machine. Every arrow leaving it is a
crossing you opened, with the gate on it named. This mirrors the egress
table in [`SECURITY.md`](SECURITY.md); if the two ever disagree, SECURITY is
the source of truth.

```mermaid
flowchart LR
  subgraph machine["Your machine"]
    RT["HoldSpeak runtime"]
    WH["Whisper, local"]
    DB[("SQLite")]
    LL["LLM, when local<br/>(GGUF / MLX)"]
  end
  RT -->|"loopback by default; token required off-loopback"| WEB(["Browser and API clients"])
  RT -->|"only when intel provider is cloud or auto; transcript text"| CLOUD(["Cloud LLM endpoint"])
  RT -->|"approved proposal only; to the configured host"| SK(["Slack webhook"])
  RT -->|"opt-in pack; entity IDs via your own CLIs"| CLI(["gh, jira, to their services"])
  RT -->|"opt-in; queue stats only, no transcript"| OPS(["Ops alert webhook"])
  RT -->|"one-time inbound fetch, about 7 MB"| WM(["Wake models, GitHub releases"])
  DEVCE(["Paired device, same LAN, PSK"]) -->|"audio in, status out"| RT
```
