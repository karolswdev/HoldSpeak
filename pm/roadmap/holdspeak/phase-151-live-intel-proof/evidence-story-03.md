# Evidence - HS-151-03

- **Story:** HS-151-03 - The headless metal proof (control vs treatment)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-30T02:56:59Z

- **Command:** `bash -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_meeting_deferred_admission.py tests/unit/test_meeting_import.py tests/unit/test_intel_queue.py && H2=$(mktemp -d); HOME=$H2 HOLDSPEAK_PEOPLE_KEYSTORE_FILE=$H2/pk.json PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright uv run --python 3.13.11 python pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-03-rig.py 2>&1 | tail -12`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 731a4aecb0c1077b7f4211dcd8e7eebffc8d201b

```text
..............................................................           [100%]
62 passed in 19.35s
  intel_status: disabled
  action_items: 0, intel_snapshots: 0
  Board cards: 0
  Brief person_sections: 0
  Frame: control-board-empty-1440.png

============================================================
SUMMARY
============================================================
  ALL ASSERTIONS PASSED

Done file: /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-151-live-intel-proof/assets/story-03-done.json
```

## Orchestrator triage — 2026-08-30

- **THE LOOP IS REAL.** The stamped capture above is my own re-run:
  real WAV → real mlx-whisper (~10 s) → the REAL import door → the
  production intel queue with the counsel-ruled skip → the REAL
  pinned resident server (8080, the story-01 override proving
  itself in production conditions) → real action items
  (review_state=pending, UNASSIGNED lane) → the REAL triage + map
  gestures → chip + staleness → the brief's People section.
  Extraction wall-clock ~8 s on the 35B. Control leg: same WAV,
  intel disabled — zero rows, empty board, empty People. sync/push
  appears NOWHERE (grep-verified in both runs).
- **The messy-reality record (the risk register's ask)**: the
  ground-truth script names Priya/Wei/Jordan, but the
  TTS-synthesized WAV transcribed to "CREO" as the audible name —
  and the model GROUNDED HONESTLY in what it heard: owners
  ["CREO","Me","Me","Me"] (builder run) vs ["CREO","CREO","Me","Me"]
  (my run) — real nondeterminism across runs, "break glass"
  transcribed "brake glass". Every owner passed the M5
  case-insensitive substring groundedness check; zero ungrounded
  findings. This is exactly why the assertions are shape-grounded.
- **Two more product fixes shipped in this story, counsel-ruled or
  precedent-clean**: (1) TranscriptionAdmission.loaded_artifact_
  reusable (defect #4 — multi-window audio import broken in
  production; verified by my own 62-test run); (2) the Design-A
  claim fix (defect #5): _plan_installed_plugin_members probes
  plugin-capability assignments via the binder's own resolution and
  excludes unassignable meeting.plugin.* members WITH the
  plugin_chain_skipped receipt; core capabilities stay terminal;
  the binder stays strict; all five counsel pins implemented; 53
  deferred-admission/queue tests green.
- **New ledger entries**: the wire-script cross-process DB
  visibility oddity (worked around in-process; needs a crisp
  repro); DeploymentRevision.from_artifact hardcodes
  kind="this_device" for remote endpoints (defect #6, recorded);
  disabled_plugins remains dispatch-only (to the close counsel with
  the Design-A record).
