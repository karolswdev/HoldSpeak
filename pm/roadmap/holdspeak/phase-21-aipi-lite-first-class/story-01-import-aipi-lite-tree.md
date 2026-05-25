# HS-21-01 — Import AIPI-Lite Tree

- **Project:** holdspeak
- **Phase:** 21
- **Status:** done
- **Depends on:** HS-20 phase close
- **Unblocks:** HS-21-02
- **Owner:** unassigned

## Problem

AIPI-Lite firmware and bridge work lived in a sibling checkout, while
HoldSpeak runtime and protocol work lived here. That split made companion UX
planning harder because changes that cross firmware, bridge, and server code
were not visible in one repo.

## Scope

### In

- Copy the AIPI-Lite firmware/bridge working tree into `aipi-lite/`.
- Keep local config files available on disk but ignored by Git.
- Exclude VCS metadata, virtualenvs, ESPHome build output, and caches.
- Document import provenance.
- Update HoldSpeak README and roadmap to treat AIPI-Lite as first-class.

### Out

- Squashing or rewriting the AIPI source.
- Live firmware flashing.
- Bridge packaging changes.
- New HoldSpeak protocol behavior.

## Acceptance Criteria

- [x] `aipi-lite/aipi.yaml` exists.
- [x] `aipi-lite/bridge/` exists.
- [x] `aipi-lite/secrets.yaml` exists locally but is ignored.
- [x] `aipi-lite/bridge.env` exists locally but is ignored.
- [x] Import provenance is recorded in `aipi-lite/IMPORT.md`.
- [x] HoldSpeak roadmap marks Phase 21 as current/in-progress.

## Test Plan

- Verify ignored secret/config files with `git check-ignore`.
- Verify imported source is visible under `aipi-lite/`.
- Run `git diff --check`.

## Notes

- This import intentionally includes the source checkout's dirty source changes
  and untracked non-secret assets. It does not include `.git`, `.venv`,
  `.esphome`, cache folders, or coverage output.
