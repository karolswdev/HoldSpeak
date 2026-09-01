# Phase 161 — Project Rooms: The GitHub Watch (P2a) — Final summary

**Verdict:** COMPLETE 7/7 · owner's shot verdict on the face: **PASS — close it**
(first presentation of the final set) · counsel: **RATIFY-W-C, all conditions paid in-round**.

## What this phase proved

The proving slice: a real provider (GitHub via `gh`) joins the Project
Rooms machine end to end — interview → compiled Watch → live test →
baseline → manual evaluation → evidence-linked Delta proposal — with
the stopwatch bar met on the REAL UI and one leg on real metal.

- **THE KERNEL ANSWER (01):** production gh reads were ALREADY
  admitted — `PermissionGate.run_read_subprocess` (principal
  OWNER+READ, manifest shell:exec), GitHubWatchSource's path since
  HS-11-04. The adapter RIDES it: one seam (`_run_gh`), one
  classified fence entry. No new door. PROV-004 proven by test (row
  + logs grepped clean of credential material).
- **The compilation (02):** five §8.1 templates as a CLOSED table +
  one compile() → every output passes watch_validation (no widening
  needed). GitHub joins the interview ONLY on a live connected probe
  (INT-007); PROV-011 proven; preset parity pinned by test.
- **THE COMPOUNDING MOMENT (03):** `evaluate_once` (MANUAL — P5 owns
  scheduling): admitted snapshot → diff_snapshots (reused kinds) →
  the first real `watch_evaluations` rows → `watch.transition`
  observations (deterministic pobs_ IDs) → an evidence-linked
  proposal in the next open_review. Idempotent under
  UNIQUE(watch_id, revision, source_revision).
- **The wire (04):** seven routes under the house law; api-surface
  599→606 purely additive; the HTTP compounding loop proven in
  fifteen calls end to end. TWO real bugs the loop exposed, fixed:
  the connector "github"→"gh" mapping and the missing pull_request
  test-read path.
- **The face (05):** Check connection → Discover → Test → Activate;
  seven state tokens each with ONE next action; SETFLOW-003 on real
  glass; EgressChip reused (no second species) at every point of
  decision; the closed owner-grade phrase table; real PR rows
  ("#42 feat: add payment gateway (open)"). CLOSED ON THE OWNER'S
  VERDICT after three orchestrator-forced consequence rounds (below).
- **The stopwatch walk (06):** **2.81s** against the 300s SETFLOW-001
  bar, measured on the REAL UI flow, segments itemized; four legs ×2
  deterministic; the REAL-METAL leg live against karolswdev/HoldSpeak
  (read-only, honest ACT-002 zero on a repo with no open PRs);
  19 shots, both viewports. Test seam: typed default-off `gh_runner`
  on MeetingWebServer — everything above the runner stays real.
- **The close (07):** 160's S-2 debt PAID (decide+create_item ONE
  transaction, fault-proven by injection); counsel's findings paid
  in-round (below); gates below.

## The three consequence rounds (the phase's lesson)

The orchestrator's shot reviews forced three rounds before the owner
ever saw pixels:
1. **THE MOUNT** — ProviderWizardStep was built + tested but rendered
   NOWHERE. A component with green tests is not a face: prove the
   MOUNT and the PIXELS.
2. **THE POLISH** — the entity label read a field the normalized
   shape never carries ("Unknown"); Query and Conditions were
   identical twins; the closed phrase table landed.
3. **THE REAL-PR TEST-READ** — the backend returned validation
   placeholders; now a real bounded snapshot renders real PRs.

## Counsel (RATIFY-W-C — all conditions paid)

- **M-1 (CONFIRMED red-first):** finalize stored
  query_kind="pull_request" + a plural repositories dict — shapes the
  snapshot path rejects; every interview-created GitHub watch would
  have failed at evaluation. The mask was a fixture lie: the
  compounding loop's snapshot_fetcher lambda ignored the query shape.
  Fixed with closed mappings + TestFinalizeQueryShape proving
  finalize→test_watch and finalize→evaluate_once through a VALIDATING
  fetcher. (`b8750b47`)
- **S-1/S-2:** web decoders read fields the wire never sends
  (owner.login, message); fixtures corrected to wire truth.
  (`746105a1`)
- **S-3:** evaluate_once TOCTOU on the UNIQUE constraint → typed
  no_op + regression test. (`b8750b47`)
- **N-1** (transient React scope key naming) noted; **N-2** paid.

## Gates

- Web: npm check PASS; inherited baseline 2148 passed, 0 failed,
  ZERO branch-new (final run after all counsel fixes).
- Python full suite (CI-style, isolated HOME, xdist): **8463
  passed, 13 failed, 59 skipped in 22:30**. Sweep vs main's 27-name
  baseline (run 33459107466): 11 of 13 BASELINE-MATCHED; the 2
  candidates (tests/e2e/test_hs152_hands_glass.py pair) PROVEN
  FLAKES — isolation green (2 passed, 55s) + `git log
  origin/main..HEAD -- tests/e2e/test_hs152_hands_glass.py
  web/src/features/desk-chat/` empty. ZERO unexplained branch-new.
- Churned old-phase PNGs restored to HEAD (213); one stray untracked
  phase-152 shot PARKED (never deleted) to the session scratchpad.
- **CI (PR #525, run 33524809739):** Linux Smoke, Route screenshots,
  Web Quality, Integration (macOS) PASS first try. E2E (macOS): 4
  failed / 103 passed — hs144_door BASELINE; hs143_assignments[393],
  hs153_practice, hs159_interview_walk[1440] all PROVEN FLAKES
  (local isolation ×2: 3 passed twice; test files untouched since
  main; the hs159 walk failed only the reload-resume wait on one
  viewport while [393] and every other 158/159/160/161 leg passed).
  Unit (serial, 5:39:57): 28 failed / 7196 passed — 25 of 28 in
  main's baseline families; the 3 candidates
  (scheduled_recording_conductor ×2 — the known sleep-race family —
  and workbench deadline-expiry) PROVEN FLAKES (isolation ×2 green
  in 2.3s; files untouched since main). ZERO unexplained branch-new
  on CI, matching the local sweep.

## Debts carried forward (named)

- P2a → P3: N-5 (widen the no-fetch spy) still open from 160; 158's
  S-1/N-1/N-3; 159's seeding walls; counsel N-1 (React scope key).
- Gate A's dogfood clock: the owner's two real EverDriven Projects
  want the interview + GitHub watches + Delta reviews IN USE.

## The arc

P0 #521 → P1 #522 → P1a #523 → P2 #524 → **P2a (this phase)** →
next: P3 The Update Factory.
