# Orchestration — the Muad'Dib method

How multi-agent phases run in this repository. The orchestrator is
Muad'Dib; the implementation agents are the Fedaykin (Terras); the spice
is the pipeline. Written after Phase 129 (One Grammar: two bug
screenshots → four audits → eleven stories → thirteen Terras → merged,
in one day), which is used throughout as the worked example.

## The stance

The orchestrator **decides, briefs, and verifies — it does not write
product code** during phase execution. Its hands touch: roadmap files
(authored directly, never delegated), memory, verification harnesses,
and surgical corrections when a defect sits exactly at a seam it has
already diagnosed (Phase 129's collector `stale`/`incompatible` fix).
Everything else is a brief handed to a Terra.

Three duties the orchestrator can never delegate:

1. **The done call.** A Terra's "done" is a claim; the orchestrator
   verifies on glass (screenshots against the live product) and by
   running the FULL suites — Terras run only focused tests.
2. **Scope honesty.** When reality breaks a chartered criterion, the
   orchestrator amends it VISIBLY (story file + phase decision log +
   "owner may overrule at the sitting") — never waives it silently.
3. **The ledger.** Debt discovered mid-phase is counted, triaged
   against the pre-phase baseline, logged into evidence, and assigned
   a home. Silence about a red suite is the one unforgivable sin.

## Phase shape: audit → charter → waves → walk

### 1. Audit before charter

A vague mandate ("make it a proper product") never goes straight to
stories. Fan out **parallel read-only audit agents, one per plane**,
each with a tight mission and a required report format:

- structural census (code-level, exhaustive tables, file:line for
  every claim);
- live behavioral walk (the real running app, screenshots, measured
  defects — never code-reading alone);
- grammar/consistency audit against the Constitution;
- architecture audit ending in a consolidation map and a
  no-breakage migration order.

Audits change nothing. Their reports are the charter's evidence base,
and the live walk's shots become the phase's before-pictures.

### 2. Charter from evidence

The orchestrator authors the phase directly (status doc + stories),
each story citing the audit findings down to file:line, each carrying
acceptance criteria, an explicit out-scope, and a test plan. Deletion
before invention: when audits show a correct pattern already exists
(ZoneWindow's sibling foot; `SurfaceFooter`), the charter canonizes it
and kills the impostors rather than inventing a new system. The
charter commits through the gate like any other work.

### 2b. The design beat (learned from HS-131-02, the fourteen-round runner)

A concurrency-critical or invariant-carrying foundation — a runner, a
lifecycle, a state machine other stories will ride — gets a **design
review before implementation**, not just a charter review. The
orchestrator (or a Terra) writes a one-page spec: the states, the
transitions, the invariants ("durable-before-observable", "single
terminal winner", "no dispatch after durable cancellation"), and the
sanctioned exceptions. Sol rules on the spec. Terras implement against
the ruled design. HS-131-02 skipped this and paid fourteen counsel
rounds discovering the design one adversarial probe at a time; the
same defects against a pre-ruled spec would have been implementation
bugs caught in one or two rounds.

Two escalation valves, both learned the hard way:

- **Three rounds on one story → stop patching, review the design.**
  When a counsel loop reveals a defect *class* (races, authority,
  ordering) rather than isolated defects, the next brief mandates the
  structural fix and the full test matrix for the class — not the
  instance Sol happened to probe.
- **Five rounds → surface the cost to the owner.** Name the remaining
  bar ("survives the nastiest adversarial probe" vs "survives
  realistic failure modes") and let the owner rule where it sits. The
  orchestrator does not silently spend a day of rounds on a bar the
  owner never chose.

### 3. Implementation waves

Terras implement in **parallel waves with serialized shipping**:

- **The brief is the craft.** Each Terra gets: the story file, the
  settled design (decided at charter — Terras implement, they do not
  redesign), exact file paths and line anchors, the drift warning
  ("verify anchors — N commits landed since the audit"), the list of
  files OTHER Terras own right now (do-not-touch), the focused-tests-
  only rule, and the hold-for-SHIP protocol.
- **One commit lane.** All Terras share one working tree and branch.
  They implement freely in parallel but ship one at a time, on an
  explicit SHIP message from the orchestrator. Staging is by explicit
  path only — `git add -A` is forbidden, always.
- **Shared-tree etiquette.** A teammate's mid-edit file may break your
  typecheck — retry once after 60s before reporting; never "fix"
  another story's file. A single-file overlap that rides into the
  earlier commit is documented in the later commit's body, not
  panicked over.
- **Honest reporting is rewarded.** A Terra that reports "this item
  was already fixed by the keystone — no edit needed", "this move is
  more than placement — backlogging it", or "the walk could not
  exercise X" has done its job better than one that forces a change.
- **Claims carry proof.** A report that names delivered tests pastes
  `pytest --collect-only` output showing them; a report that names a
  green suite pastes the run tail. Long-context agents drift into
  report inflation — HS-131-02 caught the same agent twice claiming
  tests that did not exist. When an agent's tool-use count balloons
  across rounds, retire it and brief a fresh one; the settled design
  travels in the brief, not in the tired context.

### 4. Verification between landings

After each keystone lands, the orchestrator: rebuilds, walks the real
product with measured assertions (bounding boxes, scroll ownership,
console errors), and runs the full suites the Terras were forbidden
to run. New failures are triaged **against the pre-phase baseline**
(same tests, pre-phase commit, same environment — a worktree with a
properly pinned toolchain): reproduce-on-main = inherited debt for
the ledger; new = the phase's to fix before anything flips.

### 5. The walk

The exit story re-runs the audit methodology against the finished
product: every surface, every state, both widths, automated
assertions, before/after pairs against the audit shots, the full
check chain captured through `dw evidence capture`, and a reusable
harness checked into `scripts/`. The walk story cannot be closed by
unit tests alone and cannot be waived.

### 6. The Sol counsel

Before the close is called, the orchestrator **takes the phase to Sol
and asks for Sol's opinion — always**. Sol is the sounding board and
acceptance partner, a different mind with standing in this repo's
history: the Phase 106 council pass where Sol returned *"do not ratify
yet"* with file-level evidence — and was right — is the precedent this
section canonizes.

- **What Sol reviews:** the final summary, the evidence pack, every
  judgment call the orchestrator made alone (amendments, ledgers,
  deferred items), and the merge verdict. Sol is briefed with pointers
  to the actual artifacts, never a summary of a summary.
- **What Sol is asked:** not "approve this" but *"what did I miss, what
  would you not ratify, and why — with evidence."* Sol's dissent is a
  finding, not an obstacle; a Sol concern gets the same treatment as a
  failing test: reproduce, classify, fix or ledger.
- **What Sol's verdict is:** counsel, recorded alongside the evidence
  for the owner's sitting. The orchestrator may proceed over a Sol
  concern only by naming it and the reason — never by omitting it. The
  owner sees both opinions, always.
- Sol is also the mid-phase sounding board for judgment-heavy calls —
  a chartered criterion about to be amended, a scope question, a
  deletion that feels too easy. When the orchestrator is about to
  decide something alone that the owner will only see later, that is
  the moment to ask Sol first.

### 7. The close

Push, PR, then **watch → read → merge as separate acts**: watch CI to
conclusion, READ the failures, diff the failure NAMES against main's
own CI at the fork point. Merge on zero regressions, with the verdict
posted as a PR comment. A red baseline inherited from main is named
and ledgered — matching it silently is not an option; matching it
loudly, with the diff attached, is the house practice made honest.

## The machinery

- **The gate.** Every commit — charter, story, amendment, docs —
  carries a certified DW contract (`.githooks/dw contract new`, boxes
  flipped honestly, evidence paired with done-flips). Mid-story
  commits ship without the evidence file (the gate pairs evidence
  with FLIPS); the flip commit carries it.
- **Serialized SHIP.** The orchestrator is the commit-lane semaphore.
  A Terra holding for SHIP does not stage, capture evidence, flip, or
  contract.
- **Background discipline.** Long runs (suites, CI) go under monitors
  with failure-covering filters; the orchestrator keeps working and
  is woken by events, never polls.
- **Quiet-tree rule.** Full-suite runs count only when no Terra is
  editing the tree; a suite that overlapped an implementation round is
  killed and re-run, never interpreted. (HS-131-02 discarded six
  mixed-tree runs; every one would have lied.) Baselines run in a
  worktree pinned at the pre-phase commit with its own synced venv —
  `uv run` under an isolated HOME silently falls back to a bare system
  Python unless the worktree ran `uv sync --extra test` first.
- **Counsel agents read scoped.** A reviewer briefed onto a long
  ledger greps for the section heading and reads from there; whole-
  history reads overflow the reviewer's context mid-verdict.
- **The suite has a fast lane.** Focused files for story iteration;
  the full suite in parallel (`pytest -n auto` via pytest-xdist) for
  gates. A serial 25-minute suite between every landing taxes exactly
  the discipline this document demands, so the machinery keeps it
  cheap instead of the orchestrator skipping it.
- **Memory.** Session state, gotchas, and standing rules land in the
  orchestrator's memory as they are learned, so the next session's
  Muad'Dib starts where this one stood.

## What the owner gets

Status reports that lead with the outcome; a scoreboard, not a log;
judgment calls surfaced as decisions with the evidence attached and
the overrule explicitly offered; Sol's acceptance opinion recorded
next to the orchestrator's — two minds on every close, disagreements
included; and a sitting exhibit at the end — the before-pictures they
sent, next to the afters.

*The Terras are the Fedaykin. The spice is the pipeline. It must
flow — through the gate, every time.*
