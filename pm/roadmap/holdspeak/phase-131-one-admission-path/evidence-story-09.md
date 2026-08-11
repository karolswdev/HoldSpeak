# Evidence - HS-131-09

- **Story:** HS-131-09 - Dictation and transcription are admitted per session
- **Status:** done
- **Date:** 2026-08-11

## Proof

### Captured run — 2026-08-11T08:21:44Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.wTUM7hnKzW uv run pytest -q tests/unit/test_dictation_session_admission.py tests/unit/test_dictation_pipeline_admission.py tests/unit/test_db.py tests/unit/test_wake_runtime.py tests/unit/test_transcribe_route.py tests/unit/test_meeting_session_admission.py tests/unit/test_kernel_effect_fence.py tests/integration/test_dictation_moment_of_truth.py tests/integration/test_core_path_smoke.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** dbec681214237b04661270e19e644ab505520e9c

```text
........................................................................ [ 40%]
........................................................................ [ 80%]
....................................                                     [100%]
180 passed in 44.30s
```

## Verification narrative

### The design beat (committed separately as 7e63687a)

Terra drafted [DESIGN-HS-131-09](./DESIGN-HS-131-09.md); Sol ruled
RATIFY-AS-AMENDED in ONE round with EIGHT binding amendments, each with its
hot-path cost stated — the standout being Amendment 6, where Sol computed
the deterministic 12-hour meeting-budget exhaustion the draft missed (4320
transcription children against the 4096 allocation). The full ruling and
the orchestrator disposition ride inline in the design doc.

### What shipped

- **Schema v56**: parent kinds `dictation.session` and `wake.session`; the
  new `holdspeak/speech_session/` package (plan, session, child,
  transcription, fence, provider, browser_mic, revision_target) carries the
  admission platform: content-free `DictationSessionPlan@1` /
  `WakeSessionPlan@1` frozen ONCE at session open by one resolver seam,
  with per-capability ORDERED revision lists and the frozen
  DeploymentRevision objects themselves (zero DB reads at dispatch).
- **Desktop hold**: one `dictation.session` per accepted press under the
  owner-gesture principal; a monotonic session-generation token kills the
  release-before-admission race; the two-stage deadline (30m capture
  ceiling + a release SEAL to release+90s via `seal_deadline`, a
  lowering-only durable transition costing ~0.3ms) makes the drain honest.
- **Browser open mic**: one session per authenticated mic-open interval
  (server-issued opaque `mic_` handle bound to the route principal +
  generation; a client-supplied parent id refuses); 30m/1024/90s-inactivity
  bounds with the inactivity lease refreshed ATOMICALLY inside the first
  Whisper child claim per utterance (zero extra round trips) and NO
  resurrection — a lapsed lease refuses the child at claim; any terminal
  fence forces the client interval CLOSED (a fresh click, never a silently
  replaced parent). One-shot speak-to-fill joins an active interval or
  admits its own short session.
- **Wake**: one bounded `wake.session` (30s, budget 12) under SERVICE
  `wake-capture` with `configured-wake:<revision>` derived
  deterministically from the canonical WakeWordConfig (no user-authored
  basis field); stop cancels the in-flight session FIRST, and the
  admission-to-registration window is generation-fenced (a session admitted
  across the stop boundary cancels itself). Typing keeps its separate
  Phase-107 effect admission.
- **The shared Transcriber**: every nonempty `.transcribe()` requires a
  live session context and runs as one `holdspeak.whisper-transcribe@1`
  child (audio sha256 + metadata; audio dispatch-only, never journaled);
  MLX `get_model` and the silent-audio fallback are SEPARATE sibling
  `holdspeak.whisper-preload@1` children completed before the transcribe
  child, with no lock reacquisition; pre-session warmup requires the NEW
  `model.local_model_preload_authority` knob to name the exact
  `model_config_revision()` hash (blank → required, wrong →
  mismatched, both surfacing the expected revision) — else it defers to
  the first admitted session. Meeting transcription threads the live
  `meeting.session` context (no live parent → the interval drops before
  Whisper), with the Amendment-6 budget allowance wired.
- **The pipeline seams**: classify/rewrite (and future punctuation) run
  through `run_admitted_capability` on the session's frozen plan —
  `holdspeak.dictation-intent-classify@1` / `-rewrite@1` /
  `-punctuate@1`; the OpenAI response_format compatibility leg and the
  intent router's second attempt are separate children with ordinals; the
  mesh runtime reuses the HS-131-07 envelope. CRUCIALLY, the dispatched
  runtime is verified/rebound FROM THE FROZEN REVISION
  (`revision_target.agrees`/`rebind`, cached per revision per session) —
  a config/profile change after admission cannot change the target, and
  an unbindable backend refuses `speech_revision_target_unbindable`
  BEFORE any child admission. The legacy top-level
  `program:browser-mic-pipeline-v1` admission is DELETED — the speech
  session is the one admission path — and the route's egress label
  derives from the frozen revisions through the ONE HS-130-04 classifier,
  conservatively combining every frozen provider capability (a
  classify-only pipeline reports the classify revision's boundary).
- **Cancellation**: the immutable SessionFence (sealed deadline + parent
  state + warrant revocation/expiry in one indexed read) passes explicitly
  through every continuation; mic close / hold tail / wake stop / expiry
  fence new children and discard late text before preview, rewrite,
  pipeline publication, and the delivery seam. Failed tails close their
  parents `failed` — honest parent receipts.
- **THE CONNECTION CACHE** (`holdspeak/db/connection.py`): the charter's
  A/B initially FAILED (+36ms median) — profiling showed ~26ms of every
  trusted-child admission was 24 short-lived SQLite connections each
  paying a first-statement parse of the 356-object schema. The fix:
  per-Database-instance per-thread connection reuse (identical
  commit/rollback semantics; re-entrant nested calls get fresh short-lived
  connections; per-instance lifecycle closed with the Database; a STRICT
  8-entry cap). Sol ruled it accepted in-story ("it directly removed the
  measured admission cost required to satisfy the non-waivable A/B AC").
  Per-child admission: 39.6ms → 6.8ms; zero fresh connections on the hot
  path; full-suite proof at zero new failure names.

### THE LATENCY A/B (the charter's shipping gate) — PASS, dictation FASTER

`scripts/measure_dictation_latency.py --warmups 2 --runs 20 --typing-mode
driver` (p95 nearest-rank + session_seal_ms added; the fork-point
control's own driver sink was broken — its TextTyper was already a
warrant-only proxy — so the scratch control copy was patched IDENTICALLY
to stamp the same landing seam; Sol ruled the control valid, its median
reproducing the earlier charter figure):

- Control (fork point 0fc14aca): median **82.489ms**, p95 **85.118ms**.
- Story branch (final, post-fix): median **68.304ms**, p95 **70.478ms**.
- Delta: **median −14.2ms, p95 −14.6ms** against a bound of max(25ms, 5%)
  — **PASS on both, with dictation FASTER than the fork point while
  admitting every model call** (session_seal_ms median 0.29ms). Artifacts:
  `assets/hs-131-09/ab_control.json`, `ab_treatment.json`,
  `ab_treatment_postfix.txt`.

### The counsel ledger (implementation)

Sol rode FOUR implementation rounds to RATIFY-WITH-RESERVATIONS:

- **Round 1** (8 blockers): browser stop-before-open orphan; lease
  resurrection in delayed claims; the fence ignoring the sealed deadline
  and warrant revocation; a PRODUCTION browser pipeline path dispatching
  unadmitted classify/rewrite; non-mesh dispatch discarding the
  revision-built engine (silent retargeting); preload authority unbound
  from the model revision; wake stop missing in-flight sessions; failed
  sessions closing succeeded.
- **Round 2** (2 blockers): the legacy browser-pipeline admission as a
  redundant second authority path ("not harmless scaffolding in a phase
  named One Admission Path") — retired in-story; the wake
  admission-to-registration stop race — generation-fenced.
- **Round 3** (1 blocker): classify-only pipelines falsely labeling egress
  `local` — the combined-widest-boundary label (orchestrator-implemented).
- **Round 4**: **RATIFY-WITH-RESERVATIONS**, all eight amendments and all
  charter ACs discharged.

### Sol's sitting-visible reservations (final, five + observations)

1. Make the meeting transcription budget dual-stream-aware before
   advertising the full 12-hour mic+system ceiling (the Amendment-6
   formula counts one child per interval; dual-stream spends ~2 —
   exhaustion reachable ~11.7h).
2. SHOW THE OWNER: device/automatic meeting starts without an
   authenticated principal now record audio but intentionally produce NO
   transcript (`meeting_intel_principal_required` — the Article XI
   consequence).
3. Later hardening: close the server browser interval immediately on a
   claim-time lease refusal rather than depending on the client's
   follow-up close.
4. The two recorded unadmitted seams (the dictation dry-run route at
   `web/routes/dictation/_helpers.py:541` and `commands/dictation.py:79`)
   ride to the HS-131-10 fence by name.
5. Eagerly initialize the wake generation when convenient.

Additional recorded dispositions: paired-device capture ratified only with
a validated pairing id; recording import / CLI meeting mode ratified under
authenticated caller principals; faster-whisper constructor weight loading
is non-dispatch; punctuate is planned-but-never-declared until a
provider-backed stage enters the plan; `parent_run.py` sits at exactly the
300-line fence ceiling. A REAL production hazard was root-caused during
the cache proof (a leaked meeting transcribe-loop thread can make
`runtime._service()` dispose the live global broker and invalidate other
parents' contexts — `kernel/runtime.py:155-163`) — named follow-up work.

### The verification liturgy

1. **Two-part implementation + three fix rounds** (opus agents; the
   two-part split and the model switch away from context-overflowing
   Terra implementers are recorded process learnings).
2. **Focused suites** (orchestrator re-ran after every round, output read
   from files): 319-404 tests green at the widest runs across both new
   admission suites (44 + 12 tests incl. every race proof), the
   dictation/wake/transcribe/meeting suites, every prior-story regression
   suite, and the pins; the implementers' full-unit sweeps ended at
   4124 passed / 4-5 failed — the same long-inherited names, ZERO new.
3. **Real-metal walk**
   (`assets/hs-131-09/walk_dictation_session_lan.py` on .43; output in
   `walk-output.txt`): hold session froze classify+rewrite on the real
   lan43 revision — the .43 server's pinned line-JSON grammar rejects the
   classify contract (the recurring endpoint observation), producing
   honestly-receipted failed attempts while the rewrite child SUCCEEDED
   with real output; the release seal lowered the durable deadline; the
   browser interval opened on a server-issued handle, ran a succeeded
   child, and post-close dispatch fenced `speech_provider_fenced`; a
   cancelled hold fenced BEFORE dispatch. Real-MLX Whisper end-to-end =
   the A/B's 20 live runs.
4. **Full gate** on the quiet tree: accounting below.

### Gate triage (first run → repairs → clean re-run)

The first gate surfaced eleven new names — ten deterministic (test rigs
encoding the pre-story seams: stub transcribers without the `admission=`
kwarg, meeting/import/kill-recovery rigs without authenticated principals,
the core-path smoke driving the unadmitted seam) and one serial-pass flake
(test_kernel_real_hub). Eight were test migrations with substance
preserved — including one sibling test (`test_no_speech_does_not_set_the_
milestone`) exposed as previously passing VACUOUSLY. Two were REAL product
fixes recorded as post-ratify gate repairs per the standing precedent:
(1) `services/meeting_service.py` authenticated the import caller but
DROPPED the principal before the import worker, silently falling back to
the synthesized local-owner identity — now threaded; (2) the
`JournalStore._secret()` warrant-secret mint was SELECT-then-INSERT — two
callers racing a fresh database hit the UNIQUE constraint (fired once as a
real ERROR in the keep-green set; the faster cached admissions made the
race common) — now an idempotent INSERT OR IGNORE + re-read.

### Gate accounting (final run)

Baseline: `assets/hs-131-08/gate-failures.txt` (96 normalized names).
Final gate: `assets/hs-131-09/gate-failures.txt` (**90 names**). Diff:
**ZERO new names, SIX repaired** — `test_moment_affordance_present_and_
focus_safe` (the moment-of-truth affordance, repaired by the admitted
browser seam work), the recurring `test_cloud_stream_forwards_endpoint_
deltas` flake (green this run), and the four `test_voice_macro_connector`
names from the prior story's accounted flake family (their passing
confirms that classification). Nothing left to account.
