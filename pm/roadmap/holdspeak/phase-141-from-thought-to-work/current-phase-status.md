# Phase 141 — From Thought to Work

**Status:** active (5/9); raw custody, resumable continuity, the owner-facing
Develop bridge, immediate no-model completion/reopen, and one receipt-gated
owner-triggered AI question are done. Visible context attachment is next.

**Last updated:** 2026-08-19.

## Owner mandate

A captured thought should not be classified once and thrown into a drawer. It
should enter a continuing clarification loop with AI, gain explicitly attached
context, become richer over successive turns, and suggest concrete outcomes in
real tools. The owner affirmed this direction and ordered orchestration.

## Goal

Ship one dependable loop from rough thought to durable working synthesis and an
optional typed proposal. Preserve the raw thought before AI, ask one useful
question at a time only when the owner continues, make context visible, survive
reload/conflict, remain useful without a model, and prove one external GitHub
issue through the existing authority and receipt spine.

## Ruled design

[`../proposals/thought-refinement-spine.md`](../proposals/thought-refinement-spine.md)
is the design beat and risk analysis. Three independent reviews ratified it
after adversarial amendment. Stories implement that document; they do not
redesign it in flight.

Settled product decisions:

- **power-user first, YOLO first:** the ordinary fresh-install path is capable
  immediately. Configured eligible outcomes execute under the existing default
  YOLO posture with receipts; Neutral/Safe retain their existing decision step.
  Progressive disclosure hides setup and secondary controls, never capability;
- owner-facing primary verb: **Develop a thought**;
- the working Note appears immediately in Inbox as **Unfinished** and the Chair
  offers **Resume unfinished thoughts**;
- one primary action per state, including at 393px;
- **Good enough** completes the existing working Note in one action;
- Phase 141 proves GitHub issue execution through the existing
  ActuatorProposal/kernel path;
- Jira and calendar write support are separate follow-ons because neither
  exists today.

## Stories

| ID | Story | Status | Depends on |
|---|---|---|---|
| HS-141-01 | Raw before AI | done | Phase 140 landing |
| HS-141-02 | The resumable thought | done | 141-01 |
| HS-141-03 | Develop this thought | done | 141-02 |
| HS-141-04 | One useful question | done | 141-02, 141-03, 141-06 |
| HS-141-05 | Context you can see | backlog | 141-02, 141-04 |
| HS-141-06 | Good enough means done | done | 141-02, 141-03 |
| HS-141-07 | Typed outcomes, not magic | backlog | 141-04, 141-06 |
| HS-141-08 | One real tool | backlog | 141-07 |
| HS-141-09 | The thought-to-work walk | backlog | 141-01…08 |

## Wave order

1. **Keystone alone:** HS-141-01. Counsel reviews the persisted state machine
   and concurrency matrix before UI work begins.
2. **Daily custody:** HS-141-02 freezes the read/list/recovery DTO. HS-141-03
   may prepare glass in parallel but implementation begins only after that DTO
   is stable.
3. **Local escape hatch:** HS-141-06 lands the complete no-model path before any
   model surface.
4. **Refinement:** HS-141-04 and HS-141-05, serialized at their shared grounding
   seam, then HS-141-07 adds the local Decision shape.
5. **External proof:** HS-141-08 only after local proposals are boring.
6. **Craft and walk:** HS-141-09 owns the final subtraction, both-width glass,
   restart/fault matrix, docs, counsel, and owner sitting.

## Phase gates

- No model or tool call can occur before the raw snapshot and working Note are
  durable in one transaction.
- The raw snapshot remains byte-equal through every model, edit, proposal,
  retry, conflict, and restart leg.
- No browser-copied context is authoritative; refs hydrate on the server.
- No model response changes product state without a persisted owner transition.
  The owner's **Good enough**, **Create decision**, or configured-tool action is
  that transition; the flow must not add a second confirmation. Under YOLO an
  eligible configured external proposal continues directly through the existing
  executor, while Neutral/Safe use their existing approval behavior.
- No external effect bypasses the existing actuator executor or the mandatory
  linked kernel admission for this new flow.
- A dispatched-but-ambiguous GitHub effect enters named manual reconciliation
  and cannot be automatically reissued.
- Fresh HOME without a model completes capture → edit → Good enough → reopen.
- At 393px every state shows one primary decision and zero horizontal overflow.
- The owner sees final both-width screenshots before merge.
- GitHub Actions is not watched or used as a phase gate.

## Risks carried into execution

The complete R1–R17 register is in the ruled proposal. P0 stop signals are raw
loss, concurrent false-success, hidden context, model-caused state mutation,
duplicate external effects, invented tool capability, or authority bypass.
Any one stops the wave. Three rounds in one invariant class trigger a design
review; five rounds surface the rigor/cost choice to the owner.

## Explicit non-goals

- Jira create/assign/transition or calendar write;
- autonomous tool selection or execution;
- automatic context attachment;
- multi-tool planning, background refinement, or agent assignment;
- a new generic chat thread, planner, tool router, executor, or approval stack;
- Artifact or generic follow-through authoring without a real typed adapter;
- restoration of the Speak operations console as the ordinary capture path.

## Decision log

- 2026-08-18 — Chartered from the owner-ratified thought-refinement direction.
  The design/risk proposal had three final RATIFY verdicts. “Develop a thought,”
  Inbox + Resume custody, and one GitHub external proof are settled here; Jira
  remains a truthful follow-on.
- 2026-08-18 — Owner ruled **YOLO first, power-user first**. The charter now
  forbids tutorial gates and redundant confirmations: rich defaults and fast
  configured outcomes are ordinary; progressive disclosure contains complexity,
  and the existing posture/policy/receipt spine contains effects.
- 2026-08-18 — HS-141-01 done after the three-round invariant circuit breaker
  triggered a fresh design review. The ratified aggregate-command ledger keeps
  raw custody immutable, versions content and lifecycle separately, closes
  ordinary CRUD and paired-sync bypasses, and makes tombstone replay both
  absolute and idempotent. Final adversarial counsel: RATIFY.
- 2026-08-18 — HS-141-02 done. Owner-only bounded resume/load DTOs now carry
  mandatory cursors without raw/context/result leakage. Logical refinement
  requests durably bind every physical inference attempt—including dialect
  follow-up—before dispatch, while deterministic recovery names stale,
  superseded, failed, and orphaned states without rerun or Note mutation. Native
  continuity proof remains hub-local. Final adversarial counsel: RATIFY.
- 2026-08-19 — HS-141-03 done. The ordinary Chair now enters local thought
  development directly, every ordinary Note can be adopted in place under an
  atomic source precondition, Original remains byte-equal, and Inbox/Resume
  reopen the same working Note. Serialized editor saves, authority-epoch stale
  response rejection, and sync provenance checks close the concurrency seams.
  A genuine bare-hub 1440/393 walk passed with zero overflow or console errors;
  final technical and owner-glass counsel: RATIFY.
- 2026-08-19 — HS-141-06 done. **Good enough** is the default-YOLO immediate
  owner command: it drains every accepted local edit, then atomically records
  one lifecycle transition and one origin-hub retry receipt without a Save or
  confirmation step. Completed Notes remain in place, read-only, with Original
  and explicit **Resume refining**. Public commands are OWNER-only; NODE remains
  confined to validated paired-sync convergence. A fresh no-model walk survived
  hub/database reopen and a fresh browser context at both widths. Final design,
  implementation, and cold-owner counsel: RATIFY.
- 2026-08-19 — HS-141-04 done. One explicit owner action now produces at most
  one receipt-gated question or synthesis; Stop suppresses late output, Answer
  and Accept write immediately under CAS, and no action silently starts another
  model turn. A shared refinement application service gives HTTP and MCP the
  same idempotency, cursors, receipts, named conflicts, and durable web/sidecar
  execution ownership. Fresh 1440/393 browser walks used the real API, kernel,
  projection, reconcile, and Note-write path with a labelled deterministic
  provider simulation. Technical and cold-owner counsel: RATIFY. The owner
  accepted the loop and deferred normalization of the overlapping completion/
  continuation verbs to HS-141-09's subtraction pass.
