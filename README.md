# HoldSpeak

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/holdspeak-mark.png" alt="HoldSpeak logo, a held key with rising soundwaves" width="120">
</p>

<p align="center"><strong>One local copilot, two modes: dictation that types anywhere and learns how you work, and meetings that end with decisions, actions, and follow-ups instead of a recording. Nothing leaves your machine.</strong></p>

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/karolswdev/HoldSpeak/blob/main/LICENSE)
[![Tests](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml/badge.svg)](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#platform-support)

Your voice does work in two places: at the keyboard and in meetings.
HoldSpeak covers both with one runtime on macOS and Linux. Hold a hotkey,
speak, release, and the text lands in whatever app you are in, optionally
rewritten by your own LLM with your project's context. Record or import a
meeting, and it comes back as reviewable decisions, action items, and typed
artifacts, with a follow-up panel that shows what is still open. Whisper
runs locally; the LLM is one you run or point at. No cloud, no account, no
telemetry.

> **Status: 0.x, early but real.** HoldSpeak is on PyPI (`pip install holdspeak`).
> The features are mature; APIs, config, and defaults can still change while it is
> pre-1.0. Upgrades are safe by default (your data is backed up first). Feedback
> and contributions welcome.

## The two modes

| Dictate | Meet |
| --- | --- |
| ![Pixel art microphone with hold-to-talk waves](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/hold-to-talk-microphone.png) | ![Pixel art meeting notebook with action items](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/meeting-intelligence-notebook.png) |
| Hold the hotkey, speak, release: the text goes into the active app. Turn on the dictation pipeline and rough speech is routed by intent, enriched with your project's context, and rewritten for its target (Codex, Claude, the terminal, the browser, your editor). Every run lands in the dictation journal; one tap on a wrong result teaches the correction memory. Voice commands map a spoken keyword to a real action (open a URL, launch an app, run a command). Activity pre-briefing offers what you touched recently as dictation context, source-cited. | Capture mic and system audio live with speaker labels, or import a recording or a transcript file you already have (vtt and srt keep their real timestamps and speaker names). 14 built-in plugins call your LLM to pull typed artifacts out of the transcript: decisions, action items, ADRs, risk registers, incident timelines. Meeting aftercare then shows what is open, decided, and changed since last time, and an accepted action can become a filed issue through a propose, approve, execute flow that never acts without you. The archive is searchable and filterable by date, speaker, tag, and open actions. |

This is what they look like in the product, not in pixel art. A saved meeting
comes back as typed, reviewable artifacts:

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/history.png" alt="A saved meeting open at /history: the transcript on the left, and on the right a stack of artifact cards (a Risk register table with impact, likelihood, mitigation, and owner; Decisions and open questions; typed Requirements), each with a confidence score and a copy button." width="760">
</p>
<p align="center"><em>A meeting after intelligence ran: a risk register, decisions, and requirements, each extracted by an LLM-backed plugin and rendered read-only at /history.</em></p>

## Why it's different

- **Everything is local, including the intelligence.** Whisper transcribes on
  your machine and the LLM is yours: GGUF in-process, MLX on Apple Silicon, or
  any OpenAI-compatible endpoint you choose, including one on your own LAN.
  See [Security & privacy](https://github.com/karolswdev/HoldSpeak/blob/main/docs/SECURITY.md) and [Models](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MODELS.md).
- **It learns how you work, and shows you the receipts.** The dictation
  journal records what you said, what it typed, where it routed, and how long
  it took. Fix a wrong result in one tap and the correction memory learns; the
  learning digest reports a real "learned from N similar" count, honest at
  zero; replay an old utterance through the updated pipeline and watch the
  routing change. See [the learning loop](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay).
- **Meetings end with their loops closed.** A meeting produces artifacts,
  an aftercare digest, and approval-gated actions where most tools stop at
  a transcript. Actuators are off by default, audited, and only ever run
  exactly what you previewed. See
  [meeting intelligence](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md).
- **Honest by construction.** `holdspeak doctor` reports what is actually
  broken. The import panel says which timestamps are approximate. The learning
  digest never inflates a count. Upgrades back your database up before
  touching it and refuse to open data written by a newer build. The docs hold
  themselves to the same bar.

## See it learn

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/operator-working-loop.gif" alt="Animated pixel art operator working at a terminal while companion and task cards update" width="280">
</p>

Because every dictation is recorded, you can look back at what it heard, fix
a mistake in one tap (which teaches it), and replay the utterance through the
updated pipeline. Instead of trusting that it improved, you watch it happen.
[See the full walkthrough](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_COPILOT.md).

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/journal.png" alt="The HoldSpeak dictation journal: a said-to-typed timeline of recent dictations, each card showing the spoken transcript, the typed result, its routing target, and a per-utterance latency strip; one row marked corrected." width="760">
</p>
<p align="center"><em>The dictation journal. Every utterance, with what you said, what it typed, where it routed, and how long it took.</em></p>

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/learning-digest-week.png" alt="The 'What HoldSpeak learned' digest: a this-week / all-time toggle, headline counts for corrections made, dictations corrected, and utterances nudged, a breakdown by block and target, and per-correction 'learned from N similar' rows." width="760">
</p>
<p align="center"><em>The learning digest. Honest, windowed counts from the same matcher that nudges your routing.</em></p>

And if you want a face on all of it: Qlippy, an optional pixel-art mascot,
sits on the desktop presence surface and turns the moments that need you into
dismissible cards: an action awaiting approval, a correction that actually
reached past dictations, a meeting that left open items. He never acts on his
own, and every actionable card states in plain language what data is used,
whether anything leaves your machine, and what your controls are. Off by
default, like everything ambient here.

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/presence/qlippy-decision-card.png" alt="Qlippy's decision card: the pixel-art mascot in an alert pose beside the headline 'A decision needs you', the exact preview of a proposed GitHub issue, plain-language privacy answers, and Approve and Decline buttons." width="420">
</p>
<p align="center"><em>Qlippy asking for a decision: the exact preview, the privacy answers, and your controls. Nothing runs until you approve.</em></p>

## How it compares (as of mid-2026)

Honest comparisons, architecture-level on purpose: where your audio goes,
what the tool spans, and whether it learns. These tools are good at what
they do; pick the one that fits.

| Tool | What it does better | What HoldSpeak does better |
|---|---|---|
| **OS dictation** (Apple Dictation, Windows Voice Typing) | Zero setup, free, always available | Your own models, LLM rewriting with project context, the learning loop, meetings |
| **Local Whisper apps** (superwhisper, MacWhisper, VoiceInk) | Simpler setup, polished single-purpose UX | The LLM stays local too (their AI modes often call cloud APIs), a visible learning loop, meeting intelligence, Linux support |
| **AI dictation services** (Wispr Flow, Aqua Voice) | Out-of-box accuracy and editing polish, no model management | Your voice never leaves your machine, open source, no subscription, meetings |
| **Talon** | The deepest hands-free coding and computer control there is | Prose-first dictation with LLM rewriting, lower learning curve, meeting intelligence |
| **Raw Whisper tooling** (whisper.cpp scripts) | Total control, minimal surface | A product: typing integration, routing, the journal, meetings, a web UI |

And the trade-offs in the other direction: HoldSpeak is 0.x, the smart parts
need a model you provide, setup is heavier than a menu-bar app, there is no
Windows build today, and Wayland limits global hotkeys to best effort.

## Quickstart

Install from PyPI, check your setup, and launch the web runtime:

```bash
pip install holdspeak
holdspeak doctor   # check mic permissions and backends
holdspeak          # launch the web runtime
```

Prefer [`uv`](https://docs.astral.sh/uv/)? `uv pip install holdspeak`.

Or use the install script (creates an isolated venv and a `holdspeak` launcher),
or work from a clone:

```bash
# one-line install
curl -fsSL https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/scripts/install.sh | bash

# or from a clone (for development)
git clone https://github.com/karolswdev/HoldSpeak.git && cd HoldSpeak
uv pip install -e .
holdspeak doctor && holdspeak
```

Install only the extras you need:

```bash
pip install 'holdspeak[meeting]'          # meeting mode and AI intelligence
pip install 'holdspeak[dictation-mlx]'    # the dictation pipeline on Apple Silicon (MLX)
pip install 'holdspeak[dictation-llama]'  # the dictation pipeline, cross-platform (GGUF)
pip install 'holdspeak[dictation-openai]' # the dictation pipeline via an OpenAI-compatible endpoint
```

(From a clone, use the editable form instead, e.g. `uv pip install -e '.[meeting]'`.)

The dictation and meeting LLM is yours to choose. See
[`docs/MODELS.md`](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MODELS.md) for the contract and current suggestions.

### Upgrading and your data

Your whole HoldSpeak database is a single SQLite file. Before a version jump you
can snapshot it with `holdspeak backup`, and put one back with `holdspeak
restore`. Upgrades are safe by default: HoldSpeak backs up an older database
before it touches it, and refuses to open a database written by a newer build
rather than risk your data. `holdspeak doctor` reports the schema and config
state it found. The full policy is in
[`docs/RELEASING.md`](https://github.com/karolswdev/HoldSpeak/blob/main/docs/RELEASING.md).

## Platform support

| Capability | macOS 14+ (Apple Silicon) | Linux X11 | Linux Wayland |
|---|---|---|---|
| Voice typing | ✅ | ✅ | ✅ |
| Global hotkey | ✅ | ✅ | ⚠️ Best effort |
| Cross-app typing | ✅ | ✅ | ⚠️ Best effort |
| Meeting mode | ✅ | ✅ | ✅ |
| System audio capture | ✅ BlackHole | ✅ Pulse/PipeWire | ✅ Pulse/PipeWire |

Wayland often blocks global hooks and synthetic typing, so HoldSpeak falls back to clipboard paste for injection.

## Meeting intelligence, a little deeper

Record a meeting live, or bring one you already have: import a recording
(WAV out of the box; compressed formats with ffmpeg) or a transcript file
(`.vtt`, `.srt`, `.txt`) from the archive page or with `holdspeak import
call.wav`, and it becomes a real meeting, run through the same intelligence.
The transcript is scored for intent (architecture, delivery, product,
incident, comms), a chain of plugins runs, and each one calls your LLM to
produce a typed artifact. The results render read-only at `/history`.
HoldSpeak ships 14 built-in plugins, all real and backed by an LLM.

Plugins can also propose actions. An actuator proposes an external side
effect, like filing a ticket or posting an update, that only runs after you
approve it for that specific action. Actuators are off by default. Write your
own with the [Plugin Authoring guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/PLUGIN_AUTHORING.md); for endpoints and routing, see
the [Meeting Mode Guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md).

Then close the loop. Meeting aftercare shows what is still open (by owner),
what was decided, and what changed since the last meeting. Jump to the
transcript moment that justifies any result, file an accepted action as a
human-approved issue through that same actuator flow, or draft a copyable
follow-up. It is read-only and local: nothing is sent, and nothing runs,
without your approval. See the
[Meeting Mode Guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md#meeting-aftercare-close-the-loop).

## AIPI-Lite companion

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/aipi-lite-companion.png" alt="Pixel art AIPI-Lite companion device" width="220">
</p>

AIPI-Lite is an optional ESPHome-based device you can carry between rooms. Put it
on Wi-Fi (a phone hotspot works), and it gives you meeting-capture controls and
status feedback. With Claude/Codex hooks on, it tells you when an agent is waiting
so you can speak the reply back into the coding session. Buy the hardware from the
[official page](https://aipi.com/products/aipi-lite) or the
[Amazon listing](https://www.amazon.com/dp/B0FQNNVV36); firmware and bridge setup
are in the [AIPI-Lite Developer Workflow](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AIPI_LITE_DEV_WORKFLOW.md).

## Where to go next

| I want to… | Read this |
|---|---|
| Browse all the docs | [Documentation index](https://github.com/karolswdev/HoldSpeak/blob/main/docs/README.md) |
| Get it running and verify my setup | [Getting Started](https://github.com/karolswdev/HoldSpeak/blob/main/docs/GETTING_STARTED.md) |
| Choose / configure a model | [Models (bring your own)](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MODELS.md) |
| See speech become a project-grounded task | [The Dictation Copilot](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_COPILOT.md) |
| Set up the dictation pipeline for Codex / Claude | [Intelligent Typing Setup](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INTELLIGENT_TYPING_GUIDE.md) |
| Review, correct, and replay past dictations | [The dictation journal & replay](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay) |
| Map spoken keywords to real actions | [Voice Commands](https://github.com/karolswdev/HoldSpeak/blob/main/docs/VOICE_COMMANDS.md) |
| Use meeting mode and configure AI intelligence | [Meeting Mode Guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md) |
| Wire up the AIPI-Lite companion | [AIPI-Lite Developer Workflow](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AIPI_LITE_DEV_WORKFLOW.md) |
| Install Claude / Codex agent hooks | [Agent Hook Install](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AGENT_HOOK_INSTALL.md) |
| Understand what's stored and what can leave my machine | [Security & Privacy](https://github.com/karolswdev/HoldSpeak/blob/main/docs/SECURITY.md) |

## Configuration

Config lives at `~/.config/holdspeak/config.json`, but you rarely edit it by hand.
The Settings page in the web runtime exposes the hotkey, model, meeting intel,
dictation pipeline, and presence options. The full reference is in
[Getting Started](https://github.com/karolswdev/HoldSpeak/blob/main/docs/GETTING_STARTED.md) and the guides above.

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](https://github.com/karolswdev/HoldSpeak/blob/main/CONTRIBUTING.md) for setup
(`uv`, the git hooks, the test command) and the commit-contract workflow. Recent
changes are in [`CHANGELOG.md`](https://github.com/karolswdev/HoldSpeak/blob/main/CHANGELOG.md). If you want to build on
HoldSpeak rather than just use it, the
[Plugin Authoring guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/PLUGIN_AUTHORING.md) and
[Connector Development](https://github.com/karolswdev/HoldSpeak/blob/main/docs/CONNECTOR_DEVELOPMENT.md) are the doors in.

## License

Licensed under the Apache License 2.0. See [`LICENSE`](https://github.com/karolswdev/HoldSpeak/blob/main/LICENSE).
