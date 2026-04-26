# HoldSpeak — Roadmap

**Last updated:** 2026-04-25 (HS-2-04 done — typed `PluginRun` dispatcher over the existing `PluginHost`; 913 passed end-to-end).
**Current phase:** [phase-2-multi-intent-routing](./phase-2-multi-intent-routing/current-phase-status.md)
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
- `pyproject.toml` — package contract; the source of truth for installable extras.

## Phase index

| Phase | Goal (one line) | Status | Folder |
|---|---|---|---|
| 0 | Project + roadmap setup; packaging hardening | done | [phase-0-setup](./phase-0-setup/) |
| 1 | DIR-01: Dictation intent routing + transcript enrichment pipeline | done | [phase-1-dictation-intent-routing](./phase-1-dictation-intent-routing/) |
| 2 | MIR-01: Meeting-side multi-intent routing + artifact synthesis | in-progress | [phase-2-multi-intent-routing](./phase-2-multi-intent-routing/) |

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
