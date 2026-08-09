# Sol counsel — issue #450 consolidation program (2026-08-08)

Read: the issue in full, all three audits, Muad'Dib's position,
docs/internal/CONSTITUTION.md Art. I/II/V/VII/IX/XI,
docs/internal/ORCHESTRATION.md, BACKLOG.md:242-258. Nine claims
re-derived against the tree independently.

## 1. What the audits and the position missed

**A. Sequence and Workflow bypass the kernel too — two whole run
families the audits never checked.**
- holdspeak/web/routes/primitives/chains.py:113 — `RunLifecycle.begin(db, definition_ref=f"sequence:{chain_id}", body=body)` — no principal.
- holdspeak/web/routes/primitives/workflows.py:137 — same for workflow — no principal.
The kernel branch in services/support.py:88 is gated on `principal is
not None and definition_ref.startswith("persona:")`; both fail both
halves. Of the five run families the acceptance criteria enumerate,
FOUR bypass admission, not two. Wave-0 sizing built on "Ask +
Workbench" is short by two route files plus per-step target
resolution (chains.py:143-150).

**B. Acceptance criterion 3 contradicts Article XI.** "One kernel
operation and one terminal receipt" per Sequence/Workflow vs Art. XI
cl.1 ("Each effect is judged for itself; nesting inside an admitted
operation exempts nothing") and cl.2 (child admission). A five-step
Sequence is one parent plus five children, not one operation.

**C. Kernel routing buys receipt truth, not safety — as built.**
support.py:88-93 submits then immediately self-approves in the same
call; no policy evaluation between submit and approve. Also
`start_attempt` → `broker.claim` raises ValueError on mismatch — a
NEW synchronous failure mode on the interactive Ask path; per the
errors-in-flow rule it needs its own story and shot leg.

**D. Ask has no definition and no revision — the codec requires
both.** kernel/inference.py:75-85 refuses unless definition_ref
passes valid_ref and definition_revision matches. Ask is ad-hoc
(ask_service.py:59-101). Choices: fictional `ask:adhoc` revision (a
versioning lie) or relaxing the codec for everyone. Needs an explicit
design story with an owner beat, not an implementation discovery.

**E. Deployment-revision snapshot and the sync registry are the same
work.** `profiles` is a synced field-level LWW table
(sync_service.py:38-43, wall-clock last_modified, no vector clock).
A peer edit mints revisions with no ordering; no sync bucket for
revisions means receipts naming revision N are unresolvable on other
devices; adding a bucket touches SYNC_KINDS/_BUCKET_KIND, policed by
test_schemas_cover_exactly_sync_kinds — already in Candidate Z's 96.
The 130/131 cut between snapshot and registry is the wrong boundary.

**F. Secret-name collision is credential exfiltration, not
confusion.** profile_service.py:49 — client supplies the profile id;
sync push (sync_service.py:690-705) validates only id+kind. A peer
creates `foo_bar` while `foo-bar` holds a real key, points base_url
at its own endpoint, and providers.py:347/:423 hand it the genuine
key via HOLDSPEAK_PROFILE_FOO_BAR_KEY — exfiltration of a
device-local credential through the sync channel the schema comment
(schema.py:1031-1034) declares inviolate. Reclassify as a security
fix, cut FIRST.

**G. A fourth egress lie:** providers.py:249-267 — when cloud=True
and endpoint_host() is empty, the badge stamps DEFAULT_CLOUD_HOST — a
host the run never contacted.

**H. /api/settings last-writer-wins is a Wave 0 defect** (data loss:
two open tabs destroy each other; CommandsCore re-sends stale items
array), not a Wave 1 rider.

**I. Endangered "Keep these valid layers" items:** secret-slot ID
must be stated as a derived non-secret identifier refusing on
ambiguity; the one-writer guard must be written against callers of
PUT /api/settings (allowlist per subtree), not against controls; Get
Info's "Runs on" is the ONE property with a real update path
(infoContract.ts:20-21,75) — a one-setter deletion, but Info must
show effective value AND source, so it belongs in the inheritance
phase.

**J. The largest unbounded risk: dictation and meeting intelligence.**
The AC enumerates five run families and stops; Art. XI cl.1 says
invoking a model is consequential, full stop. Meeting intel and
dictation are per-utterance/streaming; Phase 107 priced admission at
~25ms — prohibitive per utterance. The charter must say which: (a)
admitted once per SESSION; (b) explicitly exempted with a ratified
reason; or (c) the Wave-3 guard is knowingly partial. NO phase should
be chartered before the owner rules on this — it decides whether the
program is three phases or five.

## 2. Would not ratify as framed (wrong, not expensive)

1. AC3 — rewrite: one admitted operation per model invocation; nested
   invocations admitted as children; each ends in its own terminal
   receipt.
2. AC "web shows one global model dial by default" — Phase 112
   already shipped it; a criterion that flips green without work.
   Replace: every placement control states its scope, and when unset
   names the source it inherits from.
3. Wave 3's dated pre-1.0 alias boundary — a promise to run a fourth
   cleanup later, the mechanism that produced this issue. Each alias
   dies in the phase that establishes its canonical name.
4. The snapshot/sync-registry phase cut (§1E).
5. capability_ref — new capability wearing consolidation's coat. Out;
   backlog against Candidate AA.
6. "Merge Morning Push and Monday Brief" as an ENGINE merge —
   cadence/brief.py is pure/in-memory/single-source on the nudge
   path; monday_brief is four-source/persisted/idempotent. Merge the
   SURFACES; keep Cadence the scheduler.

## 3. Rulings on the open questions

- **Wave 0 is two phases — split kernel-free truth from kernel
  truth**, not deep from shallow. Phase A "one placement, one truth":
  readiness/execution/receipt unified, one meeting placement policy,
  ONE egress vocabulary absorbing all four derivations, secret slots
  first as security fix, no model-name retargeting, versioned
  /api/settings writes, double-create, dead voice intents — none of
  it needs the kernel. Phase B "one admission path": deployment
  revisions WITH their sync decision and registry, the Ask
  definition/revision design beat, all five families through
  admission, the dictation/meeting ruling recorded. Then inheritance,
  then vocabulary. Four phases, admitted honestly.
- **capability_ref: out.**
- **DecisionReceipt: rename NOW — the word only.** Blast radius
  measured: 12 backend files, 1 web file, 4 tables, 4 sync kinds.
  Cheap in code, expensive in habit if delayed. Defer the model
  convergence (Decision links to immutable receipts) to the
  vocabulary phase with an owner beat.
- **Unratifiable:** the six §2 items plus the missing
  dictation/meeting ruling (precondition to chartering anything).

## 4. Simplicity

Five of the six layers already exist under worse names (Destination =
InferenceTarget, Deployment = profiles row, Admission snapshot =
InferenceAdmission kernel/inference.py:40-48, Receipt = kernel
journal, Projection = badges/doctor). Assignment (inheritance) is the
one genuinely new concept — and the one the owner asked for. The real
trap is Wave 3's machinery (generated types, re-exports, custom
guards); cut generated-types and re-export items until something
regresses. **The one cut to maximize simplicity per unit of churn:
ship the precedence rule FIRST, alone** — one resolver returning
{effective_target_id, source}, null = inherit everywhere (never
silently this_machine), four scoped labels. It answers four of the
owner's five questions and is the only part the owner will
EXPERIENCE as simpler.

## Verdict

**Ratify as amended**, with seven named reservations: (1) AC3
rewritten to Article XI cl.1-2 before any story is cut; (2) owner
rules dictation/meeting inside or outside "every model invocation"
before chartering; (3) deployment revisions and sync registry land in
the same phase; (4) secret-slot collision reclassified as credential
exfiltration and cut first; (5) capability_ref and the dated alias
boundary out of scope; (6) the one-global-dial criterion replaced
(Phase 112 already satisfies it); (7) Sequence/Workflow admission
gaps and Ask's missing definition/revision get a design beat, not an
implementation discovery. Fix those seven and Sol signs the charter.
