# HS-41-01 — Runtime activity contract + state mapping

- **Project:** holdspeak
- **Phase:** 41
- **Status:** done (2026-06-05)
- **Depends on:** none
- **Unblocks:** HS-41-02, HS-41-03
- **Owner:** unassigned
- **Evidence:** [evidence-story-01.md](./evidence-story-01.md)

## Problem

Presence (web + desktop) needs **one** normalized notion of "what the runtime is
doing" so every surface renders the same state. Without it, each surface invents
its own vocabulary.

## Scope

- In:
  - `holdspeak/runtime_activity.py` (ported from the codex spike, no GUI deps):
    `VALID_ACTIVITY_STATES`, `normalize_activity_state`, `RuntimeActivity`
    (dataclass → `to_dict`), `RuntimeActivityTracker` (snapshot/update with a
    started-at-preserving update), and `desktop_window_policy(state)` (the
    transient hidden/active/linger visibility policy).
  - Unit tests covering normalize, the tracker's update/started-at semantics,
    and the window policy per state.
- Out:
  - Any renderer, the websocket broadcast, the `web_runtime` wiring (HS-41-02).
  - Native deps.

## Acceptance criteria

- [x] `runtime_activity.py` exists with the contract + tracker + window policy;
      pure (no GUI imports).
- [x] Unit tests pass; the default suite gains the tests with no new deps.
- [x] States cover the dictation + meeting lifecycle (listening/recording/
      transcribing/processing/typing/complete/meeting_live/saving/error/idle).

## Test plan

- Unit: `tests/unit/test_runtime_activity.py`.
- Full: `.venv/bin/python -m pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes

- Salvaged from codex PR #17 verbatim (it was clean); the Tk renderer in that PR
  is **not** ported.
