# HSM-21-02 — The Swift banned-copy + reassurance-prose guard

- **Project:** holdspeak-mobile
- **Phase:** 21
- **Status:** todo
- **Depends on:** 21-01 (the badge grammar the fixed labels adopt);
  `tests/unit/test_doc_drift_guard.py` (the guard this extends).
- **Unblocks:** banned names and privacy prose cannot reappear on Apple surfaces.
- **Owner:** unassigned

## Problem

The guard scans docs + `web/src/**/*.astro` (Wave 1) but not Swift. ~6 label sites still
say "on-device · nothing leaves" (`LocalHarnessApp.swift:253`,
`SpeakHarnessApp.swift:272`, `InferenceHarnessApp.swift:69`, `ReviewModel.swift:31`,
`MeetingCapture.swift:90`) and `DeskHome.swift:318` carries a full reassurance sentence
("… nothing leaves.") — the exact prose POSITIONING §140-143 bans: the badge IS the
privacy statement.

## The design

1. **Fix the sites:** the `egressLabel` strings and harness labels adopt the badge
   grammar ("on device"); the DeskHome snippet drops its ", nothing leaves." tail
   (the no-prose rule: labels, not manuals).
2. **Extend the guard:** `_swift_user_facing()` sweeps `apple/App/**/*.swift` +
   `apple/Sources/**/*.swift` for (a) the banned feature names, (b) the
   reassurance-prose pattern (`nothing leaves` / `never leaves` / `stays on this|your`)
   inside string literals. Red-prove with a seeded violation test (the existing
   `test_voice_guard_patterns_catch_seeded_violations` pattern).
3. **Careful scoping:** the Qlippy doc test REQUIRES "nothing leaves" verbatim in its
   doc (`test_doc_drift_guard.py:221-235`) — the Swift ban must not touch docs; code
   comments are exempt (string literals only, best-effort line heuristic is fine if
   red-proven).

## Scope

- **In:** the 6 label fixes; the Swift scan + seeded red-proof; guard green.
- **Out:** web/docs scanning (shipped); renaming `docs/INTELLIGENT_TYPING_GUIDE.md`
  (the known Wave-1 carve-out, still owner-gated).

## Test plan

- `uv run pytest -q tests/unit/test_doc_drift_guard.py` (new tests included, one seeded
  red-proof).
- `swift test` + both app sim builds green after the label changes.
