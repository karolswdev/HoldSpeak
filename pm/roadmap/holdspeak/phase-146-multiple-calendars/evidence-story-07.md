# Evidence - HS-146-07

- **Story:** HS-146-07 - The Calendar Snapshot adapter
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-28T23:50:21Z

- **Command:** `zsh -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_calendar_snapshot_service.py tests/unit/test_calendar_snapshot_route.py tests/unit/test_calendar_snapshot_production_path.py tests/unit/test_api_surface.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bcd033bff3d7ed369429434ac0631d8112d4ed2e

```text
........................................................                 [100%]
56 passed in 18.14s
```

## Orchestrator triage note

Captured: the snapshot service (23 — schema validation, the ICS
round-trip through the REAL bounded parser, anchor resolution incl.
the absent-anchor confirm block, registration reuse, refusals, atomic
lifecycle), the routes (8 — caps, ≤3 files, refusal passthrough,
confirm), the PRODUCTION-PATH proof (2 — an engine-factory-level fake
shows a dispatch travel admission → runner → VisionPromptAdapter →
multi-part content → parsed events; and a missing vision model
returns `no_vision_model_assigned`, never laundered into an
image-quality claim), the api-surface manifest guard green at 540
routes (538+2, regen shipped), and both censuses.

**The build took two rounds.** Round 1 left the production extraction
a stub (a real drop would refuse as "unreadable" because nothing
dispatched) — the orchestrator refused the flip and mandated the
wiring; round 2 followed the ask-service template (routed dispatch
when a `calendar.snapshot_extract` assignment exists; direct
runner dispatch with deployment-revision capture when not; egress
truth derived from the resolved path). The e2e stays on the route
seam by ruled necessity (the lightweight e2e hub lacks the full
assignment infrastructure); the production proof lives in the unit
rig at the engine-factory level.

**The guard chain forced three deliberate registrations** (all in
this commit, none silent): the routing census caught the new
`resolve_placement` caller (registered as an HS-146-07 adopter);
the one-path census stash-compare caught `run_prompt_messages` as an
unregistered model-execution leaf (admitted, pinned count 102→103);
the capability census demanded the same leaf + the new
`InferenceRunner.invoke` entrance carry a capability and source
owner (registered with `calendar.snapshot_extract`).

**Checkpoint sweep** (readable log `sweep_hs146_checkpoint.log`,
covering stories 03+04+07): 16 failed / 6790 passed — 11
baseline-exact; capability census ×3 = the registrations above (4
entries were pure engine line drift); `test_door_routes` golden dict
predated story 04's source_id/source_label projection (class a,
updated); `test_refinement_coordinator` = the known flake family,
serial ×2 green. **Zero branch-new product defects.**

**Glass** (orchestrator shot rig, `assets/story-07-shots/`, all
eyeballed): the review window with the prefilled editable WEEK
ANCHOR + two editable event rows (mics throughout) at 1440 and 393;
the confirmed state; and the rail showing Team sync [WORK] beside
Glass Standup/Review [O365 SNAPSHOT] with absolute dates — the whole
screenshot→review→.ics→parser→rail chain real on glass. One rig
honesty note: the first review shot photographed the lazy-load beat
and was retaken against real content.
