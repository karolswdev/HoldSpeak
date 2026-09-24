# Muad'Dib handover XXV — 2026-09-23, Phase 3 closed, Phase 4 The Morning chartered, the canvas at the owner's door

Read with `docs/internal/TWO-BRAINS.md`, `pm/roadmap/holdspeak-philo/README.md`, `pm/roadmap/holdspeak-philo/phase-4-the-morning/current-phase-status.md`, `pm/roadmap/holdspeak-philo/phase-3-the-meeting-loop/final-summary.md`.

## Where the tree is

- **Phase 3 The Meeting Loop: CLOSED by ruling** ("yes close and open") at `f40f7dad` (#619). A2 #616 merged after two Muad'Dib counsels; the closure chain ran on the rig at 1440/393 against the real LAN engine (24 retained runs, `phase-3-the-meeting-loop/assets/closure/`): steps 1–4 PASS; step 5 needs a detour (no Generate while yesterday's rows are untriaged; the decision behind the fold). Exit 1 open, linked forward to Phase 4; exit 3 = HIS SITTING, open. Usefulness partial over all 22 summaries (ASR is the bottleneck). A real crash found: a failure item selected into a second brief reuses its id → 500.
- **Phase 4 The Morning: CHARTERED, UNRATIFIED** (#620 `ab5870a7`; Astra's charter check paid). Stories: 01 Generate always reachable (Muad'Dib, canvas first), 02 the new decision in the visible rows (Astra; order + a real `created_at` source; the three-row cap is Phase 170 code, kept), 03 breakage ids never collide (Muad'Dib; brief-scoped ids, no OR IGNORE/REPLACE), 04 the triaged headline (Astra; from the canvas r3 finding). Estimate 2.5–4 days, critical path 2–3.
- **Story 01's canvas: PR #621 (`91df83b0`, MERGED as unratified at `cac98e7d`), six rounds with Astra** (r1 BOUNCE: 10 px heading/badge; r2 conditions; r3 library BOUNCE: global chip ellipsis; r4 library RATIFY, canvas conditions; r5/r6 paid). Artifact: https://claude.ai/artifact/LHjuHKL1pVZuh4aK5J9qRU (16 boards × 2 widths + 3 library probes). The library changes ride with it: section head label and chip 10→12 px (every section head/chip on the desk), head verbs no-shrink, label containment, chip truncation scoped to the Jira/Confluence host chips, EgressChip tooltip = its label; 24 healed floor allowances removed (HS-202-05 run once, green). The 71+1 remaining under-12 px lines are LEDGERED in the canvas README.
- **Phase 5 The One Service Layer: PARKED DRAFT r2** (`PHASE-5-CHARTER-DRAFT.md`), seeded by the owner's ruling "things have to flow through services" (memory `feedback_mcp_flows_through_services`); Astra r1 BOUNCE mostly paid, carried conditions in §12. Not chartered.
- **Tree laws today:** #618 ended the evidence-restoration chore (`tests/_evidence.py`; `HOLDSPEAK_EVIDENCE_WRITE=1` on the command under `dw evidence capture`); the lane law: never a serial full suite in a lane, CI runs it; main's 44 CI failures at `497d90f3` are inherited (27 = rig calibration browser launch on the Unit runner; 4 = A4 receipt lines vs HS-201-12 fence, ledgered).

## The owner's asks on the canvas (his ruling opens the build)

1. Placement: `Generate` in the BRIEF head after `THIS DEVICE`, every state, disabled only while a read/generation is open. 2. Cap kept at three; decisions first, newest by `created_at`. 3. Arrival only. 4. The 12 px library floor (paid; the head label wraps at 393 on a populated brief). 5. Empty brief: `No changes` vs today's sentence. 6. → story 04.

## Next session, in order

1. The owner's word on the canvas + the Phase 4 charter (asks 1–5). Then build 01 (Muad'Dib lane `../wt-philo-4-01` exists with the library changes already merged) with the wording fence `briefReceiptRendered202.test.tsx:79` changed in the same commit; 02 (Astra) and 03 (Muad'Dib) in parallel; Astra's brief for 02/04 must carry the ordering rule and the id rule from the charter.
2. Phase 4 exit 1 = the closure chain step 5 AS WRITTEN on the rig, both widths, proof past text containment (geometry visible + in viewport; the rig's predicate accepts off-screen text, `graph_walk.py:832`).
3. His sitting on the whole loop (Phase 3 exit 3).
4. Phase 5: his ruling on D1–D3 of the draft before anything.

## Laws learned today (add to briefs)

- A worker's symlinked `node_modules` into a worktree + `uv run` wipes MAIN's install via the build hook: real `npm ci` in the worktree, never a symlink.
- Astra's checks catch what the harness measures around: measure EVERY visible text node, not only the receipt lines; a chip default title can lie.
- A global library truncation hides disclosures (RouteDisclosure): truncate only where the full value is visibly elsewhere.
- Canvas fixtures come from the REAL producer (`_compose`), never hand-ordered rows.
- The worktree's `.venv` has no pytest: `uv run --extra dev pytest`.
