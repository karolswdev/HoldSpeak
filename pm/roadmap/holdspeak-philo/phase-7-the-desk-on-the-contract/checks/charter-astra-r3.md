VERDICT: RATIFY-WITH-CONDITIONS

Suitable to present as a conditional charter. R1–R4 settle the earlier policy questions. The remaining conditions concern refusal coverage and the grant’s lifecycle.

FINDINGS:

1. **A kernel-owned grant row is sufficient; a signed parent continuation is not required.** The schedule precedent explicitly derives authority from the LIVE row and its terms hash: `holdspeak/kernel/schedule_delegated.py:17`. Signed continuation identities govern the separate live-parent path: `holdspeak/kernel/causation.py:46`. Keep those paths distinct.

   **The cited receipt fields exist:** `actor_kind`, `actor_identity`, `delegator_kind`, `delegator_identity`, `authority_basis`, and `target_ref` are returned by the shared join: `holdspeak/kernel/journal.py:22`. Their presence does not populate them automatically; the proposed kernel integration remains necessary.

2. **Grant recognition needs a precise admission-to-execution invariant.** The `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:238` specifies checks at admission and approval, but does not settle revocation, expiry, or replacement between those checks and execution.

   Freeze the selected grant ID and terms hash at admission; approval must not substitute a newly granted row. Include expiry in the hashed terms, as the `holdspeak/services/schedule_delegation.py:37`. Define the execution cutoff and fence revoke/expire/regrant interleavings. The existing `holdspeak/kernel/executor.py:61` supplies an appropriate seam.

   A refusal during approval must also terminalize the existing operation: `holdspeak/kernel/broker.py:204` currently raises without writing a receipt. Removing HELD does not remove that transient state. **Tenets 1/3; XI.2–3.**

3. **The refusal classes miss identifiable attempts rejected before `invoke`.** I reproduced these through an isolated real hub:

   - HTTP and MCP decision updates carrying a duplicate `decision_id`: refusal from `holdspeak/operations.py:670`.
   - MCP `zone.file` missing `directory_id`: schema refusal before dispatch reaches the registry, `holdspeak/mcp/tools.py:767`.
   - MCP `zone.file` with non-object arguments: `holdspeak/mcp/server.py:402`.
   - HTTP decision creation with a non-object body: `holdspeak/web/routes/primitives/decisions.py:50`.

   Each produced **zero registry calls, zero operations, zero receipts, and zero decision changes**. A registry-only implementation of `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:216` misses them.

   Extend the fences to authenticated, identifiable consequential refusals at the adapters. Explicitly classify the existing palette refusal too: `holdspeak/mcp/tools.py:1176`. Preserve the ruled unknown/read/exempt exceptions. **Tenet 3; R2; V.2/XI.2.**

4. **Credential replacement and grant lifetime are not yet reconciled.** Reissuing through the real settings route produced a new credential ID with the **same principal identity**; the old token returned 401 and the replacement worked. Issuance revokes the previous credential internally: `holdspeak/principals.py:149`. Credentials also disappear on restart: `holdspeak/principals.py:103`.

   The proposed grant persists in the database and keys authority by that reusable identity. Specify whether it survives replacement/restart, and make issue, expiry, explicit revoke, reissue, and the row’s chip agree. I reproduced identity reuse, **not a delegation bypass**—the delegation is unbuilt. **Tenets 1/3; XI.4.**

5. **The Remote Access row is the smallest lawful location; the proposed wording overpromises.** The existing row already composes `SurfaceLedgerRow` and library `Button`: `web/src/pages/cores/SettingsCore.tsx:627`. The gate face indeed serves held proposals.

   However, **“Stop desk writes” does not stop desk writes**: R4 preserves plain note edits, renames, and other exempt writes. Scope the verb to delegated filing/decision actions. The small canvas must show grant, revoke, and failure transitions; fence the rendered result after the row changes, at both widths. No additional permissions screen is needed. **Tenets 3/4/5.**

6. **The rename repair and its proposed fences are correct.** I independently repeated both real-service interleavings, pausing after the actual read:

   - KB rename left newly added `note:b` with `deleted=1`.
   - Zone rename restored `child.parent_id="p1"` after the intervening move to `p2`.

   [Probe database](/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/astra-p7-r3-interleave-h5mhojep/probe.db). No injected rows or fabricated read results. `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-01-notes-and-directories-on-the-contract.md:32` specifies the right survival assertions. Keep genuinely plain renames exempt.

7. **Deferred rulings:** retain `decision.delete` outside the grant; R4 admission does not itself enlarge R1 delegation. Include `decision.status` as update, and `zone.delete` plus Thought-owned `note.delete` as the confirmed placement effects. These match `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/current-phase-status.md:236`.

   Story 04 correctly requires a second cold-context session using a real DESK bearer on `/api/mcp`: `pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/story-04-file-it-and-find-it-without-the-repo.md:39`. Ratify the observational claim. Bearer handling remains a legitimate first-run unknown; an owner-token fallback would not satisfy this leg.

8. **Phase 7 has no `dw check` finding.** `.githooks/dw check holdspeak-philo` exits 1 solely because this branch lacks Phase 6’s `final-summary.md`. Main contains it; `0c23750d` is the Phase 6 closure merge. Report “no Phase 7 issues,” not “project check green.”

CONDITIONS:

- Before unconditional ratification, extend refusal coverage to the concrete pre-registry paths in finding 3.
- Before story 02’s implementation brief, check one short lifecycle design covering findings 2 and 4, including terminal receipts for interrupted approval. This is the design beat required by `docs/internal/ORCHESTRATION.md:143`.
- Before face build, ratify the small canvas with accurately scoped verbs and rendered transition fences.
- Record these remaining conditions explicitly; R1–R4 need no further policy round.

MISSED:

1. Highest cost: a known filing/decision refusal can still disappear before the receipt-producing path.
2. Next: grant replacement, revocation, and credential reuse lack one consistent authority/lifetime rule.
3. Lower: the active README still promises “without repository access” without R3’s qualification (`pm/roadmap/holdspeak-philo/README.md:29`). Update current pointers with the amended claim.

TUESDAY: Yes, conditionally: grant once beside the credential, file/find/review through ordinary words, and receive a named result; the control must accurately say which actions it stops.

UNKNOWN: Reviewed `10b313b2`, ran lint, isolated real-hub probes, credential lifecycle probes, and both rename interleavings. No Phase 7 implementation, canvas, fresh Codex rehearsal, atlas walk, or full suite was verified. The worktree remains unchanged.