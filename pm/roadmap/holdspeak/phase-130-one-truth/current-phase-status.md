# Phase 130 — One Truth

**Status:** DONE (11/11).

**Last updated:** 2026-08-09.

## What we're building

The owner's verdict (GitHub issue #450), and the live rider that came with
it: *"I need this system to be simple, predictable, and easy to build and
integrate against… retain nearly all of its robustness."* HoldSpeak can today
check one model, execute another, and report a third; a LAN destination can be
badged "cloud" while a mesh route is badged "Local only"; nine different
places can answer "where does this run?" and they disagree. This phase makes
**execution and receipts true** — the kernel-free half of the consolidation.
It does not yet route every invocation through kernel admission (that is Phase
131, One Admission Path); it makes the answer to *"what did the run use in the
end?"* honest first, one phase earlier, because that is the part the owner
experiences as the product no longer lying.

The keystone is the **precedence resolver**: one function returning the
effective placement **and the source it was inherited from**, `null` meaning
inherit everywhere — never silently "this device." It answers four of the
owner's five questions by itself, needs no kernel, and is the only change in
this phase the owner will feel as *simpler* rather than merely honest.

## The evidence base (pre-charter audits)

Three parallel read-only verification audits against the post-#451 tree
(2026-08-08), reports archived under `assets/audits/` (audit-1-runtime,
audit-2-web, audit-3-ontology) and mirrored from the issue-450 counsel pack.
**23 of 25 owner claims confirmed at file:line; 1 half-fixed; 1 misread.** The
audits found ~12 adjacent defects in the same families. The claims this phase
acts on:

- **Readiness ≠ execution ≠ receipt identity.** `_this_machine_readiness`
  (inference_targets.py:152-179) checks the dictation runtime backend/paths;
  execution builds meeting intelligence from `meeting.intel_realtime_model`
  (inference_targets.py:394-414, intel/providers.py:209-237). A named
  on-device target reports `profile.model_file` but the execution branch
  loads the global meeting model (providers.py:430-438) and the receipt
  stamps `target.model` (recipe_service.py:183-185). `paired_device_target`
  hardcodes `readiness_state="ready"` (inference_targets.py:202-217).
- **Egress truth derived four times.** `_private_endpoint`
  (inference_targets.py:30-43), `endpoint_egress` (providers.py:249-267,
  collapses every remote to `cloud`, and stamps `DEFAULT_CLOUD_HOST` when the
  host parse fails), `intel_egress_posture` (providers.py:442-463, prints
  "Local only" while a `meshNode` pointer routes to the relay), plus the
  duplicated `_run_egress` copies (support.py:151-159, ask_service.py:171-180).
- **Meeting placement has two owners** (`intel_provider` +
  `intel_profile_id`, config/meeting.py:33,59; providers.py:220-237,359-377)
  and, with `intel_provider` defaulting to `"local"`, the Models destination
  picker is a **silent no-op** (audit-2 claim 10). `mir_profile` /
  `plugin_profile` (config/meeting.py:68,79): runtime reads the first, doctor
  reports the second.
- **Ask silently retargets** on a mismatching model name
  (ask_service.py:69-80) and dedupes models across destinations
  (ask_service.py:30-47).
- **Secret-slot collision is credential exfiltration.** `profile_key_env`
  (providers.py:270-274) maps `foo-bar` and `foo_bar` to one env name; profile
  ids are **client-supplied** (profile_service.py:49) and sync-merged by any
  peer (sync_service.py:690-705), so a colliding profile pointed at a hostile
  `base_url` receives another destination's real key (providers.py:347,423).
- **`/api/settings` is last-writer-wins** across four partial-tree writers
  (Readiness.tsx:45-48, useSpeakDeck.ts:265-273, CommandsCore.tsx:63-67, the
  Prefs debounce) with no version/etag — two open tabs destroy each other's
  edits; `CommandsCore.persist` re-sends a stale full `items` array on a
  checkbox toggle (data loss).
- **Placement's empty value has three readings:** the backend picks
  `this_machine` (workbench_conductor.py:453), RecipeEditor labels `""`
  "Default runs on" (RecipeEditor.tsx:107), InfoWindow labels the same `""`
  "This device" and writes `null` (infoContract.ts:80,90).
- **"Receipt" is overloaded.** `DecisionReceiptService` stores mutable
  governing content with an edit trail (decision_receipt_service.py:14-16,
  132-181,263-301) under a word the Constitution (Art. XI) and the kernel
  journal (kernel/journal.py:258-276) reserve for immutable evidence.
- **Workbench double-create** (dataSlice.ts:150 + WorkbenchTemplatePicker.tsx
  :46-76) and two dead voice intents `set-agent` / `dismiss`
  (workbench.ts:34-53 vs WorkbenchWindow.tsx:1170-1221).

## Constitutional grounding

- **Article V** — *"Every attempt leaves a receipt: who, what, where,
  outcome."* This phase makes the receipt name the deployment that actually
  ran. It also fixes the word: Receipt is immutable evidence, and the mutable
  governing document is renamed Decision.
- **Article XI** — the kernel's fixed meaning of *receipt* and *deployment*;
  this phase aligns readiness/execution/receipt onto one deployment identity
  so Phase 131's admission has one true thing to admit.
- **Article I** — placement is one authority with projections, not nine
  owners; the precedence resolver is that authority.
- **Article VII.1** — labels state what: the four scoped placement labels
  (Default / Workbench / Run this / Retry) replace the one overloaded
  "Runs on."

(Article IX, cited in the issue, governs how this phase *closes* — the walk
and the full suites — not why it exists; recorded as an adopted correction.)

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-130-01 | The precedence resolver — one placement authority | done | [story-01](story-01-the-precedence-resolver.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-130-02 | Collision-free secret slots — the exfiltration path closes | done | [story-02](story-02-secret-slots.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-130-03 | One deployment identity — readiness, execution, receipt agree | done | [story-03](story-03-one-deployment-identity.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-130-04 | One egress vocabulary — the four lies become one truth | done | [story-04](story-04-one-egress-vocabulary.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-130-05 | One meeting placement policy | done | [story-05](story-05-meeting-placement-policy.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-130-06 | Ask tells the truth — no model-name retargeting | done | [story-06](story-06-ask-tells-the-truth.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-130-07 | Settings, one honest writer — versioned, transient retry | done | [story-07](story-07-settings-one-writer.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-130-08 | DecisionReceipt → Decision — the word returns to evidence | done | [story-08](story-08-decision-rename.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-130-09 | Workbench — one gesture one record, live voice | done | [story-09](story-09-workbench-one-gesture.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-130-10 | The inherited ledger — triage and assign the 96 | done | [story-10](story-10-inherited-ledger.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-130-11 | The walk | done | [story-11](story-11-the-walk.md) | [evidence-story-11](./evidence-story-11.md) |

## Delivery order (waves)

- **Wave A (parallel, disjoint files):** 01 resolver (keystone), 02 secret
  slots (**ships first in the commit lane — the credential path closes before
  anything else lands**), 08 Decision rename, 09 workbench+voice.
- **Wave B (consume the resolver's deployment identity):** 03 one deployment
  identity, then 04 egress and 05 meeting placement.
- **Wave C:** 06 Ask truth, 07 settings versioning (both touch files Wave B
  brushes — serialized SHIP).
- **Wave D:** 10 the inherited-ledger triage (needs the backend-touching
  stories landed), then 11 the walk (orchestrator-run, cannot be waived).

## Where we are

Chartered 2026-08-09 from the issue-450 counsel pack. The owner gave the word;
Sol returned *"ratify as amended"* with seven reservations, all adopted (see
SOL-COUNSEL.md and the decision log). This phase is the kernel-free "One Truth"
half of a **four-phase program** — 130 One Truth, 131 One Admission Path, 132
One Owner Per Decision, 133 One Word Per Thing.

**Wave A in flight (2026-08-09):** three disjoint-file stories implemented by
parallel worktree-isolated Terras and integrated with zero conflicts —
**HS-130-01 (resolver, keystone)** ships first, then HS-130-08 (Decision rename)
and HS-130-09 (Workbench one-gesture + voice). Verified against a clean isolated
baseline: the integrated tree matches the inherited red baseline **exactly**
(105 fail/error, all reproduce on pre-phase main — the 96-ledger + env; HS-130-10
owns the triage), **zero new regressions** after one orchestrator seam-fix (the
v39→v40 migration test's hardcoded `SCHEMA_VERSION == 42` bumped to 43 alongside
08's schema change), web suite 797 green. The local baseline needed an isolated
HOME: the default DB path is `Path.home()`-relative and the owner's real hub DB
is at schema v43 while pre-phase code is v42 — 08's bump to v43 is what realigns
committed code with the owner's data.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The resolver becomes a ninth owner instead of the one authority | medium | 01 lands the resolver AND deletes the three empty-value readings in the same wave; a grep gate forbids new `or "this_machine"` fallbacks outside the resolver | any caller still resolving placement inline after 01 |
| Egress consolidation changes a boundary verdict for a real endpoint | medium | 04 carries a table of every current endpoint→boundary mapping as a frozen test; control-vs-treatment on .43 for the LAN case in the walk | a private LAN endpoint newly reports `cloud`, or a cloud endpoint newly reports `private_network` |
| The Decision rename churns a just-shipped Phase 127 surface | low | 08 is the word only (12 backend + 1 web + 4 tables + 4 sync kinds, measured); model convergence deferred to 133; one migration | a rename PR adds behavior or touches the receipt lifecycle |
| Settings versioning breaks a legitimate verb projection | medium | 07's guard is an allowlist per settings subtree keyed on PUT callers, not on controls (Sol reservation, "Keep valid layers") | a menu/shortcut/context-menu projection of one setting is rejected as a duplicate writer |
| Inherited-96 double-counted between 130 and 131 | medium | 10 triages against current main and assigns each failure a single home; sync-registry-dependent failures route to 131 by name, not repaired here | the same test appears as owned by both 130 and 131 |

## Decisions made (this phase)

- 2026-08-09 — **Sol's phase cut adopted over the orchestrator's.** The
  original position proposed three phases (Wave 0/1/2). Sol proved Wave 0 is
  two phases split at *kernel-free truth vs kernel truth*, not deep-vs-shallow,
  because Ask has no definition/revision for the codec and Sequence/Workflow
  admission is its own design beat. The program is four phases; 130 is the
  kernel-free truth. (SOL-COUNSEL.md #3.)
- 2026-08-09 — **The secret-slot collision is reclassified as a
  credential-exfiltration path** (client-supplied ids + shape-only sync merge)
  and cut FIRST in the commit lane, not eighth. (SOL-COUNSEL.md #4;
  auditor-found escalation of issue claim 8.)
- 2026-08-09 — **The "one global model dial" acceptance criterion is
  replaced.** Phase 112 "Enough" already shipped it (story-01-one-dial); as
  written it certifies nothing and would flip green without work. This phase's
  bar: *every placement control states its scope, and when unset names the
  source it inherits from.* (SOL-COUNSEL.md #6 — an adopted amendment to issue
  #450's acceptance criteria; the owner may overrule at the sitting.)
- 2026-08-09 — **Article IX is an adopted correction, not a basis.** The issue
  cites it as a mandate ground; it governs the close (proof over claim), which
  this phase honors in HS-130-11. (Audit-3 constitutional check.)
- 2026-08-09 — **`capability_ref` (Workbench hosts Agent/Sequence/Workflow) is
  out of the program.** New capability wearing consolidation's coat, against
  the simplicity mandate; filed against Backlog Candidate AA. (SOL-COUNSEL.md
  #5.)
- 2026-08-09 — **DecisionReceipt rename is the word only, now.** Model
  convergence (Decision links to immutable receipts for create/accept/change/
  supersede) deferred to Phase 133 with an owner beat. (SOL-COUNSEL.md #3.)
- 2026-08-09 — **HS-130-03 changed what `this_machine` readiness checks
  (intended).** Readiness now checks the LOCAL meeting-intel model
  (`meeting.intel_realtime_model`) that agent execution actually loads, not the
  dictation/transcription runtime it read before — the whole point is
  readiness == execution == receipt. Owner-facing consequence: on a machine
  with the dictation model but not the 9B meeting default (or vice versa),
  `this_machine` readiness flips to track the model a run would truly load.
  One deployment identity (`DeploymentIdentity`) is now the single snapshot;
  Phase 131 freezes it into an admission-captured revision.
- 2026-08-09 — **HS-130-02 secret-slot scheme changed the credential env-var
  names (operational impact, flagged to owner).** Slots are now injective:
  `HOLDSPEAK_PROFILE_<SLUG>_<sha256-16>_KEY` (the old lossy slug was the
  vulnerability — `foo-bar`/`foo_bar` shared one slot, exfiltratable through
  the shape-only sync merge of client-supplied ids). No backward-compat env
  fallback (a fallback reopens the collision; per the not-really-released
  rule). Keys exported under the old names must be re-exported — `doctor`
  prints the correct `export …` line. Two tests that hardcoded the old scheme
  were fixed by the orchestrator to derive the name from the production
  `profile_key_env` (doctor cloud-preflight ×3). Sync-push principal auth
  stays HS-131.
- 2026-08-09 — **HS-130-08 renamed to `DecisionRecord`, not `Decision`.** A
  bare `Decision*` rename would have collided with the existing
  `DecisionLifecycleService` / `/api/decisions` (meeting-decision lifecycle).
  The mutable governing document is now `DecisionRecordService` /
  `decision_record*` / `/api/decision-records`; "Receipt" is freed for
  immutable kernel evidence, which was the point. Behavior-preserving; schema
  v42→v43 (one idempotent migration). Owner may rename further at the sitting.
- 2026-08-09 — **HS-130-10 triage RESULT (Candidate Z reconciled).** The full
  isolated-HOME suite on phase-130 HEAD is byte-identical to the pre-phase
  baseline — **102 test failures/errors, zero repaired-by-130, zero
  newly-caused** (every story shipped at zero net regression). Split: **7
  route to Phase 131** (the sync-registry/kind-drift/changeset-envelope
  contract — test_web_routes_sync ×2, test_primitive_contract kind-drift ×3,
  test_primitive_framework_sync, companion-slack qualified-kind); **95
  re-ledgered** as still-inherited Phase 118–128 integration debt across 36
  files (workbench-walk e2e 14, web_server 13, intel_streaming 9, companion
  slack/github/webhook, dictation surfaces, history, live-bus, cadence,
  decision-records, the ConflictError NameError at meetings/crud.py:161, and
  the known mesh_dispatch flake). The 95 need a dedicated remediation phase —
  owner rules its scope at the sitting; this is Candidate Z minus the 131
  slice. Ledger + reproducible classifier: assets/hs-130-10/.
- 2026-08-09 — **The inherited-96 ledger comes to 130 for triage** (per the
  Phase 129 handoff) but its **sync-contract slice routes to Phase 131**,
  where the sync registry and deployment revisions live — the two cannot be
  fixed apart. HS-130-10 assigns each failure exactly one home. (Reconciles
  the 129 handoff with SOL-COUNSEL.md #3; Candidate Z, BACKLOG.md:242-258.)

- 2026-08-09 — **Web-suite teardown flake documented (not a regression).**
  vitest SIGABRTs ("Abort trap: 6") on jsdom/pixi WebGL teardown, which
  intermittently bleeds a DOM-query failure into a sibling test under shared
  workers (observed: `IntelligenceWalk.test.tsx` "renders Receipts with a
  search input" — passes 7/7 in isolation, failed once under full-suite
  concurrency). Story evidence is captured via vitest's JSON report (written
  before teardown) asserted by a pure-node command, so exit codes reflect
  test results, not the teardown signal. HS-130-11's walk must run web checks
  with this in mind (isolate or JSON-report).

- 2026-08-09 — **Sol CLOSE counsel: ratify with named reservations (one
  blocking, resolved).** Sol's acceptance pass on the finished phase caught:
  (a) [BLOCKING] a stale `docs/api-surface.json` — the DecisionRecord rename
  added `/api/decision-records` routes without regenerating the manifest;
  regenerated (436 routes), `test_api_surface` green, reclassified
  repaired-by-130; (b) a tautological walk assertion (`_badge_host` returned
  `{}`), deleted and made real against `endpoint_egress`; (c) the exhibit's
  '02 ships first' overstatement (it landed 4th) — corrected. All 7 charter
  reservations confirmed honored; the .43 leg confirmed genuine; the
  DecisionRecord migration confirmed row-preserving. Full counsel in
  SOL-COUNSEL-CLOSE.md. Two minds on the close, per ORCHESTRATION §6.

- 2026-08-09 — **HS-130-11 walk: live-.43 PROVEN, screenshot-walk DEFERRED.**
  The harness `scripts/walk_one_truth.py` asserts 19/19 with the live `.43`
  LAN endpoint (Qwen3.6-35B): private_network end-to-end across badge,
  DeploymentIdentity, and receipt (control: api.openai.com → cloud). The
  Playwright screenshot-walk (1440+393) is deferred to the owner's sitting —
  this job has no browser/built bundle — with the one-command harness handed
  over. Amended visibly per the walk; owner may overrule at the sitting.

## Decisions deferred (Phase 131 preconditions — owner rules at or before the 131 charter)

- **AC3 rewrite (Article XI cl.1-2).** The issue's criterion "one kernel
  operation and one terminal receipt" per Sequence/Workflow contradicts
  Art. XI cl.1 (*"nesting inside an admitted operation exempts nothing"*).
  The adopted rewrite: *one admitted operation per model invocation; nested
  invocations are admitted as children of the run that offered them; each ends
  in its own terminal receipt.* Recorded now, applied in 131. (SOL-COUNSEL.md
  #1.)
- **Dictation and meeting kernel admission** — the highest-volume model paths
  (per-utterance, streaming); Phase 107 priced admission at ~25ms/op.
  **RULED by the owner 2026-08-09: "per sesh" — admit once per SESSION, not
  per utterance.** This resolves SOL-COUNSEL.md #2, keeps the program at four
  phases, and is the admission contract Phase 131 builds the streaming paths
  against (a session opens one admitted operation; per-utterance runs are
  children/continuations of it, not fresh admissions). Overrulable at the
  sitting, but this is the standing ruling.
- **Sequence and Workflow admission** — chains.py:113 and workflows.py:137
  begin lifecycles with no principal and non-`persona:` refs; four of five run
  families bypass admission today. Belongs to 131 with the Ask-definition
  design beat. (SOL-COUNSEL.md #7.)
