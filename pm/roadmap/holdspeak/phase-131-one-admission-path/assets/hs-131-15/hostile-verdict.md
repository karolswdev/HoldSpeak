# HS-131-15 hostile verdict

**Verdict:** **SHIP-CANDIDATE**

The final read-only hostile pass rechecked the three blocking invariants against
the primary shared tree:

1. **Plan/parent binding.** `require_entry_admission()` binds the supplied
   provider, fence, broker, opaque parent context, principal, plan SHA, session
   ID, and insertion aim to the durable parent metadata. A live plan from a
   second session cannot retarget the first parent's revision or egress proof.
2. **Publication-release recovery.** A completed callback retries only its exact
   random SQLite publication token after a transient write failure. It never
   replays the callback and cannot clear a later owner's claim. Startup stale
   lease reconciliation remains the crash-recovery owner.
3. **Expiry/reaper serialization.** Generic operation transition translates the
   v58 publication trigger into a bounded named
   `parent_publication_in_progress` refusal. `reap_expired()` defers that one
   operation rather than leaking `sqlite3.IntegrityError` or aborting the pass.

No P0/P1 correctness, durability, constitutional, or kernel-content finding
survived the final pass. Focused failure-injection and race tests accompany each
repair; the final hostile suite reports 501 passing tests.
