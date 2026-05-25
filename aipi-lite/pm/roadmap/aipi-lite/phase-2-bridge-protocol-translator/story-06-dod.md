# AIPI-2-06 - Phase Exit + DoD + HoldSpeak Bridge Runbook

- **Project:** aipi-lite
- **Phase:** 2
- **Status:** done
- **Depends on:** AIPI-2-01, AIPI-2-02, AIPI-2-03, AIPI-2-04, AIPI-2-05
- **Unblocks:** AIPI-3
- **Owner:** karol

## Problem

Close phase 2: ship the user-facing runbook so a fresh user (or
future-you in three months) can stand up a HoldSpeak satellite from
clone → working voice typing → meeting recording in under ten
minutes.

## Scope

### In

- `docs/HOLDSPEAK_BRIDGE.md` covering, in order:
  1. **Architecture overview** — one paragraph + a diagram (ASCII or
     mermaid) showing device → bridge → HoldSpeak. Reference
     `~/dev/HoldSpeak/docs/DEVICE_PROTOCOL.md` as the canonical
     wire contract — do NOT duplicate field schemas in this runbook.
  2. **Prerequisites** — running HoldSpeak instance (link to its
     install docs), a flashed AIPI-Lite (link to
     `docs/PROVISIONING.md`), Python 3.10+.
  3. **First-time setup** — clone, `pip install -r requirements.txt`,
     `cp bridge.env.example bridge.env`, fill in fields, run
     `python3 bridge.py --check`, then run for real.
  4. **Voice typing** — press the right button, speak, release;
     where the text appears (the focused app on the HoldSpeak host).
  5. **Recording a meeting with the device** — `POST /api/meeting/start`
     payload, what HoldSpeak does, where the transcript lands, what
     the LCD shows during a meeting (today: nothing; future:
     HS-14-07 work).
  6. **Daemonising** — systemd unit example (ship it as
     `scripts/aipi-bridge.service`), `journalctl` for logs.
  7. **PSK rotation** — `holdspeak device-psk rotate` → update
     `bridge.env` → restart bridge.
  8. **Troubleshooting** — handshake fails (4001/4003/4009), audio
     not flowing, reconnect loops, etc.
- Top-level `README.md` rewritten:
  - Drop the "Brain (Middleman & Backend)" + faster-whisper / DeepSeek /
    gTTS narrative — that's legacy.
  - New shape: AIPI-Lite is a HoldSpeak satellite; bridge is a thin
    forwarder; HoldSpeak owns the brain. Link to
    `docs/HOLDSPEAK_BRIDGE.md` and `docs/PROVISIONING.md`.
  - Acknowledgements section preserved (Robert Lipe, sticks918) +
    HoldSpeak added.
- `pm/roadmap/aipi-lite/README.md`: phase 2 status flips to `done`,
  phase 3 row stays `not-started`, `Last updated` bumped, `Current
  phase` pointer moves to phase 3.
- `phase-2-bridge-protocol-translator/final-summary.md` per
  `roadmap-builder.md` §2.5: goal recap, exit criteria final state
  with evidence links, story table, surprises + lessons, handoff to
  AIPI-3.
- All AIPI-2-01..05 stories show `Status: done` with paired
  `evidence-story-{n}.md` files.
- `current-phase-status.md` frozen — no further edits after phase
  close.
- A `scripts/aipi-bridge.service` systemd unit example.

### Out

- AIPI-3 work (cross-network transport). That phase opens after
  this DoD lands.
- Web onboarding / GUI configuration — `docs/HOLDSPEAK_BRIDGE.md`
  is the canonical source.
- macOS `launchd` plist — runbook mentions it as a follow-up;
  systemd is enough for v1.
- Docker image / pip package distribution — defer until usage
  warrants it.

## Acceptance Criteria

- [x] `docs/HOLDSPEAK_BRIDGE.md` exists, covers all eight
  numbered sections (architecture, prerequisites, first-time
  setup, voice typing, meeting recording, daemonising, PSK
  rotation, troubleshooting). Shipped 2026-05-07.
  Fresh-user-walkthrough verification is pending live HoldSpeak.
- [x] `scripts/aipi-bridge.service` systemd unit shipped 2026-05-07.
  Supports both system-wide and rootless installs; references
  `bridge.env` via the working-dir; ships `--check` as
  `ExecStartPre` for fast-fail on misconfiguration.
- [ ] Top-level `README.md` describes the new architecture; the
  legacy STT/LLM/TTS narrative is gone or moved to an appendix.
  **Pending phase exit.**
- [ ] All AIPI-2-01..05 stories show `Status: done` with paired
  `evidence-story-{n}.md` files.
  **Pending hardware verification of stories 01..05** —
  inline evidence is in each story file's acceptance brackets;
  evidence-story-{n}.md files are created at story-close per
  the `roadmap-builder.md` contract (created when a story
  actually ships, never before).
- [ ] `final-summary.md` records what shipped + what surprised
  us + handoff notes for AIPI-3 (cross-network transport).
  **Pending phase exit.** Per the contract,
  `final-summary.md` is created on phase exit and is immutable
  afterwards.
- [ ] `pm/roadmap/aipi-lite/README.md` reflects phase 2 done +
  phase 3 not-started; `Current phase` pointer moves to phase 3.
  **Pending phase exit.**

## Test Plan

- **Manual fresh-user simulation:**
  1. Stash the local `bridge.env`.
  2. Read only `docs/HOLDSPEAK_BRIDGE.md`.
  3. Stand up the bridge from the docs.
  4. Verify voice typing works.
  5. Verify meeting recording works.
  6. Note any friction; fix in the runbook or record in
     `final-summary.md` as a known sharp edge.
- **Methodology compliance:**
  - Verify each story-{n}.md has a status of `done` and a paired
    `evidence-story-{n}.md` file.
  - Verify `final-summary.md` follows
    `~/dev/HoldSpeak/pm/roadmap/roadmap-builder.md` §2.5 sections.

## Notes

- **Reuse the AIPI-1-06 runbook layout** (TL;DR table, numbered
  sections, troubleshooting cheatsheet). It worked cleanly for
  provisioning.
- **Acknowledge what's NOT in scope** in the runbook — specifically
  that the LCD doesn't show meeting state yet (HS-14-07 work).
  Setting expectations matters more than papering over the gap.
- **Handoff to AIPI-3** in `final-summary.md` should name what
  contracts AIPI-2 baked in: WS protocol version, frame schema,
  PSK auth, reconnect cadence. AIPI-3 (cross-network) extends the
  transport, not the protocol; calling out the seam matters.
- **LCD-pushback follow-up:** the bridge ships a no-op
  inbound-`status`-frame handler in story-01. HS-14-07 *has*
  shipped, so the substrate is available; promoting the no-op to
  a real handler that calls ESPHome's `update_screen` service is
  a small follow-up (a dedicated AIPI-2-followup story, or the
  kickoff of AIPI-3). Final-summary should explicitly tee this
  up — including the LCD UX decisions deferred (ttl handling,
  conflict with the existing mode label, behaviour during a
  meeting vs. voice typing).
- **Bookmark-gesture follow-up:** HS-14-07's server-side
  `MeetingSession.add_bookmark` hook is dormant in phase 2 — no
  device gesture is wired to emit `{"type":"event","name":"long_press"}`.
  Final-summary should call out the candidate gesture (a
  left-button quick-tap during a meeting feels natural) so the
  follow-up has a starting point.
