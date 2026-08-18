# Orchestration — the Muad'Dib method

How multi-agent phases run in this repository. The orchestrator is
Muad'Dib; the implementation agents are the Fedaykin — every one a
`claude-opus-4-6[1m]` session ("Opus workers" hereafter); the spice
is the pipeline. Written after Phase 129 (One Grammar: two bug
screenshots → four audits → eleven stories → thirteen workers → merged,
in one day), which is used throughout as the worked example. Revised
2026-08-17 after the reckoning: the day the owner ruled the engine
great and the product unusable, and the method learned to gate on
usability, seat a sober eye, ask the Tuesday question, and put the
owner's nod before every merge.

## The model rule (owner ruling, 2026-08-15)

**All research, audit, implementation, test-writing, verification, and
counsel work delegated to agents runs on `claude-opus-4-6[1m]`. Never
on the orchestrator's own model. No exceptions.** The orchestrator's
model decides, briefs, and makes the done call; `claude-opus-4-6[1m]`
does the delegated work. The repo's `.claude/agents/opus-worker.md`
definition pins this; any orchestration harness (Workflow, Agent) must
route through it or an equivalent explicit Opus override.

One carve-out exists and only the owner can invoke it: the owner may
explicitly order a specific task onto a different model (the 2026-08-17
sober-eye audit ran on a fresh Fable at the owner's word). The order is
per-task, never a precedent; the default rule resumes the moment the
task ends.

## The stance

The orchestrator **decides, briefs, and verifies — it does not write
product code** during phase execution. Its hands touch: roadmap files
(authored directly, never delegated), memory, verification harnesses,
and surgical corrections when a defect sits exactly at a seam it has
already diagnosed (Phase 129's collector `stale`/`incompatible` fix).
Everything else is a brief handed to an Opus worker.

Three duties the orchestrator can never delegate:

1. **The done call.** A worker's "done" is a claim; the orchestrator
   verifies on glass (screenshots against the live product) and by
   running the FULL suites — workers run only focused tests.
2. **Scope honesty.** When reality breaks a chartered criterion, the
   orchestrator amends it VISIBLY (story file + phase decision log +
   "owner may overrule at the sitting") — never waives it silently.
3. **The ledger.** Debt discovered mid-phase is counted, triaged
   against the pre-phase baseline, logged into evidence, and assigned
   a home. Silence about a red suite is the one unforgivable sin.

## The use loop and the bar (learned 2026-08-17, the reckoning)

For 139 phases this method verified correctness magnificently and
usability not at all — because correctness could FAIL a gate and
usability could not. The build loop outran the use loop: every day
ended with a merged PR; no gate ever asked whether the owner could do
the job. The sober-eye audit then measured the truth: zero of the five
owner jobs passed cold. Three standing corrections:

- **The usability bar is a gate, not a hope.** A scripted cold-run
  (fresh HOME, real hub, no lore) that can FAIL: first capture to
  visible transcript ≤3 min; every hero action visible feedback
  ≤500 ms; capture never silently lost; Ask answers or onboards; a
  created object findable on the home surface in ≤60 s. Every UI
  phase's walk story runs it. A failed bar is a failed suite.
- **The Tuesday question at every charter.** Before any worker rides,
  the orchestrator asks the owner: *"will you use this on a
  Tuesday?"* — and pushes back on a no instead of building it
  beautifully. The orchestrator that never says "don't build this"
  is part of the disease.
- **Success is a job passing cold, not a phase merging.** Status
  reports lead with jobs and mornings, not merge counts.

## The sober eye (institution, learned 2026-08-17)

Distinct from the counsel. The counsel has standing and history; the
sober eye's entire value is that it has NEITHER. On a cadence (every
few phases, and always before a "this is usable now" claim), a
fresh-context reviewer with zero project lore cold-starts the real
product and attempts the owner's jobs WITHOUT reading internal docs
first — then reads the promise (README, POSITIONING) last and scores
the gap. It reports: the minute-one narrative, a per-job scorecard,
the ranked pain list, the noun count at first contact. One such audit
found in an hour what phase counsels missed for months, because
counsels review law-compliance and the sober eye reviews
human-compliance. Its report is charter evidence, not commentary.

## Phase shape: audit → charter → waves → walk

### 1. Audit before charter

A vague mandate ("make it a proper product") never goes straight to
stories. Fan out **parallel read-only audit agents, one per plane**
(all `claude-opus-4-6[1m]`), each with a tight mission and a required
report format:

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
orchestrator (or a worker) writes a one-page spec: the states, the
transitions, the invariants ("durable-before-observable", "single
terminal winner", "no dispatch after durable cancellation"), and the
sanctioned exceptions. The Opus counsel rules on the spec. Workers
implement against the ruled design. HS-131-02 skipped this and paid
fourteen counsel rounds discovering the design one adversarial probe
at a time; the same defects against a pre-ruled spec would have been
implementation bugs caught in one or two rounds.

Two escalation valves, both learned the hard way:

- **Three rounds on one story → stop patching, review the design.**
  When a counsel loop reveals a defect *class* (races, authority,
  ordering) rather than isolated defects, the next brief mandates the
  structural fix and the full test matrix for the class — not the
  instance the counsel happened to probe.
- **Five rounds → surface the cost to the owner.** Name the remaining
  bar ("survives the nastiest adversarial probe" vs "survives
  realistic failure modes") and let the owner rule where it sits. The
  orchestrator does not silently spend a day of rounds on a bar the
  owner never chose.

### 3. Implementation waves

Opus workers implement in **parallel waves with serialized shipping**:

- **The brief is the craft.** Each worker gets: the story file, the
  settled design (decided at charter — workers implement, they do not
  redesign), exact file paths and line anchors, the drift warning
  ("verify anchors — N commits landed since the audit"), the list of
  files OTHER workers own right now (do-not-touch), the focused-tests-
  only rule, and the hold-for-SHIP protocol.
- **One commit lane.** All workers share one working tree and branch.
  They implement freely in parallel but ship one at a time, on an
  explicit SHIP message from the orchestrator. Staging is by explicit
  path only — `git add -A` is forbidden, always.
- **Shared-tree etiquette.** A teammate's mid-edit file may break your
  typecheck — retry once after 60s before reporting; never "fix"
  another story's file. A single-file overlap that rides into the
  earlier commit is documented in the later commit's body, not
  panicked over.
- **Honest reporting is rewarded.** A worker that reports "this item
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
console errors), and runs the full suites the workers were forbidden
to run. New failures are triaged **against the pre-phase baseline**
(same tests, pre-phase commit, same environment — a worktree with a
properly pinned toolchain): reproduce-on-main = inherited debt for
the ledger; new = the phase's to fix before anything flips.

When a deliberate behavior change (a default flip, a posture change)
produces fallout, the fix brief carries the **a/b/c classification
duty** with the doctrine stated: (a) the test asserts the OLD posture
→ update the test to the new law, keeping still-valid states tested
by pinning them explicitly; (b) a REAL regression the change exposed
→ fix the code and say so loudly; (c) unrelated flake → prove
serial-green twice and name it. The classification table is the
deliverable; papering a (b) with a test edit is the sin the table
exists to catch. (Phases 139's two fallout rounds: 43 failures, all
honestly classified, zero real regressions — because the frame was in
the brief.)

### 5. The walk

The exit story re-runs the audit methodology against the finished
product: every surface, every state, both widths, automated
assertions, before/after pairs against the audit shots, the full
check chain captured through `dw evidence capture`, and a reusable
harness checked into `scripts/`. The walk story cannot be closed by
unit tests alone and cannot be waived.

Walk discipline hardened by the 138/139 closes:

- **The owner sees shots before merge — standing law.** On every
  reworked room: before/after pairs, both widths, to the owner; a
  flinch is a redo, the nod is the merge trigger. And the **beauty
  pass follows the functional pass**: structural pressure (counts,
  folds, bars) produces correct rooms, not lovely ones; the owner's
  Workbench 2.0 directive ("show the inspo, never a POS") gets its
  own craft round before the shots go up.
- **Assertion honesty.** A walk check that ORs generic selectors
  passes on the wrong element (the 138 walk's `.egress-badge` matched
  the desk chrome, not the badge under test — caught only by counsel).
  AND-assert the SPECIFIC element; scope clicks and locators to the
  owning container (the same text can render on a surface BEHIND the
  window); two "different" shots that are byte-identical are a
  false-positive tell. Keep the false-positive → honest-fail →
  strict-pass capture chain in the evidence as provenance.
- **Walks never touch the owner's real machine state.** Isolated HOME
  for data — and for anything HOME does not isolate (the macOS login
  keychain resolves from $HOME: create a walk-scoped keychain inside
  the fake HOME), every subprocess env-scoped to the walk HOME, or
  the drill you are simulating lands on the owner's REAL credentials.
  Cleanup deletes what the walk created and prints it.

### 6. The counsel

Before the close is called, the orchestrator **takes the phase to the
Opus counsel — a fresh `claude-opus-4-6[1m]` session — and asks for
its opinion — always**. The counsel is the sounding board and
acceptance partner, a different mind with standing in this repo's
history: the Phase 106 council pass where the counsel (Sol, in that
era) returned *"do not ratify yet"* with file-level evidence — and was
right — is the precedent this section canonizes.

- **What the counsel reviews:** the final summary, the evidence pack,
  every judgment call the orchestrator made alone (amendments,
  ledgers, deferred items), and the merge verdict. The counsel is
  briefed with pointers to the actual artifacts, never a summary of a
  summary.
- **What the counsel is asked:** not "approve this" but *"what did I
  miss, what would you not ratify, and why — with evidence."* The
  counsel's dissent is a finding, not an obstacle; a counsel concern
  gets the same treatment as a failing test: reproduce, classify, fix
  or ledger.
- **What the counsel's verdict is:** counsel, recorded alongside the
  evidence for the owner's sitting. The orchestrator may proceed over
  a counsel concern only by naming it and the reason — never by
  omitting it. The owner sees both opinions, always.
- The counsel is also the mid-phase sounding board for judgment-heavy
  calls — a chartered criterion about to be amended, a scope question,
  a deletion that feels too easy. When the orchestrator is about to
  decide something alone that the owner will only see later, that is
  the moment to ask the counsel first.
- **Every counsel brief carries the human-compliance question**
  alongside the constitutional one: not only "does this obey the
  laws" but *"could the owner — tired, on a Tuesday — do the thing on
  this screen?"* A hundred counsel passes reviewed badges, prose
  rules, and material law while dead hero buttons and silent failures
  sailed through, because nobody asked. The sober eye audits it
  wholesale; the counsel asks it on every pass.

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
  A worker holding for SHIP does not stage, capture evidence, flip, or
  contract.
- **Background discipline.** Long runs (suites, CI) go under monitors
  with failure-covering filters; the orchestrator keeps working and
  is woken by events, never polls.
- **Quiet-tree rule.** Full-suite runs count only when no worker is
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
the overrule explicitly offered; the Opus counsel's acceptance opinion
recorded next to the orchestrator's — two minds on every close,
disagreements included; and a sitting exhibit at the end — the
before-pictures they sent, next to the afters.

*The Opus workers are the Fedaykin. The spice is the pipeline. It must
flow — through the gate, every time.*
