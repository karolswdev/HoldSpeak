# Phase 107 - Close the Side Doors

**Status:** IN PROGRESS (1/7). Activated 2026-07-29 — Phase 106
closed on the owner's sitting (8/8). Chartered from the number
Phase 106 could not move.

**Last updated:** 2026-07-29 (HS-107-01 done: the commit-boundary
contract, pinned; baseline latency on real metal).

## Why this phase exists

Phase 106 built the kernel and proved it real: four caller calls, a
hash-chained journal, six registered operation types, and a spine that
stayed **byte-unchanged** while four heterogeneous drivers plugged into
it. The kill criterion passed.

And the census delta was **zero**. It started at 4 covered of 40 and
ended at 4 covered of 40.

That is not a failure of Phase 106 — building the desk and closing the
doors are different jobs, and the ladder said so. But it means the
central promise is still mostly unkept. Article XI clause 2 says every
consequential operation HoldSpeak performs, brokers, or authorizes is
admitted once and ends in a terminal receipt. Today **36 of 40
effect-capable call sites bypass that entirely**, held as declared debt
by the transitional clause 6.

This phase is what makes clause 2 begin to be true.

## The honest ceiling — read this before scoping anything

**The register cannot reach empty in this phase, and this charter does
not pretend otherwise.**

The 36 debt sites split by what can actually close them:

| family | sites | closable by migration? |
|---|---|---|
| tmux transport | 2 | **yes** — route through `process.input` |
| TextTyper callers | 8 | **yes** — route through a typing operation |
| subprocess | 5 | **yes** — route through an operation per call site |
| egress | 11 | **partly — see below** |
| raw desktop | 10 | **no** — see below |

**The egress count is already known to be wrong**, before the phase
starts. Writing HS-107-04 against the actual site list showed that
N10-N12 (`plugins/dictation/runtime_openai_compatible.py`) are
dictation **transcription**, which RFC §12 keeps on the low-latency
path permanently and Article XI clause 5 exempts as computation.
N05-N09 are model invocations, which clause 1 names separately from
egress. So HS-107-04 triages before it migrates, and the honest target
for this family is "each site migrated OR re-classified with a written
reason" rather than a count. The 4 → 30 figure below is therefore an
upper bound, and HS-107-05 re-derives the real one from the file.

All 10 raw-desktop sites live in `holdspeak/typer.py`. They are the
**primitives themselves** — the actual keyboard, Accessibility,
clipboard and AppleScript calls. Routing their *callers* through the
kernel does not cover them: any in-process Python can still call them
directly. They close only when raw effect primitives move into a
privileged executor process holding warrants instead of imports —
**RFC §5b confinement**, which is its own phase.

So the honest target is **4 → 30 of 40**, with 10 explicitly deferred
to confinement and clause 6 remaining in force. A phase that promised
an empty register would be lying at charter time.

## Constitutional grounding

- **Article XI clause 2** — this phase is its first real enforcement
  pass. Every site migrated is a site that can no longer act without a
  receipt.
- **Article XI clause 6** — the transitional provision. Every migrated
  site is **removed from the register** in the same commit, so the debt
  visibly shrinks. The clause survives this phase; it does not
  self-repeal until confinement lands.
- **Article V** — nothing becomes implicit. Migration must not turn a
  visible consent step into a silent one, and must not add ceremony to
  the owner's direct gestures (clause 4: the owner's own gesture is
  approval).
- **Article IX** — every family closes with proof on real metal, not a
  green unit suite.

## Goal

Twenty-six declared-debt effect sites stop being side doors. Each one
routes through admission, derives its authority rather than asserting
it, and leaves a terminal receipt — including on refusal, failure, and
the outcome that cannot be determined. The register shrinks by 26
entries, in public, one family at a time.

## Scope

- **In:** the four migratable families; dictation's commit-boundary
  semantics settled first; the register shrinking as work lands; docs;
  closeout.
- **Out:** RFC §5b confinement and the 10 raw-desktop primitives (the
  phase after this one); any change to the kernel spine — if a family
  needs one, that is a finding and the story stops; new capability of
  any kind; the second userland program (project memory /
  decisions-to-artifacts), still parked.

## The sequencing rule that is not negotiable

**Dictation is migrated once, with settled semantics, or not at all.**

`holdspeak/runtime/dictation_capture.py` appears in **both** the tmux
family and the TextTyper family — it is the crux of the census, and it
is the path the owner uses most. RFC §7 rung 5 is explicit: define
dictation's commit-boundary semantics FIRST, then reroute. HS-107-01
exists solely to settle those semantics and reroutes nothing. Any story
that touches dictation before 01 lands is out of order.

The trap to avoid: routing dictation through the kernel in a way that
puts a hold, a confirmation, or measurable latency on the hold-key
gesture. Article XI clause 4 was written specifically to prevent that —
the owner's direct gesture IS approval. A migration that makes
dictation slower or chattier has failed regardless of how many sites it
closes.

## Exit criteria (evidence required)

- [ ] HS-107-01 lands dictation's commit-boundary semantics as a
      written, tested contract — with zero rerouting.
- [ ] The register shrinks from 36 debt entries to 10, each removal a
      deliberate reviewed edit in the same commit as its migration.
- [ ] `holdspeak/kernel/effect_ledger.json` and the fence test agree at
      every step; the fence never goes green by being loosened.
- [ ] The kernel spine is byte-unchanged across the whole phase:
      `git diff --exit-code` over `broker/admission/journal/model/executor`
      exits 0 at close.
- [ ] Density guards green; zero driver-specific conditionals.
- [ ] Dictation latency measured before and after, on real metal, with
      the numbers printed. No regression on the hold-key path.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green
      (pre-existing unrelated failures documented per-story).
- [ ] HS-107-06 docs: the register's new number at the entry points,
      and the security narrowing updated to match reality.
- [ ] HS-107-07 closeout: the owner's sitting and verdict (Article
      IX.4), and the census delta printed as a number.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-107-01 | Dictation's commit boundary — semantics before rerouting | done | [story-01-dictation-semantics](./story-01-dictation-semantics.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-107-02 | The typing families — 10 sites through the kernel | planned | [story-02-typing-families](./story-02-typing-families.md) | — |
| HS-107-03 | The subprocess family — 5 sites | planned | [story-03-subprocess-family](./story-03-subprocess-family.md) | — |
| HS-107-04 | The egress family — triage before migration | planned | [story-04-egress-family](./story-04-egress-family.md) | — |
| HS-107-05 | The register, honestly — what remains and why | planned | [story-05-register-honestly](./story-05-register-honestly.md) | — |
| HS-107-06 | Docs — the new number at the entry points | planned | [story-06-docs](./story-06-docs.md) | — |
| HS-107-07 | Closeout — the sitting and the census delta | planned | [story-07-closeout](./story-07-closeout.md) | — |

## Sequencing

01 first and alone — it settles semantics and reroutes nothing. Then
02 (which depends on it), and 03/04 which are independent of dictation
and of each other and may run in parallel. 05 after all migration
lands. Then docs, then closeout.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Dictation gets slower or chattier | **high** | 01 settles semantics before any reroute; latency measured before/after on real metal; Article XI clause 4 protects the direct gesture | The hold-key path gains a hold, a confirmation, or measurable latency |
| A family needs a spine change | medium | The spine survived four drivers byte-unchanged; a fifth needing changes is a finding, not a detail | Any diff in `broker/admission/journal/model/executor` |
| The fence goes green by being loosened | medium | Every register removal is a reviewed edit paired with its migration in the same commit | A register entry disappears without a migration beside it |
| Migration turns visible consent implicit | medium | Article V review per family; refusals stay named | A previously-visible approval step vanishes |
| "Covered" claimed for a site still reachable directly | **high** | Covered means routed AND the direct path removed or fenced; the census counts statements, not intentions | A site is marked covered while its raw call still compiles |

## Decisions made (this phase)

- 2026-07-28 - Chartered from Phase 106's census delta of ZERO (4/40 → 4/40) - the kernel was built and proven, and closed no doors; that was the ladder's design, and this is the phase that pays it off - orchestrator.
- 2026-07-28 - Honest ceiling set at 4 → 30 of 40, NOT an empty register - all 10 raw-desktop sites are the primitives in `typer.py` and close only under RFC §5b confinement; clause 6 therefore survives this phase - orchestrator, from the register's own family split.
- 2026-07-28 - The charter's own "11 migratable egress sites" was WRONG and is corrected before the phase starts - three of them are dictation transcription (exempt computation, RFC §12) and five are model invocations, which Article XI clause 1 names separately from egress; HS-107-04 triages before migrating and HS-107-05 re-derives the real count from the file - orchestrator, caught while authoring the story against the actual site list.
- 2026-07-28 - Dictation semantics settled in their own story before any rerouting (RFC §7 rung 5), because `dictation_capture.py` sits in BOTH the tmux and TextTyper families and is the owner's most-used path - orchestrator.
- 2026-07-29 - T03 (dictation → agent pane) is `process.input@1`, not a desktop typing operation: its destination is a controlled tmux-backed process and the Enter is terminal input - HS-107-01 contract, `docs/internal/DICTATION_COMMIT_BOUNDARY.md`.
- 2026-07-29 - No new authority-basis name for any dictation path: every covered effect derives `direct_gesture` (`operation_policy.py:238`). Two findings for HS-107-02: a voice macro reached WITHOUT an active owner hold/release has no honest basis today, and the process-input decision encoder (`delivery/commands.py:84-88`) cannot yet carry `direct_gesture` — driver adaptation, not a spine change - HS-107-01.

## Decisions deferred

- **RFC §5b confinement** — the privileged executor process, warrants
  over IPC, and the 10 raw-desktop primitives. The phase after this
  one; it is what finally lets clause 6 self-repeal and turns the
  security narrowing in `docs/SECURITY.md` from "cooperating code" into
  something stronger.
- **The second userland program** — project memory and
  decisions-to-artifacts, named in the owner's original charge and
  still parked.
- **The process window** — "what is running" as a `read` + `events`
  projection.

## Where we are

**2026-07-29 — ACTIVE, 1/7.** HS-107-01 done: dictation's commit
boundary is a written, pinned contract
(`docs/internal/DICTATION_COMMIT_BOUNDARY.md` — five paths + T03, each
with effect, commit point, authority basis cited to
`operation_policy.py` by line, receipt shape, and exemptions), with 8
boundary tests passing against UNMODIFIED dictation and the register
byte-identical (36 debt entries; spine diff exit 0). Baseline hold-key
latency measured on real metal and captured in evidence:
**median release-to-landed 926.3 ms** (transcribe 191.5, pipeline
576.6, type 155.8) via
`uv run python scripts/measure_dictation_latency.py --runs 3
--warmups 1 --typing-mode driver --pipeline active --backend mlx` —
HS-107-02 re-runs that exact command and must not regress it. Zero
sites rerouted, as chartered. Next: HS-107-02 (typing families),
then 03/04 in parallel. The number this phase exists to move:
**4 covered of 40**.
