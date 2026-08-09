# HS-131-12 — The walk

- **Project:** holdspeak
- **Phase:** 131
- **Status:** backlog
- **Depends on:** HS-131-10, HS-131-11
- **Owner:** unassigned

## Problem

The phase is not done because every focused test is green. The assembled runtime
must prove on real metal that provider dispatch, admission, revision capture,
cancellation, session continuation, scheduled delegation, and terminal receipts
stay one coherent path. The inherited red backend baseline must not hide a new
failure.

## Scope

### In

- Add a reusable `scripts/walk_one_admission_path.py` harness using an isolated
  database and the live LAN endpoint pattern from `scripts/walk_one_truth.py`.
- Prove a real Ask and Agent invocation; a multi-step Sequence; a branched
  Workflow; a manual Workbench item plus memory writeback; and one Rails,
  Decision, Delivery, or voice reference call.
- Prove a Workbench schedule created through deliberate owner enablement, one
  scheduler-authenticated tick, and named refusal after target/cadence change or
  disable.
- Prove one admitted MLX preload/warmup, one meeting session with intelligence
  plus shared-Whisper transcription children, one dictation session with
  multiple utterance/model children, and one configured wake transcription
  child. Revoke a session before another
  child claim and prove named refusal with no provider dispatch.
- Pause between admission and dispatch, mutate the editable target, and prove
  execution plus receipt retain the admitted deployment revision.
- Cancel during streaming and prove provider cancellation/indeterminate handling,
  no late domain output, and one immutable terminal receipt.
- Prove fallback/retry cardinality where a controlled adapter can force the first
  provider attempt to fail and the second to run.
- Round-trip the deployment revision and operation references through sync and
  query them after restart.
- Run every focused Phase 131 test, the web suite, and the full backend suite.
  Read the full output and diff failing test names against HS-130-10; no new or
  changed failure name may ship without repair and explicit classification.
- Capture the walk output and operation/receipt excerpts under
  `assets/hs-131-12/`. If any user-visible receipt/projection changed, perform
  the real production screenshot walk at 1440 and 393 before closure.

### Out

- Fixing the 94 unrelated inherited failures.
- Declaring the product or issue #450 finished. Phases 132 and 133 remain.
- Waiving real-model evidence because a fake adapter passed.

## Acceptance criteria

- [ ] The reusable harness exits 0 against the real LAN model and asserts exact
  dispatch/admission/receipt cardinality for every exercised path.
- [ ] Target mutation after admission does not alter execution or receipt
  deployment identity.
- [ ] Sequence, Workflow, and Workbench evidence shows parent operations plus
  exact invocation children, including the separate memory child.
- [ ] Scheduled evidence shows scheduler actor, owner delegation, exact bounds,
  one successful tick, and a no-model named refusal after invalidation.
- [ ] Preload evidence shows one admitted Whisper warmup with a truthful actor
  and authority basis; meeting, dictation, and wake evidence covers shared local
  Whisper plus all intelligence/classification/rewrite invocations under the correct session
  parent; a revoked session refuses the next child before dispatch; journal
  excerpts contain no content bodies.
- [ ] Cancellation produces no late domain output and one terminal child receipt;
  unknown remote outcome is recorded indeterminate.
- [ ] Retry/fallback evidence shows one child and receipt per provider dispatch.
- [ ] Sync plus restart preserves deployment-revision and receipt resolution.
- [ ] All seven HS-130-10 Phase-131-assigned tests pass or have a stricter
  replacement with retirement rationale; no Swift source changed.
- [ ] Full backend failure-name diff reports zero Phase-131 regressions, and Sol
  has personally read the output before the final done decision.
- [ ] Any changed UI was screenshot-walked on the production bundle at 1440 and
  393 with success and refusal legs.

## Test plan

- Focused: every command named in stories 01–11 through
  `.githooks/dw evidence capture`.
- Backend full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`, captured to
  evidence and read before status change.
- Web full: `npm --prefix web run test:web -- run`, using the established JSON
  report/isolation workaround only if the known jsdom/Pixi teardown abort
  recurs; the actual test result must still be read.
- Live: `uv run python scripts/walk_one_admission_path.py` with the real LAN
  target configured, plus browser production walk only if UI changed.

## Notes / open questions

Terra verifies focused contracts adversarially. Sol owns the assembled walk,
reads the full-suite outputs, compares the inherited ledger, and makes the final
done or not-done call. The fleet cannot self-certify this story.
