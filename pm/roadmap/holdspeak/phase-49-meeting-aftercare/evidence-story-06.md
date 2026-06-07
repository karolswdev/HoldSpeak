# Evidence — HS-49-06: Closeout (before/after + dogfood + PR)

Write-once record of the verified exit. The phase result: a meeting closes its own
loops, proven end to end without a mic or LLM, captured as before/after, with the
full suite green and the PR merged.

## Before / after

- `screenshots/story-06-before-artifact-only.png` — a meeting with a risk_register
  artifact and nothing open / decided / changed: the aftercare digest is empty so
  the panel does not render. This is the pre-Phase-49 experience (read an artifact,
  go do the work elsewhere).
- `screenshots/story-06-after-aftercare.png` — a meeting with open items, decisions,
  and a since-last diff: the "Your next move" panel sits above the artifacts.
- Captured by `scripts/screenshot_aftercare_before_after.py` (boots the real
  `MeetingWebServer` over a seeded temp DB, no mic/LLM). The per-story captures
  (`story-01`..`story-04`) cover each surface in detail.

## Dogfood (green, no mic / no LLM)

`scripts/dogfood_meeting_aftercare.py` -> `dogfood-transcript.txt`. It drives the
real HTTP endpoints + the real `ActuatorExecutor` (a stub connector stands in for
`gh`) over a seeded temp DB:

1. seed a prior + a current meeting (decisions + action items);
2. aftercare digest: still open by owner (Priya 1, Unassigned 1), decided (2), and
   the real since-last diff (new decision "Adopt feature flags", closed "Stand up
   the staging cluster");
3. provenance: "Wire the rate limiter" (source 72.0s) resolves to segment #1;
4. accept the action, file it -> a `proposed` GitHub-issue proposal (recorded only);
5. the guard: a proposed proposal is refused by the executor (no connector call);
   approve -> execute via the stub connector -> issue #12; audit
   `proposed -> approved -> executed`;
6. the local follow-up draft (decisions + open items by owner + since-last delta).

It asserts each step and prints `PASS`. Nothing ran without approval; the draft
sent nothing.

## Suite + build

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` -> **2426 passed, 17 skipped**
  (skips are pre-existing opt-in / missing-fixture / missing-model, not regressions).
- `(cd web && npm run build)` clean (12 pages); `git ls-files
  holdspeak/static/_built` -> empty (0 tracked; source-only).

## Cadence + closeout

- `final-summary.md` written.
- story-06 + the phase status flipped to **CLOSED (6/6)**; the story-status table
  row + "Where we are" + Last-updated updated.
- the project `README.md` phase row + Current-phase + Last-updated updated.
- `BACKLOG.md` candidate A flipped from "scaffolded" to "shipped (CLOSED 6/6)".
- one PR for the phase opened to `main`, merged with a merge commit on green CI
  (Unit, Integration macOS, E2E macOS, Linux Smoke, Route screenshots).

## Invariants held (whole phase)

Read-only aggregation + the existing actuator path + a local draft. Capture,
plugin runs, and synthesis are byte-identical; actuators stay off by default.
Nothing leaves the machine and nothing changes state without explicit per-action
human approval; every open/decided/changed claim is real; provenance shows only
where a real timestamp exists.
