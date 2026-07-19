# Phase 100 — The Application Layer

**Status:** IN PROGRESS (10/13, 2026-07-19) — building on the approved thesis by the owner's direct
directive, verbatim in spirit: *"a phase that will cause a deep, deep,
deep grounding in the philosophy, seams, use cases — to then form an
opinion on the entire UI/UX with regards to its applicability to the
Desk OS — and then finally deliver something beautiful, not mangled,
easy to use: a proper application layer on our Desk OS to drive the
value of HoldSpeak."*

**Last updated:** 2026-07-19 (HS-100-10 done: Studio dead, guide absorbed, arrival quiet, ONE vocabulary canon end-to-end, POSITIONING amended).

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
5. **Deliver** (HS-100-05..12, authored at the gate from the approved
   thesis): build the
   application layer the thesis describes — beautiful, not mangled,
   easy — with the mechanical guards that make regressions
   unshippable.
6. **Close** (HS-100-13): the assembled proof and the owner's sitting.

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
| HS-100-04 | The owner's gate | done | [story-04-gate](./story-04-gate.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-100-05 | B1: the vocabulary guard | done | [story-05-vocabulary-guard](./story-05-vocabulary-guard.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-100-06 | B2: the honest mic | done | [story-06-honest-mic](./story-06-honest-mic.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-100-07 | B3: Speak | done | [story-07-speak](./story-07-speak.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-100-08 | B4: Meetings | done | [story-08-meetings](./story-08-meetings.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-100-09 | B5: Agents | done | [story-09-agents](./story-09-agents.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-100-10 | B6: Settings and the arrival | done | [story-10-settings-arrival](./story-10-settings-arrival.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-100-11 | B7: one launcher | backlog | [story-11-one-launcher](./story-11-one-launcher.md) | — |
| HS-100-12 | B8: geometry walk + assembled chain | backlog | [story-12-geometry-walk](./story-12-geometry-walk.md) | — |
| HS-100-13 | Closeout (the owner's sitting) | backlog | [story-13-closeout](./story-13-closeout.md) | — |

## Where we are

**HS-100-04 done (2026-07-19): the owner called it.** The verdict,
verbatim: "Yeah dude. I am calling it. And I'm saying - yes, good
step forward. Keep being better and better." Zero revision rounds;
the thesis stands as presented. B1–B8 are authored as HS-100-05..12
(one story, one guard, one commit each); the closeout is HS-100-13
and still closes only on the owner's live sitting over the BUILT
layer. B1 shipped: the vocabulary guard is live with seven allowlisted offender files to burn down, and the model-missing refusal names its fix instead of leaking a path. B2 shipped: a mic without capture is visible, disabled, and says why — proven live on the plain-HTTP LAN origin. B3 shipped: Speak opens on the job — hero mic, verdict pair, correction in place; Journal/Blocks as head wings, six config sections behind one gear, and the flow budget pinned live at 4 interactions in one window. B4 shipped: Meetings opens on outcomes — needs-you leads with the approve verbs in place, the transcript folds to a receipt, the list is a rail, plumbing is behind the door; meetingflow pinned at 3 interactions. B5 shipped: Agents opens on who needs you — blocked sessions lead with a primary Answer verb into the audited steering seam; Delivery and Chat are wings; the persona vocabulary left the glass and the allowlist shrank to two files. B6 shipped: Studio is dead and its address demoted; Settings gained the Guide wing; the arrival is two starts and one trust line; the pre-Constitution product-language registry was amended to the Agent canon (the split-brain's engine), the docs and backend copy swept, and the vocabulary allowlist locked EMPTY; POSITIONING now says the Desk IS the front door. Next: HS-100-11 — one launcher. (Earlier today:
01 GROUNDING.md · 02 UIUX_JUDGMENT.md + traces · 03 the thesis +
ten mockups.)
