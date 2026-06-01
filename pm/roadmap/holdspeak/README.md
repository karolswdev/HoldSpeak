# HoldSpeak — Roadmap

> **New here? Read [`HANDOVER.md`](./HANDOVER.md) first** — current state, where to
> pick up (Phase 26 / HS-26-02), and the repo conventions that bite (PMO commit
> gate, write-once evidence, no `Co-Authored-By`, metal-test exclusion).

**Last updated:** 2026-05-31 (Phase 26: HS-26-04 done — 38 activity/connector/plugin-job routes extracted to `routes/activity.py`, web_server.py 5658→1817 cumulative (−68%); Phase 25 7/8 done + green, HS-25-07 blocked on hardware dogfood).
**Current phase:** [phase-26-web-runtime-decomposition](./phase-26-web-runtime-decomposition/) — break the `web_server.py` monolith into route modules. (Phase 25 stays open, blocked only on HS-25-07's in-person dogfood.)
**Status:** in-progress.

## Vision

HoldSpeak is a local, private, hold-to-talk voice typing tool for macOS
and Linux. The current product is a working voice typer with a web
runtime, meeting mode, transcription via MLX-Whisper / faster-whisper,
deferred meeting intelligence, and an emerging intelligent-typing layer
for project-aware local writing.

This roadmap exists because the project is graduating from "useful
script" to a real product. The current chapter is **local intelligent
typing**: utterances can flow through ordered, user-configurable stages
between Whisper and the keyboard, optionally using target-profile
detection, project context, agent hooks, and OpenAI-compatible local or
LAN LLM endpoints before text is injected.

## Source canon

Phase content must be grounded in these. If a phase disagrees with
canon, canon wins.

- `README.md` — public install + usage surface.
- `docs/SECURITY.md` — security & privacy posture: data classes, trust boundaries, egress points, encryption-at-rest stance (HS-25-03).
- `docs/USER_GUIDE.md` — user-facing product workflows.
- `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` — parent RFC for the plugin system.
- `docs/PLAN_PHASE_MULTI_INTENT_ROUTING.md` — sibling phase: meeting-side multi-intent routing (MIR-01).
- `docs/PLAN_PHASE_DICTATION_INTENT_ROUTING.md` — DIR-01 spec for the dictation pipeline.
- `docs/PLAN_PHASE_WEB_FLAGSHIP_RUNTIME.md` — web-first runtime migration.
- `docs/PLAN_ACTIVITY_ASSISTED_ENRICHMENT.md` — local activity assisted enrichment design.
- `aipi-lite/` — first-class AIPI-Lite firmware, bridge, docs, tests, and imported device-side roadmap.
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
| 14 | AIPI-Lite devices: remote audio ingest substrate — `AudioSource` Protocol, `RemoteAudioRecorder`, `/api/devices/audio` WebSocket, per-device speaker labels in transcripts; same-LAN scope (cross-network is phase 15) | done | [phase-14-aipi-lite-devices](./phase-14-aipi-lite-devices/) |
| 15 | Out-and-about: cross-network reach for AIPI-Lite — tunneling (Tailscale / Cloudflare Tunnel / WireGuard candidate evaluation), TLS, per-device PSKs, paired with the AIPI-Lite firmware's portable WiFi (multi-SSID + captive portal + Improv-WiFi) on the device-side roadmap | not-started | [phase-15-out-and-about](./phase-15-out-and-about/) |
| 16 | First real synthesizer: replace `mermaid_architecture`'s `DeterministicPlugin` stub with a real LLM-backed plugin, wire the LLM capability gate, render `mermaid` artifacts as inline SVG in the web view, reality-check the plugin RFC | paused | [phase-16-first-real-plugin](./phase-16-first-real-plugin/) |
| 17 | Device Initiative: device → server upstream frames (`device_health` + `query` w/ `last_segment` case) lighting up AIPI-Lite phase 4's `blocked` bridge stories; minimal web UI rendering for device health. Sibling to HS-14, paired with AIPI-4 in the AIPI-Lite roadmap. | done | [phase-17-device-initiative](./phase-17-device-initiative/) |
| 18 | Intelligent Typing Copilot: project-aware local intelligent typing with target profiles, Claude/Codex hooks, optional external-agent summarization, `.hs` context conventions, OpenAI-compatible runtimes, and web cockpit support | done | [phase-18-intelligent-typing-copilot](./phase-18-intelligent-typing-copilot/) |
| 19 | Intelligent Typing Daily-Use Hardening: safe `.hs/.../*.md` project-doc suggestions, telemetry, target-profile overrides, and real endpoint dogfooding | done | [phase-19-intelligent-typing-hardening](./phase-19-intelligent-typing-hardening/) |
| 20 | AIPI Companion: same-LAN physical companion UX for agent-waiting status, voice replies, gestures, and debug visibility | done | [phase-20-aipi-companion](./phase-20-aipi-companion/) |
| 21 | AIPI-Lite First-Class Integration: import firmware and bridge source into HoldSpeak and define the unified developer workflow | done | [phase-21-aipi-lite-first-class](./phase-21-aipi-lite-first-class/) |
| 22 | AI PI Companion UX: state model, gestures, LCD cadence, bridge display wiring, and live hardware dogfood | done | [phase-22-ai-pi-companion-ux](./phase-22-ai-pi-companion-ux/) |
| 23 | AI PI Companion UX Polish: long-prompt display, multi-session identity, preview/browse, and target confidence | done | [phase-23-ai-pi-companion-ux-polish](./phase-23-ai-pi-companion-ux-polish/) |
| 24 | AI PI Companion Productization: web companion overview, stale-session controls, confidence affordances, and display update cadence | paused | [phase-24-ai-pi-companion-productization](./phase-24-ai-pi-companion-productization/) |
| 25 | Trust & Hardening: no silent cloud egress, web-runtime auth + bind guard, threat-model/encryption-at-rest doc, LLM-runtime thread-safety, transcription timeout, config-knob audit. Prerequisite to Phase 15. | in-progress | [phase-25-trust-and-hardening](./phase-25-trust-and-hardening/) |
| 26 | Web Runtime Decomposition: break the `web_server.py` monolith into route modules + a shared context, behavior-preserving. Fast-follow to Phase 25. | in-progress | [phase-26-web-runtime-decomposition](./phase-26-web-runtime-decomposition/) |

(Status values: `planning`, `in-progress`, `done`, `paused`, `cancelled`.)

Phase 15 (cross-network reach) is gated on Phase 25 landing the web-runtime
auth + bind guard.

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
