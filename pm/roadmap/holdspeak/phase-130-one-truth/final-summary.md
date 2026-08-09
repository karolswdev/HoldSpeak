# Phase 130 — One Truth — final summary (sitting exhibit)

**DONE 11/11, one day (2026-08-09).** Branch `phase-130`. The kernel-free half
of issue #450: *make execution and receipts true.*

## What the owner asked

> "Consolidate execution ownership and simplify the Python + web product… I
> need this system to be simple, predictable, and easy to build and integrate
> against, yet retain nearly all of its robustness."

HoldSpeak could check one model, execute another, and report a third; a LAN box
could be badged "cloud" while a mesh route was badged "Local only"; nine places
answered "where does this run?" and disagreed.

## What shipped (11 stories, each gated, verified against baseline)

| Story | What it made true |
|---|---|
| **01 precedence resolver** (keystone) | one placement authority — `{effective_target_id, source}`, unset = inherit, never accidental "this device"; the Agent default the Workbench used to ignore is honored |
| **02 secret slots** (security; chartered to lead the lane, landed 4th) | the credential-**exfiltration** path is closed — injective `slug+sha256` slots; `foo-bar`/`foo_bar` no longer share a key |
| **03 deployment identity** | readiness, execution, and the receipt name ONE `DeploymentIdentity`; the "reports A, runs B" split is dead |
| **04 egress vocabulary** | four disagreeing egress derivations → one classifier; a LAN box is `private_network` everywhere; no "Local only" over mesh; no fabricated host |
| **05 meeting placement** | one policy, stated precedence — a selected destination takes effect (the silent no-op is fixed); `mir_profile`+`plugin_profile` → one `routing_profile` |
| **06 Ask truth** | id selects placement; a model may only name what the target advertises, else refuse — no silent retarget across egress boundaries |
| **07 settings one writer** | versioned `/api/settings` (stale PUT → 409); no macro-clobber; "Run elsewhere" is transient, not a standing write |
| **08 DecisionRecord** | "Receipt" means immutable kernel evidence again; the mutable governing doc is DecisionRecord (dodged the `Decision*` collision) |
| **09 Workbench** | one creation gesture → one record; the two dead voice intents wired |
| **10 inherited ledger** | the 102 inherited failures triaged: 7 → Phase 131, 94 re-ledgered, 1 repaired (api-surface drift Sol caught at close); 0 newly-caused |
| **11 the walk** | 19/19 live assertions incl. real `.43` — the truth proven, not inspected |

## The proof (HS-130-11, live)

`scripts/walk_one_truth.py` — a reusable harness — asserts **19/19** with the
live `.43` LAN endpoint (Qwen3.6-35B): it classifies **private_network
end-to-end** (badge == DeploymentIdentity == receipt, `owner=you`), while the
control `api.openai.com` classifies `cloud`. Placement provenance, injective
secret slots, deployment-identity coherence, and settings versioning all pass
live. Full output: `assets/hs-130-11/walk-output.txt`.

## Method and honesty

- Terras implemented in isolated worktrees (Wave A) then on the shared tree
  (the serial inference stack); the orchestrator integrated, ran the FULL
  suites between landings, and gate-committed each story.
- **Every feature story shipped at zero net regression.** The full
  isolated-HOME backend suite stayed byte-identical to the pre-phase baseline
  (105 fail/error) across all nine feature stories. Sol's close counsel then
  caught one 130-caused drift the ledger had mis-homed — a stale API-surface
  manifest from the DecisionRecord rename — now regenerated and reclassified
  repaired-by-130 (HS-130-10).
- Reading the actual test output (not summaries) caught what summaries hid: a
  schema-version cascade from the owner's real DB, a teardown-flake, and a test
  encoding the exact contract 06 removed — each handled, not waved off.

## Amendments (owner may overrule at the sitting)

1. **Screenshot-walk deferred** — this job has no browser/built bundle; the
   backend/CLI truth is proven live, the harness is handed over for the
   sitting's UI shots.
2. **Two Phase-131 preconditions recorded** (see the decision log): AC3
   rewritten to Article XI cl.1-2; the owner's **"per session"** ruling on
   dictation/meeting admission.

## Two operational findings for the owner

1. **Your hub DB is at schema v43; pre-phase `main` was v42** — a v42 build
   refused to open it. HS-130-08 brings committed code to v43, so this branch
   restores your hub's ability to read its own database.
2. **HS-130-02 changed the credential env-var names** (the collision *was* the
   vulnerability). Keys exported under the old names need re-exporting; `doctor`
   prints the correct line. No compat fallback by design.

## Sol counsel

Recorded in `SOL-COUNSEL-CLOSE.md` (the acceptance-partner pass on the finished
phase), alongside this summary, for the owner's sitting.
