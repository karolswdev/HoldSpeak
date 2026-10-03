# H-rig-clearof — Astra lane report

**RATIFIED by Muad'Dib; mechanical main integration authorized.**

LANE: PHILO Phase 13, H-rig-clearof (C1/11 handoff). Worktree `../wt-philo-13-rig-astra`; branch `feat/philo-13-rig-astra`; base `5912fcb9474cae7b058838f120a2c216189be89a`.

OUTCOME: partial. The rig and schema support `clear_of_by_viewport` and UI `then` steps after a restart. The actual replayed summary-retention case passes at 1440 and 393 (native touch). Arrival passes at 1440; at 393 it still fails an inherited C1 placement defect, below. No story flips done.

PROOF:

- Five new fences failed before the fix; the 125 shared checks passed. [Red output](assets/h-rig-clearof/red-valid.txt).
- 143 focused tests collected and passed, including `test_philo_graph_atlas.py`, `test_api_surface.py`, `test_philo_graph_reference.py`, the existing touch rig checks and the new viewport/schema checks. [Collection](assets/h-rig-clearof/collect-final.txt), [run](assets/h-rig-clearof/green-final.txt).
- All 12 Documentation Navigation commands passed. [Output](assets/h-rig-clearof/navigation.txt).
- Actual atlas observations, before/after shots and run verdicts: [index](assets/h-rig-clearof/runs.json), [SHA-256 manifest](assets/h-rig-clearof/manifest.json). The real hub restarts on the same isolated database; `summary_retained`, `receipt_retained` and `meeting_identity_retained` are true. The 393 trigger's follow-up clicks record `ui-touch`. The provider response is explicitly replayed; persistence and restart are real. No live engine or owner sitting is claimed.
- The viewport fence uses real DOM geometry and rejects an overlapping or missing required target. An undeclared viewport blocks. The 1440 clearance contract is unchanged; 393 requires summary and Dock clearance. The card must still render in its declared flow slot: no guard was waived.

LEDGER: (b, inherited on the named base) at 393, The week is open while Capture is unmounted. `ChairHome.tsx` puts `arrival-aftercare-slot` inside Capture; the arrival card therefore falls back to `ambient-aftercare-fixed`. The actual observation fails the missing-slot predicate and its Dismiss follow-up. Home: PHILO-13-11/C1 faces lane, also observed by the phone story. Tenets 3 and 6: the overlay covers work. Per-width clearance cannot repair the missing host. The base run and the post-fix touch run both retain this failure. No product/CSS file changed here.

AMENDMENTS: no acceptance waived. Summary retention is checked after explicitly reopening The week at 393. Automatic open-window return remains B2/story 07 and is not proved by that case. Old atlas source anchors moved with the rig functions and the generated graph is refreshed in this commit. Node 25 fails to load its installed llhttp library; verification uses the already installed Node 22.21.0. Scratch HOME directories are cleaned by their owners; the owner's DB/keychain/microphone were not used. No full suite ran, per the dispatch.

UNKNOWN: the unreplayed real-engine restart case, the missing Capture host at 393 (C7) and the owner's sitting. Tuesday: the saved summary survives restart; the phone arrival overlay remains a face-lane defect.

## Muad'Dib check and integration — 2026-10-03

[Single-pass check](https://github.com/karolswdev/HoldSpeak/pull/737#issuecomment-5965265632): **RATIFY**. Muad'Dib rehomes the remaining phone arrival failure to PHILO-13-17/C7: arrival opens Capture, where the card lives. The strict placement guard stays.

[Mechanical instruction](https://github.com/karolswdev/HoldSpeak/pull/737#issuecomment-5965266992): "Rebase/merge main in (pre-authorized, mechanical), re-run the shared atlas/graph-reference checks, then merge — RATIFY stands."

Main `65b0025abd0fd5c9d7189f78ce4770efc6605f29` is integrated without changing the ratified rig behavior. Both status entries are retained; the graph output is regenerated. The stories already delivered on main travel with the merge; no new story closure is claimed. Integration proof: [collection](assets/h-rig-clearof/integration-collection.txt), [captured tests](assets/h-rig-clearof/integration-captured.md), [all 12 Documentation Navigation commands](assets/h-rig-clearof/integration-navigation.txt).
