> **STATUS BANNER (2026-08-22, appended by the orchestrator — read this first).**
> This handover's "Status: interrupted partial, dirty, uncommitted, not
> ratified" is OBSOLETE. Since it was written, on this branch: tranche A–C was
> stabilized, cold-ratified (two-round counsel; Sol RATIFY, 17/17 §16 items),
> and committed (`f4f6a470`); Phase B slice 1 (live Meeting intelligence on
> the router) shipped in `34c3a9b3`/`b72204bd`/`be9dda58`; slice 2
> (transcription) is implemented awaiting day-one proof. Orient from
> `current-phase-status.md` §"Where we are", the story file's Progress
> section, and `assets/story-08-phase-b-cutover-design.md` (binding counsel
> amendments + the owner's minimal-migration scope ruling). Standing owner
> orders in force: no CI (Actions minutes out; local verification only),
> migrations stay minimal, never hamstring daily use. Sections 8's P0s are
> CLOSED; sections 5, 9–17 remain valid orientation for Phases C–F.

# Phase 143 / Story 08 agent handover

**Prepared:** 2026-08-22  
**Repository:** HoldSpeak  
**Canonical base:** `main` at `89d232f3c7f149cf5a6047680e58768db142aa31`  
**Active implementation worktree:** `.tmp/worktrees/hs143-08`  
**Active implementation branch:** `feat/hs143-08-meeting-adoption`  
**Status:** interrupted partial, dirty, uncommitted, unpushed, **not ratified**  
**Immediate objective:** stabilize and cold-ratify Story 08 tranche A–C before
cutting over any Meeting, Speech, or Background production entrance.

This is the restart document for the next implementation agent. Read it before
editing. Then read the normative files named below. Do not infer that an old
failure, an existing design, or a red test is someone else's problem. In this
project, finding a defect makes it part of the work until it is fixed or named
as an honest blocker.

---

## 1. The product vision

HoldSpeak is moving to one intelligence-routing system:

1. **Models** are reusable model profiles. Local artifacts, OpenRouter models,
   Anthropic models, private OpenAI-compatible endpoints, paired devices, and
   mesh-backed models can all become profiles.
2. **Providers** own hub-local endpoint, credential, binding, and readiness
   facts. Secrets and local paths never become model identity.
3. **Assignments** connect a named HoldSpeak capability to an ordered profile
   chain. Entry 1 is primary; later entries are fallbacks.
4. Every invocation freezes one immutable, content-free route plan before
   egress. Later assignment edits cannot retarget that invocation.
5. Every physical model call is a distinct admitted and receipted
   `inference.invoke@1` child.
6. One fallback controller—not feature code, provider SDKs, or the browser—owns
   retry/fallback advancement.
7. Fallback advances only for a closed, frozen, eligible disposition. Refusal,
   cancellation, permission denial, deadline, and indeterminate/unknown send do
   not fall through to another model.
8. Adding/downloading/connecting a model makes it available. It never silently
   assigns that model to Thoughts, Meetings, Dictation, or anything else.
9. The owner experience is task-first and compact: Model Library, Providers,
   and Assignments. No giant capability-by-model matrix, no verbose wizard, and
   no browser-authored routing truth.
10. Each capability can eventually have a primary plus explicit ordered
    fallbacks. Boundary crossings such as local to cloud must already be saved
    and visible; availability alone is not egress authority.

The motivating owner experience is roughly:

```text
Assignments
Default for AI work       Quick Qwen -> Deep Qwen
Thoughts & notes          Uses default
Writing & dictation       Tiny Qwen -> Quick Qwen
Meetings                  This device -> Deep Qwen
Agents & tools            Uses default
```

Story 08 is backend/application adoption. Story 13 owns the shared editable
Assignments glass. Do not build a second Meeting-specific routing UI here.

---

## 2. Normative reading order

Read these in order before changing Story 08:

1. [`assets/architecture-contract.md`](./assets/architecture-contract.md)
2. [`story-08-meetings-speech-background-adoption.md`](./story-08-meetings-speech-background-adoption.md)
3. [`current-phase-status.md`](./current-phase-status.md)
4. [`evidence-story-07.md`](./evidence-story-07.md)
5. [`evidence-story-06.md`](./evidence-story-06.md)
6. [`assets/generated-inference-capability-census.md`](./assets/generated-inference-capability-census.md)
7. [`assets/generated-routing-authority-census.md`](./assets/generated-routing-authority-census.md)
8. [`assets/generated-surface-fallback-census.md`](./assets/generated-surface-fallback-census.md)
9. [`assets/repository-census.md`](./assets/repository-census.md)
10. [`assets/owner-experience.md`](./assets/owner-experience.md)

The architecture contract is authority. If code and the contract disagree,
stop and resolve the disagreement explicitly. Do not add a second persisted
type or authority to work around it.

---

## 3. What is already merged

Stories 01–07 are merged and marked done.

| Story | Delivered authority |
|---|---|
| 143-01 | Fail-closed repository/call-site/routing/fallback censuses |
| 143-02 | Sealed canonical capability and retry-policy registry |
| 143-03 | Immutable model-profile revisions, bindings, readiness, v1 adapter |
| 143-04 | Sparse ordered assignments, precedence, CAS, migration markers |
| 143-05 | Frozen route plans and private admitted-request evidence |
| 143-06 | Durable fallback controller, failure law, attempt receipts |
| 143-07 | Production adoption for Ask, Thought interview, intent, rewrite |

Important merged commits:

- `87b46545` — Story 07 implementation
- `8fc6e476` — Story 07 merge
- `38ae6ce2` — Story 06 closeout evidence
- `914b6f15` — Story 06 closeout merge
- `a6156d60` / `0639c77b` — Model acquisition glass corrected to
  library-only `Added`, with no silent assignment
- `f90a6e01` / `89d232f3` — runtime-proof glass stabilized across clean CI
  environments

Story 07 proved the first lawful saved local-to-cloud fallback. An available
but unsaved cloud profile received zero calls. Preserve that law.

---

## 4. Git and worktree state

The root worktree is clean on `main` at `89d232f3`.

The Story 08 implementation is isolated in:

```text
.tmp/worktrees/hs143-08
branch: feat/hs143-08-meeting-adoption
base:   89d232f3
```

Current dirty files:

```text
M  holdspeak/db/schema.py
M  holdspeak/inference_capabilities.py
M  holdspeak/kernel/parent_run.py
M  holdspeak/services/inference_fallback_controller.py
M  holdspeak/services/inference_route_plan_service.py
M  holdspeak/services/sync_service.py
?? holdspeak/services/inference_parent_route_bundle_service.py
?? holdspeak/services/inference_semantic_adapters.py
?? holdspeak/services/inference_service_route_policy.py
?? tests/unit/test_phase143_meeting_route_primitives.py
```

Do not reset, overwrite, or casually rebase this worktree. Preserve the dirty
partial and inspect every diff. No Story 08 commit, push, PR, or CI run exists.

---

## 5. Story 08 scope

Story 08 must eventually adopt:

### Meetings

- `meeting.live_analysis`
- `meeting.bookmark_label`
- `meeting.auto_title`
- `meeting.deferred_analysis`
- every installed, revision-bound `meeting.plugin.<id>`

### Speech

- `speech.transcribe`
- internal `speech.preload`

`speech.preload` is lifecycle work. It is internal/nonassignable and must never
appear as an owner-facing model assignment. Silent-audio/model-holder warming
is not model fallback.

### Background

- `background.rails_summary`
- `background.cadence_draft`
- `decision.promotion_draft`
- `delivery.pr_review_draft`

### Required removals/cutovers

- `MeetingIntelPlan` as a new-work routing authority
- remaining `SpeechSessionPlan` route authority for transcription/preload
- feature-owned meeting fallback loops
- provider-owned dialect retry loops
- post-marker Config/profile/target reads and writes
- request-authored `inference_target_id` selectors in Decision/Delivery
- Rails/Cadence direct placement resolution
- duplicated Settings controls for migrated families

Historical v1 rows and DTO readers remain readable. Do not rewrite history.

---

## 6. The current tranche: A–C only

The dirty Story 08 worktree intentionally implements primitives before any
production entrance cutover.

### A. Semantic result contracts and adapters

New file: `holdspeak/services/inference_semantic_adapters.py`

Implemented direction:

- Meeting analysis normalizes to exact semantic output:

  ```json
  {
    "summary": "...",
    "topics": ["..."],
    "action_items": [{"task": "...", "owner": null, "due": null}]
  }
  ```

- Bookmark label normalizes to `{"label": "..."}`.
- Meeting title normalizes to `{"title": "..."}`.
- Transcription normalizes to `{"text": "...", "language": null|string}`.
- Preload normalizes to `{"state": "..."}`.
- Plugin adapters validate the exact inner plugin result, not a
  `PluginRunResult` wrapper.
- Rails summary normalizes to `{"summary": "..."}`.
- Cadence, Decision, and Delivery drafts normalize to `{"draft": "..."}`.
- Provider/model/boundary metadata is excluded from semantic result bytes.
  Placement comes from the frozen deployment and controller receipt.
- Invalid/missing/extra fields become `InferenceInvalidTypedOutput` before a
  successful Runner result can be elected or projected.

Revision rule now attempted in the partial:

- Only the six genuinely corrected text contracts are bumped to revision 2:
  bookmark, title, Rails, Cadence, Decision, Delivery.
- Meeting analysis, transcription, preload, and installed plugin contracts
  remain revision 1 where their canonical schema is unchanged.
- A historical adapter preserves the exact old v1
  `{output, provider, model}` shape.
- Operation binding reconstructs the frozen capability definition from route
  authority evidence instead of demanding that it equal today's registry.

This last point is essential: a registry upgrade must not make pre-upgrade
frozen work non-resumable.

### B. Feature-principal route policy

New file: `holdspeak/services/inference_service_route_policy.py`

Implemented direction:

- OWNER work may use normal invocation -> subject -> capability -> group ->
  global assignment precedence.
- SERVICE work is default-deny.
- A service policy binds exact:
  - service identity
  - authority basis
  - allowed operation names/versions
  - parent kind
  - capability ID/revision/schema
  - allowed boundaries
  - allowed assignment source layers
- The current meeting queue policy permits only exact capability assignments.
  It cannot inherit OWNER group/global rows.
- Full principal policy evidence is frozen privately with the route.
- `inference_route_plans.principal_policy_sha256` marks evidence as mandatory,
  preventing downgrade by deleting the evidence row.

Do not weaken OWNER stores to support SERVICE. Do not fabricate OWNER for a
queue, Rails observer, preload service, or background worker.

### C. Parent + multi-route bundle and Stop handoff

New file: `holdspeak/services/inference_parent_route_bundle_service.py`

Schema additions currently include:

- `inference_route_plan_principal_evidence`
- `inference_parent_route_bundles`
- `inference_parent_route_bundle_members`
- `inference_parent_stop_handoffs`
- `inference_parent_stop_handoff_executions`
- `inference_parent_stop_handoff_settlements`
- immutable UPDATE/DELETE triggers for the new evidence/history rows

Implemented direction:

- The kernel operation shell is admitted through the existing Broker.
- Parent row, every declared route, and the ordered route-set manifest commit in
  one SQLite transaction.
- Bundle members cross-bind route SHA, principal policy SHA, parent identity,
  deadline, and budget.
- Child budget is intended to be derived from frozen retry-policy truth and to
  match the kernel envelope and parent row exactly.
- Synchronous bundle refusal terminalizes the shell and leaves no partial
  route rows.
- Stop derives the complete active/stopping execution set server-side. Callers
  cannot provide an empty or selectively incomplete list.
- Controller Stop happens inside the same durable handoff transaction.
- Parent epoch is fenced.
- An adopter-owned evidence provider persists/reconstructs the displaced-work
  effect.
- Pending -> committed settlement is append-only rather than mutating history.

The controller now has `request_stop_in_transaction(...)`, allowing the adopter
handoff to fence all route executions in its own transaction.

---

## 7. Current verification state — do not overclaim

The partial is **not green and not ratified**.

Last exact implementation command:

```bash
cd .tmp/worktrees/hs143-08
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m compileall -q \
  holdspeak/db/schema.py \
  holdspeak/inference_capabilities.py \
  holdspeak/kernel/parent_run.py \
  holdspeak/services/inference_fallback_controller.py \
  holdspeak/services/inference_route_plan_service.py \
  holdspeak/services/inference_parent_route_bundle_service.py \
  holdspeak/services/inference_semantic_adapters.py \
  holdspeak/services/inference_service_route_policy.py \
  tests/unit/test_phase143_meeting_route_primitives.py

PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q -x \
  tests/unit/test_phase143_meeting_route_primitives.py
```

Observed result before pause:

```text
compileall: clean
pytest: 8 passed, 1 failed in a 10-test file
```

The failure expected `KernelParentHandoffFence@1`; the implementation emits
`ParentHandoffFence@1`. The test was corrected, but **not rerun** after the
pause. A mandatory principal-evidence marker also changed after prior green
runs and has not been rerun.

Earlier, before the latest changes:

```text
new primitive file: 9 passed in 1.29s
existing route/capability/schema/controller matrix: 114 passed in 20.75s
```

Those earlier counts are historical context, not current evidence.

---

## 8. Remaining blockers at handover

### P0 — displaced work may become runnable too early

This is the most important remaining authority defect.

The current Stop handoff can persist adopter displaced-work evidence while an
old physical attempt is still `dispatch_intent`/unknown and the controller is
only `stopping`. The provider contract does not yet prove that the displaced
work is inert until settlement.

A real provider could enqueue runnable deferred work immediately. That creates
the forbidden overlap:

```text
old physical call may still egress
                 +
new deferred replacement starts
                 =
duplicate/overlapping egress
```

The current test provider writes an inert `test_handoff_effects` row, so it
does not prove execution safety.

Required closure:

1. Election transaction persists only a **reserved, inert** displaced-work
   record.
2. That record is explicitly blocked from claim/dispatch.
3. Only after every fenced old execution reaches a known terminal settlement
   may one atomic settlement activate the displaced work.
4. Restart reconstruction must preserve the inert/active distinction.
5. Crash after reserve but before settlement must not egress.
6. Unknown old dispatch must keep replacement inert forever or until a lawful
   reconciliation terminalizes the old attempt.
7. Add an executable test, not only a metadata-row test.

### P0 — no current fully green checkpoint

Rerun the 10 primitive tests immediately. Any red result is owned work. Do not
continue to entrance cutover until this is green.

### P1 — future non-default assignment policy

The bundle currently precomputes the kernel child budget from each capability's
default retry policy and later compares it with the resolved assignment policy.
Today's built-ins permit one policy, so fixtures pass. A future lawful
non-default permitted assignment policy could be refused only after shell
admission.

Either:

- derive the exact resolved policy before shell admission and revalidate it in
  the bundle transaction; or
- explicitly constrain and startup-validate this primitive's registry contract.

Do not allocate a guessed budget or admit a shell under one policy and execute
under another.

### P1 — missing tamper/restart proof

Still required:

- nested principal-policy material tamper
- deletion of mandatory principal evidence
- bundle payload/row/member cross-substitution
- handoff effect hash and provider revision tamper
- settlement cross-command substitution
- Stop command/effect provenance tamper
- crash after shell but before bundle
- crash after inert handoff reserve but before settlement
- restart replay with zero duplicate egress
- hostile sync refusal for every new table

### P1 — generated artifacts and schema fixture

The canonical schema snapshot and all generated censuses are stale relative to
the dirty Story 08 worktree. Regenerate/update only after the design stabilizes:

- canonical DB schema snapshot
- inference capability census
- routing authority census
- surface/fallback census
- one-path/cardinality census, if new production entrances appear

The current tranche should add primitives but no production entrance. Census
changes must say exactly that.

---

## 9. Existing production forks Story 08 must eventually remove

### Meeting parallel authority

Current files:

- `holdspeak/meeting_session/intel_plan.py`
- `holdspeak/meeting_session/intel_child.py`
- `holdspeak/meeting_session/intel_admission.py`
- `holdspeak/meeting_session/deferred_admission.py`

Problems:

- `MeetingIntelPlan` resolves Config/profile placement separately.
- `run_admitted_capability` advances entries on broad `failed` outcomes.
- route-leg and physical-attempt ordinals can collide.
- streaming may expose primary tokens before typed validation/winner election.
- live parent, frozen plan, deferred claim, and Stop handoff span separate
  transactions.

Required ordinal truth for dialect retry then fallback:

```text
leg 1 / physical 1
leg 1 / physical 2   compatibility/dialect retry
leg 2 / physical 3   route fallback
```

### Deferred Meeting queue

Queue scheduling/backoff is a new job/parent attempt, not provider retry.
Recovery must adopt the exact claimed job/parent/route bundle. It must not
re-resolve current Config after a crash.

Installed plugins are exact revision-bound capabilities. Arbitrary
`plugin:<id>` strings are not routable. Dedup/skipped/fault-injected plugin work
creates no model child.

### Speech transcription and preload

Current files:

- `holdspeak/speech_session/plan.py`
- `holdspeak/speech_session/transcription.py`
- `holdspeak/speech_session/provider.py`
- `holdspeak/speech_session/session.py`

Story 07 adopted routed intent/rewrite, but transcription/preload still use the
parallel speech plan.

Laws:

- transcription result is exact `{text, language}`
- actual audio bytes or a trusted immutable audio reference must be hashed;
  never trust a caller-provided audio SHA
- a transcription timeout with an abandoned live worker is
  `dispatch_outcome_unknown`; no second model starts
- preload is internal lifecycle work derived from the selected transcription
  artifact
- model-holder warmup and silent-audio warmup are explicit bounded lifecycle
  strategies, not owner model fallbacks
- no preload owner assignment row

### Rails

Current `holdspeak/rails_observer.py` resolves mutable placement and runs a root
Runner call under SERVICE. It needs a stable event-batch identity, exact service
policy, frozen material, controller receipt, and idempotent publication.
Event-only degradation happens only after controller terminal exhaustion.

### Cadence

Current `CadenceService._drafted_next_action` resolves mutable placement.
HTTP and MCP must delegate one application service and exact semantic draft
schema. Deterministic fallback copy is product degradation after controller
terminal exhaustion, not another hidden model attempt.

### Decision

`DecisionLifecycleService.draft_promoted_with_model` accepts an open payload
containing `inference_target_id`. Remove/close that selector and freeze the
accepted Decision revision to prevent promotion races.

### Delivery

`holdspeak/web/routes/delivery_prs.py` currently performs orchestration in the
transport and accepts `inference_target_id`. Extract a transport-neutral
application service, close the body, freeze exact linked/diff context, and keep
drafting distinct from send/propose effects.

---

## 10. Failure law that must survive every adopter

Only frozen policy decides advancement.

| Condition | Fallback? | Required truth |
|---|---:|---|
| Known no-generation transient | if policy says yes | retry/advance with new child |
| Provider permanent failure | if policy says yes | advance only after typed receipt |
| Invalid typed output | if policy says yes | correction/retry then fallback per budget |
| Context overflow | only to provably larger frozen context | never re-resolve chain |
| Local capacity unavailable | only if policy says yes | capacity is operation-time truth |
| Refusal | no | zero fallback |
| Permission denial | no | zero fallback |
| Owner cancellation / Stop | no | fence future reservations |
| Deadline | no | zero fallback |
| Dispatch/effect unknown | no | terminal/indeterminate, never guess |

All physical provider calls need distinct kernel children and receipts.
Provider SDK retries must be disabled or represented as controller attempts.
Feature code may degrade its product output after terminal exhaustion, but that
degradation is not model fallback and must not erase the route receipt.

---

## 11. Migration and cutover rules

Suggested migration families:

- `meeting-route-assignments`
- `speech-recognition-route-assignments`
- `background-route-assignments`, or narrower background subfamilies if one
  broken pointer must not block all background adoption

Migration must:

1. Preserve actual historical effective primary and saved boundary consent.
2. Never guess a replacement for blank/dangling/incompatible pointers.
3. Never silently add cloud to an old local-only configuration.
4. Map explicitly saved Meeting `auto` only if the old setting already encoded
   owner consent for that visible local-to-cloud behavior.
5. Create exact profiles/bindings where a legacy built-in local artifact has no
   v1 ProfileRecord, or emit one named repair issue.
6. Write assignment effects and marker atomically, or use a formally crash-safe
   protocol that reconstructs the exact effects.
7. After the marker, make old Config/settings writers refuse and make runtime
   execution independent of old reads.
8. Keep old plan/history readers intact for existing rows.

Acceptance tests should monkeypatch every legacy resolver/Config read to explode
after the marker and still pass execution/reprojection.

---

## 12. Recommended execution sequence

### Phase A — stabilize the current primitive tranche

1. Rerun `test_phase143_meeting_route_primitives.py` from the dirty worktree.
2. Fix every red result.
3. Close the inert displaced-work/settlement P0.
4. Close exact future policy/budget derivation.
5. Add hostile tamper, crash, restart, and sync tests.
6. Regenerate schema/censuses.
7. Run the full local A–C matrix.
8. Request cold counsel. Do not self-ratify.

### Phase B — live Meeting + transcription

1. Atomically admit live parent plus exact route-set bundle.
2. Freeze operation material only when actual child work exists.
3. Route live analysis/bookmark/title through coordinator/controller.
4. Route transcription through exact audio evidence.
5. Buffer/discard attempt output until controller winner election.
6. Implement Stop fencing and inert displaced-work handoff.
7. Prove crash/restart and assignment-edit-after-freeze laws.

### Phase C — deferred Meeting and plugins

1. Atomically bind claimed queue attempt + parent + route bundle.
2. Keep scheduling retry/new parent distinct from model retry.
3. Adopt deferred analysis/bookmark/title.
4. Adopt every installed plugin using exact inner result schema/revision.
5. Refuse unknown plugin IDs and revision drift.
6. Prove no duplicate egress across restart/manual retry/Stop handoff.

### Phase D — speech lifecycle

1. Adopt standalone/session transcription.
2. Model preload as explicit internal lifecycle stages.
3. Remove hidden candidate loops and response-format retry ownership.
4. Treat live timeout as unknown/no fallback.
5. Prove actual-audio evidence and no owner-facing preload assignment.

### Phase E — background adopters

Order: Rails -> Cadence -> Decision -> Delivery.

For each:

- exact principal policy
- stable material identity
- atomic route/operation/controller admission
- typed validation before publication
- controller receipt-gated effect
- idempotent restart
- no request-authored target/profile selector
- deterministic degradation only after terminal exhaustion

### Phase F — migration and cleanup

1. Run family migrations.
2. Cut over Settings/application readers.
3. Remove post-marker legacy writes.
4. Update API/MCP inventories if surfaces change.
5. Update all censuses.
6. Run local broad gates and cold audit.
7. Only then update Story 08 status/evidence.

---

## 13. Required local tests

Start with:

```bash
cd .tmp/worktrees/hs143-08
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q -x \
  tests/unit/test_phase143_meeting_route_primitives.py
```

Then run the adjacent authority matrix:

```bash
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q \
  tests/unit/test_phase143_meeting_route_primitives.py \
  tests/unit/test_phase143_production_adoption.py \
  tests/unit/test_phase143_inference_route_plans.py \
  tests/unit/test_phase143_inference_fallback_controller.py \
  tests/unit/test_phase143_inference_assignments.py \
  tests/unit/test_phase143_inference_capability_registry.py \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/unit/test_one_path_cardinality.py \
  tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot \
  tests/unit/test_db_schema_policy.py
```

As adopters land, add focused Meeting/Speech/background tests rather than
substituting the broad suite for semantic evidence.

Run static checks locally:

```bash
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m compileall -q \
  holdspeak/services/inference_parent_route_bundle_service.py \
  holdspeak/services/inference_semantic_adapters.py \
  holdspeak/services/inference_service_route_policy.py

/Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m ruff check --select F \
  holdspeak/services/inference_parent_route_bundle_service.py \
  holdspeak/services/inference_semantic_adapters.py \
  holdspeak/services/inference_service_route_policy.py \
  holdspeak/services/inference_route_plan_service.py \
  holdspeak/services/inference_fallback_controller.py \
  tests/unit/test_phase143_meeting_route_primitives.py

git diff --check
```

Use the repository's exact Node setup only when Story 08 touches web code:

```bash
source /Users/karol/.nvm/nvm.sh
nvm use 22.21.0
```

---

## 14. GitHub Actions budget rule

GitHub Actions minutes are exhausted/constrained. Four duplicate active runs
were cancelled on 2026-08-22:

```text
32583384302  main push
32582857865  runtime-proof PR
32582374609  prior main push
32582372892  prior acquisition-glass PR
```

All four reached `completed/cancelled`.

Do not push merely to obtain CI. Do not open draft PRs as a test runner. Work
locally, record exact commands/counts, and spend Actions minutes only on one
deliberate final verification after local ratification and owner agreement.

The repaired Models browser glass did pass on the clean macOS Actions image
before cancellation. Local adjacent proof was:

```text
31 passed in 20.22s
```

across both Models E2E files and setup/acquisition authority suites.

---

## 15. Things the next agent must not do

- Do not call a red test “pre-existing” and move on.
- Do not land the current dirty Story 08 tranche.
- Do not mark Story 08 in progress/done merely because primitives exist.
- Do not cut over production entrances before tranche A–C cold-ratifies.
- Do not let SERVICE inherit OWNER group/global assignments.
- Do not create a second route plan, fallback controller, deployment registry,
  or inference gateway.
- Do not let browsers, Settings, or request bodies supply raw target/profile IDs
  after cutover.
- Do not put prompt/audio/transcript/note bytes, local paths, endpoints, or
  secrets into route plans, receipts, sync, or ordinary DTOs.
- Do not expose primary/fallback attempt output before winner election.
- Do not advance after unknown send/effect.
- Do not treat queue scheduling retry, preload strategy, silent audio, lexical
  degradation, or manual recovery as model fallback.
- Do not auto-assign a newly added/downloaded model.
- Do not rewrite historical v1 bytes.
- Do not use GitHub Actions as the normal development loop.
- Do not commit, push, or open a PR before explicit ratification/authority.

---

## 16. Definition of a stable A–C checkpoint

The next agent may request cold audit only when all are true:

- [ ] `test_phase143_meeting_route_primitives.py` is fully green from a fresh run.
- [ ] Displaced work is provably inert until old unknown egress settles.
- [ ] Restart cannot activate both old and replacement work.
- [ ] Principal evidence is mandatory and deeply reconstructed.
- [ ] SERVICE group/global inheritance is impossible.
- [ ] Historical frozen routes execute through exact historical adapters.
- [ ] Bundle member/row/payload/hash cross-substitution refuses.
- [ ] Stop derives and fences the complete execution set.
- [ ] Stop/handoff/effect/settlement provenance tamper refuses.
- [ ] Exact resolved retry policy and child budget agree before admission.
- [ ] New tables are hostile-sync refused.
- [ ] Canonical schema snapshot is updated and green.
- [ ] All three generated Phase 143 censuses are exact and green.
- [ ] One-path/cardinality census is green.
- [ ] Adjacent Story 05–07 regression matrix is green.
- [ ] Focused Ruff/compileall/diff-check are green.
- [ ] Independent counsel has rerun hostile/restart cases and returned RATIFY.

---

## 17. First commands for the next agent

```bash
cd /Users/karol/dev/tools/HoldSpeak
git status --short --branch
git log -5 --oneline

cd .tmp/worktrees/hs143-08
git status --short --branch
git diff --stat
git diff --check

PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/python -m pytest -q -x \
  tests/unit/test_phase143_meeting_route_primitives.py
```

Then inspect the P0 path before making any broad edits:

```bash
rg -n "request_stop_handoff|reconcile_stop_handoff|HandoffEvidenceProvider" \
  holdspeak/services/inference_parent_route_bundle_service.py \
  tests/unit/test_phase143_meeting_route_primitives.py
```

Design and prove the inert displaced-work state first. That is the current
critical path.

---

## 18. Final orientation

The project is not starting over. Stories 01–07 provide a strong canonical
spine: profiles, assignments, frozen plans, a durable controller, and the first
production adopters. Story 08 is where the hardest long-lived and service-owned
work joins that spine.

The partial tranche has valuable work: semantic adapters, historical contract
support, explicit SERVICE authority, atomic route bundles, and controller-aware
Stop handoff. Preserve it. But do not confuse “valuable” with “safe to land.”
The duplicate-egress handoff risk is real, the last test checkpoint was not
rerun, and the generated guards are stale.

Proceed in small, adversarially tested slices. Freeze truth once. Reconstruct it
on restart. Make unknown completion stop. Keep replacement work inert until it
is lawful. Let the controller—not feature lore—decide fallback. Then ask for an
independent cold audit.
