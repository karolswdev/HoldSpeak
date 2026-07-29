# Phase 106 — The Kernel: final summary

**CLOSED 10/10, 2026-07-29.** The owner drove the eight beats and gave
his verdict: *"all passed, make progress."*

## The number, first

| | |
|---|---|
| Effect sites covered at phase start | **4 of 40** |
| Effect sites covered at close | **4 of 40** |
| **Census delta** | **0** |

This phase built the kernel and proved it real. **It closed no side
doors.** That was the ladder's design — building the desk and closing
the doors are different jobs — but it is the number, not the
machinery, that says how much of Article XI clause 2 is actually kept.
Phase 107 ("Close the Side Doors") is chartered to move it.

## The kill criterion

Quoted from RFC §12, and applied for real at HS-106-07:

> If the first three drivers — terminal input, actuator egress,
> inference runs — cannot share admission, principal, journal, and
> receipt code without driver-specific conditionals in the broker,
> **stop calling it a kernel.**

**Verdict: PASS.** Demonstrated, not asserted — an executable trace
observed all three operation types reaching the same functions:

| stage | shared function |
|---|---|
| admission + principal | `Broker.submit` → `Broker._admit_authority` |
| operation write | `JournalStore.create_operation` |
| journal events | `JournalStore.append` |
| receipt | `ExecutorPlane.receipt` → `_terminal` → `JournalStore.add_receipt` |

Then HS-106-08 went further than the criterion asked: a **fourth**
driver (`process.spawn`) plus a real product feature plugged in with
`git diff --exit-code` over `broker/admission/journal/model/executor`
returning **zero** — the spine's own code did not change by a single
character.

## The kernel ledger

**Registered operation types (6)** — the caller interface remains
exactly four calls (`read`, `submit`, `decide`, `events`) plus the
executor plane (`claim`, `receipt`, `reconcile`):

| type | driver |
|---|---|
| `tool.call@1` | the Phase-104 gate (adapted, not rebuilt) |
| `process.input@1` | terminal delivery — `HubCommandService` / `coder_steering` |
| `process.spawn@1` | worktree + agent launch — `factory_launch` |
| `actuator.egress@1` | `ActuatorExecutor` and the existing proposal machine |
| `inference.run@1` | `RunLifecycle`, recipes first |
| `inference.cancel@1` | cancellation as a submitted operation |

**Spine size:** 973 lines at HS-106-04, every module under its 300-line
budget, guards never relaxed. Where pressure appeared, `executor.py`
was split out rather than the budget raised.

**The debt register** (`holdspeak/kernel/effect_ledger.json`), which is
Article XI clause 6's own enumeration — **36 sites remain, and no agent
principal may reach any of them**:

| family | remaining | closes when |
|---|---|---|
| tmux transport | 2 | migration (Phase 107) |
| TextTyper callers | 8 | migration (Phase 107) |
| subprocess | 5 | triage, then migration |
| egress | 11 | triage — several are exempt computation, not debt |
| raw desktop | 10 | **RFC §5b confinement only** — these are the primitives in `typer.py` |

## Article XI, re-audited against the shipped tree

| clause | standing at close |
|---|---|
| 1 — the definition of consequence | **Materially satisfied.** The process-topology error the fourth council pass caught was removed before ratification. |
| 2 — admitted once, terminal receipt | **North star.** True for registered paths; 36 sites remain outside. Clause 6 enumerates exactly where. |
| 3 — caller never asserts authority | **Materially satisfied** for kernel-admitted work: authenticated principal, derived authority, immutable envelope, revocation and revision checks. |
| 4 — shared schemas, never shared rights | **Materially satisfied at the edge.** Typed owner/agent/node principals; an agent refused `decide` by name against a real agent process. |
| 5 — reads and computation exempt | **Materially satisfied.** Authenticated reads; token streams refused before the journal by a recursive `forbidden_content()` check. |
| 6 — the transitional register | **Material and executable**, and **still in force.** It does not self-repeal until the register is empty, which requires §5b. |

Clause 2 was **knowingly false at ratification** and said so in
HS-106-01's evidence. It remains the honest gap.

## What shipped

1. **HS-106-01** — Article XI ratified. The fourth council pass returned *do not ratify yet* and was sustained on three counts, including a process-topology definition error the first three passes missed. Clauses 1-5 landed as the council rewrote them; the drafted clause 6 was deleted; the owner overruled the recommendation to defer and ratified behind a migration provision. **The dissent is recorded in three places** — the archive, the RFC council record, and the Constitution's own amendment record.
2. **HS-106-02** — principal separation on loopback. The confused deputy closed: `decided_by` now derives from the authenticated principal instead of `body.get("actor") or "owner"`. Deny-by-default routing. Proven with a real `claude -p` process refused by name.
3. **HS-106-03** — the effect census pinned as an executable fence. A review pass caught it missing from-import evasions; fixed by resolving imported names across all five families.
4. **HS-106-04** — the broker and hash-chained journal. Four calls, executor plane, tamper-evident, cursor replay across a real SIGKILL.
5. **HS-106-05** — terminal input on the kernel. The gated deny reason still reaches the agent **verbatim**.
6. **HS-106-06** — actuator egress: the first genuinely heterogeneous driver. Survived a hub restart between approval and execution.
7. **HS-106-07** — inference, child operations, and the kill criterion. `_causality` closes the nested-effects loophole as generic spine machinery.
8. **HS-106-08** — PR follow-through, the tech-lead's loop, on real PR #387.
9. **HS-106-09** — docs. **Four claims narrowed** because the code did not support them, rather than prose outrunning the implementation.
10. **HS-106-10** — this closeout.

Plus two riders: the live-bus e2e harness (#390) and gated spawn (#397).

## Findings worth carrying forward

- **"Pre-existing relative to my story" and "not caused by this phase" are different claims.** HS-106-05's failure list contained three regressions from HS-106-02 that its own honest adjudication missed.
- **CI is blind to the live-bus tests** — they skip without Playwright and a built bundle, and the bundle is gitignored. Three sat red on `main` across three merges.
- **Style review does not catch invariant damage.** Three review agents read slice I's diff and reported on import caching while a two-line relaxation of the executor claim invariant went unmentioned.
- **The charter contradicted itself** — story-05 deferred `process.spawn` to rung 5 while story-08 required it. The implementing agent stopped with nothing built rather than reaching around the kernel.
- **Unresolved:** send latency measured **772.55 ms** during the machine sitting against **84.76 ms** at HS-106-05 and a 250 ms budget. The owner did not report it as slow on his walk. Worth a real measurement on an unloaded machine.

## Remainders

Filed as BACKLOG candidate: RFC §5b confinement and the ten raw-desktop
primitives; the second userland program (project memory,
decisions-to-artifacts); the process window; the generic liveness seam
(*pending forever is not indeterminate*); and the CI blind spot above.

Phase 107 is chartered and scaffolded, PLANNED, with an honest ceiling
of 4 → 30 stated at charter time rather than discovered at close.
