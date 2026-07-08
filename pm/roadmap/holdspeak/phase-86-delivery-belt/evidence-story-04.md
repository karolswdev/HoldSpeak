# Evidence — HS-86-04 — The conveyor completes: station lights + evidence in place

- **Shipped:** 2026-07-07
- **Commit:** (this commit)
- **Owner:** agent (Claude), owner-directed

## Files touched

- `holdspeak/missioncontrol_bridge.py` — `story_evidence_payload`:
  the evidence path comes from the repo's own CLI (`dw context
  <project> --compact`, `evidence_path`), the read contained to
  `<repo>/pm/roadmap/**/*.md`, typed refusals/absence, 200 KB cap.
- `holdspeak/web/routes/missioncontrol.py` — `GET
  /api/missioncontrol/evidence` (to_thread, GET-only).
- `web/src/desk/missioncontrol.ts` — receipts on the poll
  (`mergeReceipts`, `ciLight` worst-conclusion: fail > pending >
  pass; zero checks is "none", never fake green), `gateLightFor`
  (newest gate event speaks; refusals carry their rule verbatim),
  `isBeltFrame`, evidence open/close store actions.
- `web/src/desk/components/MissionControlConveyor.tsx` — the
  repo-lane head with `StationLights` (PR link + count, CI dot,
  gate pass/refusal chip), the evidence `✓` on story chips opening
  `EvidencePanel` in place (pull-out inside the conveyor, no
  modal, no route away), `hs-broadcast` listener refreshing on
  `scope:"belt"` frames (poll stays the fallback).
- `web/src/desk/desk.css` — Signal-token styles for lights + panel.
- `tests/unit/test_web_routes_missioncontrol.py` — 7 evidence-route
  cases (happy path, traversal/absolute/non-md/unknown-repo
  refusals, absent file, GET-only).
- `web/src/desk/__tests__/missioncontrol.test.ts` — ciLight,
  mergeReceipts (typed absence stays typed), gateLightFor,
  isBeltFrame.
- `scripts/screenshot_hs86_conveyor.py` — the live proof (real map,
  real rails, real gh, zero seeding).
- `docs/api-surface.json` / `docs/API_SURFACE.md` regenerated after
  the web call sites landed (the consumer rule).

## Verification artifacts

```text
$ uv run pytest -q tests/unit/test_web_routes_missioncontrol.py \
    tests/unit/test_desk_locks.py tests/unit/test_api_surface.py
39 passed in 1.08s
$ (cd web && npm run test:desk)
Tests  63 passed (63)
$ (cd web && npm run build)
17 page(s) built — clean
```

Live screenshots (real project map: holdspeak + delivery-workbench;
no seeded data), committed under `./screenshots/`:

- `hs-86-04-conveyor-lanes-and-lights.png` — both lanes: holdspeak's
  86 phase segments with 86 current-boxed and HS-86-01…03 done
  chips, holdspeak-mobile's 25, work-log-automation's 16; the
  delivery-workbench lane's gate light wearing a REAL
  `✕ contract-missing` refusal from that repo's own rail log; the
  holdspeak gate light green off its newest gate_pass; live agent
  sessions honestly shelved (off rails / ambiguous); the real event
  ticker.
- `hs-86-04-evidence-in-place.png` — HS-86-01's real evidence file
  open inside the conveyor (path header + monospace body), no
  modal; the script asserts the body carries the real `dw check`
  text.
- `hs-86-04-gate-refusal-chip.png` — the refusal chip state.

PR/CI lights: both repos currently have zero open PRs, so the PR and
CI lights are honestly absent in the shots (the light logic is
pinned by the vitest cases; a lit state is captured in HS-86-05's
walk when its PR opens).

```text
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
3312 passed, 37 skipped in 257.87s (0:04:17)
```

## Acceptance criteria — re-checked

- [x] Screenshots show the lanes, lights, a real refusal chip, and
      evidence open in place — above. (PR/CI lit-state: deferred to
      the HS-86-05 walk where a PR actually exists; the derivation
      is test-pinned.)
- [x] The file route refuses traversal/absolute/non-md/non-map —
      `TestEvidenceInPlace`.
- [x] Belt-frame → refresh: the predicate is test-pinned; the
      handler is five audited lines; the live proof rides the
      HS-86-05 walk (as the story's own AC provides).
- [x] Desk locks green; page tests green; build clean; api-surface
      guard green.
- [x] Full suite green — the line above, read from the output file
      after completion.

## Deviations from plan

The story's "hover-free labels" for PRs landed as a title-attribute
list plus the always-visible count — the count is the glanceable
signal; titles stay one hover away without widening the lane.

## Follow-ups

None — the walk (HS-86-05) closes the phase.
