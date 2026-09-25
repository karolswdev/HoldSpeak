# PHILO-7-02 — The grant lifecycle (design beat)

- **Status:** round three. Astra r1 (`../checks/lifecycle-beat-astra-r1.md`) and r2 (`../checks/lifecycle-beat-astra-r2.md`), both RATIFY-WITH-CONDITIONS; r2 ratified the round-two payments 3–7 as design decisions and the desk-only scoping as lawful. Every condition is paid below ("Round two" and "Round three" ledgers at the end). Story 02's implementation brief waits for Astra's re-check.
- **Why a beat:** the grant is a lifecycle that other stories ride (`docs/internal/ORCHESTRATION.md:143-155`, "The design beat"). Astra r3 asked for it (`checks/charter-astra-r3.md` findings 2 and 4, CONDITIONS 2).
- **Pinned to:** main `dcf3eaeb`. The owner's R5 ("Put it in the grant": `decision.delete` IS in the set) is on main: `current-phase-status.md:25` (Authority) and `:259` (the enumerated set). Main moved from `02a862f2` to `dcf3eaeb` by three roadmap files only, so the probes below still hold.
- **Scope:** kernel and service lifecycle only. The face (verb and chip strings, shots, the layout of the rows) is the canvas's (story 02 Preconditions). No product code changes in this beat. **The desk codec, its `authorize` and its `validate_claim` are story 02's to WRITE:** `kernel/executor.py:61-67` is the dispatch hook that calls a codec's `validate_claim`, not a desk validator (Astra r1 finding 1).

## What the grant is

| Item | Decision |
|---|---|
| Holder | ONE AGENT principal identity (`Principal.identity`, recorded as `principal_identity`; `principals.py:156`, `broker.py:93`). |
| Terms | `{"agent_identity": <id>, "operations": <sorted list of DESK_GRANT_OPERATIONS>}`. The list is stored in the row, so a later code change to the set never widens an old grant. |
| `DESK_GRANT_OPERATIONS` (R1 + R5) | Exactly the ADMITTED desk writes: `zone.file`, `zone.unfile`, `decision.create`, `decision.update`, `decision.status`, `decision.supersede`, `decision.delete` (R5), `kb.member.add`, `kb.member.remove`, `kb.create` (admitted form), `kb.update` (admitted form), `zone.create` (admitted form), `zone.update` (admitted form), `zone.delete`, `note.delete` (Thought-owned form). 15 names. It NEVER contains `delegation.grant` or `delegation.revoke`. Every rule below that says "desk grant operation" means a name in this set. |
| `DESK_KERNEL_OPERATIONS` | `DESK_GRANT_OPERATIONS` ∪ {`delegation.grant`, `delegation.revoke`}. Used ONLY to scope the atomic terminal writes and the startup recovery (invariant 4). It is never an authority set: an agent's grant never contains `delegation.*`. |
| Hash | `terms_sha256 = _hash(terms, expires_at)`, imported from `services/schedule_delegation.py:37-39` (the value carries the `sha256:` prefix). |
| Expiry | Optional `expires_at` (epoch seconds). The face sends none. NULL = no expiry. (Ratified, Astra r1 finding 1.) |
| Cardinality | One LIVE grant per agent identity (unique partial index). A re-grant marks the old row REVOKED `reapproved` in the same transaction (precedent `schedule_delegation.py:58`). |
| Operations | `delegation.grant`, `delegation.revoke`: kernel operations, owner-only, each ADMITTED with its own receipt (XI.1, XI.4). HTTP only; in no MCP palette. |
| Not reused | The actuator scoped grants (`services/authority_service.py:141-181`): one proposal, a fixed destination, `max_uses`, refused in YOLO (`:160-164`), the owner's default posture. The signed continuation path (`kernel/causation.py:46-68`) stays separate (Astra r3 finding 1). |

## The table (additive; beside `kernel_schedule_delegations`, `db/schema.py:1816-1831`; ratified, Astra r1 finding 1)

```sql
-- Device-local owner delegation of desk filing and decisions to one agent. Never sync.
CREATE TABLE IF NOT EXISTS kernel_desk_delegations (
    id TEXT PRIMARY KEY,                       -- "deskdeleg_" + uuid4 hex
    agent_identity TEXT NOT NULL,
    delegator_kind TEXT NOT NULL, delegator_identity TEXT NOT NULL,
    operations_json TEXT NOT NULL,             -- the sorted set; part of the terms
    terms_sha256 TEXT NOT NULL, expires_at REAL,
    state TEXT NOT NULL CHECK (state IN ('LIVE','REVOKED','EXPIRED')),
    revoked_at REAL, revocation_reason TEXT NOT NULL DEFAULT '',  -- owner_revoked | reapproved | credential_revoked
    grant_operation_id TEXT NOT NULL,          -- the delegation.grant operation that made the row
    created_at REAL NOT NULL, updated_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_desk_delegation_one_live
ON kernel_desk_delegations(agent_identity) WHERE state='LIVE';
CREATE INDEX IF NOT EXISTS idx_desk_delegations_agent_state
ON kernel_desk_delegations(agent_identity, state);
```

No column on `kernel_operations` changes: `authority_basis`, `delegator_kind`, `delegator_identity` exist (`db/schema.py:2137-2139`), the INSERT takes them (`kernel/journal.py:138`), and every receipt read joins them (`journal.py:21-27`).

## One function, two entry points

`check_row(row, *, agent_identity, operation_name, frozen_sha256, now, authoritative) -> "" | code`. It is the precedent's `delegated_refusal` (`kernel/schedule_delegated.py:17-31`) for the desk row, with the order fixed so that the codes match the outcomes (Astra r1 finding 4). Expiry is classified BEFORE revocation, and the same answer comes back after EXPIRED is persisted.

| Order | Condition | Code |
|---|---|---|
| 1 | `row is None`, or `row.agent_identity != agent_identity`, or `operation_name` not in `row.operations_json` | `desk_delegation_required` |
| 2 | `row.state == 'EXPIRED'`, or (`row.state == 'LIVE'` and `expires_at` set and `expires_at <= now`; when `authoritative`, UPDATE the row to EXPIRED, as `schedule_delegated.py:24-27`) | `desk_delegation_expired` |
| 3 | `row.state == 'REVOKED'`, or `frozen_sha256` given and `row.terms_sha256 != frozen_sha256` | `desk_delegation_revoked` |
| 4 | otherwise | `""` |

| Entry point | Which row it passes | Used by |
|---|---|---|
| **Admission** (`by_identity`) | The LIVE row for the identity. If there is none: the LATEST historical row for the identity (`ORDER BY updated_at DESC, id DESC LIMIT 1`), used for the CODE only (never granted → `_required`; last row REVOKED → `_revoked`; last row EXPIRED → `_expired`). A historical row never authorises anything. | the desk codec's `authorize`; the chip |
| **Frozen** (`by_basis`) | The row whose id is parsed from the operation's own `authority_basis`: `kind, grant_id, sha = basis.split(":", 2)` (at most two splits, so `sha` keeps its `sha256:` prefix); `kind` must be `desk-delegation`. It NEVER falls back to a LIVE or historical row selected by identity. | approval; the desk codec's `validate_claim` |

## The five invariants, decided

### 1. The grant is frozen at admission

- **Decision:** the desk codec's `authorize` (`broker.py:320`) calls `by_identity`. If it returns `""`, the admission carries the grant, and `submit` writes it in the same INSERT (`broker.py:86-105`): `authority_basis = desk-delegation:<id>:<terms_sha256>`, `delegator_kind = owner`, `delegator_identity = <row.delegator_identity>`. The change in `submit`: take these three values from the admission when present; else today's default (`broker.py:98`). This is the precedent's shape (`schedule_delegated.py:95`).
- Approval and claim use `by_basis` only. A re-grant between admission and approval cannot approve the older operation: its row is REVOKED `reapproved` → `desk_delegation_revoked`.
- **Reason:** one source of truth, already on the operation and in every receipt. No new column. (Ratified, Astra r1 finding 1.)
- **Fence:** F1, F2.

### 2. Expiry is inside the hashed terms

- **Decision:** `terms_sha256 = _hash(terms, expires_at)` (`schedule_delegation.py:37-39`), imported, not copied. The receipt's `authority_basis` names the expiry that approved the write.
- **Reason:** a changed expiry is a changed grant: a new row, and old operations stay bound to the old one.
- **Fence:** F3, F5b.

### 3. The execution cutoff is the claim check

- **Decision:** story 02 writes the desk codec's `validate_claim`, which calls `by_basis` (authoritative). The executor hook calls it (`executor.py:61-67`) and a refusal ends the operation (`:68-73`, made atomic for desk operations by invariant 4). The grant must be LIVE and unexpired AT THE CLAIM. Frozen-at-admission alone is not enough.
- **The cutoff:** the read inside `validate_claim`. A change that commits before that read refuses the write. A change that commits after it does not stop THAT write: it runs once, and its receipt names the frozen grant G1.
- **Why not a re-check inside the domain write transaction:** it couples the kernel row to every service transaction, for a window of microseconds inside one call. Tenet 1.
- **The interleavings (each is a fence):**

| Between | Revoke | Expire | Re-grant (G1 → G2) |
|---|---|---|---|
| admission → approval | approval refuses `desk_delegation_revoked`, terminal receipt (invariant 4) — F4 | `desk_delegation_expired`, row EXPIRED — F5 | G1 REVOKED `reapproved` → `desk_delegation_revoked`; never approved under G2 — F2 |
| approval → claim | claim refuses `desk_delegation_revoked`, receipt — F6 | `desk_delegation_expired` — F7 | `desk_delegation_revoked` — F8 |
| after the claim's check | THIS write lands once under G1; the NEXT write is refused `desk_delegation_revoked` — F9a | THIS write lands once under G1; the NEXT write is refused `desk_delegation_expired` — F9b | THIS write lands once under G1; the NEXT valid write SUCCEEDS under G2 — F9c |

### 4. Every desk terminal path is atomic; approval is caller- and state-scoped

- **Today:** `decide` raises at `broker.py:204` and writes nothing; the operation stays `awaiting_decision` with no receipt (probe a). Worse, the existing terminal paths write the state and the receipt in two steps (`transition` then `_terminal`: reject `broker.py:220-225`, claim refusal `executor.py:68-73`, `recover_invalidated` `broker.py:30-33`, the reaper `liveness.py:40-53`). Astra interrupted two of them between the steps and got `state=refused`, `receipt=NULL`, which no recovery finds (Astra r1 finding 2).
- **Decision (atomicity; Astra r1 finding 2, r2 finding 1):** EVERY terminal write of an operation named in `DESK_KERNEL_OPERATIONS` couples the terminal state and the receipt in ONE SQLite transaction, followed by `_terminal` only for the journal event (its `add_receipt` returns the existing row, `journal.py:423-432`; the event stays a separate write, as `executor.py:124-128`). The complete inventory:

| # | Terminal write | Where today | Atomic form |
|---|---|---|---|
| T1 | Admission refusal (the ordinary no-grant path; also owner-only and capability refusals of `delegation.*`) | `_refuse_attempt`: `create_operation` in state `refused`, then `_terminal` (`broker.py:332-344`) | NEW store method `create_refused_with_receipt(values, outcome)`: the operation INSERT (state `refused`) and the receipt INSERT in one `with self._connection()` block. It mirrors the seam; the seam itself needs an existing row. |
| T2 | Native-admission failure | `transition` + `_terminal` (`broker.py:131-137`) | `transition_and_receipt` |
| T3 | Refusal at approval (new) | — (`broker.py:204` writes nothing) | `transition_and_receipt(..., strict=True)` |
| T4 | Explicit owner rejection | `transition` + `_terminal` (`broker.py:220-225`) | `transition_and_receipt(..., strict=True)` |
| T5 | Claim refusal | `transition` + `_terminal` (`executor.py:68-73`) | `transition_and_receipt(..., strict=True)` |
| T6 | Startup recovery of `admitting`/`awaiting_decision` | (none for desk) | `transition_and_receipt(..., strict=True)`, `indeterminate`, `hub_restart_during_decision` |
| T7 | Reaper of `awaiting_execution`/`claimed` | `transition` + `_terminal` (`liveness.py:40-53`) | `transition_and_receipt(..., strict=True, warrant_revoked=1)`; a strict conflict = today's `continue` |
| T8 | Success/failure receipt after the effect | already atomic (`executor.py:124-128`) | unchanged |
| T9 | `delegation.grant`/`revoke` effect + its receipt | — | ONE transaction: `transition_and_receipt(..., effect=<the grant-table write>)` runs the grant UPDATE/INSERT on the same connection before the state UPDATE and the receipt INSERT (invariant 5, F21) |

- **The seam gains three optional keywords, nothing else:** `strict` (below), `warrant_revoked` (T7), `effect: Callable[[conn], None]` (T9; an exception rolls back all three writes). The kernel tables and `kernel_desk_delegations` live in the same database (`db/schema.py:1816`, `:2125`), so one connection transaction covers them; the precedent does the same (`schedule_delegated.py:80-95`: the delegation re-check, the tick INSERT and the operation UPDATE under one `BEGIN IMMEDIATE`).
- **Strict conflict semantics (Astra r2 finding 2):** today the seam returns an EXISTING receipt BEFORE its revision check (`journal.py:380-384`), so a stale refusal after a winner finished gets the winner's `succeeded` receipt back without an error (Astra reproduced it). With `strict=True`, inside the transaction: an existing receipt → raise `KernelRefused("operation_already_terminal")`; a revision that moved → raise `KernelRefused("operation_revision_conflict")`; in both cases write NOTHING and append no event. The caller then raises that conflict; it never returns another outcome's receipt as its own. Default `strict=False` keeps today's idempotent retry for every existing caller (`executor.py:124`, and the rest).
- **Scope of the change:** the shared sites (T1, T2, T4, T5, T7) take the atomic form when `operation.name in DESK_KERNEL_OPERATIONS`; other kinds keep today's two-step path. **Reason:** the same UPDATE on parent runs meets the publication trigger (`db/schema.py:3590-3608`) and the inference attestation branch (`journal.py:400-420`). Astra r2 ruled this scoping lawful. The shared defect for other kinds goes to the BACKLOG as its own row (orchestrator to file).
- **Decision (the approval branch):** a new authority in `decide`, beside the four at `broker.py:190-199`. `desk_delegated` is true only when ALL hold: `principal.kind is AGENT`; `operation.principal_kind == 'agent'` and `operation.principal_identity == principal.identity` (the caller IS the operation's actor — an explicit bind, Astra r1 finding 3); `operation.name in DESK_GRANT_OPERATIONS`; and `by_basis(...)` returns `""` (authoritative).
- **Decision (the refusal branch):** when authority fails AND the caller is the operation's own agent actor AND the name is in `DESK_GRANT_OPERATIONS`, `decide` checks, BEFORE it writes anything, `operation.state == 'awaiting_decision'` and `operation.revision == expected_revision` (`store.transition` compares revision only, `publication_transition.py:33`; every transition increments the revision, so the revision CAS after this state read proves the state has not moved). Then `transition_and_receipt(op, revision, "refused", <code>)`, then the journal event, then `raise KernelRefused(<code>, receipt=<receipt>)`. `<code>` is `by_basis`'s code; a missing or foreign basis gives `desk_delegation_required`. The state read and the strict seam together decide: a terminal winner that lands between the read and the atomic call makes the seam raise `operation_already_terminal` (or `operation_revision_conflict`), and `decide` raises that conflict with no receipt and no event (F10e). Any other state raises with no receipt.
- **What does NOT terminalise:** another actor's decide (a stranger must not end another principal's work), a repeated decide after terminal (`operation_already_decided`, `broker.py:207-208`; the existing receipt is unchanged), and every non-desk operation (a `tool.call` gate proposal waits for the owner by design; probe a stays true for it).
- **The receipt:** `state=refused`, `outcome=<code>`, `result_ref=""`; joined: `actor_kind=agent`, `actor_identity=<agent>`, `delegator_kind=owner`, `delegator_identity=<owner identity>`, `authority_basis=desk-delegation:<id>:<terms_sha256>`, `target_ref=<the admitted target>`.
- **Restart during decision:** T6. The desk service does not call `recover_invalidated` (`broker.py:24-35`), which is two-step.
- **Fence:** F10, F10b, F10c, F10d, F10e, F11, F20.

### 5. Credential reissue, credential revoke, restart

- **Decision (ratified, Astra r1 finding 1):** the grant is keyed by the principal identity and SURVIVES a reissue and a hub restart. The owner granted the AGENT, not the token.
- **Decision (durable first, Astra r1 finding 5):** an explicit OWNER revocation revokes the grant FIRST, durably, with its own `delegation.revoke` receipt (`credential_revoked`), and removes the in-memory credential SECOND.

| Owner route | Order |
|---|---|
| `DELETE /api/principals/agents/{identity}` (`gate_routes.py:56-58`, right DELEGATE) | 1. If a LIVE grant exists for `identity`: run `delegation.revoke` inline; on a kernel failure return the error and leave the credential. 2. `store.revoke(identity)`. The grant is revoked **even when no credential remains** (after TTL cleanup or self-revoke the store returns `revoked=false` today; Astra reproduced it). The response adds `grant_revoked` and the receipt. |
| `DELETE /api/settings/remote/credentials/{id}` (`mcp_http.py:315-328`) | 1. Resolve the identity from the id WITHOUT removing anything (the store's `_by_id` → credential, `principals.py:232-242`). Unknown id → 404 as today, grant untouched (no identity is known; the identity route or "Stop filing" still ends the grant). 2. Grant revocation as above. 3. `store.revoke_by_id(id)`. |

- **The two commit boundaries (Astra r2 finding 3).** The inline precedent does the effect, then the receipt (`desktop_typing.py:139`, `:163`), which leaves a window between them. The delegation operations close that window instead of recovering from it: T9 commits the grant-table write, the terminal state and the receipt in ONE transaction. So:
  - **(A) After the completed revoke operation, before the credential removal:** the grant is REVOKED with its `succeeded` receipt; the token still authenticates, and every desk grant operation is refused. The owner's retry removes the token (the grant step is then a no-op: no LIVE row, no second operation). The safe direction.
  - **(B) Between the grant-table commit and its receipt:** does not exist; it is one commit. An interruption before that commit leaves the grant LIVE and the operation `claimed` with no receipt; the reaper (T7) ends it `indeterminate` with a receipt, which is true (nothing committed), and the owner retries. No rollback, no new recovery path.
- **Not the owner:** reissue (`principals.py:149`), TTL cleanup (`:194-196`) and agent self-revoke (`gate_routes.py:60-63`) all call `AgentCredentialStore.revoke`; none touches the grant. So the hook lives in the two owner ROUTES, never in the store.

| Event | Credential column | Grant | Delegation chip |
|---|---|---|---|
| Issue (first) | new id, active | none, or the LIVE grant the identity already has | from `by_identity` |
| Reissue (`:149`; probe b) | old id gone, old token 401; new id, active | unchanged, LIVE | FILING ALLOWED at once |
| TTL passes, no request yet | the row STAYS with `active=false` (`list_credentials` keeps expired rows, `principals.py:244-249`; Astra's real route returned it) | unchanged | FILING ALLOWED (the grant is live; a reissue uses it) |
| TTL passes, then any authentication attempt | row removed by cleanup (`:194-196`) | unchanged | no row (see "A LIVE grant with no credential") |
| Agent self-revoke | row removed | unchanged | no row |
| Owner revokes (either route) | row removed (step 2/3) | REVOKED `credential_revoked`, receipt (step 1) | no row; a later issue of X shows FILING STOPPED |
| Hub restart (`principals.py:103-110`, module store `:43`) | all rows gone | unchanged, in the DB | no rows; a reissue of X shows FILING ALLOWED |
| Grant expiry | unchanged | EXPIRED at the next authoritative check | FILING STOPPED |

- **The two columns are independent.** The credential column is today's lead `StateChip` (`SettingsCore.tsx:630`, from `active`). The delegation chip derives ONLY from `by_identity` (non-authoritative, `now` = read time): FILING ALLOWED when it returns `""`, FILING STOPPED for `_revoked` or `_expired`, no chip for `_required` (never granted). An expired credential with a LIVE grant shows both truths: credential idle, FILING ALLOWED.
- **A LIVE grant with no credential (Astra r2 finding 4):** `GET /api/settings/remote` also returns `delegations: [{identity, state, grant_id, expires_at}]` for each LIVE grant whose identity has no credential row. The EXISTING Remote Access ledger renders those rows too: today it renders only when remote access is on and `credentials.length > 0` (`SettingsCore.tsx:612`, `:615`), so a surviving grant would vanish (the branch-removal scar). The condition becomes "any credential OR any delegation row", and delegation rows render whatever the remote switch says (the grant is authority; the owner must be able to stop it). Each such row carries the identity, the FILING ALLOWED chip and the "Stop filing" verb. No new screen; the look is the canvas's (noted there).
- **The alternative, and why not:** key the grant by the credential id. Every 12-hour default reissue (`principals.py:140`) and every restart would drop it, and the owner would re-grant again and again (Tenet 3). And the credential id never reaches the kernel; only `Principal.identity` does.
- **The accepted risk:** after a restart, a new credential issued under the SAME identity string inherits the grant. The row shows FILING ALLOWED at once, and one verb ends it.
- **Fence:** F12–F15, F21a, F21b, F22, F23.

## `delegation.grant` and `delegation.revoke`

| Item | Decision |
|---|---|
| Transport | `PUT /api/settings/remote/delegations/{identity}` (grant; body `{expires_at?}`) and `DELETE` of the same path (revoke, `owner_revoked`). The route runs the whole kernel path inline, as `desktop_typing.py:63-178`. |
| Edge right | `required_right` (`principals.py:283-336`) gives this path `AGENT_SUBMIT`, as `/api/kernel/submit` (`:312-313`), so an agent's attempt reaches the kernel. Unauthenticated → edge 401 (protocol, no receipt). |
| Spec capability | Both `OperationSpec`s declare `required_capability = "agent.submit"`, like every spec today (`kernel/runtime.py:87-118`). Otherwise `_admit_authority` refuses the agent at `broker.py:303-307` with `declared_capability_required` (still a receipt, but the wrong rule). |
| Owner-only | The spec's `authorize` (`broker.py:320`) refuses any non-OWNER principal: `owner_principal_required` → `_refuse_attempt` (`broker.py:79-80, 332-344`), a terminal refused receipt, zero rows changed. |
| MCP | In no palette, no tool: an unknown tool, a protocol refusal with no receipt (the R2 boundary). |
| Malformed requests | An authenticated `PUT`/`DELETE` of this path with a non-object body, a blank identity or a non-numeric `expires_at` is an identifiable consequential attempt: a refusal receipt `invalid_arguments` (the codec's `validate`, `broker.py:314`, or the route's body check routed to the kernel refusal), joining the R2 adapter fences (class 4). |
| Grant effect | One transaction: old LIVE row → REVOKED `reapproved`; INSERT the new LIVE row with `grant_operation_id`. Receipt `succeeded`, `target_ref = agent:<identity>`, `result_ref = desk-delegation:<id>`. |
| Revoke effect | LIVE row → REVOKED. No LIVE row → domain refusal `desk_delegation_required` with a receipt. |

**The receipt and provenance plumbing (Astra r1 finding 7), the minimal change:**

| Where | Today | Change |
|---|---|---|
| `KernelRefused` (`kernel/model.py:16-22`) | `reason`, `operation_id` only | two optional keywords: `provenance: Mapping[str, str] \| None = None`, `receipt: Mapping \| None = None` |
| `submit`'s refusal (`broker.py:79-80`) | forwards `exc.reason` only | also pass `provenance=exc.provenance` to `_refuse_attempt` (it already accepts it, `:333-338`). The desk `authorize` raises `desk_delegation_revoked`/`_expired` with the historical row's `delegator_kind/identity`, `authority_basis`, as `schedule_delegated.py:45-51`. The returned handle already carries the receipt (`_handle(operation, receipt)`, `:344`). |
| `decide`'s desk refusal (invariant 4) | raises without a receipt | raises `KernelRefused(code, operation_id=…, receipt=<receipt>)` |
| The desk service and routes | — | return `{operation_id, receipt}` on success AND on refusal (the named error keeps its status), as `desktop_typing.py:163-178` carries its receipt on `DesktopTypeRefused`. |

The refusal codes, verbatim: `desk_delegation_required`, `desk_delegation_revoked`, `desk_delegation_expired`; for the delegation operations `owner_principal_required`.

**The receipt example (illustrative ids and `result_ref`):**

```json
{"state": "succeeded", "outcome": "succeeded", "result_ref": "zone-membership:<note>@<zone>",
 "actor_kind": "agent", "actor_identity": "remote-desk-agent",
 "delegator_kind": "owner", "delegator_identity": "owner-session",
 "authority_basis": "desk-delegation:deskdeleg_3f…:sha256:9b1c…", "target_ref": "note:<id>"}
```

## Probes (main `02a862f2`, isolated HOME, real code paths; Astra re-ran both: 2 passed)

| Probe | What ran | Result | Files |
|---|---|---|---|
| (a) refusal at approval | The configured kernel broker (`kernel/runtime.py:210-224`) over an isolated DB; an AGENT submits a real `tool.call` v1, then calls `decide` | `awaiting_decision` → `KernelRefused owner_principal_required_to_decide`; after: `state=awaiting_decision`, `receipt=None`, 0 receipt rows. REPRODUCED. | `probes/probe_a_approval_refusal.py`, `.out.txt` |
| (b) reissue | The real hub (`tests/unit/test_philo5_the_loop.py:116-150`); two `POST /api/settings/remote/credentials`, one identity; `/api/mcp` with each token from a non-loopback host | new id, same identity `probe-desk-agent`; old token 401, new 200; one ledger row. REPRODUCED. | `probes/probe_b_reissue.py`, `.out.txt` |
| restart | NOT probed. The store is a module singleton (`principals.py:43`) captured by the middleware (`web_server.py:638`); only a new process is a real restart. | unknown by probe | — |

`probe_*.py` stays out of the suite (`pyproject.toml:145-146`). Probe (a) asserts today's defect: evidence, not a fence.

## Fences story 02 must write

Every fence runs the real kernel, the real desk codec and the real hub. Interleaving fences drive `submit` / `decide` / `claim` of the real broker with an injected clock (`_configure(db, clock=…)`, `tests/unit/test_kernel_broker.py:44-52`). "Red on main" = fails on a copy of main through the real producer. "Mutation red" = a named deliberate mutation turns it red. "Valid inputs" = an active, authenticated credential for the identity, and an existing note and zone.

| # | Fence | Red condition |
|---|---|---|
| F1 | An agent's `zone.file` under G1: one operation, `authority_basis = desk-delegation:G1:<sha256:…>`, `delegator_kind = owner`, receipt `succeeded`. | Red on main: zero kernel operations (`test_philo5_the_loop.py:618` pins it). |
| F2 | Re-grant (G2) between admission and approval → `desk_delegation_revoked`, the receipt names G1, zero effects; G2 never on the operation. | Mutation red: approval selects the LIVE row by identity. |
| F3 | Equal terms, different `expires_at` → different hashes; the basis's hash (with its `sha256:` prefix) equals `_hash(terms, expires_at)`. | Mutation red: drop `expires_at` from the hash; or `split(":")` without the limit. |
| F4 | Revoke between admission and approval → terminal `refused`, `desk_delegation_revoked`, zero effects. | Mutation red: remove the approval re-check. |
| F5 | Expiry between admission and approval → `desk_delegation_expired`, row EXPIRED, zero effects. | Mutation red: skip the expiry check. |
| F5b | Repeated classification: after F5 persisted EXPIRED, a new admission and a second frozen check both return `desk_delegation_expired` (never `_revoked`). | Mutation red: check `state != 'LIVE'` before expiry. |
| F5c | Admission codes: never granted → `_required`; after "Stop filing" → `_revoked`; after expiry → `_expired`. | Mutation red: admission returns `_required` whenever no LIVE row exists. |
| F6 | Revoke between approval and claim → claim refuses, `desk_delegation_revoked`, zero effects. | Mutation red: remove the desk `validate_claim`. |
| F7 | Expiry between approval and claim → `desk_delegation_expired`, zero effects. | Mutation red: as F6. |
| F8 | Re-grant between approval and claim → `desk_delegation_revoked`, zero effects. | Mutation red: the claim selects LIVE by identity. |
| F9a | Revoke after the claim's check → this write lands once under G1; the next → `desk_delegation_revoked`. | Red on main: no receipt at all. |
| F9b | Expiry after the claim's check → this write lands once under G1; the next → `desk_delegation_expired`. | Red on main: as F9a. |
| F9c | Re-grant after the claim's check → this write lands once under G1; the next valid write succeeds under G2. | Red on main: as F9a. Mutation red: the next write stays bound to G1. |
| F10 | Refusal during approval (F4) → `state=refused`, the receipt of invariant 4, never `awaiting_decision`; the raised error carries the receipt. | Red by mechanism: probe (a). Mutation red: raise before the receipt. |
| F10b | Compat: an agent's self-decide of a `tool.call` still leaves `awaiting_decision`, no receipt. | Mutation red: terminalise every refusal at `broker.py:204`. |
| F10c | Cross-actor isolation: agent B decides agent A's desk operation → refused, no receipt, state and revision unchanged; B can never APPROVE it, even with B's own LIVE grant. | Mutation red: drop the caller-identity bind from `desk_delegated`. |
| F10d | Repeated decide after terminal → `operation_already_decided`; exactly one receipt, unchanged. | Mutation red: terminalise without the state check. |
| F10e | A terminal winner between the state read and the atomic call: an injected hook runs a winner (approve, claim, `succeeded` receipt) after `decide` reads `awaiting_decision` and before the strict seam; `decide` raises `operation_already_terminal`; exactly one receipt (the winner's `succeeded`), no refusal event. | Mutation red: `strict=False` (Astra's r2 reproduction: the winner's receipt comes back as a refusal). |
| F11 | A desk operation left in `awaiting_decision` is `indeterminate` (`hub_restart_during_decision`) with a receipt after hub start. | Red on main: nothing recovers it. |
| F12 | Reissue through the real route: old token 401; the new token's `zone.file` succeeds under the SAME grant id; chip FILING ALLOWED. | Red on main: no grant, no receipt. |
| F13 | REAL restart: a hub PROCESS over an isolated HOME and DB; grant G1; the process is killed and a NEW process boots on the same DB; a credential is issued through the real route; its `zone.file` succeeds under G1. The same rig proves F11's startup recovery in that process. | Red on main: as F12. |
| F14 | Agent self-revoke and TTL cleanup leave the grant LIVE; reissue leaves it LIVE. | Mutation red: the hook moved into `AgentCredentialStore.revoke`. |
| F15 | Chip agreement, with valid inputs: for {no grant, LIVE, expired by clock, Stop filing, owner credential revoke, reissue, expired credential}, the chip is FILING ALLOWED if and only if `by_identity` returns `""`; and with valid inputs the agent's `zone.file` then succeeds, while FILING STOPPED matches a `desk_delegation_*` refusal. | Mutation red: the chip reads the `state` column only. |
| F16 | An agent's `PUT`/`DELETE` of the delegation path → `owner_principal_required` receipt (not `declared_capability_required`), zero rows; unauthenticated → 401, no receipt. | Red on main: 404, zero receipts. Mutation red: spec capability `owner`. |
| F16b | Malformed authenticated delegation requests (non-object body, blank identity, bad `expires_at`) → `invalid_arguments` refusal receipt, zero rows. | Red on main: 404, zero receipts. |
| F17 | One LIVE per identity: a re-grant leaves one LIVE row and one REVOKED `reapproved`. | Mutation red: drop the index and the UPDATE. |
| F18 | `decision.delete` under a LIVE grant succeeds with a delegation receipt (R5); a stored set without an operation refuses it `desk_delegation_required`. | Red on main: no kernel path. |
| F19 | Grant to A; agent B's write → `desk_delegation_required`, receipt, zero effects. | Red on main: B's write succeeds with zero receipts. |
| F20 | Atomic receipt, one case per in-scope path T1–T7 and T9, including `delegation.grant`/`revoke` refused at admission: a fault injected inside the one transaction (after the state write, before the receipt INSERT) leaves either nothing written (T1: no operation row) or the operation non-terminal with no receipt; never terminal without a receipt. | Mutation red: the two-step form at any one site (Astra's r1 and r2 reproductions: `state=refused`, `receipt=NULL` at `broker.py:332`, `:131`, `:220`). |
| F21a | Boundary A: a fault after the completed `delegation.revoke` (receipt written) and before the credential removal → grant REVOKED with its receipt; the token authenticates but every desk grant operation is refused; a retry removes the token and writes no second operation. A fault before the revoke commits → nothing changed. | Mutation red: remove the credential first. |
| F21b | Boundary B: a fault injected in the `effect` of T9 after the grant-table write → the grant stays LIVE, no receipt, the operation not terminal; the reaper ends it `indeterminate` with a receipt; a retry revokes. | Mutation red: commit the grant write outside the receipt transaction (then REVOKED with no receipt). |
| F23 | Visibility with no credential, API and rendered: remote on, credential issued, grant G1; the credential is removed (self-revoke, and separately TTL cleanup); `GET /api/settings/remote` lists G1 under `delegations`; the Remote Access ledger RENDERS the row with FILING ALLOWED and "Stop filing" at 1440 and 393; clicking it writes the `delegation.revoke` receipt (`owner_revoked`); the row then disappears and the ledger is empty; the receipt is still readable after the last row is gone. Repeat with the remote switch OFF. | Red on main: no `delegations` field and the ledger hidden by `credentials.length > 0` (`SettingsCore.tsx:615`). |
| F22 | Revocation with no credential: after TTL cleanup or self-revoke, `DELETE /api/principals/agents/{identity}` revokes the surviving LIVE grant, with a receipt. | Red on main: the route returns `revoked=false`, the grant stays LIVE. |

## Open

- **For the owner:** none. Each point is decided with its reason.
- **For the canvas (story 02 Preconditions):** the verb and chip strings, and how a LIVE grant with no credential row (invariant 5, F23) looks on the existing ledger.
- **For the orchestrator:** a BACKLOG row for the two-step terminal writes of non-desk operations (admission refusal, native-admission failure, reject, claim refusal, `recover_invalidated`, reaper), reproduced by Astra on `tool.call` (r1 finding 2, r2 finding 1).

## Round two (Astra r1 conditions → where paid)

| Astra r1 | Where paid |
|---|---|
| Finding 1: the codec and `validate_claim` are story 02's to write; ratified parts kept | Scope (header); invariants 1, 3; the table and expiry rows unchanged |
| Finding 2: atomic terminal receipts on every desk path | Invariant 4 "Decision (atomicity)" and "Scope of the change"; recovery via the seam; F20; Open (BACKLOG row) |
| Finding 3: approval bound to the caller; the set defined; state/revision before terminalisation; `sha256:` parsing | "What the grant is" (`DESK_GRANT_OPERATIONS`); "One function, two entry points" (`split(":", 2)`, no identity fallback); invariant 4 approval and refusal branches; F3, F10c, F10d |
| Finding 4: codes match the outcomes; expiry before revocation; post-claim interleavings | The check order table; the admission fallback (code only, never at approval or claim); invariant 3 table row 3; F5b, F5c, F9a–F9c |
| Finding 5: durable-first owner revocation; revocation with no credential | Invariant 5 owner-route table; F21, F22 |
| Finding 6: expired credential rows; the two columns; F15 inputs; real restart | Invariant 5 matrix rows 3–4 and "The two columns are independent"; "A LIVE grant with no credential"; F13, F15 |
| Finding 7: spec capability; provenance and receipt plumbing; malformed delegation requests | `delegation.*` table (spec capability, malformed rows); the plumbing table (`model.py:16-22`, `broker.py:79`); F16, F16b |

## Round three (Astra r2 conditions → where paid)

| Astra r2 | Where paid |
|---|---|
| Finding 1: complete the terminal-path inventory (admission refusal, native-admission failure, rejection); cover `delegation.*` without widening the agent set | Invariant 4 inventory T1–T9; `DESK_KERNEL_OPERATIONS` row in "What the grant is"; F20 |
| Finding 2: strict conflict semantics on the decision path | Invariant 4 "Strict conflict semantics" and the refusal branch; F10e |
| Finding 3: F21's two commit boundaries and recovery | Invariant 5 "The two commit boundaries" (T9 one transaction); F21a, F21b |
| Finding 4: the owner can see and stop a no-credential grant before a reissue | Invariant 5 "A LIVE grant with no credential"; F23; Open (canvas) |
| BACKLOG row for non-desk two-step terminal writes | Open (orchestrator to file) |
