# Full main recovery — capture, receipts and Brief checks

The #1237 runtime change takes `meeting_glue.py` from 591 to 607 lines. The
existing runtime concern guard allows 600. The completed full main run confirms
this violation alongside the two recovery defects below.
Keep the guard and its budget. Move the completed Stop/save concern to its own
small function module, following the existing `meeting_context.py` pattern.

Settled change: move only `_finish_meeting_stop` into
`holdspeak/runtime/meeting_stop.py` as
`finish_meeting_stop(runtime, session, *, audio_owner)`. Preserve every operation,
its order, exact result, logging category, same-ID save, error handling and
locking. Runtime Stop keeps its claim/finally guard and delegates with the
existing owner constant. No new class, framework or behavior; no whitespace
compression to evade the guard. Anchors are meeting_glue 379–541 and drift.

Worker owns only `holdspeak/runtime/meeting_glue.py` and the new helper. Root
owns docs, tests, full-run diagnosis and release. Do not edit running proof or
serving trees. Focused budget after the full-run lock releases: collect/run
`tests/unit/test_density_guard.py` and `tests/unit/test_meeting_native_stop.py`
with isolated HOME and native effects disabled through `scripts/test_lock.py`.
Use the proof worktree's Python interpreter with cwd and imports resolving here.
No other tests/builds, no staging/commits/deployment; HOLD FOR SHIP. Report exact
module lengths and collection/run output. Root verifies the moved body and runs
ordinary quick, merge/delivery and full main follow-through.

## Full-run result and disjoint recovery work

Main `add3c231c` completed: **3 failed, 16,571 passed, 27 skipped, 1 expected
failure**, 559.22 seconds; mandatory live bus separately passed3. Archived
trace: proof worktree `.tmp/recovery/main-full-add3c231c.log`. R093 is the
confirmed module-budget failure above. Two additional failures entered recovery:

- `tests/integration/test_meeting_kill_recovery.py:149`: the killed process has
  the exact checkpointed DB row/transcript but journal `recoverable()` is empty.
  The Meeting recovery worker owns that integration file, journal and session
  lifecycle/persistence only. First reproduce and trace the finalized-audio /
  unfinished-meeting boundary; report the exact solution to root before product
  edits. Preserve prompt audio sealing, complete durable bytes, discovery,
  one meeting ID and idempotent restart. Never weaken the real SIGKILL proof.
- `tests/integration/test_delivery_pr_poll_real_hub.py:78`: the real hub briefly
  returns no flight while its tracked PR changes to merged. The delivery worker
  owns that integration file and `holdspeak/delivery/factory_launch.py` only.
  Reproduce the read/write seam deterministically. Every read must see the
  complete previous or next ledger, never a truncated intermediate document;
  use the existing atomic-file pattern if that is the established cause. Keep
  same flight/PR identity, merge/close timing and current test assertions.

Workers do not touch each other's paths, the frozen runtime module move, root
docs, or the serving/proof trees. Their focused budget is their named original
integration file plus one directly relevant producer/journal unit file if root
agrees. Jobs serialize under the lock with isolated HOME and native effects
off; no providers, owner DB, microphone, broad runs, staging or commits. HOLD
FOR SHIP. Source/new deterministic proof precedes a claimed defect or repair.

### Settled recovery seam

The original SIGKILL pair reproduces one failure/one pass. Early journal
finalization marks its manifest complete before the final DB transaction;
the audio and checkpointed transcript survive, but recovery discovery excludes
them. Separate `seal()` (durable audio, close handles, reject later appends,
retain discovery) from completion after the final DB checkpoint. A failed DB
checkpoint stays discoverable as recoverable. Preserve original SIGKILL and
same-ID/idempotent-restart assertions. This is a discovery defect with retained
bytes/DB checkpoint; no new owner-data-loss incident is claimed.

The recovery worker also owns the narrowly necessary seal methods in existing
FakeJournal fixtures in `test_meeting_session_admission.py`,
`test_meeting_deferred_admission.py` and `test_hs201_record_speech_only.py`, plus
meaningful sealing/recovery proof in `test_meeting_capture_durability.py`.
Focused coverage expands to those files, native Stop and the original kill
integration. No compatibility fallback for stale doubles or guard changes.

Root verified the Stop completion move by AST comparison after the two parameter
renames: body operations, branches, constants and ordering are identical.
Caller467/helper153; 27 density/native-Stop checks pass. The local Mermaid skip
was an executable lookup mismatch; a probe using the existing cached Chromium
renders successfully. The next full run pins that executable and exercises
the actual diagram guard. Optional hardware/provider cases remain explicit.

### Integrated focused proof

- Meeting recovery: 97 collected/97 passed in15.67 seconds across the bounded
  seven files. Original SIGKILL/control pair remains; the killed capture has
  the exact128,000 PCM bytes before and after repeated same-ID recovery.
  Four additional cases prove seal/late append, pre-join durability, DB refusal
  and final-marker failure. Four existing journal doubles gain only `seal()`.
  Session core835 remains below its850-line guard.
- Receipt publication: actual launch/PR polling read after truncate exposed
  empty bytes and no flight before repair (1 failed). Unique same-directory
  temporary publication now keeps the complete prior/next ledger visible.
  Original real-hub case plus deterministic boundary proof:2 passed4.57seconds;
  exact flight/origin/PR identity, merged/closed result and timing remain.
  This proves atomic reader publication, not multiwriter transactions or
  power-loss durability.
- Independent source counsel finds no blocker. Native hardware is unverified.
  Root inspected code, exact run tails, and desktop Room/phone Meeting shots
  from the release sweep. No face composition changed.

### Midnight release-check failure

The first ordinary quick passed726 affected checks,109 sweeps and17 canon
guards, but failed the Brief staleness test at local00:00. Its source subtracts
30minutes from the real current time, then expects that prior-day brief to be
fresh today. Product daily staleness is correct. The copy worker owns only
`tests/unit/test_monday_brief_service.py` to make the event chronology
deterministic while preserving meeting/decision/real-engine invalidation and
the separate prior-day rule. Archived failure:
`.tmp/recovery/quick-full-followup-affected-red.log`; no release on that red.

The original midnight premise fails deterministically under a controlled clock.
The corrected test starts at midnight and advances through each event and
rebuilt brief. The real assignment service uses that same clock; its persisted
head timestamp is asserted later than the fresh brief. The named case passes;
the complete Brief service file passes126 checks in15.40seconds. No production
staleness rule changed. The separate prior-day test remains.

Combined ordinary quick GREEN:727 affected checks in32.11seconds,109 desktop/
phone sweep checks in62.97seconds,17 canon guards in1.90seconds;28 documentation
guards pass in2.60seconds. The frontend remains `2759d0c6c13d4b6b`; this release
changes backend recovery and tests. Full-main follow-through remains open until
the merged product source completes its full run.
