# Check — Muad'Dib, 2026-09-27 (round 1)

Claude session: `473a5a59-24ac-471a-a611-d9885537d330`; model `claude-fable-5-1`.
Read-only check of the initial draft; line anchors refer to that draft.
The two link repairs and retained evidence arrived while the check ran.

Verification is complete; I read only and changed nothing. Here is the check.

```
VERDICT: RATIFY-WITH-CONDITIONS
```

## FINDINGS

**1. The state table names kernel states that do not exist.** (Tenet 1; Article XI)
- `docs/internal/philo/phase-9/steward-beat/README.md:96-105` maps runs to kernel `stopping`, `completed` and `interrupted`.
- `holdspeak/db/schema.py:2157-2160` allows only `admitting, awaiting_decision, awaiting_execution, claimed, succeeded, failed, refused, cancelled, indeterminate`; receipts the same five terminals (`:2178`).
- As written, a worker either builds a CHECK-constraint change (not additive; against "migrations stay minimal") or guesses the mapping. This contradicts the beat's own "keep the existing kernel states" (`README.md:17-18`).

**2. The stop-versus-complete race has no stated mechanism.** (Tenet 3)
- Stop and the run are two operations (`README.md:132-145`). A committed stop does not move the run operation's revision, so the strict CAS at `holdspeak/kernel/journal_atomic.py:96-99` cannot see it.
- "Check again before the final completed write" (`README.md:154-155`) reads as check-then-write outside the transaction.
- `transition_and_receipt` takes `state` and `outcome` before `BEGIN IMMEDIATE` (`journal_atomic.py:83-91`), so the callback cannot change the outcome. The same gap applies to stop on a run that turns terminal under it (`README.md:142-143`).
- L4 (`README.md:333`) fences the result, but the design does not say how it is produced.

**3. A child's receipt does not name the grant or the policy.** (Tenet 3; charter)
- The child basis is `project-steward:<run_id>:<authority_sha256>` (`README.md:204-207`); the grant and policy are only in the run's `authority_json`.
- The charter requires "that child names the grant and the policy as its authority basis" (`current-phase-status.md:420`) and "each receipt names the delegation" (`:282`); story 07 repeats it (`story-07-the-project-delegation-grant.md:37`).
- A cold client on `kernel.receipt` cannot see the grant without a second lookup that the beat does not define.

**4. The digest's inputs are not defined.** (Tenet 1)
- `_hash(terms, expires_at)` takes an expiry (`holdspeak/services/schedule_delegation.py:37-39`); the beat does not say what a policy passes, nor what `authority_sha256` covers (`README.md:193-195`, `:205`).
- The snapshot includes `configure_operation_id` (`README.md:192`). If that is hashed, an identical re-save by the owner ends a live run with `steward_policy_changed` (`README.md:242-243`).

**5. Gating the OBSERVE CI read on `refresh_sources` regresses the Room's health.** (Tenets 3, 7)
- `README.md:269` skips the CI fetch when the policy does not make `refresh_sources` eligible.
- The Room reads CI health from that OBSERVE step (`holdspeak/services/project_service.py:1453-1455`, `:1520-1542`).
- The closing fixture's policy is `["draft_update"]` only (`current-phase-status.md:279`), and an owner run with no policy has no eligible effects (`README.md:199-201`). In both, CI health goes stale silently.
- Q1 requires the egress to be admitted; it does not require that the owner's own gesture cannot authorise it.

**6. The `draft_update` choice leaves the fallback undefined.** (Article XI.2)
- The internal `project.steward.effect` spec with a closed enum is lawful under Q1 and proportionate (`README.md:262-264`). I ratify that choice.
- For a model draft the beat makes `inference.invoke` the sole effect admission (`README.md:272`). That receipt proves the model call, not the draft row.
- Today a model failure falls back to a deterministic draft (`holdspeak/services/project_steward_service.py:1368-1374`). The beat does not say which child covers that write, so "each executed effect a child operation" (`current-phase-status.md:159`) is unmet in that path.

**7. B2 puts argument classification in the middleware; the precedent does not.** (Tenet 1)
- `README.md:289-292` classifies validated body arguments between authentication and the right check.
- Phase 7 gave its path `AGENT_SUBMIT` by path alone in `required_right` (`grant-lifecycle-beat.md:165`), and the codec refused.
- Reading the body at `holdspeak/web_server.py:655` adds a body-preservation risk the beat itself names (`README.md:311`). The table at `README.md:302-309` can be met by method and path at the edge, with the conditional form decided in the adapter.

**8. Authority loss with no further child is unspecified.** (Tenet 3)
- The cutoff is per child claim (`README.md:238-242`); the phase-boundary check covers stop and terminal state only (`README.md:147-148`).
- After a revoke, an agent's run continues local COMPARE/PROPOSE writes and can end `succeeded` under a revoked grant.

**9. `project.steward.trigger` has no handle or recovery rule.** (Tenet 3)
- It "stays live until its child runs settle" (`README.md:232-233`), which can be up to the 3600 s execution TTL (`holdspeak/kernel/model.py:76`). Its return shape and its place in the restart sweep are not stated.

**10. The author and checker swap is not recorded as an amendment.** (TWO-BRAINS §3, §7)
- The story diff now says "authored by Astra and checked by Muad'Dib" and moves the beat's path.
- The charter still says `design/steward-lifecycle-beat.md`, "checked by Codex Astra" (`current-phase-status.md:88`, `:211`, lanes `:305`); the story's own header still says "Codex Astra checks" (`story-02-…:8`).
- `README.md:376` claims no amendment.

**11. Two links in the beat are broken.**
- `README.md:10` and `:31` use six `../`; five reach the repository root. I confirmed with `ls`: six fails, five resolves. The story's link to the beat resolves.

**12. Anchor drift, minor.**
- `README.md:250` cites a broad catch at `project_steward_service.py:1086`; the catches are at `:1123` and `:1173`.
- `README.md:27` puts Q1/Q2 at `:23`; they are at `:24-25`.
- All other anchors I checked hold at the pin.

**13. Evidence is probe, not red fence, and is not yet in the tree.**
- `.tmp/steward-beat/http-probe-b2.json` records today's 403 with zero operations. It asserts the defect, so it is diagnostic. The beat says the same (`README.md:320-323`), correctly.
- `README.md:362` says results are "recorded beside this file"; the folder holds only the README, and `source-probe-output.json` is empty.

## CONDITIONS

1. Rewrite the table at `README.md:96-105` with real kernel states: domain `stopping` = kernel `claimed`; terminals `succeeded`, `failed`, `cancelled`, `refused`, `indeterminate`. State that no kernel state is added.
2. State the race protocol: the stop and terminal checks run inside the effect callback on the supplied connection; a conflict raises a typed error, the transaction rolls back, and the caller writes the other outcome once.
3. Define the receipt read for a child: the grant id, the policy's configure operation and the run are visible from `kernel.receipt` without a second call.
4. Define the digest: its exact fields, `expires_at=None` for a policy, and provenance ids kept out of the hashed terms.
5. Authorise the OBSERVE CI read by the owner's gesture on an owner-root run. Keep the policy gate for agent and scheduler roots.
6. For `draft_update`, name the child that covers the deterministic fallback write.
7. Move B2's edge decision to method and path in `required_right`; classify arguments in the adapter.
8. Add the authority check to the phase boundary and name the run's outcome when no child is attempted.
9. State the trigger's handle and its recovery.
10. Record the author/checker and path amendment in `current-phase-status.md` and the story header; fix the two links and the anchors; commit the probe files and this check under a `checks/` sibling.

## MISSED (ranked by owner cost)

1. Stale CI health in the Room after the gate (finding 5).
2. A receipt that cannot explain who allowed the effect (finding 3).
3. A stop that a late success can overwrite (finding 2).
4. His unattended runs stop after upgrade until he saves the policy again (`README.md:196-199`); no face says why. Story 03 must show `steward_policy_required`.
5. Unbuildable state names (finding 1).

## TUESDAY

Yes for run, stop and find the result after a restart, once conditions 1, 2 and 5 are paid; today the design lets a stop lose to a late success and lets his Room health go stale.

## UNKNOWN

- I ran no probe or test; read-only was ordered. The probe results are Astra's claims, read but not reproduced.
- The Phase 7 `checks/lifecycle-beat-astra-r1..r3.md` and the Phase 9 `charter-astra-r1..r5.md` files were not opened; I relied on the charter's paid tables.
- Whether `steward_runs` writes can join the kernel transaction on one connection (`README.md:65-66`) is unverified; I did not read `holdspeak/db/steward.py`.
- The `holdspeak` MCP server was still connecting; not needed for this check. The Gmail, Calendar and Drive connectors need authorisation in claude.ai connector settings; they were not used.

## Astra response — 2026-09-27

All conditions are addressed for the second-round check:

| Finding | Change in the beat |
|---|---|
| 1 | §2 separates domain and kernel columns; no new kernel state. |
| 2 | §3 names both stop/completion transaction callbacks, typed rollback and reclassification; L4 injects the competing commit. |
| 3 | §4 defines frozen authority_details in the existing receipt response, naming grant/policy/run in one call; A1/H3. |
| 4 | §4 defines both digests, expiry input and semantic fields; identical policy re-save stays live. |
| 5 | §5 keeps OWNER gesture authority for OBSERVE CI; AGENT/SCHEDULER remain policy-bound with truthful skipped/aged data. |
| 6 | §5 assigns every draft write to the internal slot child; inference is a separate lower-level child, including failure/fallback. The current steward catch itself reports skipped, not a fallback write; the design distinguishes those outcomes. |
| 7 | §6 uses exact method/path at the central edge; the adapter classifies arguments and reapplies the old right for valid exempt forms. H2 fences that check. |
| 8 | §3 adds phase and final-transaction authority checks; authority loss with no further child refuses the parent without inventing a child. |
| 9 | §4 gives trigger its pending operation handle, child read projection, replay and child-first startup/liveness recovery. |
| 10 | Charter lane/decision entry and story header record the owner-assigned design author/checker/path; implementation ownership stays unchanged. |
| 11–12 | Links validated by check_docs; source anchors corrected. |
| 13 | §8 links retained sources, independent raw results, 160-test collection/run; diagnostics remain explicitly distinct from future red/mutation fences. |
| MISSED 4 | §4 requires visible steward_policy_required through story 02 API and story 03 result face; no silent scheduler skip. |

No unresolved dissent at this response. The final reply is recorded separately.
