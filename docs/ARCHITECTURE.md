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

An iPad companion can join over your own network. It is a typed client of
the same FastAPI routes the web UI calls, not a second runtime: it reads
meetings, artifacts, aftercare, and faceted search, decides proposals, and
sends dictation back to a focused app or a waiting coding agent. The desktop
stays the hub; the iPad is an authoring port. Its piece of the
[device path](#the-device-path) is the typed client layer, and the LAN
crossing it opens is listed in the [trust boundary](#the-trust-boundary).

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

  subgraph ipad["iPad companion (apple/Sources/Providers/)"]
    HC["Typed hub client<br/>(Desktop/HTTPDesktopClient*.swift)"]
    LS[("On-device SQLite<br/>(Storage/SQLiteStorage.swift)")]
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
  HC -. "meeting / dictation / proposal routes, LAN, Bearer token" .-> SRV
  HC <--> LS
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

### The iPad companion

The iPad joins the same hub over your own network (LAN or Tailscale, no
hosted relay). It is a typed client of the FastAPI routes, built around one
HTTP client (`apple/Sources/Providers/Desktop/HTTPDesktopClient.swift`)
split into focused extensions, one per surface it reads or drives:

- `HTTPDesktopClient+Aftercare.swift` reads the aftercare digest and files an
  accepted action as a GitHub issue proposal (`GET .../aftercare`,
  `POST .../aftercare/file-issue`).
- `HTTPDesktopClient+Facets.swift` lists and searches meetings with the
  server-side facets (`GET api/meetings/facets`, `GET api/meetings`).
- `HTTPDesktopClient+Artifacts.swift` reads a meeting's typed artifacts
  (`GET api/meetings/{id}/artifacts`).
- `HTTPDesktopClient+Proposals.swift` reads pending proposals and submits an
  approve or reject decision (`GET`/`POST .../proposals`); the executor still
  runs on the hub, so the iPad approves but never acts on its own.
- `HTTPDesktopClient+Dictation.swift` previews the dictation pipeline and
  reports readiness (`POST api/dictation/dry-run`,
  `GET api/dictation/readiness`); the base client sends the dictation itself
  to a focused app or a waiting coding agent (`POST api/dictation/remote`).

Every request carries the desktop's Bearer token, joined at call time and
never stored in a payload. The hub is the only place state changes; the iPad
is an authoring port onto it.

```mermaid
sequenceDiagram
  participant IP as iPad companion
  participant HC as Typed hub client
  participant SRV as Web server + API
  participant RT as WebRuntime
  IP->>HC: read meeting, decide proposal, send dictation
  HC->>SRV: route call over LAN, Bearer token
  SRV->>RT: dispatch to the runtime
  RT->>SRV: meetings, artifacts, aftercare, facets, decision result
  SRV->>HC: typed response
  HC->>IP: render on the authoring port
```

The iPad keeps its own SQLite store
(`apple/Sources/Providers/Storage/SQLiteStorage.swift`) for what it captures
on device. It runs in WAL mode for crash safety: an integrity check on
reopen confirms a committed write survives a crash, and an uncommitted write
is rolled back. The schema carries a `user_version`, and a forward migration
runs only when an older database is opened. This mirrors, on the mobile side,
the same safe-by-default posture the desktop store takes. The desktop store
is the one that also runs the four-way schema matrix below, where a database
newer than the build is refused rather than rewritten.

The desktop schema matrix:

- **Newer than this build:** refuse to touch it, and let `doctor` report the
  mismatch, so a newer build never gets a downgrade rewrite from an older one.
- **Older than this build:** back up first, then apply the migration, so the
  pre-migration database is always recoverable.
- **Already current:** no-op.
- **Missing:** create a fresh database.

Back up on demand with `holdspeak backup` and put a snapshot back with
`holdspeak restore`. The matrix lives in `holdspeak/db/core.py`.

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
  IPAD(["iPad companion, same LAN / Tailscale, Bearer token"]) -->|"meeting / dictation / proposal route calls"| RT
```
