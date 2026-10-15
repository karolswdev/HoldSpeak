# Follow-through backend build — 2026-10-15

**DRAFT · UNCHECKED — awaiting Muad'Dib. HOLD FOR SHIP.**

Base `420a0eb28`; worktree `/Users/karol/dev/tools/wt-follow-through-20261015`.
Implemented `holdspeak/services/follow_through_service.py`,
`tests/unit/test_follow_through_service.py`, and the explicitly authorized
parking expectation update in one existing `test_meeting_service.py` case.
Root owns live walks, final review,
quick check, staging, PR, merge, and release.

Tenets 2/3/5/7: a new task can leave the board when snoozed; an accountable
decision has one obligation and its existing writer. No new schema, service,
collector, route, status authority, or People persistence.

## Changes

- `holdspeak/services/follow_through_service.py:514`: validate the existing
  nonempty-string Snooze payload, insert a missing canonical
  `(meeting_action, action.id)` loop with the existing table defaults, then
  apply the existing snooze update in the same connection transaction. Return
  the stored loop id. Repeat Snooze reuses that id. Other verbs create no loop.
  The action's owner, due date, source, status, and other stored fields remain
  unchanged by Snooze.
- `holdspeak/services/follow_through_service.py:176`: one canonical action /
  optional decision-commitment relation query supplies the identities for
  board deduplication. A represented decision loop is suppressed before
  recollection, including after Done. Genuine standalone decision loops and
  equal-text unrelated loops remain independent.
- `holdspeak/services/follow_through_service.py:168`: on filtered boards, reuse
  the existing loop query without owner/project filters for action enrichment.
  The canonical action's Snooze facts survive stale loop display fields.
  Standalone loop display continues to use the requested filters.

### Explicit amendment from root

The first patched run exposed an existing action-mirror issue: delegate an
action from Ada to Grace after creating its action loop, then read the board
with `owner=Ada`. The action row was filtered out, so its stale Ada loop became
a separate card (`.tmp/follow-through/backend-green.log`; 41 passed, 1 failed).
Root explicitly authorized the narrow same-deduplication amendment: canonical
action identity governs mirror suppression under owner/project filters, with
no owner writer changes or new projection. The same relation query now includes
all action ids; it suppresses both action and decision mirrors independently
of a filtered action list. The focused regression retains stale Ada action and
decision loops while asserting that Ada sees neither and Grace sees the action.

Root then authorized one bounded completion of the same canonical-fact seam:
Snooze must remain effective after changing the action's owner, including an
owner-filtered board whose loop still carries the old owner. The new regression
first failed with `1 failed, 43 passed in 3.00s`
(`.tmp/follow-through/backend-enrichment-red.log`), showing the snoozed action
on Grace's filtered board. The existing loop query is now reused for source
enrichment, with no writer changes, new controller, or new projection. The test
also proves the canonical Grace action returns at expiry and independent Ada/
Grace loops retain their requested owner filters. The backend files are frozen
after this completion; root owns the final source review.

## Scoped proof

Every pytest invocation used `.venv/bin/python .tmp/follow-through/locked.py`
with the exact three allowed files (plus one authorized parking node at the
final scope extension), an isolated scratch HOME, machine test lock,
the wrapper's machine-state isolation flags, and `-n 8 --dist worksteal` for
execution. No browser, build, install, provider CLI, hardware, or owner DB access.

Collection command:

```sh
.venv/bin/python .tmp/follow-through/locked.py backend-enrichment-collect .venv/bin/python -m pytest --collect-only -q tests/unit/test_follow_through_service.py tests/unit/test_follow_through_pipeline.py tests/unit/test_follow_through_person_enrichment.py
```

New collected names (full output: `.tmp/follow-through/backend-enrichment-collect.log`):

```text
tests/unit/test_follow_through_service.py::test_new_note_task_snooze_creates_one_durable_canonical_loop
tests/unit/test_follow_through_service.py::test_collector_upsert_keeps_snoozed_action_identity_and_lifecycle
tests/unit/test_follow_through_service.py::test_snooze_survives_owner_filter_until_expiry_after_delegate
tests/unit/test_follow_through_service.py::test_snooze_keeps_existing_nonempty_string_input_compatibility[ 2099-01-01 ]
tests/unit/test_follow_through_service.py::test_snooze_keeps_existing_nonempty_string_input_compatibility[2099-01-01T09:30:00Z]
tests/unit/test_follow_through_service.py::test_snooze_keeps_existing_nonempty_string_input_compatibility[tomorrow]
tests/unit/test_follow_through_service.py::test_refused_snooze_does_not_create_a_loop[None]
tests/unit/test_follow_through_service.py::test_refused_snooze_does_not_create_a_loop[]
tests/unit/test_follow_through_service.py::test_refused_snooze_does_not_create_a_loop[ ]
tests/unit/test_follow_through_service.py::test_refused_snooze_does_not_create_a_loop[123]
tests/unit/test_follow_through_service.py::test_snooze_loop_creation_rolls_back_if_the_transition_fails
tests/unit/test_follow_through_service.py::test_unrelated_action_verbs_do_not_create_loops[done-None]
tests/unit/test_follow_through_service.py::test_unrelated_action_verbs_do_not_create_loops[dismiss-None]
tests/unit/test_follow_through_service.py::test_unrelated_action_verbs_do_not_create_loops[delegate-payload2]
tests/unit/test_follow_through_service.py::test_unrelated_action_verbs_do_not_create_loops[due-payload3]
tests/unit/test_follow_through_service.py::test_unrelated_action_verbs_do_not_create_loops[reopen-None]
tests/unit/test_follow_through_service.py::test_collected_decision_is_represented_by_its_action_not_a_second_loop

44 tests collected in 0.87s
```

Initial red, before product changes (`backend-red.log`): 42 collected;
`6 failed, 36 passed in 3.29s`. Missing canonical Snooze loop failed the real
Note/Thought + Door producer case and three accepted-input variants. An SQLite
trigger exposed the no-op transition; real accepted decision → commit → collector
exposed the duplicate card. The later additional collector-upsert case was not
part of that initial red run.

Backend completion command and complete tail before the parking pin update:

```sh
.venv/bin/python .tmp/follow-through/locked.py backend-enrichment-green .venv/bin/python -m pytest -q -n 8 --dist worksteal tests/unit/test_follow_through_service.py tests/unit/test_follow_through_pipeline.py tests/unit/test_follow_through_person_enrichment.py
```

```text
bringing up nodes...
bringing up nodes...

............................................                             [100%]
44 passed in 3.18s
```

Source assertions cover the new open task before collection; one durable loop
and returned identity after repeated Snooze; unchanged action row; actual
collector missing-source and source-upsert passes preserving Snooze; cadence
repository source-upsert preservation; transactional rollback on failure;
invalid input refusal; unrelated verbs; standalone/equal-text loops; stale-owner
mirror suppression; owner-filtered Snooze through delegation and expiry;
and canonical Done/decision-commitment closure. Existing
pipeline and person-enrichment/privacy scopes also pass. `git diff --check`
passed for the two owned code/test files.

## Quick-check parking expectation adaptation

Root's first release quick check recorded `1 failed, 1334 passed in 20.68s`
in `.tmp/follow-through/quick-release/py.log`. This is root's affected Python
run, not a broader worker run. Its sole failure was
`test_follow_through_decision_commitment_hides_parked_source_and_restores_it`
at `tests/unit/test_meeting_service.py:2562`: the old assertion required the
decision mirror to appear alongside the commitment's canonical action.

Root explicitly authorized adapting only that existing case. Before and after
restore, the canonical action ids must remain visible and action/decision loop
mirror ids must be absent. The parked-state all-hidden assertion is unchanged,
as is the exact physical action-loop id restoration check. No backend source
change was made for this expectation update.

Final collection and run use the original three files plus that exact node:

```sh
.venv/bin/python .tmp/follow-through/locked.py backend-parking-collect .venv/bin/python -m pytest --collect-only -q tests/unit/test_follow_through_service.py tests/unit/test_follow_through_pipeline.py tests/unit/test_follow_through_person_enrichment.py tests/unit/test_meeting_service.py::test_follow_through_decision_commitment_hides_parked_source_and_restores_it
.venv/bin/python .tmp/follow-through/locked.py backend-parking-green .venv/bin/python -m pytest -q -n 8 --dist worksteal tests/unit/test_follow_through_service.py tests/unit/test_follow_through_pipeline.py tests/unit/test_follow_through_person_enrichment.py tests/unit/test_meeting_service.py::test_follow_through_decision_commitment_hides_parked_source_and_restores_it
```

Additional collected node and summary (`backend-parking-collect.log`):

```text
tests/unit/test_meeting_service.py::test_follow_through_decision_commitment_hides_parked_source_and_restores_it

45 tests collected in 0.84s
```

Final complete run tail (`backend-parking-green.log`):

```text
bringing up nodes...
bringing up nodes...

.............................................                            [100%]
45 passed in 3.17s
```

Backend and test files are frozen again for root's second quick check and final
source review. No other test case or source was changed in this scope extension.

## Unknowns and limits

No live route, browser, 1440/393 screenshot, owner desk, encrypted sidecar,
or release outcome is claimed. Root must verify those. Accepted Snooze input
compatibility is unchanged: a nonempty non-date string is stored, although only
an interpretable future date/stamp hides a card.

**HOLD FOR SHIP.**
