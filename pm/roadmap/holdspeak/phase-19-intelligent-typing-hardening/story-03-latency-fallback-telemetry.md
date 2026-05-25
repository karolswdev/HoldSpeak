# HS-19-03 — Dictation Latency and Fallback Telemetry

- **Project:** holdspeak
- **Phase:** 19
- **Status:** done
- **Depends on:** HS-18-03
- **Unblocks:** —
- **Owner:** unassigned

## Problem

Intelligent typing only works if users trust its latency and fallback behavior. The web cockpit should show when a stage rewrote text, skipped work, timed out, or preserved the transcript.

## Scope

### In

- Per-stage latency and reason metadata surfaced in readiness/dry-run.
- Fallback reason summaries for runtime unavailable, timeout, malformed output, no context, and no suggestion.
- Lightweight counters for recent local session behavior.

### Out

- Hosted analytics.
- Long-term telemetry storage.

## Acceptance Criteria

- [x] Dry-run shows stage latency/reason/fallback state clearly.
- [x] Readiness shows recent p50/p95 or session counters where available.
- [x] Tests cover fallback metadata shape.

## Test Plan

- Unit tests for metadata/counter helpers.
- Integration tests for dry-run payload.
- Web build.
