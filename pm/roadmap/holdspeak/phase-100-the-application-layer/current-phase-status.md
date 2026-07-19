# Phase 100 — The Application Layer

**Status:** IN PROGRESS (3/6, 2026-07-19) by the owner's direct
directive, verbatim in spirit: *"a phase that will cause a deep, deep,
deep grounding in the philosophy, seams, use cases — to then form an
opinion on the entire UI/UX with regards to its applicability to the
Desk OS — and then finally deliver something beautiful, not mangled,
easy to use: a proper application layer on our Desk OS to drive the
value of HoldSpeak."*

**Last updated:** 2026-07-19 (HS-100-03 done: the thesis + mocked applications at both form factors; the owner's gate is next).

## Why this phase exists — the honest post-mortem

Phases 95–99 and the materials spike each made the Desk OS more
consistent, more mechanical, more governed — and the owner's verdict
after every one was the same: still not it. The failure mode is now
undeniable: **pixels were iterated without a grounded thesis about
what the application layer is FOR.** Every sweep fixed what a
screenshot showed and shipped what a walk could assert, but nobody —
agent included — had written down what a person at this desk is
trying to DO, which surfaces serve that, which exist only because a
route once existed, and what "beautiful and easy" means for THIS
product's jobs. Chrome without a thesis is decoration.

This phase inverts the order. Nothing is built until the grounding
and the opinion exist and the owner has gated them.

## The arc

1. **Ground** (HS-100-01): read everything that defines this product —
   the Constitution, POSITIONING, the plan RFCs, the user guide, the
   UAT campaigns and debriefs (the closest thing to real usage
   transcripts), the phase history — and write THE GROUNDING: the
   jobs HoldSpeak is hired for, the moments where its value is felt,
   the seams the architecture actually offers, and the honest map of
   who sits at this desk and when.
2. **Judge** (HS-100-02): audit the ENTIRE current UI/UX against the
   grounding — not "is it styled" but "does it serve a job": every
   window, flow, and affordance judged keep / merge / re-shape /
   kill, with the mangled paths named end-to-end (not per-screenshot).
3. **Propose** (HS-100-03): THE THESIS — what the application layer
   of the Desk OS should be: the few real applications and their
   information architecture, the interaction model, the design
   language commitments (carrying forward what the materials spike
   proved), with real mockups of the core screens.
4. **The gate** (HS-100-04): the owner sits with the grounding, the
   audit, and the thesis + mockups. NOTHING builds before this
   verdict. The thesis is revised until the owner calls it.
5. **Deliver** (HS-100-05, shaped by the approved thesis): build the
   application layer the thesis describes — beautiful, not mangled,
   easy — with the mechanical guards that make regressions
   unshippable.
6. **Close** (HS-100-06): the assembled proof and the owner's sitting.

## Scope

### In

- the grounding, the audit, the thesis, the mockups, the gate;
- the build that the APPROVED thesis defines (its stories will be
  written into this phase at gate time — deliberately not
  pre-scaffolded, because pre-scaffolding the build before the
  thesis is exactly the failure mode this phase kills);
- the materials-spike branch (`design/inset-groups-spike`) as INPUT
  evidence to the thesis — merged, cherry-picked, or discarded per
  the thesis, not by default.

### Out

- any UI change on main before HS-100-04's verdict;
- new capabilities/routes; the wire contracts stay byte-identical;
- iPad parity (consumes the thesis after).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-100-01 | The grounding | done | [story-01-grounding](./story-01-grounding.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-100-02 | The judgment | done | [story-02-judgment](./story-02-judgment.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-100-03 | The thesis | done | [story-03-thesis](./story-03-thesis.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-100-04 | The owner's gate | backlog | [story-04-gate](./story-04-gate.md) | — |
| HS-100-05 | The build (shaped at the gate) | backlog | [story-05-build](./story-05-build.md) | — |
| HS-100-06 | Closeout | backlog | [story-06-closeout](./story-06-closeout.md) | — |

## Where we are

**HS-100-03 done (2026-07-19): the thesis is written and mocked.**
docs/internal/APPLICATION_LAYER_THESIS.md — four applications and a
desk (Speak / Meetings / Agents / Settings), posture-first interiors
with one config door each, the kill/merge accounting (Studio dies,
three launchers collapse to dock + ⌘K), and the B1–B8 build plan with
a guard per story. Ten mockups (five screens × 1440/393) on the
spike's material with real sprites and real trace content, census-
proven complete (scripts/mockup_census.py). Next: HS-100-04 — the
owner's gate. NOTHING builds on main before that verdict. (Earlier
today: HS-100-01 GROUNDING.md; HS-100-02 UIUX_JUDGMENT.md +
judgment_census + the three live flow traces.)

