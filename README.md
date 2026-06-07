# HoldSpeak

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/holdspeak-mark.png" alt="HoldSpeak logo, a held key with rising soundwaves" width="120">
</p>

<p align="center"><strong>Hold a key. Speak. It types in any app. 100% local. And it learns how you work.</strong></p>

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://github.com/karolswdev/HoldSpeak/blob/main/LICENSE)
[![Tests](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml/badge.svg)](https://github.com/karolswdev/HoldSpeak/actions/workflows/test.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform: macOS | Linux](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](#platform-support)

HoldSpeak is local-first voice input for macOS and Linux. Hold your hotkey, speak,
release, and the text appears in whatever app you're in. No cloud, no account, no
telemetry. Nothing leaves your machine except the model endpoint you choose to
point at. Use it on its own as a voice-typing tool, or grow into meeting
intelligence, project-aware dictation, and the AIPI-Lite companion device.

> **Status: 0.x, early but real.** HoldSpeak is on PyPI (`pip install holdspeak`).
> The features are mature; APIs, config, and defaults can still change while it is
> pre-1.0. Upgrades are safe by default (your data is backed up first). Feedback
> and contributions welcome.

## Why it's different

- **100% local by default.** Whisper transcription and your own LLM. Nothing is
  sent anywhere unless you deliberately point it at a cloud endpoint. See
  [Security & privacy](https://github.com/karolswdev/HoldSpeak/blob/main/docs/SECURITY.md).
- **It gets better at your voice, and shows you the proof.** Every dictation is
  saved: what you said, what it typed, where it routed, how long it took. Fix a
  wrong one with a single tap and it learns; a "What HoldSpeak learned" digest
  shows the honest "learned from N similar" count; replay an utterance through the
  updated pipeline and watch the routing change. Local, off by default for
  routing, no hidden retraining.
  See [the learning loop](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay).
- **Your voice gets the afterlife your meetings already have.** A dictation doesn't
  vanish the second it's typed. It's saved, searchable, and reviewable, the same
  way a recorded meeting is.
- **14 real LLM-backed meeting plugins.** Architecture diagrams, ADRs, risk
  registers, incident timelines, decisions, and stakeholder updates, all pulled out
  of the transcript. See [meeting intelligence](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md).
- **Bring your own model.** GGUF in-process, MLX on Apple Silicon, or any
  OpenAI-compatible endpoint. See [Models](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MODELS.md).
- **Ambient desktop presence, if you want it.** A native, focus-safe HUD shows
  whether it's listening, transcribing, or typing while you dictate into another
  app. Off by default. See
  [Desktop Presence](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INTELLIGENT_TYPING_GUIDE.md#11-desktop-presence-ambient-on-desktop-status).
- **AIPI-Lite companion, if you have one.** A small device for meeting-capture
  controls, and for speaking a reply to your coding agent from another room. See
  [the workflow](https://github.com/karolswdev/HoldSpeak/blob/main/docs/AIPI_LITE_DEV_WORKFLOW.md).

## What it does, at a glance

| Voice typing | Meeting intelligence | Project-aware typing |
| --- | --- | --- |
| ![Pixel art microphone with hold-to-talk waves](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/hold-to-talk-microphone.png) | ![Pixel art meeting notebook with action items](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/meeting-intelligence-notebook.png) | ![Pixel art code editor connected to local context](https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/project-aware-typing.png) |
| Hold the hotkey, speak, release. The text goes into the active app. Punctuation commands (`"period"`, `"comma"`) and `"clipboard"` substitution work out of the box. | Capture mic and system audio together, get a live transcript with speaker labels, and let the AI pull out topics, actions, and artifacts you can review at `/history`. | Rough speech runs through intent classification, project-KB enrichment, and an LLM rewrite before it lands, tuned for Codex, Claude, the terminal, the browser, or your editor. |

## See it learn

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/pixellab/operator-working-loop.gif" alt="Animated pixel art operator working at a terminal while companion and task cards update" width="280">
</p>

Speech turns into transcript context, reviewable actions, summaries, and replies
for your coding agent, while the local runtime stays in charge. Because every
dictation is recorded, you can look back at what it heard, fix a mistake in one tap
(which teaches it), and replay the utterance through the updated pipeline. Instead
of trusting that it improved, you watch it happen.
[See the full walkthrough](https://github.com/karolswdev/HoldSpeak/blob/main/docs/DICTATION_COPILOT.md).

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/journal.png" alt="The HoldSpeak dictation Journal: a said-to-typed timeline of recent dictations, each card showing the spoken transcript, the typed result, its routing target, and a per-utterance latency strip; one row marked corrected." width="760">
</p>
<p align="center"><em>The dictation journal. Every utterance, with what you said, what it typed, where it routed, and how long it took.</em></p>

And it shows you what it learned. The Memory tab opens with a "What HoldSpeak
learned" digest: how many corrections you made, how many dictations you corrected,
and for each correction a real "learned from N similar" count, computed by the
same matcher that nudges routing. No inflated numbers, quiet when nothing matched.

<p align="center">
  <img src="https://raw.githubusercontent.com/karolswdev/HoldSpeak/main/docs/assets/screenshots/learning-digest-week.png" alt="The 'What HoldSpeak learned' digest: a this-week / all-time toggle, headline counts for corrections made, dictations corrected, and utterances nudged, a breakdown by block and target, and per-correction 'learned from N similar' rows." width="760">
</p>
<p align="center"><em>What HoldSpeak learned. Honest, windowed counts from the same matcher that nudges your routing.</em></p>

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
pip install 'holdspeak[dictation-mlx]'    # intelligent dictation on Apple Silicon (MLX)
pip install 'holdspeak[dictation-llama]'  # intelligent dictation, cross-platform (GGUF)
pip install 'holdspeak[dictation-openai]' # intelligent dictation via an OpenAI-compatible endpoint
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

## Meeting intelligence

Record or save a meeting and HoldSpeak turns the transcript into structured,
reviewable artifacts. It scores the transcript for intent (architecture, delivery,
product, incident, comms), runs a chain of plugins, and has each one call your LLM
to produce a typed artifact. The results render read-only at `/history`. HoldSpeak
ships 14 built-in plugins, all real and backed by an LLM.

Plugins can also propose actions. An actuator proposes an external side effect,
like filing a ticket or posting an update, that only runs after you approve it for
that specific action. Actuators are off by default. Write your own with the
[Plugin Authoring guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/PLUGIN_AUTHORING.md); for endpoints and routing, see
the [Meeting Mode Guide](https://github.com/karolswdev/HoldSpeak/blob/main/docs/MEETING_MODE_GUIDE.md).

Then close the loop. After a meeting, the "Your next move" aftercare panel at
`/history` shows what is still open (by owner), what was decided, and what changed
since the last meeting. Jump to the transcript moment that justifies any result,
file an accepted action as a human-approved issue through that same actuator flow,
or draft a copyable follow-up. It is read-only and local: nothing is sent, and
nothing runs, without your approval. See the
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
| Set up project-aware dictation for Codex / Claude | [Intelligent Typing Setup](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INTELLIGENT_TYPING_GUIDE.md) |
| Review, correct, and replay past dictations | [Dictation journal & replay](https://github.com/karolswdev/HoldSpeak/blob/main/docs/INTELLIGENT_TYPING_GUIDE.md#12-dictation-journal-corrections--replay) |
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
changes are in [`CHANGELOG.md`](https://github.com/karolswdev/HoldSpeak/blob/main/CHANGELOG.md).

## License

Licensed under the Apache License 2.0. See [`LICENSE`](https://github.com/karolswdev/HoldSpeak/blob/main/LICENSE).
