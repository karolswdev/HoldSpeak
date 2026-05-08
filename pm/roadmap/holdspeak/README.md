# HoldSpeak — Roadmap

**Last updated:** 2026-05-07 (HS-14-07 shipped — server → device status push-back live; long_press inbound → meeting bookmark).
**Current phase:** [phase-14-aipi-lite-devices](./phase-14-aipi-lite-devices/current-phase-status.md) — extract an audio-source protocol, light up `/api/devices/audio` WebSocket, make per-device speaker labels first-class so AIPI-Lite (and other compatible devices) can feed both the voice-typing and meeting paths from across the LAN.
**Status:** in-progress.

## Vision

HoldSpeak is a local, private, hold-to-talk voice typing tool for macOS
and Linux. The current product is a working voice typer with a web
runtime, meeting mode, transcription via MLX-Whisper / faster-whisper,
and a deferred meeting-intel pipeline.

This roadmap exists because the project is graduating from "useful
script" to a real product with a plugin architecture. The next chapter
is a **pluggable transcript pipeline**: utterances flow through ordered,
user-configurable stages between Whisper and the keyboard. The first
concrete stage is an on-device LLM intent router that classifies the
utterance against a user-defined block taxonomy and triggers grounded
context injection from project knowledge bases.

## Source canon

Phase content must be grounded in these. If a phase disagrees with
canon, canon wins.

- `README.md` — public install + usage surface.
- `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — parent RFC for the plugin system.
- `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` — sibling phase: meeting-side multi-intent routing (MIR-01).
- `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` — DIR-01 spec for the dictation pipeline.
- `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` — web-first runtime migration.
- `docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md` — local activity assisted enrichment design.
- `pyproject.toml` — package contract; the source of truth for installable extras.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | Project + roadmap setup; packaging hardening | done | [phase-0-setup](./phase-0-setup/) |
| 1 | DIR-01: Dictation intent routing + transcript enrichment pipeline | done | [phase-1-dictation-intent-routing](./phase-1-dictation-intent-routing/) |
| 2 | MIR-01: Meeting-side multi-intent routing + artifact synthesis | done | [phase-2-multi-intent-routing](./phase-2-multi-intent-routing/) |
| 3 | DIR-01 loop closure: project context, llama_cpp leg, runtime counters, cold-start cap | done | [phase-3-dictation-loop-closure](./phase-3-dictation-loop-closure/) |
| 4 | WFS-01 extended: audit web flagship + interactive config for blocks / project KB / dictation runtime / dry-run preview | done | [phase-4-web-flagship-runtime](./phase-4-web-flagship-runtime/) |
| 5 | Usability powerhouse: reduce setup/dogfood friction and make web workflows faster | done | [phase-5-usability-powerhouse](./phase-5-usability-powerhouse/) |
| 6 | Action follow-through: make meeting action items and artifacts reviewable and traceable | done | [phase-6-action-follow-through](./phase-6-action-follow-through/) |
| 7 | Local handoff exports: make reviewed meeting work portable as local Markdown/JSON outputs | done | [phase-7-local-handoff-exports](./phase-7-local-handoff-exports/) |
| 8 | Local activity intelligence: mine Safari/Firefox history metadata into a private default-on work-context ledger | done | [phase-8-local-activity-intelligence](./phase-8-local-activity-intelligence/) |
| 9 | Assisted activity enrichment: add opt-in local connectors, annotations, and meeting candidates | done | [phase-9-assisted-activity-enrichment](./phase-9-assisted-activity-enrichment/) |
| 10 | Web design system & character pass: tokens, components, identity, route rebuilds, refreshed designer handoff | done | [phase-10-web-design-system](./phase-10-web-design-system/) |
| 11 | Local connector ecosystem: reusable manifests, fixtures, first-party connector packs, and developer docs | done | [phase-11-local-connector-ecosystem](./phase-11-local-connector-ecosystem/) |
| 12 | Workbench voice: replatform tokens + components on a Workbench-evoking palette + pixel font; dashboard polish; designer handoff refresh | done | [phase-12-workbench-voice](./phase-12-workbench-voice/) |
| 13 | Connector runtime + pipelines + meeting context: turn the framework on, chain packs, surface pre-meeting briefings + cross-meeting summaries | done | [phase-13-connector-runtime-and-context](./phase-13-connector-runtime-and-context/) |
| 14 | AIPI-Lite devices: remote audio ingest substrate — `AudioSource` Protocol, `RemoteAudioRecorder`, `/api/devices/audio` WebSocket, per-device speaker labels in transcripts; same-LAN scope (cross-network is phase 15) | in-progress | [phase-14-aipi-lite-devices](./phase-14-aipi-lite-devices/) |
| 15 | Out-and-about: cross-network reach for AIPI-Lite — tunneling (Tailscale / Cloudflare Tunnel / WireGuard candidate evaluation), TLS, per-device PSKs, paired with the AIPI-Lite firmware's portable WiFi (multi-SSID + captive portal + Improv-WiFi) on the device-side roadmap | not-started | (folder created at phase open) |

(Status values: `planning`, `in-progress`, `done`, `paused`, `cancelled`.)

## Operating cadence

Per `pm/roadmap/roadmap-builder.md` §3, every shipping commit updates,
in the same commit:

1. The story file header (status flip).
2. The phase's `current-phase-status.md` story-status row + "Where we are".
3. This README's "Last updated" line.
4. Any project-canon doc touched by the story.

Per `pm/roadmap/PMO-CONTRACT.md`: the pre-commit hook gates every
commit on a fresh `.tmp/CONTRACT.md`.

## Project metadata

- **Slug:** `holdspeak`
- **Story ID prefix:** `HS` (e.g. `HS-0-01`, `HS-1-04`)
- **Greenfield?:** no — `v0.2.0` is released and `scripts/install.sh` is the public install path. Backwards-compatibility is real but limited (no committed external API surface beyond CLI flags and the `holdspeak` shell command).

## Glossary

- **DIR-01** — Dictation Intent Routing, phase 1 of this roadmap. See `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md`.
- **MIR-01** — Multi-Intent Routing for meetings. Sibling phase, separate runtime, shares plugin contracts only.
- **Block** — a user-defined intent class with match examples and an injection template (DIR-01 §8).
- **Transducer** — DIR-01's new plugin kind: transcript-in, transcript-out stage.
