# Phase 117 — The Foundation

**Status:** done (16/16).

**Last updated:** 2026-08-05.

## The vision

DeskOS has shipped 116 phases and ~530 stories. The product works.
But the internal architecture — born from a sprint that never stopped —
has accumulated gravity wells that slow every subsequent phase. This
phase does not add features. It refactors the six load-bearing
subsystems so that every future phase lands faster, safer, and with
fewer regressions.

The Foundation is the phase where DeskOS gets serious about its own
bones. Twelve stories, six domains, zero new user-facing capabilities.
Every story is independently shippable and verified by existing tests
plus new characterization tests. The desk looks identical before and
after; the codebase does not.

**Domains:**

1. Store architecture (Zustand slice split)
2. CSS modularization (desk.css → co-located modules)
3. Wire layer typing (discriminated union entities)
4. Window manager extraction (DeskWindow.tsx decomposition)
5. Core component unification (shared patterns + decomposition)
6. Python backend stabilization (schema, repos, errors, config)
7. App framework (detail contract, exhaustiveness gate, pullout
   protocol, surface declaration)

**Constitutional grounding:** Article VIII (native-grade craft requires
a codebase that can evolve at native-grade speed), Article VI (honest
construction — the architecture must be as honest as the UI), Article
IX (proof over claim — every story has a screenshot walk or test suite
gate).

## Story status

| # | Story | Status | Depends on |
|---|-------|--------|------------|
| 01 | The typed primitives | done | — |
| 02 | The store split | done | — |
| 03 | The CSS foundation | done | — |
| 04 | The window subsystem | done | — |
| 05 | The typed cores | done | 01 |
| 06 | The component narrowing | done | 01 |
| 07 | The core unification | done | 05 |
| 08 | The dictation decomposition | done | 07 |
| 09 | The history decomposition | done | 07 |
| 10 | The schema extraction | done | — |
| 11 | The backend errors | done | — |
| 12 | The backend cleanup | done | 10, 11 |
| 13 | The detail contract | done | 01, 15 |
| 14 | The kind exhaustiveness gate | done | 01 |
| 15 | The pullout protocol | done | 01, 14 |
| 16 | The surface declaration | done | 01 |

## Where we are

Six stories shipped (01, 02, 13, 14, 15, 16) — the app-framework
pipeline is complete. The typed primitives, store split, exhaustiveness
gate, pullout protocol, surface declaration, and detail contract are
all implemented and Terra-verified. Test suite: 89 files, 604 tests,
all passing. TypeScript clean.

Adding a new primitive kind is now compile-guided: add the interface,
the compiler tells you everywhere else. The openPullout god-method is
replaced by declaration-driven dispatch. Pullout.tsx went from 983 to
94 lines. The store monolith is 4 focused slices.

Remaining: 10 cleanup stories (03-12) covering CSS modularization,
window decomposition, component unification, and backend stabilization.
Stories 03-12 need recipe files before implementation.

## Execution strategy

Stories 01-04 are independent and can run in parallel. Story 05
depends on 01 (typed primitives must land before cores can consume
them). Stories 08-09 depend on 07. Stories 10-11 are independent
Python-side work. Story 12 depends on 10 and 11.

Stories 14 and 16 are cheap type-level unlocks that should land
early — right after 01. Story 14 (exhaustiveness gate) makes every
subsequent refactor compiler-verified. Story 16 (surface declaration)
is one field on an existing map. Story 15 (pullout protocol) is the
big mechanical move and depends on 14. Story 13 (detail contract)
rewires window internals that 15 restructures, so it lands last of
the app-framework stories.

The recommended critical paths are:

```
Frontend cleanup pipeline:
  01 → 05 → 06 + 07 → 08 + 09

App framework pipeline (land 14 and 16 early):
  01 → 14 → 15 → 13
  01 → 16

Independent frontend (parallel):
  02, 03, 04

Backend pipeline:
  10 + 11 → 12
```
