# Phase 37 — Actuators

**Status:** in-progress (opened 2026-06-04). 6/7 stories shipped.

**Last updated:** 2026-06-04 (**HS-37-06 shipped — actuator documentation (the dedicated
docs story).** All relevant project docs now match the shipped surface. `docs/
PLUGIN_AUTHORING.md` gains a full **Actuators** section (the propose → approve → execute
flow, the `ActuatorProposal` field table, the lifecycle + the three gates [capability /
human approval / `MeetingConfig`], the `ActuatorExecutor` parity+audit, and a worked
example on `followup_ticket_actuator` with links to the real modules + the e2e test) and
its four stale claims are reconciled (kind table, the "deferred to a future phase" note,
"not a valid kind yet", the Out-of-scope bullet). The public `README.md` plugin section
gains an actuators paragraph (third kind, approval-gated, off by default, the reference
actuator, linked to the new section). Doc-truth scope: `docs/evidence/**` frozen; MIR-01's
"disabled by default" left (still true — the master gate is off by default). Doc
drift-guard + link-check green; all new relative links resolve; suite 2080/15 (docs-only).
Next: HS-37-07 (closeout + final-summary). Earlier: **HS-37-05 shipped — reference actuator
end-to-end.** The
first concrete actuator proves the whole loop. `holdspeak/plugins/builtin/
followup_ticket_actuator.py`: `FollowupTicketActuator` (`kind=actuator`,
`required_capabilities=["actuator"]`) whose `run()` finds the first **unowned** action item
and proposes a follow-up ticket (faithful preview + Markdown payload; never reaches out) +
`build_outbox_connector` (the executor's egress point — a local **outbox file** write,
CI-safe) + `register_followup_actuator` (explicit/opt-in, **not** in
`register_builtin_plugins`). **Design note:** the gh/jira CLI default was dropped — the
existing `github_cli` pack is read-only by Phase-25 policy + real `gh issue create` needs
creds/makes real tickets — so the reference side effect is a local outbox file (a real,
observable, reversible artifact); gh/jira/webhook are future connectors on the same
executor contract. 7 tests: faithful proposal, nothing-to-propose→error, capability-off→
blocked, the **full loop** (propose→persist→refused-before-approval→approve→execute→a
**real file on disk**→audit `[proposed,approved,executed]`), gate-off/not-allow-listed→no
file, and `ACTUATOR_ID not in register_builtin_plugins`. Suite 2080/15; module ruff+F821
clean. Next: HS-37-06 (actuator documentation). Earlier: **HS-37-04 shipped — guarded
executor + audit + governance gate.** The one place a side effect happens, so the one place the invariant is enforced:
`holdspeak/plugins/actuator_executor.py` `ActuatorExecutor.execute(proposal_id)` runs an
`approved` proposal through a guard stack — (1) status (only `approved`), (2) **policy
gate** (`allow_actuators` master switch + an optional per-project allow-list; refusal
raises with no state change), (3) **payload parity** (a wrong approved-hash aborts to
`failed`, no outbound call — TOCTOU guard), (4) egress via an **injected** connector (this
module never opens a socket; HS-37-05 supplies the Phase-25-gated one), (5) **audit**
(`executed`/`failed` recorded via `transition_proposal`, payload hash in the audit
detail). The gate's home is the new default-safe `MeetingConfig.allow_actuators` +
`allowed_actuators`. 14 executor/config tests (status/policy/parity/connector-error/audit,
all with a spy connector → no real outbound call); suite 2073/15; modules ruff+F821 clean.
Next: HS-37-05 (reference actuator end-to-end). Earlier: **HS-37-03 shipped — approval
surface (preview → approve/reject, no execution).** The safety invariant made real to the user. API
(`web/routes/meetings.py`): `GET …/proposals` (a pure `db.actuators.list_proposals` read)
+ `POST …/proposals/{id}/decision` (`approved`|`rejected` → `transition_proposal`, records
`decided_by` + audit; illegal transition → 400; unknown/other-meeting → 404) — it **never
executes** (HS-37-04 owns that). UI (`history.astro` + `history-app.js`): a "Proposed
actions" card stack in the meeting modal — each a Signal card with a typed status pill +
reversibility, a `CommandPreview`-style **preview** of `action → target` + the human
preview + the exact machine payload, and **Approve**/**Reject** controls (with the guard
"nothing runs without your approval"); decided rows update in place, rejected is terminal/
quieted. 7-case API test (list/approve+audit/reject-terminal/illegal-400/invalid-400/
404s); screenshot `evidence/approval_surface.png`; bundle rebuilt; suite 2059/15. Next:
HS-37-04 (guarded executor + audit + governance gate). Earlier: **HS-37-02 shipped —
proposal persistence + lifecycle.** A
durable home for actuator proposals: a new `holdspeak/db/actuators.py` `ActuatorRepository`
(joined to the `Database` container as `db.actuators`) with two tables —
`actuator_proposals` (idempotent on `idempotency_key`; the `target`/`action`/`preview`/
`payload`/`reversible` fields; `decided_by`/`decided_at`/`executed_at`) and
`actuator_proposal_audit` (a row per transition). The lifecycle is an explicit
`_LEGAL_TRANSITIONS` map — `proposed → {approved, rejected}`, `approved → {executed,
failed}`, `failed → {approved}` (retry), `executed`/`rejected` terminal — illegal
transitions raise. The pipeline persists a proposal for any `proposed` run (via
`record_actuator_proposal`; dormant until an actuator is dispatched in HS-37-05); `proposed`
added to `PLUGIN_RUN_STATUSES` in lockstep. Canonical schema snapshot regenerated (+2
tables/+3 indexes); 13 new repo tests; suite 2052/15; db package ruff-clean. Next: HS-37-03
(approval surface). Earlier: **HS-37-01 shipped — actuator contract + unblock the kind.**
The plugin system's third kind is now *proposable*: a new `holdspeak/plugins/actuators.py`
defines `ActuatorProposal` (target/action/preview/payload/reversible/required_capabilities)
with `from_run_output` validation; `plugin_sdk` accepts `kind: actuator` + the `actuator`
capability (the deferred rejection removed); and the host runs an actuator to produce a
**`proposed`** result (the proposal on `output`) — **never an inline side effect** (a
malformed proposal is a plain `error`). The safety model is set: proposing is safe + opts
in via the off-by-default `actuator` capability, while `allow_actuators` is retained,
reserved for gating *execution* (HS-37-04). Default path byte-identical (no actuator
registered; routing tests green); suite 2040/15; modules ruff+F821 clean. Next: HS-37-02
(proposal persistence + lifecycle). Earlier: phase **scaffolded** — plan + 6 stories
grounded
in `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md` (the parent RFC, open question #5) and
the Phase-25 egress posture. The host already has the seam: `PluginHost(allow_actuators=
False)` blocks any `actuator`-kind plugin (`status="blocked"`), and
`plugin_sdk.validate_manifest` rejects the `actuator` kind as deferred. This phase turns
actuators on **behind a preview → human approval → execute flow with an audit trail**,
default-off, with a single reference actuator proven end-to-end. Not yet started — HS-37-01
is the entry point.)

## Goal

Turn on the plugin system's **third kind** — the **actuator** — without ever letting an
external side effect happen silently. Today an actuator-kind plugin is blocked at the host
(`allow_actuators=False`) and rejected at manifest validation (`plugin_sdk`). An actuator
is a plugin that, instead of emitting a read-only artifact, proposes an **external side
effect** (file a follow-up ticket, post a stakeholder update, open a PR comment, …).

The whole phase is organized around one invariant, which is the RFC's open question #5
sharpened by the Phase-25 egress posture:

> **No external side effect occurs without an explicit, audited, per-action human
> approval — and what executes is exactly what was previewed.**

So the unit of work is a **proposal**, not an action: an actuator emits a proposal
(target + human-readable preview + machine payload + reversibility), it persists with a
status lifecycle, a human sees the preview and **approves or rejects**, and only on
approval does a **guarded executor** perform the side effect through the existing
connector/egress surface and write an **audit-log** entry. Actuators stay **off by
default**; the default routing/dispatch path is byte-identical.

## Scope

### In

- **Actuator contract + unblock the kind, gated (HS-37-01).** Define the actuator result
  shape — an `ActuatorProposal` (target system, action verb, `preview` string, machine
  `payload`, `reversible: bool`, `required_capabilities`) — distinct from an
  artifact-generator's read-only output. Unblock `actuator`/`actuators` in
  `plugin_sdk.KNOWN_PLUGIN_KINDS`, and have the host route an actuator's `run()` to
  **produce a proposal, never an inline side effect**; the `allow_actuators` gate (default
  off) and the `blocked` status are retained for *execution*, not for *proposing*. Pure +
  unit-tested; with no actuator registered the default path is byte-identical.
- **Proposal persistence + lifecycle (HS-37-02).** A repository in `holdspeak/db/` storing
  proposals with the status ladder `proposed → approved → executed | rejected | failed`,
  an idempotency key, `created_at` / `decided_at` / `decided_by` / `executed_at`, the
  preview + payload, and the audit fields. Mirrors the plugin-run / artifact persistence;
  the canonical fresh-build schema snapshot is regenerated in the same commit.
- **Approval surface — preview → approve/reject, NO execution (HS-37-03).** Proposed
  actions render in the meeting detail as a Signal card with the **preview** (reusing
  `CommandPreview.astro`), the target + reversibility, and explicit **Approve** / **Reject**
  controls; approving only flips DB state. Nothing egresses on render; an API exposes the
  proposals + the decision endpoint.
- **Guarded executor + audit + governance gate (HS-37-04).** On approval, a guarded
  executor (a) re-derives the preview and asserts **payload parity** (no swap between
  approve and execute — TOCTOU guard), (b) honors the **policy gate** (RFC #5: external
  actuators require explicit human approval; a per-project allow-list in `MeetingConfig`),
  (c) executes the side effect through the existing connector/egress surface
  (`connector_runtime` / `activity_connectors`) so it honors the **Phase-25 provider
  gate**, and (d) writes an **audit-log** entry (actor / action / target / result /
  timestamp). Failures land as `failed` and are retryable. No silent egress: the dry-run
  preview equals the executed payload.
- **Reference actuator end-to-end (HS-37-05).** One concrete actuator wired
  proposal → approve → execute → audit, behind the `actuator` gate + a capability, with an
  **opt-in** integration/spoken test proving the full loop (preview shown → approve →
  executed → audited) **and** that nothing runs without approval. Default suite unaffected
  (gate off).
- **Actuator documentation (HS-37-06).** Bring **all relevant project documentation** in
  line with what shipped: a new **"Actuators"** section in `docs/PLUGIN_AUTHORING.md` (the
  `ActuatorProposal` contract, the propose → approve → execute lifecycle, the capability +
  gate + allow-list, the payload-parity + audit guarantees, a worked example from the
  HS-37-05 reference actuator); an accurate mention in the public `README.md`; and a
  **doc-truth reconciliation** so no *live* doc still calls actuators deferred/blocked.
  Doc drift-guard + link-check stay green. (Dedicated story per user ask — docs are a
  first-class deliverable, not a closeout footnote.)
- **Closeout (HS-37-07).** Egress-posture review (no path egresses without a recorded
  approval + audit); verify the HS-37-06 docs; capture an e2e demo; `final-summary.md`;
  README phase row → done; HANDOVER refresh.

### Out

- **A general connector/integration framework.** Reuse the existing connector surface
  (gh/jira CLI connectors, `connector_runtime`); ship exactly **one** reference actuator.
- **Multi-step / autonomous action chains** (an actuator triggering another). One
  proposal → one approval → one side effect this phase.
- **Auto-approval / unattended execution.** Every external side effect needs a human
  approval this phase; a per-project allow-list may pre-authorize *which actuator ids*
  may be proposed, but execution still records an approval + audit entry.
- **New read-only artifact types or changes to existing artifact schemas** (that was
  Phase 29/36's domain).

## Exit criteria (evidence required)

- [ ] The `actuator`/`actuators` kind is accepted by `plugin_sdk.validate_manifest` and
      proposable by the host, but **no side effect executes** without the
      `allow_actuators` gate + an approval; with no actuator registered the default
      routing/dispatch path is byte-identical (routing tests unchanged). (HS-37-01)
- [ ] Proposals persist with the full lifecycle + audit fields; the canonical fresh-build
      schema snapshot is regenerated in the same commit. (HS-37-02)
- [ ] The approval UI shows the preview + target + reversibility with working
      **Approve**/**Reject**; **nothing egresses on render or on load** — only an explicit
      approval can lead to execution. (HS-37-03)
- [ ] The guarded executor enforces **payload parity** (approve == execute), the **policy
      gate** (external actuator ⇒ approval required), and writes an **audit-log** entry;
      it routes egress through the Phase-25-gated connector surface. (HS-37-04)
- [ ] One reference actuator is proven **end-to-end** (opt-in test): preview → approve →
      execute → audit, **and** a negative test that no action runs without approval.
      (HS-37-05)
- [ ] **All relevant project docs updated:** `docs/PLUGIN_AUTHORING.md` has an Actuators
      section (contract + lifecycle + gate/allow-list + parity/audit + a worked example),
      the public `README.md` mentions actuators accurately, and no *live* doc still calls
      them deferred/blocked; doc drift-guard + link-check green. (HS-37-06)
- [ ] An e2e demo is captured; `final-summary.md` leads with the egress-safety argument;
      README phase row → done; HANDOVER refreshed. (HS-37-07)
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green throughout; the routing
      unit/integration tests stay green (actuators are additive + gated, not a routing
      change). (HS-37-07)

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-37-01 | Actuator contract + unblock the kind (gated, proposal-only) | done | [story-01-actuator-contract.md](./story-01-actuator-contract.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-37-02 | Proposal persistence + lifecycle | done | [story-02-proposal-persistence.md](./story-02-proposal-persistence.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-37-03 | Approval surface — preview → approve/reject (no execution) | done | [story-03-approval-surface.md](./story-03-approval-surface.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-37-04 | Guarded executor + audit + governance gate | done | [story-04-guarded-executor.md](./story-04-guarded-executor.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-37-05 | Reference actuator end-to-end | done | [story-05-reference-actuator.md](./story-05-reference-actuator.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-37-06 | Actuator documentation (project docs update) | done | [story-06-documentation.md](./story-06-documentation.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-37-07 | Closeout + final-summary | not-started | [story-07-closeout.md](./story-07-closeout.md) | — |

## Where we are

**Scaffolded 2026-06-04**, immediately after Phase 36 closed (merged via PR #13). The
recon is done. The seam already exists from Phase 35's groundwork:

- **Manifest gate:** `holdspeak/plugin_sdk.py` — `KNOWN_PLUGIN_KINDS` deliberately omits
  `actuator`; `validate_manifest` raises `unknown_kind` "(actuators are deferred to a
  later phase)". HS-37-01 adds the kind here, behind the host gate.
- **Host gate:** `holdspeak/plugins/host.py` — `PluginHost(allow_actuators=False)` +
  `_is_actuator_plugin()`; an actuator currently returns `status="blocked"` with
  "Actuator plugins are disabled by default". This becomes the *execution* gate; HS-37-01
  makes `run()` *propose* instead.
- **Egress surface:** `holdspeak/connector_runtime.py` / `activity_connectors.py` /
  `connector_packs/{github_cli,jira_cli}.py` — the existing **guarded outbound path**
  (gh/jira CLI), already subject to the Phase-25 provider gate. HS-37-04's executor routes
  through this rather than inventing new egress.
- **Persistence precedent:** `holdspeak/db/plugins.py` (`PluginArtifactRepository` — runs,
  jobs, artifacts) is the shape to mirror for the proposal repo (HS-37-02). The
  fresh-build schema is pinned by `tests/fixtures/db_schema_canonical.txt` +
  `TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot` — **any schema change
  regenerates that snapshot in the same commit.**
- **UI precedent:** artifacts render in `web/src/pages/history.astro` +
  `web/src/scripts/history-app.js`; the clipboard/preview pattern is
  `web/src/components/CommandPreview.astro` (HS-37-03 reuses it for the proposal preview).

## Pickup order

1. **HS-37-01** — actuator contract + unblock the kind (proposal-only, gated) ✅ **done**
   (`ActuatorProposal` + the `proposed` host status; `actuator` kind/capability unblocked).
2. HS-37-02 — proposal persistence + lifecycle ✅ **done** (`ActuatorRepository` +
   `actuator_proposals`/`_audit` tables; lifecycle-enforced + idempotent + audited).
3. HS-37-03 — approval UI ✅ **done** (proposals API + the Signal proposal cards with
   preview → Approve/Reject; no execution on view).
4. HS-37-04 — guarded executor + audit + governance gate ✅ **done** (`ActuatorExecutor`:
   status + policy + payload-parity + injected-connector egress + audited terminal states;
   `MeetingConfig.allow_actuators`/`allowed_actuators`).
5. HS-37-05 — reference actuator end-to-end ✅ **done** (`followup_ticket_actuator` +
   outbox connector; full loop with a real file side effect + the negatives; gated/opt-in).
6. HS-37-06 — **actuator documentation** ✅ **done** (`PLUGIN_AUTHORING.md` Actuators
   section + README + doc-truth reconciliation; worked example on `followup_ticket_actuator`).
7. HS-37-07 — closeout + final-summary. **◀ next (the last story)**

The arc is deliberately linear (each story consumes the prior), unlike Phase 36's two
parallel tracks: the safety invariant is only meaningful end-to-end, so the proposal
shape → persistence → approval → guarded execution → reference actuator must stack in
order; documentation (06) then captures the stable surface, and the closeout (07) is the
record. (Documentation was promoted to its own story on direct user ask.)

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| **Silent egress** — a side effect fires without approval/audit (the whole point) | High if careless | The proposal/approval/execute split; the executor only runs on an `approved` row; an audit entry is written before/around every outbound call; default-off gate | Any code path that performs an outbound action without a recorded approval id |
| Approve→execute **payload swap** (TOCTOU) — what's executed differs from what was previewed | Medium | The executor re-derives the preview and asserts payload parity before acting; the payload is stored on the proposal, not recomputed from mutable state | The executed payload != the approved/previewed payload |
| Scope creep into a **general connector framework** | Medium | Reuse the existing connector surface; exactly one reference actuator; no new egress primitive | A PR adding a second actuator or a generic integration registry |
| Actuators **regress the existing chains** / default behavior | Low (additive + gated) | No actuator registered by default; the proposal path doesn't touch artifact synthesis; routing tests stay green | A `-k`-filtered green hiding a default-path diff |
| The reference actuator's **real egress flakes the suite** | Medium | The end-to-end test is **opt-in** (like the spoken-e2e); the default suite exercises the proposal/approval/audit logic with a stubbed executor | The default suite makes a real outbound call |
| Audit log is **incomplete** (a failure path that doesn't record) | Medium | Every terminal state (`executed`/`rejected`/`failed`) writes an audit row; a test asserts the audit entry exists for each | A terminal proposal with no audit row |

## Decisions made (this phase)

- 2026-06-04 — **Phase is its own unit (not a tail of Phase 35)** because the safety
  invariant intersects the Phase-25 egress posture and needs the full
  proposal→approval→audit stack. (Carried from the Phase 35 handoff + the Phase 37 stub.)
- 2026-06-04 — **The unit of work is a *proposal*, not an action.** An actuator never
  executes inline; it emits a proposal that a human must approve. (Design, grounded in RFC
  open question #5.)
- 2026-06-04 — **Documentation is its own story (HS-37-06), not a closeout footnote**
  (direct user ask). The project-docs update — authoring guide Actuators section + README
  + doc-truth reconciliation — is a first-class deliverable; the closeout renumbered to
  HS-37-07 and now *verifies* the docs rather than writing them.

## Decisions deferred

- ~~**The reference actuator's concrete target**~~ — **resolved in HS-37-05:** a **local
  outbox file write** (not the deferred gh/jira default). The existing `github_cli` pack is
  read-only by Phase-25 policy and real `gh issue create` needs creds/makes real tickets;
  a local outbox is a real, observable, reversible, CI-safe side effect. gh/jira/webhook are
  future connectors on the same `ActuatorExecutor` contract.
- **Proposal storage home** — a new `ActuatorRepository` vs folding into
  `PluginArtifactRepository` — trigger: HS-37-02 — default: a dedicated repo (clean
  lifecycle + audit surface), mirroring the `IntelRepository` queue precedent.
- ~~**Governance granularity**~~ — **resolved in HS-37-04:** per-action approval *always*
  (the `approved` status), with the `MeetingConfig.allow_actuators` master switch + the
  `allowed_actuators` per-project allow-list as *additional* gates that never remove the
  approval+audit step. (Prior deferred wording kept below for the record.)
  ~~per-action approval always vs per-project trust levels that pre-authorize specific
  actuator ids — trigger: HS-37-04 — default: per-action approval always.~~
- ~~**Where the audit log lives**~~ — **resolved in HS-37-02:** a dedicated
  `actuator_proposal_audit` table tied to the proposal row (CASCADE-scoped), not the
  activity ledger.
