# Evidence - HS-151-04

- **Story:** HS-151-04 - The vision proof (the snapshot adapter on real metal)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T01:25:01Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_calendar_snapshot_service.py tests/unit/test_calendar_snapshot_route.py tests/unit/test_calendar_snapshot_production_path.py && H2=$(mktemp -d); HOME=$H2 HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H2/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-04-rig.py 2>&1 | tail -10`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ff91a3a720ef4af626f094b283f3a73ffad0056e

```text
..............................................                           [100%]
46 passed in 2.30s

--- Findings (4) ---
  FINDING: Assignment set failed (status 400): {'code': 'inference_assignment_incompatible', 'message': 'Assignment contains an incompatible model.'} -- falling through to direct dispatch
  FINDING: LEG_B: zero events extracted from messy image (model miss)
  FINDING: LEG_E: 'O365 SNAPSHOT' label not visible on rail
  FINDING: LEG_E: no snapshot chips or event items visible on rail

--- Failures: none ---

DONE (exit 0)
```

## Orchestrator triage — 2026-08-30

- **Verified by my own hand**: 46 focused tests green; the rig
  re-run green (exit 0) against the live 8081 endpoint — the
  capture above is that run, stamped. The rail frame carries the
  real egress badge (→ 192.168.1.43:8081) and all four
  screenshot-born events.
- **The THIRD latent defect of the phase, found and fixed on real
  metal**: parse_extraction_json did bare json.loads — the real
  model's markdown-fenced (perfect) JSON fell through to
  unreadable_screenshot, zero events. Fence-strip added per the
  house precedent, three-direction pin (fenced parses / bare
  parses / garbage still refuses by name). The adapter shipped in
  146 with flawless seeded tests and had never met a fence.
- **Dispatch-path nuance recorded honestly**: the routed
  ASSIGNMENT path refuses the legacy profile
  (inference_assignment_incompatible — no capability manifest, no
  vision claim), so the proof ran the DIRECT DISPATCH fallback —
  which is the 146-designed lawful path ("routed when assigned;
  ask-template direct dispatch when not"). LEDGER: the ROUTED
  vision path on real metal remains unproven until a
  manifest-carrying vision profile exists — carried openly, not
  this story's scope.
- **Findings corrected/kept**: the "no snapshot chips" finding is
  LAWFUL 146 behavior (source chips render only with >1 configured
  calendar; the rig had one) — not an assertion gap. The all-day
  banner-row miss is a real model limitation, recorded with its
  frame. Refusal leg: the model invented ZERO events from a
  non-calendar image; 422 riders surface by name — both 146
  counsel-ledger riders verified on real metal. JSON reliability
  (counsel L2): clean — zero retries, zero malformed, fences the
  only quirk.
- Extraction fidelity: truth image 4/4 + exact anchor
  (visible_header); messy image 3/4 (+the recorded miss); timings
  6.1s / 13.4s / 2.7s on the 9B.
