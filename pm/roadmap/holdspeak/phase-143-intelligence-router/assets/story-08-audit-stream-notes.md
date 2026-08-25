# C3 sitting notes (pending fold-in to the C3 counsel record)

- Peer observation (opus-worker session, 2026-08-24): every process turn
  calls `_reconcile_stop_handoffs` (intel_queue.py ~557-564; drain loop
  ~1017-1042) and `admit_unknown_stop_handoff_recoveries`, each opening a
  BEGIN IMMEDIATE scan; a still-stopping child stays unsettled (bundle
  service reconcile ~1135-1174) and is re-examined on every pass until it
  terminates. Per-pass cost is concrete, not amortized. No damage
  reproduced, no edits. RULED A NOTE under the owner's yolo bar
  (single-user SQLite, bounded by drain cadence, settles on child
  terminal). Candidate cheap improvement if it ever matters: gate the
  scans on a dirty flag / unsettled-count check instead of
  unconditionally per pass.

- Peer finding 2 (opus-worker, read-only, UNVERIFIED — queued for the C3
  fix round with reproduce-first mandate): alleged permanent-stuck
  meeting after a fence fault on Stop. Chain: failed C3 handoff marks
  route_fence_pending but stamps in-memory status queued
  (intel_admission.py:494-535) → normal web Stop runs session.stop()
  then session.save() (meeting_glue.py:391-416) → save sees
  queued+segments and enqueues legacy plain-slug work
  (persistence.py:86-102) → that work hashes identically to C3's
  reservation descriptor (db/intel.py:410-418, 610-631) while the
  unique index forbids queued+reserved coexisting (schema.py:244-246) →
  recovery retries C3, catches IntegrityError, re-marks pending forever
  (db/meetings.py:763-800) → claims require route_fence_pending=0
  (db/intel.py:896-906) → permanently unclaimable. Existing durability
  test (test_meeting_capture_durability.py:222-256) omits the save()
  call the real web flow makes. If reproduced: real (b), fix in the
  capped round. If refuted: note with the probe attached.

- Peer finding 3 (opus-worker, read-only, UNMEASURED — queued for the
  fix round with measure-first mandate): Stop's post-commit cancel loop
  is serial-synchronous — after the durable handoff commit
  (inference_parent_route_bundle_service.py:1120) it iterates every
  child calling inference_runner.cancel (1122-1132), each synchronous
  (kernel/inference_runner.py:76-110) and able to wait up to
  cancel_timeout (inference_cancel_signal.py:48-61); live bundles
  declare four routes ordinarily. Latency accumulates per child on the
  owner's hero action (Stop) — the usability bar demands visible
  feedback ≤500ms on hero actions. Since the ruled law is "durable
  fence BEFORE best-effort physical cancellation", the cancels are
  lawful to background/parallelize. Measure first; bound/background if
  it breaches.
- Peer finding 4 (opus-worker, read-only): unsettled-handoff scans in
  db/intel.py:653-710 have no provider/revision/created_at index
  (schema.py:3043-3056 has only PK + parent_operation UNIQUE) — SQLite
  EXPLAIN shows SCAN + temp ORDER BY, invoked pre-claim, per drain
  item, and per worker poll. Efficiency NOTE (single-user table sizes);
  a one-line index may ride the fix round for free.
