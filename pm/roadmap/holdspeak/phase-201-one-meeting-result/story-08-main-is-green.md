# HS-201-08 - Main is green

- **Project:** holdspeak
- **Phase:** 201
- **Status:** done
- **Depends on:** none
- **Owner:** Astra

## Problem

Six inherited failures and an xdist notification pollution family make main red. Warm dictation and saved-Ask custody are on the first-use path. Tenets 1–3 call for small repairs and an honest green baseline. Tuesday: the owner can return to saved work and dictate without losing the warm engine.

## Scope

- **In:** classify and fix the six named failures and TestNotificationTransitions. Repair guardrail hydration, test isolation, and any demonstrated runtime defect. Include the completed-project roadmap read path (b), stale current-tree documentation and OpenAPI references (a). Keep existing guardrail face grammar.
- **Out:** microphone, owner's HOME and desk, main checkout, wt-201-b, merging, unrelated cleanup.

## Acceptance criteria

- [x] Each named failure has a/b/c classification and captured red/green evidence; environment-specific red is identified honestly.
- [x] Guardrail Deny survives hydration and reload and remains primary/focused at 1440 and 393; explicit Allow remains valid.
- [x] Same-desk custody survives restart and database replacement; different and unknown desks remain tested.
- [x] Warm-start reuse is pinned for each supported backend without erasing real backend changes or deployment provenance.
- [x] Notification tests pin a nonquiet clock. The exact eight failures reproduce with ambient time at 02:30 UTC, then pass with the same ambient-clock probe and under -n 4; explicit quiet-hours states stay tested. Two ordinary serial-green runs are retained; no serial marker.
- [x] Quiet-tree full suite passes with isolated HOME, -n 4 --dist=worksteal, and --ignore=tests/e2e/test_metal.py. All eleven documentation CI commands and OpenAPI checks pass. Focused tests, web checks, and both-width shots are recorded.
- [x] Muad'Dib checks the settled design and built result; closing conditions are verified and recorded.

## Test plan

- **Unit:** tests/unit/test_phase200_ci_isolation.py; tests/unit/test_phase200_task_resume.py; tests/unit/test_transcriber_init_race.py; tests/unit/test_phase200_attention.py. Collect names; capture focused red then green. TestNotificationTransitions serial twice; ambient clock fixed at 02:30 UTC red/green; then -n 4.
- **Glass:** tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused; tests/e2e/test_hs200_task_resume_glass.py::test_a_saved_ask_survives_a_hub_restart; tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440; scoped added regressions and shots at 1440/393.
- **Full:** HOME=$(mktemp -d) with absolute browser/npm caches; uv run pytest -q -vv -n 4 --dist=worksteal --ignore=tests/e2e/test_metal.py. Verbose names make a failure visible before the final summary; selection is unchanged. Build/typecheck and web inherited-baseline check. Restore unrelated tracked PNG churn from git show HEAD:path.

## Settled repair boundaries — Muad’Dib checked, conditions accepted

1. CI HOME: isolate the Unit CI run before collection (Integration stays unchanged to retain its existing model cache); preserve the refusal test's valid bare-runner and real-installation cases.
2. Custody: preserve the existing persisted machine identity. Model a replacement with a genuinely distinct live inode, not allocator reuse; diagnose first-boot readiness: both CI glass failures precede saving or restart. Gate start() on Uvicorn listener readiness, with bounded failure/timeout handling, after an event-gated red probe. Retain the isolated config and pin SAVED HERE at both widths.
3. Transcriber: pin platform/backend availability in the test to model the same resolved engine. Keep different-engine, model/language, and deployment-provenance states covered; repair code only for a reproduced reuse defect.
4. Guardrail: compute default_decision before persisting the tool_call metadata, write it to that metadata, and emit the same value. Hydration reads the persisted decision and retains a received live decision only if persisted metadata is absent. Keep hydration result/state updates authoritative; do not merge stale live state over terminal results. No new interface. Assert Deny, focus and reload; keep explicit Allow tested.
5. Attention: the shared input was the ambient clock, not a singleton. An injected 02:30 UTC ambient clock reproduced precisely eight failures (held_quiet_hours versus sent). Pin the helper default to a known nonquiet instant; keep explicit quiet-hours clocks. This is class (a), not historical class (c).

## Classification doctrine

(a) Test asserts an old posture or invalid platform assumption: update to current law and pin still-valid states explicitly. (b) Real product regression: fix code; never paper it over with a test edit. (c) Unrelated/order-dependent flake: prove serial-green twice, name the polluter, fix the source. Final table and exact evidence live in evidence-story-08.md.

## Named baseline and amendment record

Completed main CI run [35478778899](https://github.com/karolswdev/HoldSpeak/actions/runs/35478778899), commit 675401a8. The 321247d2 main run was queued at initial inspection; subsequent Unit and docs failures are recorded in evidence-story-08.md. Mac baseline on 321247d2 reproduced guardrail; other five passed.

| Test node | CI job / OS |
|---|---|
| tests/unit/test_phase200_ci_isolation.py::test_the_running_suite_is_itself_isolated | Unit / Ubuntu |
| tests/unit/test_phase200_task_resume.py::test_custody_survives_the_database_file_being_recreated | Unit / Ubuntu |
| tests/unit/test_transcriber_init_race.py::test_boot_warm_is_reused_by_a_legacy_dictation | Unit / Ubuntu |
| tests/e2e/test_hs153_practice_glass.py::test_guardrail_row_renders_and_deny_focused | E2E / macOS |
| tests/e2e/test_hs200_task_resume_glass.py::test_a_saved_ask_survives_a_hub_restart | E2E / macOS |
| tests/e2e/test_hs200_task_resume_glass.py::test_the_custody_token_after_a_restart_at_1440 | E2E / macOS |

2026-09-19: AC5 and boundary 5 amended after Muad’Dib’s falsifier reproduced exactly eight failures at 02:30 UTC. The prior pollution diagnosis is withdrawn; a clock precondition fixes the source without serialization. Boundary 2 now addresses observed first-boot connection refusal. Boundary 4 includes the missing backend persistence. Check: checks/story-08-design-muaddib.md. Owner may overrule at the sitting.

## Scope amendments — 2026-09-20 UTC

- **Roadmaps (b):** a completed project emits `next_story: null`. One project then makes the entire list return 500, including active projects. Repair only `holdspeak/web/routes/roadmaps.py`; add `tests/unit/test_roadmaps_api.py` for explicit null, the four still-valid forms and a mixed list. No DW or web changes. AC6 includes this path. Local 321247d2 reproduces it; CI 675401a8 predates Philo and those glass tests passed there. Check: `checks/story-08-roadmaps-muaddib.md`.
- **Documentation (a):** correct three doctor anchors and the lane-induced redactor anchor; regenerate existing API, boundary, doctor, capability and OpenAPI references. Snapshot and repository census remain historical. Generator scope strings distinguish census baseline from current source. AC6 includes all eleven commands at `.github/workflows/test.yml:27-37` and `tests/unit/test_api_surface.py`. Checks: `checks/story-08-docs-muaddib.md`, `checks/story-08-docs-delta-muaddib.md`; OpenAPI continuation is recorded separately. No weakened checks or schema redesign.
- **Scheduling:** the default-load diagnostic was interrupted at about 95%, exit 2, with eleven reported failures. It is NOT full-suite proof; the set of tests not run is unknown. The final run uses `--dist=worksteal`, preserving all selections and four workers. It must reach 100% with no failures. Check: `checks/story-08-scheduler-muaddib.md`.

Additional focused test plan: `tests/unit/test_roadmaps_api.py`, the ten reported HS-141/144/145 glass nodes, and `tests/unit/test_api_surface.py`. Docs use the eleven workflow commands verbatim with Python 3.12; OpenAPI uses the existing isolated runtime venv. Regenerate from the full worktree after product edits, review every output delta, stage inputs, then capture final checks and prove subsequent index changes contain only roadmap closure records.

- **Weekly brief (a):** the face-wide zero regex rejects legitimate 00:33 and 08:00 timestamps. Scope counters to their three primary labels, require the brief to open, and pin timestamp plus zero/positive states in the real BriefView tests. No UI change. Scoped glass red is captured at 06:48:08Z. Check: `checks/story-08-weekly-muaddib.md`. Test plan adds `tests/e2e/test_hs175_rhythm_brief_glass.py` and `web/src/desk/pullouts/views/BriefView.test.tsx`; web checks, documentation inputs and full-suite closure restart after edits.

- **Interrupted send (a):** the test assumes a pipe descriptor is below select’s fixed limit. Replace only its readiness primitive with DefaultSelector; retain the real SIGKILL, landed bytes and reconciliation assertions. The identical 1,050-descriptor probe must turn red to green. No product change or descriptor-leak fix is claimed. Test plan adds `tests/integration/test_process_input_real_hub.py` and `assets/story-08-probes/fd_pressure.py`. Check: `checks/story-08-send-muaddib.md`.

- **Remote settings (c):** two serial greens and the named loopback credential producer reproduce both glass failures in sequence. The glass fixture receives its own AgentCredentialStore before boot, stops its hub before restoration, and revokes its own row while a second credential remains valid. No global store or producer edit. Test plan adds the remote-settings glass file serial and -n 4, and the ordered `test_hs174_runner_loopback.py` → remote-settings file sequence. Check: `checks/story-08-daily-remote-muaddib.md`.
- **Daily loop (a):** the accepted analysis-only summary posture leaves zero proposals. Prove summary success, coverage, no plugin calls/proposals and Review NOT RUN first. Then invoke the real retained plugins and bridge as an explicitly labelled historical fixture, preserving all Review-to-day-2 continuity assertions. Day 2 continuity is proven from a seeded day-1 state; the current summary path does not create the decision or commitment it carries. No new skip/xfail or production entry. Test plan adds both daily-loop widths, NOT RUN shots and the negative no-proposal canary. Check: `checks/story-08-daily-remote-muaddib.md`.

The first complete worksteal run was red: six failures in these four added families, 11,258 passed, 116 skipped and four existing strict xfails. Closure requires a new complete passing run after all edits. The seven scope groups are: original six plus notifications; roadmap list; Philo/OpenAPI references; weekly brief; interrupted send; remote isolation; daily-loop current-law/continuity split.

## Verified closure and delivery protocol

The final local full capture is 2026-09-20T07:18:40Z: 11,264 passed, 116 skipped, four existing strict xfails, zero failures/errors. The eleven final documentation CI commands passed at 07:17:48Z; web has 2,601 passing tests. The original and added failure families are covered in the classification table and captured proof.

AC7 now separates the completed peer check from the delivery action: this pre-commit record cannot claim a future commit or PR exists. Delivery remains required, unchanged: one gated commit, push `feat/hs-201-green`, PR titled exactly “HS-201-08 main is green” against main, no merge. The commit and PR are the external delivery evidence. A red PR check reopens verification.
