# PHILO-7-02 — The grant lifecycle (design beat)

- **Status:** DRAFT for the other brain's check (Astra). Story 02's implementation brief waits for that check.
- **Why a beat:** the grant is a lifecycle that other stories ride (`docs/internal/ORCHESTRATION.md:143-155`, "The design beat"). Astra r3 asked for it (`checks/charter-astra-r3.md` findings 2 and 4, CONDITIONS 2).
- **Pinned to:** main `02a862f2`. The owner's R5 ("Put it in the grant": `decision.delete` IS in the set) is on the ratification commit `10b9ba3b` (`origin/docs/philo-7-ratified`, `current-phase-status.md` Authority and "The delegation grant").
- **Scope:** kernel and service lifecycle only. The face (verb and chip strings, shots) is the canvas's (story 02 Preconditions). No product code changes in this beat.

## What the grant is (settled by the charter, restated in one table)

| Item | Decision |
|---|---|
| Holder | ONE AGENT principal identity (`Principal.identity`, the string the kernel records as `principal_identity`; `principals.py:156`, `broker.py:93`). |
| Terms | `{"agent_identity": <id>, "operations": <sorted list of the 15 operation names below>}`. The list is stored in the row, so a later code change to the set never widens an old grant. |
| The set (R1 + R5) | `zone.file`, `zone.unfile`, `decision.create`, `decision.update`, `decision.status`, `decision.supersede`, `decision.delete` (R5), `kb.member.add`, `kb.member.remove`, `kb.create` (admitted form), `kb.update` (admitted form), `zone.create` (admitted form), `zone.update` (admitted form), `zone.delete`, `note.delete` (Thought-owned form). The admission table decides which calls reach the kernel; the grant only says which admitted names the agent may run. |
| Hash | `terms_sha256 = _hash(terms, expires_at)`, the precedent's function byte for byte (`services/schedule_delegation.py:37-39`). |
| Expiry | Optional `expires_at` (epoch seconds). The face sends none (one verb, no picker). NULL = no expiry. |
| Cardinality | One LIVE grant per agent identity (unique partial index). A re-grant marks the old row REVOKED `reapproved` in the same transaction (precedent `schedule_delegation.py:58`). |
| Operations | `delegation.grant`, `delegation.revoke`: kernel operations, owner-only, each ADMITTED with its own receipt (XI.1, XI.4). HTTP only; in no MCP palette. |
| Not reused | The actuator scoped grants (`services/authority_service.py:141-181`): one proposal, a fixed destination, `max_uses`, and refused in YOLO (`:160-164`), the owner's default posture. A standing grant over an operation set is a different contract. The signed continuation path (`kernel/causation.py:46-68`) stays separate (Astra r3 finding 1). |

## The table (additive; beside `kernel_schedule_delegations`, `db/schema.py:1816-1831`)

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

No column on `kernel_operations` changes. The operation already has `authority_basis`, `delegator_kind`, `delegator_identity` (`db/schema.py:2137-2139`), and every receipt read joins them (`kernel/journal.py:21-27`).

## One function answers "may this agent do this now?"

`desk_grant_refusal(conn, *, grant_id, terms_sha256, agent_identity, operation_name, now, authoritative)` returns `""` or a refusal code. It is the precedent's `delegated_refusal` (`kernel/schedule_delegated.py:17-31`) for the desk row. Admission (by identity, to SELECT the grant), approval, claim and the credential row's chip all call it. There is no second copy of the rule.

| Check, in order | Code |
|---|---|
| No row for the id, or (at admission) no LIVE row for the identity | `desk_delegation_required` |
| Row identity is not the operation's principal identity, or the operation name is not in `operations_json` | `desk_delegation_required` |
| Row state is not LIVE, or the row's `terms_sha256` differs from the frozen hash | `desk_delegation_revoked` |
| `expires_at` is set and `expires_at <= now` (when `authoritative`, the row becomes EXPIRED, as `schedule_delegated.py:24-27`) | `desk_delegation_expired` |

## The five invariants, decided

### 1. The grant is frozen at admission

- **Decision:** the desk codec's `authorize` (`broker.py:320`) SELECTs the LIVE row for the agent identity, calls the function, and returns the grant in the admission. `submit` writes it on the operation row in the same INSERT (`broker.py:86-105`): `authority_basis = desk-delegation:<id>:<terms_sha256>`, `delegator_kind = owner`, `delegator_identity = <row.delegator_identity>`. This is the precedent's shape (`schedule_delegated.py:95`, `schedule-delegation:<id>:<terms_sha256>`). The change in `submit`: take these three values from the admission when it carries them; else keep today's default (`broker.py:98`).
- Approval and claim parse `<id>` and `<terms_sha256>` from the operation's own `authority_basis` and re-check THAT row. They never SELECT "the LIVE row for this identity" again. So a re-grant between admission and approval cannot approve the older operation: the old row is REVOKED `reapproved`, so the check returns `desk_delegation_revoked`.
- **Reason:** one source of truth, already on the operation, already in every receipt. No new column.
- **Fence:** F1, F2.

### 2. Expiry is inside the hashed terms

- **Decision:** `terms_sha256 = _hash(terms, expires_at)` (`schedule_delegation.py:37-39`). Import it; do not copy it. The receipt's `authority_basis` therefore names the expiry that approved the write.
- **Reason:** a changed expiry is a changed grant. It needs a new row, and old operations stay bound to the old one.
- **Fence:** F3.

### 3. The execution cutoff is the claim check

- **Decision:** the desk codec's `validate_claim` (`kernel/executor.py:61-67`) calls the function with the frozen id and hash. A refusal there already ends the operation with a `refused` receipt (`executor.py:68-73`). The grant must be LIVE and unexpired AT THE CLAIM. Frozen-at-admission alone is NOT enough: a revoke between approval and execution must stop the write.
- **The cutoff:** the read inside `validate_claim`. A revoke that commits before that read refuses the write. A revoke that commits after it does not stop that write: the write runs once and its receipt names the frozen grant. The next write is refused. This agrees with the charter ("a grant revoked after a write executed does not undo that write").
- **Why not a re-check inside the domain write transaction:** it couples the kernel row to every service transaction, for a window of microseconds inside one call. Tenet 1.
- **The interleavings (each is a fence):**

| Between | Revoke | Expire | Re-grant |
|---|---|---|---|
| admission → approval | approval refuses, `desk_delegation_revoked`, terminal receipt (invariant 4) — F4 | `desk_delegation_expired`, row EXPIRED — F5 | old row REVOKED `reapproved` → `desk_delegation_revoked`; never approved under the new row — F2 |
| approval → claim | claim refuses, `desk_delegation_revoked`, receipt — F6 | `desk_delegation_expired` — F7 | `desk_delegation_revoked` — F8 |
| after the claim's check | the write lands once; receipt `succeeded` names the frozen grant; the next write is refused — F9 | same — F9 | same — F9 |

### 4. A refusal during approval ends the operation with a receipt

- **Today:** `decide` raises `KernelRefused` at `broker.py:204` and writes nothing. The operation stays `awaiting_decision` and has no receipt. Probe (a) reproduced this on main (below).
- **Decision:** a new authority branch in `decide`, beside the four at `broker.py:190-199`: `desk_delegated` = AGENT principal + `authority_basis` starts with `desk-delegation:` + the function returns `""` (authoritative). When the authority check fails AND the refused principal is the operation's own actor (same kind and identity) AND the operation name is a desk grant operation, `decide` does this before it raises: CAS `awaiting_decision → refused` at the operation's revision (`store.transition`), then `_terminal(operation, "refused", <code>)` (the same two calls as the reject branch, `broker.py:220-225`), then raise `KernelRefused(<code>)` with the receipt on it. The code is the function's code (`desk_delegation_revoked` / `desk_delegation_expired` / `desk_delegation_required`). If the CAS loses (another caller moved the operation), raise with no receipt, as today.
- **Why not every refusal at :204:** a stranger's failed decide must not end another principal's work (anyone authenticated could then refuse anything). And a `tool.call` gate proposal waits for the owner by design; an agent's bad self-approval must not end it. Probe (a)'s behaviour stays true for `tool.call` (compat row, F10b).
- **The receipt:** `state=refused`, `outcome=<code>`, `result_ref=""`; joined: `actor_kind=agent`, `actor_identity=<agent>`, `delegator_kind=owner`, `delegator_identity=<owner identity>`, `authority_basis=desk-delegation:<id>:<terms_sha256>`, `target_ref=<the admitted target>`.
- **Restart during decision:** at hub start the desk service passes the native ids of its own `admitting`/`awaiting_decision` operations to `broker.recover_invalidated` (`broker.py:24-35`; today only `gate_service.py:154` calls it) → `indeterminate`, `hub_restart_during_decision`. Unclaimed approved work is already reaped to `refused` (`kernel/liveness.py:14-36`).
- **Fence:** F10, F10b, F11.

### 5. Credential reissue, credential revoke, restart

- **Decision:** the grant is keyed by the principal identity and SURVIVES a reissue and a hub restart. The owner granted the AGENT, not the token. An explicit owner revoke of the credential REVOKES the grant, with a `delegation.revoke` receipt.

| Event | Credential | Grant | Chip on the row |
|---|---|---|---|
| Issue (first) | new id, identity X | none, or the LIVE grant X already has | from the function |
| Reissue, same identity (`principals.py:149`; probe b) | old id gone, old token 401, new id | unchanged, LIVE | FILING ALLOWED at once |
| Credential TTL expiry (`principals.py:194-196`) | gone | unchanged | no row |
| Agent self-revoke (`DELETE /api/principals/self`, `gate_routes.py:60-63`) | gone | unchanged (only the owner changes authority) | no row |
| Owner revokes the credential (`DELETE /api/settings/remote/credentials/{id}`, `mcp_http.py:315-328`; `DELETE /api/principals/agents/{identity}`, `gate_routes.py:56-58`) | gone | REVOKED `credential_revoked` via `delegation.revoke`, own receipt; only when a LIVE grant exists | no row; a later issue of X shows FILING STOPPED |
| Hub restart (`principals.py:103-110`, module store `:43`) | all gone | unchanged, in the DB | no rows; a reissue of X shows FILING ALLOWED |
| Grant expiry | unchanged | EXPIRED on the next authoritative check | FILING STOPPED (the chip evaluates `expires_at`, not only the column) |

- **Where the hook lives:** in the two owner revoke ROUTES, after the store revoke succeeds. NOT in `AgentCredentialStore.revoke`: reissue (`:149`) and TTL expiry (`:195`) call that same method.
- **The chip:** `GET /api/settings/remote` adds `delegation: {state, grant_id, expires_at}` per row, computed by the function with `now` (non-authoritative). FILING ALLOWED only when the function returns `""` for the row's identity. So the chip never says ALLOWED where the kernel refuses.
- **The alternative, and why not:** key the grant by the credential id. Every 12-hour default TTL reissue (`principals.py:140`) and every restart would silently drop it, and the owner would re-grant again and again (Tenet 3: "never a million interfaces"). And the credential id never reaches the kernel: only `Principal.identity` does (`principals.py:156`, `broker.py:93`).
- **The accepted risk:** after a restart, a new credential issued under the SAME identity string inherits the grant. The owner chooses that string, and the row shows FILING ALLOWED as it appears. "Stop filing" ends it.
- **Fence:** F12–F15.

## `delegation.grant` and `delegation.revoke`

| Item | Decision |
|---|---|
| Transport | `PUT /api/settings/remote/delegations/{identity}` (grant; body `{expires_at?}`) and `DELETE` of the same path (revoke). The route runs the whole kernel path inline, as `desktop_typing.py:63-178`. |
| Edge right | `required_right` (`principals.py:283-336`) gives this path `AGENT_SUBMIT`, as `/api/kernel/submit` (`:312-313`). So an agent's attempt REACHES the kernel and is refused with a receipt, not with an edge 403 and no receipt. Unauthenticated → edge 401 (protocol, no receipt). |
| Owner-only | The spec's `authorize` refuses any non-OWNER principal: `owner_principal_required` → `_refuse_attempt` (`broker.py:79-80, 332-344`), a terminal refused receipt, zero rows changed. An agent never grants itself. |
| MCP | In no palette, no tool. A call by that name is an unknown tool: a protocol refusal with no receipt (the R2 boundary). |
| Grant effect | One transaction: old LIVE row → REVOKED `reapproved`; INSERT the new LIVE row with `grant_operation_id`. Receipt `succeeded`, `target_ref = agent:<identity>`, `result_ref = desk-delegation:<id>`. |
| Revoke effect | LIVE row → REVOKED (`owner_revoked` or `credential_revoked`). No LIVE row → domain refusal `desk_delegation_required` with a receipt. |
| Admission refusal provenance | For `desk_delegation_revoked` / `desk_delegation_expired` at admission, the receipt names the latest row for the identity through `_refuse_attempt(..., provenance=)` (`broker.py:332-338`), as `schedule_delegated.py:45-51`. `desk_delegation_required` names none. |

**The receipt example (an agent's filing under the grant; the ids and `result_ref` are illustrative):**

```json
{"state": "succeeded", "outcome": "succeeded", "result_ref": "zone-membership:<note>@<zone>",
 "actor_kind": "agent", "actor_identity": "remote-desk-agent",
 "delegator_kind": "owner", "delegator_identity": "owner-session",
 "authority_basis": "desk-delegation:deskdeleg_3f…:sha256:9b1c…",
 "target_ref": "note:<id>"}
```

The refusal codes, verbatim: `desk_delegation_required`, `desk_delegation_revoked`, `desk_delegation_expired`; for the delegation operations `owner_principal_required`.

## Probes (on main `02a862f2`, isolated HOME, real code paths)

| Probe | What ran | Result | Files |
|---|---|---|---|
| (a) refusal at approval | The configured kernel broker (`kernel/runtime.py:210-224`) over an isolated DB; an AGENT submits a real `tool.call` v1, then calls `decide` | `submit → awaiting_decision`; `decide → KernelRefused owner_principal_required_to_decide`; after: `state=awaiting_decision`, `receipt=None`, 0 `kernel_receipts` rows. Astra's fact REPRODUCED. | `design/probes/probe_a_approval_refusal.py`, `.out.txt` |
| (b) reissue | The real hub (`MeetingWebServer`, the Phase 5 fixture `tests/unit/test_philo5_the_loop.py:116-150`); two `POST /api/settings/remote/credentials` with one identity; `/api/mcp` with each token from a non-loopback host | ids `a5fe…` → `9541…`, identity `probe-desk-agent` both times; old token 401, new token 200; ledger has one row. Astra's fact REPRODUCED. | `design/probes/probe_b_reissue.py`, `.out.txt` |
| restart | NOT probed. A new process is the only real restart: the store is a module singleton (`principals.py:43`), so a second in-process hub keeps it. Code-read only: `principals.py:103-110`. | unknown by probe | — |

The probe files are `probe_*.py`; `testpaths = ["tests"]` and `python_files = ["test_*.py"]` (`pyproject.toml:145-146`) keep them out of the suite. Probe (a) asserts today's defect; it is evidence, not a fence.

## Fences story 02 must write

Every fence runs the real kernel, the real desk codec and the real hub. Interleaving fences drive `submit` / `decide` / `claim` of the real broker with an injected clock (`_configure(db, clock=…)`, `tests/unit/test_kernel_broker.py:44-52`) and do the revoke, expiry or re-grant between steps. "Red on main" = the fence fails on a copy of main through the real producer. "Mutation red" = a named deliberate mutation turns it red (fence law, story 02 Acceptance).

| # | Fence | Red condition |
|---|---|---|
| F1 | An agent's `zone.file` under grant G1: one operation, `authority_basis = desk-delegation:G1:H1`, `delegator_kind = owner`, receipt `succeeded`. | Red on main: zero kernel operations for the write (`test_philo5_the_loop.py:618` pins it). |
| F2 | Re-grant (G2) between admission and approval → `desk_delegation_revoked`, the receipt names G1, zero effects; G2 never appears on the operation. | Mutation red: approval SELECTs the LIVE row by identity. |
| F3 | Two grants with equal terms and different `expires_at` have different hashes; the receipt's hash equals `_hash(terms, expires_at)` recomputed. | Mutation red: drop `expires_at` from the hash. |
| F4 | Revoke between admission and approval → terminal `refused` receipt `desk_delegation_revoked`, zero effects. | Mutation red: remove the approval re-check. |
| F5 | Expiry (clock) between admission and approval → `desk_delegation_expired`, row EXPIRED, zero effects. | Mutation red: compare `<` against the wrong clock or skip expiry. |
| F6 | Revoke between approval and claim → claim refuses, receipt `desk_delegation_revoked`, zero effects. | Mutation red: delete `validate_claim` from the desk codec. |
| F7 | Expiry between approval and claim → `desk_delegation_expired`, zero effects. | Mutation red: as F6. |
| F8 | Re-grant between approval and claim → `desk_delegation_revoked`, zero effects. | Mutation red: claim checks LIVE-by-identity. |
| F9 | Revoke after the claim's check → the write lands once, receipt `succeeded` names G1; the next write is refused `desk_delegation_revoked`. | Red on main: no receipt at all. |
| F10 | Refusal during approval (F4's case) leaves `state=refused`, a receipt with the fields of invariant 4, and never `awaiting_decision`. | Red on main by mechanism: probe (a) (`awaiting_decision`, receipt NULL). Mutation red: remove the receipt write before the raise. |
| F10b | Compat: an agent's self-decide of a `tool.call` still leaves `awaiting_decision`, no receipt (the owner can still decide). | Mutation red: write the receipt for every refusal at `broker.py:204`. |
| F11 | A desk operation left in `awaiting_decision` is `indeterminate` (`hub_restart_during_decision`) after hub start. | Red on main: nothing recovers it. |
| F12 | Reissue through the real settings route: old token 401; the new token's `zone.file` succeeds under the SAME grant id; chip ALLOWED. | Red on main: no grant, no receipt for the write. |
| F13 | Restart stand-in: a fresh `AgentCredentialStore` over the same DB, a reissued credential writes under the LIVE grant. | Red on main: as F12. |
| F14 | Owner revoke of the credential (both routes) → grant REVOKED `credential_revoked` + a `delegation.revoke` receipt; agent self-revoke and TTL expiry leave it LIVE. | Red on main: no grant row. Mutation red: the hook moved into `AgentCredentialStore.revoke` (then a reissue revokes the grant). |
| F15 | Chip agreement: for {no grant, LIVE, expired by clock, Stop filing, credential revoke, reissue}, the ledger's `delegation.state` is ALLOWED if and only if the agent's `zone.file` succeeds. | Mutation red: the chip reads the `state` column only (expired-by-clock says ALLOWED). |
| F16 | An agent's `PUT`/`DELETE` of the delegation path → `owner_principal_required` refusal receipt, zero rows; unauthenticated → 401, no receipt. | Red on main: the route does not exist (404, zero receipts). |
| F17 | One LIVE per identity: a re-grant leaves exactly one LIVE row and one REVOKED `reapproved`. | Mutation red: drop the unique partial index and the UPDATE. |
| F18 | The set: `decision.delete` under a LIVE grant succeeds with a delegation receipt (R5); a stored row without an operation refuses that operation `desk_delegation_required`. | Red on main: no kernel path for `decision.delete`. |
| F19 | A grant to identity A; agent B's write → `desk_delegation_required`, receipt, zero effects. | Red on main: B's write succeeds with zero receipts. |

## Open for the owner

None. Each point above is decided with its reason; the verb and chip strings stay with the canvas that the owner ratifies (story 02 Preconditions). The one accepted risk (an identity string reused after a restart inherits the grant, invariant 5) is visible on the row and ends with one verb; Astra's check may raise it.
