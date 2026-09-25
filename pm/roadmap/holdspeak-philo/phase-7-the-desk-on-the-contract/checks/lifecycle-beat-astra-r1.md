VERDICT: RATIFY-WITH-CONDITIONS

The core lifecycle is sound. Resolve the conditions below before using this beat as story 02’s implementation brief.

FINDINGS:

1. **Ratify identity-based persistence, optional expiry with no default, and the additive table.** Reissue really preserves the principal identity (`holdspeak/principals.py:149`, `:156`). A persistent grant need not expire with its bearer credential. These choices fit Tenets 1/3 and bounded delegation; no new owner policy round is needed. R5’s `decision.delete` belongs in the stored set.

   Freezing grant ID, hash and delegator in the operation INSERT is supported by `holdspeak/kernel/journal.py:138`. Hashing expiry uses the correct precedent (`holdspeak/services/schedule_delegation.py:37`). The proposed table and indexes are sufficient; no additional migration machinery is justified.

   **The desk codec and its `validate_claim` are still story 02’s work.** `holdspeak/kernel/executor.py:61` supplies the dispatch hook, not a desk validator.

2. **The proposed refusal sequence can permanently lose its receipt.** `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:86` explicitly copies separate `transition` and `_terminal` calls. Claim refusal and `recover_invalidated` use the same pattern.

   I submitted real `tool.call` operations and interrupted the existing rejection/claim-refusal paths immediately before `_terminal`. Both persisted `state=refused`, `receipt=NULL`; recovery and reaping each recovered zero. [Probe output:1](/tmp/astra-656-review.rEpAij/out.txt:1), [database](/tmp/astra-656-review.rEpAij/kernel.db).

   Use the existing atomic `transition_and_receipt` seam (`holdspeak/kernel/journal.py:372`) for the desk terminal paths, including recovery. This needs no new safety framework. **Tenets 1/3; XI.2.**

3. **Approval’s successful authority predicate needs explicit caller and state scoping.** `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:86` checks “own actor” only when authority fails. Its successful predicate says AGENT + prefix + valid grant; the helper compares the grant with the *operation’s* identity (`:51`). That does not explicitly bind the deciding caller to that identity.

   Require the successful branch to approve only the authenticated actor’s own granted desk operation. Define “desk grant operation” unambiguously as the admitted desk-write set, not `delegation.grant/revoke`.

   Check state/revision before terminalization: `store.transition` compares revision only (`holdspeak/kernel/publication_transition.py:33`); it does not enforce an `awaiting_decision` source state. Fence another actor’s decide and a repeated decide after terminal completion.

   The frozen-basis approach itself is sound. Specify parsing that preserves the hash’s `sha256:` prefix—split at most twice—and never substitute a grant selected by identity. **Tenet 3; XI.3–4.**

4. **The refusal table contradicts the promised outcomes.** `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:50` returns `desk_delegation_required` whenever admission finds no LIVE row. After Stop filing, that prevents the promised `desk_delegation_revoked`. At `:52`, EXPIRED also becomes “revoked” before the expiry check runs.

   Define deterministic admission fallback to the latest historical row, without using that fallback at approval or claim. Distinguish never granted, revoked and expired; repeat checks after EXPIRED has been persisted.

   Also correct `:81`: after a **re-grant** following G1’s claim check, that operation finishes under G1, while the **next** valid operation succeeds under G2. “The next write is refused” cannot cover all three columns. F9 currently fences only revoke. **Tenet 3; V.3.**

5. **Owner credential revocation must not depend on successfully removing an in-memory token first.** `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:106` places durable grant revocation after credential removal. Interruption there removes the token and its ID mapping while leaving a grant that the next reissue inherits.

   There is also a non-crash case: after expiry cleanup or self-revoke, the identity route returns `revoked=false`; the proposed success-only hook would skip a still-LIVE grant. I reproduced the credential-side precondition: expired authentication returned 401, then owner revocation by ID returned 404 and by identity returned `revoked=false`. [Probe output:4](/tmp/astra-656-review.rEpAij/out.txt:4).

   Resolve identity before removal, persist the grant revocation first, and let an explicit owner revocation by identity revoke a surviving grant even when no credential remains. Keep automatic expiry/reissue/self-revoke separate as proposed. **Tenet 3; XI.4.**

6. **The credential matrix and restart fence need correction.** “TTL expiry → no row” at `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md:100` is false until authentication performs cleanup. `list_credentials` deliberately includes expired credentials (`holdspeak/principals.py:244`); the real settings route returned an expired row with `active=false`. [Probe output:3](/tmp/astra-656-review.rEpAij/out.txt:3).

   Define the displayed combination of an expired credential and a LIVE grant. F15’s “ALLOWED iff `zone.file` succeeds” also needs valid authentication and valid domain inputs; grant permission alone cannot promise execution success.

   Replace F13’s fresh-store stand-in with a fresh-process hub restart against the same isolated database. A new store object proves neither startup recovery nor correct authentication wiring: middleware uses the captured global store (`holdspeak/web_server.py:638`). **Tenets 3/4; VI.1; IX.1.**

7. **The delegation route plan is correct, but its receipt plumbing must be explicit.** `AGENT_SUBMIT` at the edge lets an authenticated agent reach the kernel. The operation spec must likewise allow `agent.submit` to reach owner-only `authorize`; otherwise `broker.py:303` refuses earlier with `declared_capability_required`.

   Two further edits belong in the brief: today `submit` catches only the refusal reason, without forwarding grant provenance (`holdspeak/kernel/broker.py:79`), and `KernelRefused` has no receipt field (`holdspeak/kernel/model.py:19`). Name how provenance and the terminal receipt reach the response. Include malformed identifiable delegation requests in the existing R2 adapter fences.

   Preserving another actor’s operation and the existing `tool.call` owner-wait behavior is appropriate; the new desk path still owes its own terminal receipt. **Tenet 3; R2; XI.2.**

CONDITIONS:

- Amend the beat with atomic terminal receipts and explicit approval caller/state checks.
- Reconcile historical refusal codes and all three post-claim interleavings.
- Settle durable-first owner revocation, absent-credential behavior and expired-row presentation.
- Extend the fences for these cases; make F13 a real process restart and specify the receipt/provenance plumbing. Retain story 02’s separate canvas precondition.

MISSED:

1. Highest cost: a terminal operation can become permanently invisible to receipt recovery.
2. Next: credential disappearance can prevent explicit owner revocation from ending persistent authority.
3. Next: the fence list does not yet prove cross-actor decision isolation, repeated expiry classification, or post-claim re-grant behavior.

TUESDAY: Conditionally yes—grant once beside the credential, file immediately, and see a durable named result; expiry and revoke must not leave the owner guessing.

UNKNOWN: Reviewed `0c8ddce5` and R5 on `dcf3eaeb`. Both checked-in probes are honest: independently collected two and ran both successfully (`2 passed`). Additional isolated probes verified the receipt gap and credential behavior above. The desk implementation, real restart, canvas and atlas walk remain unverified. The tree is unchanged.