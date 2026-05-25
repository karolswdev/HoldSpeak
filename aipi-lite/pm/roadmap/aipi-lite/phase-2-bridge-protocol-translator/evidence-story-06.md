# Evidence — AIPI-2-06 — Phase Exit + DoD + HoldSpeak Bridge Runbook

- **Shipped:** 2026-05-07 (runbook + systemd unit, partial); top-level README rewritten 2026-05-09; phase-exit close-out land at the same close-out commit that ships this evidence file.
- **Commit:** `105bb1a` (`feat(bridge): AIPI-2-06 partial — HOLDSPEAK_BRIDGE.md runbook + systemd unit`) + close-out commit pending on branch `mine`.
- **Owner:** karol

## Files touched

- `docs/HOLDSPEAK_BRIDGE.md` — new + revised. 8-section runbook: Architecture, Prerequisites, First-time setup, Voice typing, Recording a meeting, Daemonising, PSK rotation, Troubleshooting. AIPI-2-07 rewrote §5 to drop the "no-op stub" caveat and add the link-state legend + activity symbol map.
- `scripts/aipi-bridge.service` — new + revised. Systemd unit; supports system-wide and rootless installs; references `bridge.env` via working-dir; AIPI-2-08 dropped `ExecStartPre=--check` (made startup brittle on reboots where systemd-resolved isn't up yet) and switched the entry point to `python -m bridge` with `%h` paths.
- `README.md` — rewritten 2026-05-09: legacy STT/LLM/TTS narrative replaced with the new shape (thin forwarder onto HoldSpeak, three-zone LCD, `python -m bridge`). Quick-start, repo-layout table, project-status section, pointers to the canonical runbook. Acknowledgements section preserved.
- This file (`evidence-story-06.md`), the seven sibling `evidence-story-*.md`, `final-summary.md`, the phase-2 `current-phase-status.md` "frozen" state, and `pm/roadmap/aipi-lite/README.md` (phase 2 → done, current-phase pointer → phase 3) — all land in the close-out commit alongside this file.

## Verification artifacts

```
$ .venv/bin/python -m pytest -q
98 passed in 2.80s

$ .venv/bin/ruff check .
All checks passed!

$ .venv/bin/python -m bridge --help
usage: __main__.py [-h] [--check | --send-test-audio WAV | --audio-loopback]
```

Methodology compliance per `~/dev/HoldSpeak/pm/roadmap/roadmap-builder.md` §2.4 and §2.5:
- Each `story-{n}.md` has `Status: done` (close-out commit).
- Each story has a paired `evidence-story-{n}.md`.
- `final-summary.md` follows §2.5 sections: opened/closed dates, goal recap, exit-criteria final state with evidence links, stories shipped, surprises and lessons, handoff to phase 3, final asset/test posture.
- `current-phase-status.md` frozen — no further edits after this commit.

## Acceptance criteria — re-checked

- [x] `docs/HOLDSPEAK_BRIDGE.md` covers all eight numbered sections — file present, sections numbered.
- [x] `scripts/aipi-bridge.service` shipped — file present; system-wide + rootless install paths documented.
- [x] Top-level `README.md` describes new architecture; legacy narrative gone — verified by inspection (architecture diagram with one-way audio + bridge-as-forwarder + HoldSpeak-as-brain).
- [x] All AIPI-2-01..05 stories show `Status: done` with paired `evidence-story-{n}.md` files — landed in the close-out commit. (AIPI-2-07/08 stories also closed out; original story-06 acceptance bracket pre-dated those promotions.)
- [x] `final-summary.md` records what shipped, surprises, handoff to phase 3 — landed in close-out commit.
- [x] `pm/roadmap/aipi-lite/README.md` reflects phase 2 done + current-phase pointer → phase 3 — landed in close-out commit.

## Deviations from plan

- Test-plan §1 ("manual fresh-user simulation: stash `bridge.env`, read only the runbook, stand up the bridge from the docs, verify voice typing + meeting recording, note friction") **was not performed at phase close** — the user is not co-located with hardware on 2026-05-10 (Barnes & Noble). The runbook was rewritten (AIPI-2-07 §5 + AIPI-2-08 `python -m bridge` updates) but its fresh-user friction list is unverified. Tracked as a phase-level deferred item in `final-summary.md`.
- AIPI-2-07 + AIPI-2-08 were promoted into phase 2 after this story was originally written; the acceptance brackets in the story-06 file still reference "AIPI-2-01..05" rather than 01..08. Recorded for honesty.

## Follow-ups

- Fresh-user runbook walkthrough (test-plan §1) once hardware is back in reach.
- macOS launchd plist — explicitly deferred; systemd is the v1 supervised path.
- Docker image / pip package — defer until usage warrants it.
