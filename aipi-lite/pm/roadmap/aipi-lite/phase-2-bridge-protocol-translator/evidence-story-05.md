# Evidence — AIPI-2-05 — Meeting-Mode Integration Verification

- **Shipped:** 2026-05-08 (verified live alongside AIPI-2-02's UDP fix)
- **Commit:** verified against `9ff88a6` (no bridge code change for this story; the audio channel is identical to voice typing). Documentation deliverable shipped in `105bb1a` (runbook §5).
- **Owner:** karol

## Files touched

This story is **bridge-side a no-op** — HoldSpeak's `MeetingSession.attach_device` routes audio from the same `/api/devices/audio` channel into the active meeting buffer. No code change required in the bridge.

- `docs/HOLDSPEAK_BRIDGE.md` §5 — "Recording a meeting with the device" section: HoldSpeak start (web UI + `curl POST /api/meeting/start {"devices":["aipi-1"]}`), what the LCD shows during a meeting (post-AIPI-2-07: link state + activity status frames; pre-07: just the firmware mode label), the no-op attached-device button semantics, and per-device-labeled transcript output.

## Verification artifacts

**Live HoldSpeak verification (2026-05-08, alongside AIPI-2-02's UDP fix):**

- `POST /api/meeting/start {"devices":["aipi-1"]}` against the running HoldSpeak instance — meeting started, `MeetingState.devices` accepted the device descriptor (transcripts subsequently arrived tagged with the device's identity, which only happens if attach succeeded).
- Speech captured via the device's mic during the meeting → audio streamed continuously through the bridge → meeting transcript page showed per-segment entries tagged with the configured `DEVICE_LABEL`.
- Per-source attribution `[Karol]` / `[Me]` / `[Remote]` resolved correctly when multiple sources participated in the same meeting.
- Pressing the right button while the meeting was active: server-side no-op as designed (HoldSpeak's voice-typing arbiter doesn't reclaim the channel from a meeting-owning recorder); audio kept flowing into the meeting buffer; no `session_busy` returned.

```
$ .venv/bin/python -m pytest -q
98 passed in 2.80s
```

## Acceptance criteria — re-checked

- [x] Meeting started with `devices:["aipi-1"]`: verified live 2026-05-08.
- [x] Transcript segments tagged with the device label: verified live 2026-05-08.
- [~] Ending the meeting triggers HoldSpeak's intel pipeline: not explicitly captured in the 2026-05-08 trace (intel runs deferred-cloud or local depending on HoldSpeak config; the trace recorded transcripts but not topic/action-item population). **Pending an explicit intel-pipeline observation** — tracked as a phase-final-summary deferred item but not blocking.
- [x] Right-button press during active meeting → server-side no-op, no audio disruption: verified live 2026-05-08.
- [x] Audio-path stability through the meeting: verified live 2026-05-08 (no metrics-counter dropouts noted; meeting completed cleanly).
- [x] Runbook §5 shipped — file present in `docs/HOLDSPEAK_BRIDGE.md`.

## Deviations from plan

- Intel-pipeline output verification (topics / action items / summary) wasn't explicitly captured in the 2026-05-08 trace. Transcripts confirmed; intel deferred. Treated as evidence-thin rather than failed.
- LCD-during-meeting visibility was originally listed in this story's notes as "today: nothing — HS-14-07 follow-up." That follow-up shipped in AIPI-2-07 within phase 2; the meeting-LCD experience is now bridge-painted (status frames → activity slot). **Live LCD-during-meeting smoke deferred** to the phase final-summary's open list.

## Follow-ups

- One explicit intel-pipeline observation (topic / action item / summary populated for a device-driven meeting transcript) — phase final-summary lists it as low-priority.
- Multi-device meeting (two AIPI-Lites in one meeting) — explicitly out of phase 2 scope; HoldSpeak supports it server-side; would land as a phase-3 or phase-4 verification.
