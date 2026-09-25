VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The transaction is the right place for the grant write, but `BEGIN IMMEDIATE` is not present today.** `holdspeak/kernel/journal.py:379` reads the receipt before SQLite begins the transaction at the UPDATE. The real-producer [trace:2](/tmp/astra-656-r3.txLQVQ/seam-trace.txt:2) confirms this.

   Make the transaction entry explicit: begin, check receipt/revision, execute `effect(conn)`, update state, insert receipt, commit. The callback must use **that supplied connection**. Nested database contexts open another connection (`holdspeak/db/connection.py:140`; [probe:2](/tmp/astra-656-r3.txLQVQ/out.txt:2)), so calling an ordinary service method inside the callback can break atomicity or block on the outer writer. Release the credential lookup lock before entering the kernel; keep the callback to local SQL. **Tenets 1/3; XI.2.**

2. **`create_refused_with_receipt` is a minimal, compatible addition; the strict semantics are sound.** T1 needs an INSERT path because the transition seam requires an existing operation. Preserve the fields, defaults and idempotency handling at `holdspeak/kernel/journal.py:127`, including provenance, using one connection.

   The strict error names distinguish a terminal winner from a moved revision correctly. Check both before invoking any effect; return the existing receipt without rerunning the effect on the default idempotent path. T7 must catch both strict conflict codes as the beat specifies.

   **One omitted field:** T4 currently records `decision="reject"` (`holdspeak/kernel/broker.py:220`); the proposed seam has no corresponding parameter. Preserve that field inside the same transaction. Fence the operation row as well as its receipt. **Tenet 3; VI.1.**

3. **The reaper outcome is valid, but its timing needs qualification.** A pre-commit interruption leaves the grant unchanged and the previously committed claim outstanding. The reaper waits for `execution_expires_at` (`holdspeak/kernel/liveness.py:20`). My real-broker probe returned zero before that deadline, then `indeterminate / execution_liveness_expired` afterward ([output:3](/tmp/astra-656-r3.txLQVQ/out.txt:3)).

   F21b must explicitly advance past the deadline. `indeterminate` is the generic reaper’s conservative classification; it does not itself prove rollback. Assert the unchanged grant separately. No new recovery subsystem is justified. **Tenets 1/3; IX.1.**

4. **Keeping the ledger available with the switch off is lawful; its orphan-row chip has one contradiction.** Lifting the ledger out of the `enabled` branch and keeping the receipt outside the row-count branch addresses the scar at `web/src/pages/cores/SettingsCore.tsx:612`. The switch controls transport; it must not hide persistent authority.

   However, `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:143` gives every stored LIVE orphan grant `FILING ALLOWED`. A LIVE row whose expiry has passed already fails `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:52`. Apply the same time-aware rule here; never derive ALLOWED from stored state alone. Extend F23 with that case. The canvas must also replace the literal `CREDENTIALS` caption when it includes rows without credentials. **Tenets 3/4/5; VI.1.**

5. **The revised scope is proportionate.** T1–T9 and the separate `DESK_KERNEL_OPERATIONS` set close the identified coverage gaps without enlarging agent authority (`pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:94`). I would cut no lifecycle invariant. Keep the callback narrow and file the six non-desk paths as the promised separate debt; do not grow this into a general transaction or recovery framework. **Tenet 1.**

CONDITIONS:

- Put the explicit transaction ordering and supplied-connection callback contract into the implementation brief.
- Preserve T4’s rejection metadata atomically.
- Reconcile orphan-grant expiry with the common chip rule and extend F23.
- Qualify F21b’s deadline and rollback assertions. Retain the canvas precondition and file the named BACKLOG row at merge.

MISSED:

1. Highest cost: “same database” does not mean nested service calls share the transaction.
2. Next: an expired orphan grant can display permission the kernel refuses.
3. Next: immediate recovery and preservation of rejection metadata are not supplied by the proposed seam automatically.

TUESDAY: Conditionally yes—grant once, stop filing on the same face even with transport off, and retain the receipt after the last row disappears.

UNKNOWN: Reviewed `29970c22`. Isolated real-broker probes verified transaction entry, nested connections and reaper timing. The new helper, callback, strict paths, canvas, fresh-process recovery and atlas cases remain unbuilt or unverified here. No full suite or live walk ran. The tree is unchanged.