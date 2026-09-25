# PHILO-7-01 round two — Astra's check on built (r1), conditions paid

- **Check:** `checks/story-01-built-astra-r1.md` — RATIFY-WITH-CONDITIONS ("merge after findings 1 and 2").
- **Branch:** `feat/philo-7-01-notes-directories`; round one = `2ad17ee8` (the story was already `done`, so the gate keeps `evidence-story-01.md` as it was; this file is the round-two record).
- **Author:** the Fedaykin lane (Opus 5.5) for Muad'Dib.

## Finding 1 (highest cost) — the rig dropped arguments on read/delete projections

**Cause.** `scripts/graph_walk.py` `_op_arguments` projected `note|zone|kb .read|.delete` (and, inherited from Phase 5, `decision.read`) to `desk.get`/`desk.delete`, whose MCP envelope carries `kind` and `id` only, and kept the id while silently dropping every other argument. The rig therefore sent a different request than the case stated.

**Repair.** `_id_only` (`scripts/graph_walk.py:793`), called for `decision.read` (`:825`) and for the slice's read/delete rows (`:838`): any argument other than the id makes the rig refuse the step by name (`Blocked`: "cannot carry args [...] through its MCP envelope (kind and id only)") BEFORE any request is sent. The step records `blocked` — never a success and never a refusal it did not observe. A case that needs the registry's `authority_in_arguments` refusal proves it through an operation whose envelope carries the arguments (create, update: the `data` slot reaches `invoke` unchanged). The published MCP schemas are unchanged (no `data` slot was added to `desk.delete`).

**Fences** (`tests/unit/test_philo7_rig_faithful.py`, through the REAL hub `MeetingWebServer` over `/api/mcp` via the rig's own `_op_call`):

- (a) `test_a_refused_call_never_becomes_an_execution_through_the_rig` — the registry refuses `note.delete {note_id: "n", owner: "forged"}` (`authority_in_arguments`); through the rig the step is blocked and the note is still live.
- (b) `test_valid_thought_revisions_never_disappear_through_the_rig` — `note.delete` of a Thought's note with its valid cursors: the rig either carries both cursors or blocks the step by name with the note untouched.
- `test_no_read_or_delete_projection_drops_an_argument[...]` — every read/delete projection (seven, `decision.read` included) carries an extra argument or blocks on it; `test_an_id_only_read_and_delete_still_project` — the id-only envelope is unchanged.

**Red on round one `2ad17ee8` (before the repair), first lines:**

```text
E           AssertionError: the rig executed a refused call: {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': 'desk.delete', 'arguments': {'kind': 'notes', 'id': 'n'}}}
E       AssertionError: the rig dropped ['expected_aggregate_revision', 'expected_lifecycle_revision']; the hub answered {'code': 'thought_expected_revision_required', 'error': 'thought-owned notes require aggregate and lifecycle revisions'}
E       AssertionError: note.read dropped extra_field: {... 'arguments': {'kind': 'notes', 'id': 'x'}}}
E       AssertionError: note.delete dropped extra_field: ...
E       AssertionError: zone.read dropped extra_field: ...
E       AssertionError: zone.delete dropped extra_field: ...
E       AssertionError: kb.read dropped extra_field: ...
E       AssertionError: kb.delete dropped extra_field: ...
E       AssertionError: decision.read dropped extra_field: ...
9 failed, 1 passed
```

**Green after:** 10 passed (the file), with `tests/unit/test_philo5_graph_op.py` 16 passed beside it. No atlas case sends `decision.read` with arguments beyond `decision_id` (scanned `docs/internal/philo/graph/atlas*.json`), so the inherited `decision.read` guard blocks nothing that runs today.

## Finding 2 — `kb.create`'s admission condition missed the mapping form

**Cause.** The declared condition said "member_ids is a list that is not empty"; MCP accepts `member_ids` as a mapping (main and round one), and the repository iterates its keys (`holdspeak/db/primitives.py:406`), filing live memberships. Reproduced on a `git archive` copy of main `02a862f2`, through the real MCP dispatch:

```text
main 02a862f2: MCP desk.create kbs with member_ids={'note:n': True} accepted; live memberships: ['note:n']
```

**Repair.**
- `Admission` carries the condition itself as a predicate over the validated arguments, `holds` (`holdspeak/operations.py:100`), and `admits(args)` (`:108`) answers True/False, or None where stored state decides (the Thought's `note.delete`). An argument condition without a predicate, or a stored-state one with one, fails at import (`__post_init__`). The predicate is not exported; the words are.
- `kb.create` (`:925-930`): admitted when `member_ids` is given and not empty in ANY accepted form (a list, a mapping whose keys are filed, any other non-empty value), or `kb_id` is given and not empty. Acceptance is unchanged (no input narrowed).
- `kb.update` checked for the same form: its condition was already "present and not null", which covers a mapping; its words now name the mapping and the empty value that removes every member (`:986`).
- `zone.create` (`:803`) and `zone.update` (`:858`) carry their predicates too.
- `kb.create`'s `member_ids` description names the accepted mapping. `docs/generated/operations.json` regenerated.

**Fences** (`tests/unit/test_philo7_contract.py`):
- `test_the_admission_condition_classifies_every_accepted_form[...]` (`ADMISSION_PROBES`, :123; test :148): nineteen probes, each first validated against the descriptor's own schema (an accepted input), then classified. A mapping `member_ids` must be ADMITTED on `kb.create` and `kb.update`; the HTTP adapters' empty create (`kb_id: None, member_ids: []`) and rename (`member_ids: None`) stay exempt.
- `test_every_membership_producing_kb_create_is_admitted[...]` (:164) — the effect fence: the real MCP dispatch accepts the mapping (acceptance preserved), the real database holds a live `note:n` membership, and the declaration admits the call.
- `test_a_mapping_kb_update_changes_memberships_and_is_admitted` (:183) — the same for `kb.update`.

**Red.** The classifier is new, so it cannot run on round one (a missing symbol is not a red, by the fence law). The two reds are: the effect reproduced on main above (a live membership from the mapping, while the round-one words said "a list"), and a deliberate mutation — the predicate made list-only again:

```text
E       AssertionError: assert False is True
E        +  where False = admits({'member_ids': {'note:n': True}, 'name': 'K'})
```

**Green after:** `tests/unit/test_philo7_contract.py` 55 passed.

## MISSED 3 — R5 during the merge

Main `4d427d9c` (after `dcf3eaeb`, PR #655: the owner ratified the charter; R5 puts `decision.delete` IN the delegation grant) is merged into this branch. The branch had not edited the charter's grant wording, so main's R5 text stands everywhere it is; nothing of the ratification record regressed. Checked after the merge: see the merge commit and `current-phase-status.md`.

## MISSED 4 — "including optional id"

`holdspeak/mcp/tools.py:84-85`: the `desk.create` `data` description now says each kind names its own optional id field (`note_id`, `directory_id`, `kb_id` ...), a new id is made when it is absent, and a field named `id` is refused — which is what the contract does.

## Not changed

- No published schema changed in round two; the only word changes are the `data` description (MISSED 4) and the `kb.create` `member_ids` description.
- Residual set unchanged: `RESIDUAL FENCE GREEN: 293 identities`.
