# Check — Muad'Dib, 2026-09-27 (round 1)

Checker: Muad'Dib's Fedaykin worker (Claude Opus 5.5), acting for Muad'Dib
on PR #678, branch `design/philo-9-02-steward-beat` @ `470b3b43`. This is
Muad'Dib's first check of the beat. The two earlier files were an
Astra-invoked Claude session; they are relabelled
`steward-beat-astra-invoked-claude-r1.md` / `-r2.md` (handover XXIX law 8).
Code anchors are read at the source pin `ffbeb04b` (product code is the
same on this branch).

VERDICT: RATIFY-WITH-CONDITIONS (both conditions docs-only; paid in the beat
in this round)

## FINDINGS

1. **Labelling defect, fixed.** Astra recorded its own `claude -p` session
   (`claude-fable-5-1`, `473a5a59…`) as "Check — Muad'Dib", and the README
   Status and `current-phase-status.md` "Where we are" said "Muad'Dib's reply
   is RATIFY". Muad'Dib had not checked the beat. Files moved and retitled;
   README:3-8, README "Notes for the story 02 brief" heading and
   `current-phase-status.md` "Where we are" corrected. The commit message of
   `470b3b43` still says "Muad'Dib RATIFY"; history is not rewritten.
2. **(1) Async lifecycle: settled.** The pending handle, the run-to-operation
   link, one terminal winner, stop and restart are specified (README §2-§3).
   The seam is real: `transition_and_receipt` runs `BEGIN IMMEDIATE`, the
   receipt check, the strict revision CAS and then `effect(conn)` in one
   transaction (`holdspeak/kernel/journal_atomic.py:83-120`). The beat
   correctly rereads the run's stop flag inside the callback, because a separate
   stop operation does not move the run operation's revision (README §3).
   Today's gap is confirmed: insert-then-daemon, `run_id` only
   (`holdspeak/web/routes/steward.py:100-119`,
   `holdspeak/mcp/families/project.py:1594-1628`). Recovery runs on an
   under-composed service (`holdspeak/web_server.py:1310-1322`).
3. **(2) Child authority: settled, no owner manufactured.** Confirmed: a
   same-identity AGENT child fails `parent_continuation_identity_required`
   (`holdspeak/kernel/causation.py:35-42`). The beat adds one validated
   steward predicate as an alternative at four named seams, and leaves
   generic agent children refused. Seams checked: `broker.py:195-209`,
   `:298-310`; `executor.py:61-66`. Effects outside the grant
   (`apply_proposal_effects` → `decide_proposal`) run only when the policy
   is eligible, as R4-1 requires (`current-phase-status.md:423`). Children
   name both authorities through `authority_details`. Revoke/expiry cutoff
   is Phase 7's claim-check boundary (`phase-7…/design/grant-lifecycle-beat.md:76-87`).
   Stop is bound to `requested_by` (`project_steward_service.py:467`) and
   to the operation's actor.
4. **A deliberate difference from Phase 7, stated correctly.** Phase 7 F9c
   lets the next desk write succeed under a re-grant G2
   (`grant-lifecycle-beat.md:87`). The beat refuses the next child inside a
   running parent ("G1 is never replaced by G2"). This is right: each desk
   write is its own root, but the run froze G1. A3 fences it.
5. **(3) B2 placement: settled and lawful.** The exact method+path patterns
   get AGENT_SUBMIT in `required_right` before the OWNER default
   (`holdspeak/principals.py:296-355`; the PHILO-7-02 precedent at `:328-331`).
   The gate fires before the route (`holdspeak/web_server.py:654-657`).
   AGENT holds AGENT_SUBMIT (`principals.py:47-53`). The adapter reapplies
   the old right to a valid exempt form, so reads and exempt edits keep
   their protocol refusal. This agrees with Phase 7's four refusal classes
   (`holdspeak/services/desk_kernel.py:10-24`).
6. **(4) Fences per rule: present.** L1-L7, A1-A7, H1-H3 and D1-D2 cover
   each rule (README §7). Each row names a behavioral red or a mutation, and
   the beat does not claim any fence as present.
7. **Tenet 1: passes.** Reuses `transition_and_receipt`, the imported
   `_hash` (`holdspeak/services/schedule_delegation.py:37-39`), the desk
   startup-recovery precedent (`holdspeak/kernel/desk_broker.py:125-140`)
   and the executor's claim hook. It adds no kernel state and no second
   engine. Storage is two additive columns plus one on policies. Small
   redundancy: `authority_sha256` wraps `policy_sha256`. This is acceptable
   and not a condition.
8. **Policy provenance hole (C1).** `project.archive` also writes the policy
   (`unattended_enabled=0`, `holdspeak/services/project_service.py:3029-3035`).
   As drafted, only configure stamped `configure_operation_id`. A later
   snapshot would pair archive-changed terms with an older configure
   operation.
9. **No-policy owner digest left to a worker (C2).** Before this round, the
   brief notes delegated "fixed empty-terms digest" and the mid-run
   first-save rule to the story 02 brief. That is a design decision, so it
   belongs in the beat.
10. **Cross-story face obligation.** README §4 requires the face to show
    `steward_policy_required` ("story 03 face"), but story 03's file does not
    name it. This is a brief item for Muad'Dib's lane and not Astra's.
11. **Owner rulings unchanged.** The Q2 bound is intact; delivery and
    project-grant operations are kept out of the grant set (README §3).
    Mark delivered, `nudge.send`, configure and trigger stay owner-only.
    `github_comment` only prepares a nudge; this is verified at
    `project_steward_service.py:1528-1540`, and the charter row
    "`github_comment` crosses egress" (`current-phase-status.md:159`) is
    corrected as grounding, not as a ruling.
12. **Anchors verified at the pin:** `steward.py:99-119`; `project.py:1594-1628`;
    `project_steward_service.py:467`, `:804`, `:852`, `:871`, `:1263`,
    `:1313-1330`, `:1528`; `project_delta_service.py:1848`; `causation.py:28-42`;
    `broker.py:201`, `:304`; `executor.py:46-66`; `journal_atomic.py:58`, `:83`;
    `desk_broker.py:125`; `workbench_conductor.py:621`; `schema.py:4194-4196`,
    `:4211`; `principals.py:354`; `web_server.py:655`, `:1317`;
    `kernel/model.py:76`; `schedule_delegation.py:37`; `kernel/desk.py:56`, `:77`.
    All match.

## CONDITIONS

- **C1 (paid, docs):** `project.archive`'s atomic callback sets
  `configure_operation_id` to the archive operation. The column names the
  latest owner operation that wrote the terms. README §4 and A4.
- **C2 (paid, docs):** a no-policy owner run freezes `policy_id=null`,
  `configure_operation_id=null` and `policy_sha256=""`. Policy boundary
  checks apply only to a run that froze a policy id. A first policy saved
  mid-run does not stop it. README §4, A4 and the brief notes.

No condition is owed by Astra.

## MISSED

- The archive write to the policy (finding 8).
- The story 03 face half of `steward_policy_required` (finding 10). It goes
  into the story 03 brief.

## TUESDAY

Yes. He starts the steward, and it returns a handle at once. He stops it and
sees two receipts. After a restart he finds one named result. His agent,
under the three-operation grant, drafts and publishes within his policy,
and each receipt names both the grant and the policy.

## UNKNOWN

- The owner's assignment of this beat's lane to Astra (the lane table now
  says the checker is Muad'Dib, not Codex Astra) is recorded only by Astra,
  who quotes its own task prompt. I did not see the owner's words.
- I did not rerun the two probes or the 160 focused tests. No claim looked
  wrong against the code I read.
- `steward_policies` has no unique key on `project_id`. The read takes the
  newest row (`holdspeak/db/steward.py:171-174`). The frozen `policy_id`
  binds the exact row, so I judge this harmless. It is not verified by a
  run.
