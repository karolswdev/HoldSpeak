VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **The four-path list does not cover every desk terminal write.** `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:91` omits admission refusal, native-admission failure and explicit rejection. Those remain separate writes at `holdspeak/kernel/broker.py:332`, `:131` and `:220`. Admission refusal is the ordinary no-grant path, not an exotic case.

   I interrupted all three through the configured broker and real `tool.call` producer; each persisted `state=refused`, `receipt=NULL`. [Probe output:1](/tmp/astra-656-r2.D2KaSW/out.txt:1). These prove the shared mechanism, not the unbuilt desk codec.

   **Desk-only scoping is lawful; incomplete desk coverage is not.** Leave unrelated kinds to the promised BACKLOG row. Include this story’s `delegation.grant/revoke` receipt paths in the coverage without adding them to the agent’s 15-operation authority set. **Tenets 1/3; XI.2.**

2. **Revision-as-state is sound only when the helper actually checks revision.** Production transitions increment revision: `holdspeak/kernel/publication_transition.py:19`, `journal.py:341`, `:386`. However, `transition_and_receipt` returns an existing receipt **before** its revision check (`journal.py:380`).

   Reproduced: observe revision 2, let approval/claim/success finish at revision 5, then request a refusal using revision 2. The helper returns the winner’s **succeeded** receipt without raising. [Probe output:4](/tmp/astra-656-r2.D2KaSW/out.txt:4).

   Consequently, `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:94` could raise a delegation refusal carrying a success receipt and append a misleading refusal event. Give this decision path strict conflict semantics while preserving existing receipt-retry behavior elsewhere. F10d’s sequential repeat does not fence this interleaving. **Tenet 3; VI.1.**

3. **Durable-first credential revocation is correct; F21 needs an exact commit boundary.** The identity lookup, absent-credential revocation and route-level hook pay the earlier ordering defect. Unknown credential ID → 404 is acceptable because identity-based revocation remains available.

   But `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:207` promises a receipt immediately after the grant mutation commits. The cited inline precedent performs the effect before calling `broker.receipt` (`holdspeak/desktop_typing.py:139`, `:163`); the atomic terminal helper does not include the grant-table mutation.

   Distinguish interruption after the **completed revoke operation** from interruption between its domain commit and receipt. Specify recovery for the latter. The grant can remain revoked; no rollback or general transaction framework is required. **Tenets 1/3; IX.1.**

4. **The credential matrix is coherent, but the new visibility promise lacks a fence.** Credential validity and filing permission are different facts; expired credential + live grant is legitimate. Their clarity remains the canvas’s job.

   `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:125` promises visibility without a credential. F13 reissues before filing; F22 checks revocation through the identity route. Neither proves that the owner can see and stop the surviving grant **before reissue**.

   Add that API and rendered-transition fence, including the receipt after the last grant/credential row disappears. Today’s ledger depends on `credentials.length > 0` (`web/src/pages/cores/SettingsCore.tsx:615`), precisely the branch-removal scar. Keep this on the existing face. **Tenets 3/4.**

5. **The remaining payments are ratified as design decisions.** Frozen basis parsing, caller binding, expiry classification, post-claim re-grant behavior, persistent identity grants, capability declarations and provenance plumbing fit the cited seams.

   The atomic helper accepts the proposed terminal transitions; I verified refusal from `awaiting_decision`, recovery from `admitting`, and rollback when SQLite rejects receipt insertion. [Probe output:5](/tmp/astra-656-r2.D2KaSW/out.txt:5). Receipt-before-journal-event matches `holdspeak/kernel/executor.py:124`; the event remains a separate write. An optional `warrant_revoked` keyword is a minimal extension for the reaper.

   F10c/d, F5b and F9c cover r1 MISSED 3; the revised ordering and F22 address MISSED 2. F20 still does not fully pay MISSED 1 because of finding 1 above.

CONDITIONS:

- Complete the terminal-path inventory and extend F20 to the omitted in-scope paths.
- Specify strict decision-conflict behavior and fence a terminal winner arriving between the state read and atomic call.
- Clarify F21’s two commit boundaries and recovery outcome.
- Add the no-credential visibility/Stop filing transition fence; retain the separate canvas precondition. File the named non-desk BACKLOG debt.

MISSED:

1. Highest cost: ordinary admission refusals can still become terminal without receipts.
2. Next: an idempotent receipt return can masquerade as a successful refusal CAS.
3. Next: returning surviving grants in JSON does not prove the owner can find and stop them.

TUESDAY: Conditionally yes—grant once, file immediately, and stop filing from the same face, including after the credential disappears.

UNKNOWN: Reviewed `2ce98c89`; verified R5 in `dcf3eaeb`. Isolated seam probes passed. The desk codec, fresh-process restart, canvas and actual atlas cases remain unbuilt or unverified here. No full suite or live walk was run. The tree is unchanged.