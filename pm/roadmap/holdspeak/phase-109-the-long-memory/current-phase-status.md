# Phase 109 - The Long Memory

**Status:** PLANNED (0/8). Chartered 2026-07-29 by owner direction:
Phase 109 (the second userland program) delivered next; Phase 108
(The Locked Room, RFC §5b confinement) stays reserved with its
machine-asserted work list in BACKLOG candidate Y.

**Last updated:** 2026-07-29 (scaffolded — eight stories, sequencing
below).

## Why this phase exists

The owner's original web-OS charge (Phase 106 charter) named the
person this product serves: *"who keeps project memory, who chats to
agents, who records decisions and then creates artifacts out of those
decisions and meetings."* Phase 106 built the kernel and shipped ONE
userland program well — PR follow-through — and deliberately parked
this one as the NEXT program (story-08: "Project memory and
decisions-to-artifacts are named in the owner's charge and parked as
the NEXT program, deliberately").

The substrate is real: durable meetings with transcript FTS, a
decision-capture plugin, fifteen artifact syntheses with lineage
(`artifact_sources`), aftercare's what-was-decided rollup, project
relationships, and Ask grounding that can already take a Project. What
is missing is the memory itself:

- **A decision is not a record.** It is an anonymous item inside
  `artifacts.structured_json["decisions"]` — no stable ID, no date of
  its own, no accepted/superseded lifecycle, no "replaced by", no way
  for an ADR to cite the decision it came from.
- **Search covers transcripts only.** No index over artifacts,
  decisions, or notes. "Query it years later" today means knowing
  which meeting to open.
- **Project grounding is the newest sixteen.** `grounding.py` caps at
  16 qualified refs ordered by modification time — fine for this
  month's project, silently wrong after two years.
- **Projects are not touchable.** Stronger APIs than surface: in the
  Meetings window, a project is a row in the plumbing drawer with no
  open action, no timeline, no memory face.
- **The kernel's own work is invisible.** "What is running" — the
  process window — has been deferred out of two phases and is now
  honestly a cheap `read` + `events` consumer.

This phase makes the memory real: decisions become first-class
records with provenance, accepted decisions become artifacts that
cite them, the archive becomes queryable with sources, the Project
becomes a desk object with a memory window, and the kernel's running
work gets its window — one modest rider, not a second pillar.

## Honest limits — read this before scoping anything

**"Years later" is a retrieval claim, not an immortality claim.**
Meetings hard-delete today and meeting-born artifacts CASCADE
(`db/core.py:416-423`). This phase settles retention semantics
honestly (HS-109-01 defines what survives a meeting deletion; the
docs story says it plainly) — it does not promise immutable
institutional memory, and no copy may imply it.

**Retrieval is ranked and cited, not omniscient.** A grounded answer
names its sources; when the index misses, the miss is visible
(Article VI — counts honest at zero, approximations labeled). The
surface never claims "all project knowledge."

**The process window watches; it does not act.** Read-only in this
phase — no kill, no retry, no controls. Pending-forever renders as
exactly what it is (`Waiting`/`Running`/`Unknown` as projected); the
window must not invent "failed" from age. The generic liveness reaper
stays in BACKLOG candidate Y.

## Constitutional grounding

- **Article I / II** — the memory ships as OS-owned desk surfaces and
  primitives, never feature pages: the Project becomes a real desk
  primitive with one derived Info contract; the process window is a
  normal window in the one grammar.
- **Article III** — memory is a local index; nothing leaves by
  default. A model-assisted query wears the egress badge at the point
  of decision, exactly as Ask does today.
- **Article V** — watching is free: search, the timeline, and the
  process window are reads. Promotion (an accepted decision becoming
  an artifact) is the owner's direct gesture — approval, not a second
  modal. Model-assisted generation admits and receipts through
  `inference.run@1`.
- **Article VI** — no invented continuity: missing provenance says so,
  a partial index says so, "since last meeting" names WHICH meeting.
- **Article VII** — review and promotion happen in-world; no modals,
  no prose.
- **Article IX** — proof on real data and real metal: old meetings,
  a superseded decision, a source jump, a grounded query answered
  with visible citations against the `.43` endpoint.
- **Article XI clause 5** — reads owe authentication and read
  authority, never admission: the constitutional basis for both the
  memory reads and the process window's `read` + `events` design.

## Goal

The Desk remembers. A decision recorded in a meeting two years ago is
findable by text, openable to its transcript moment, traceable to the
ADR that formalized it and the decision that later superseded it —
and the project it belongs to is a desk object whose memory window
answers "what did we decide, what changed, what is still open" with
sources. Beside it, one quiet window shows what the kernel is running
right now.

## Scope

- **In:** decisions as first-class records with lifecycle and
  supersession; transcript provenance on capture; promotion of
  accepted decisions into artifacts with `decision:<id>` lineage;
  a memory index (decisions/artifacts/notes) with ranked, cited
  project grounding; the Project as desk primitive with a memory
  window; the process window rider; docs; closeout.
- **Out:** RFC §5b confinement and everything in BACKLOG candidate Y's
  confinement list (reserved as Phase 108); any kernel spine change —
  if a story needs one, that is a finding and the story stops; process
  controls (kill/retry) in the process window; embedding/vector
  retrieval (FTS + ranking first; vectors are a future phase if FTS
  proves insufficient); retention/backup tooling beyond honest
  semantics; sync-protocol changes beyond additive schema.

## The sequencing rule that is not negotiable

**The decision record lands first, alone, and everything else builds
on its identity.** HS-109-01 defines what a decision IS — ID,
lifecycle, supersession, project key — with a backfill projection
from every existing `decisions` artifact. Provenance (02), promotion
(03), retrieval (04), and the surface (05) all consume that identity.
Any story that invents a second decision shape is out of order.

The trap to avoid: a "memory" that is really a new write path.
Existing meetings, artifacts, and aftercare keep working unchanged;
the decision record is derived from and reconciled with what the
plugins already produce, never a rival store the plugins must learn.

## Exit criteria (evidence required)

- [ ] HS-109-01: a decision from an existing archived meeting has a
      stable ID, lifecycle, project key, and survives re-running its
      meeting's plugins without duplicating (backfill idempotent,
      proven on the real archive).
- [ ] HS-109-02: a newly captured decision carries its transcript
      moment; opening it jumps to the segment; absence renders as
      honest absence, never a fabricated timestamp.
- [ ] HS-109-03: an accepted decision promotes to an ADR whose
      `artifact_sources` cite `decision:<id>`; superseding it links
      both ways; every model-assisted generation leaves an
      `inference.run@1` receipt; zero modals.
- [ ] HS-109-04: a text query over a multi-year archive returns
      ranked decisions/artifacts/notes with per-source citations;
      project grounding cites sources instead of dumping the newest
      sixteen; the Meetings-window search wire defect (`q` vs
      `search`) is fixed with a regression test; proven live against
      `.43`.
- [ ] HS-109-05: the Project is a desk primitive — openable memory
      window with timeline, decisions, search, and ask-this-project;
      "since last meeting" is project-qualified and names the
      meeting; screenshot walks at 1440 + 393.
- [ ] HS-109-06: the process window renders live kernel operations
      from `read` + `events` only — no new syscall, no controls, no
      invented states; cursor replay proven.
- [ ] HS-109-07: docs at the real entry points, truth-audited against
      the shipped tree; retention semantics stated plainly; stale
      BACKLOG/SECURITY drift from the 107 close reconciled.
- [ ] HS-109-08: the owner's sitting and verdict (Article IX.4), on
      real archive data, machine beats rerunnable as one command.
- [ ] The kernel spine is byte-unchanged across the whole phase:
      `git diff --exit-code` over `broker/admission/journal/model/
      executor` exits 0 at close.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green
      (pre-existing unrelated failures documented per-story).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-109-01 | The decision record — first-class, with lifecycle | backlog | [story-01-decision-record](./story-01-decision-record.md) | — |
| HS-109-02 | Provenance — the transcript moment | backlog | [story-02-provenance](./story-02-provenance.md) | — |
| HS-109-03 | Decisions become artifacts — promotion | backlog | [story-03-promotion](./story-03-promotion.md) | — |
| HS-109-04 | Long-horizon retrieval — the memory index | backlog | [story-04-retrieval](./story-04-retrieval.md) | — |
| HS-109-05 | The Project Memory window | backlog | [story-05-memory-window](./story-05-memory-window.md) | — |
| HS-109-06 | The process window — what is running | backlog | [story-06-process-window](./story-06-process-window.md) | — |
| HS-109-07 | Docs — memory at the entry points | backlog | [story-07-docs](./story-07-docs.md) | — |
| HS-109-08 | Closeout — the sitting on real memory | backlog | [story-08-closeout](./story-08-closeout.md) | — |

## Sequencing

01 first and alone — it defines the identity everything else
consumes. Then 02 and 03 (both depend on 01; 03 also wants 02's
provenance for the promoted artifact's citations). 04 depends on 01
(it indexes decision records) and may run alongside 02/03. 05 depends
on 01/03/04 — the window renders records, promotions, and search. 06
is independent of everything and may land at any point before 07.
Then docs, then closeout.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A rival decision store the plugins must learn | **high** | 01 derives records from existing artifacts; plugins unchanged; reconciliation is one-way with idempotent backfill | Any plugin or synthesis edit that exists to feed the new store |
| Retrieval over-promises ("all project knowledge") | **high** | citations mandatory; misses visible; copy audited in 07 | A grounded answer without per-source citations |
| The memory window becomes a feature page | medium | Desk Grammar review; Project primitive through the one contract; verbs on the registry | A route-owned page or a modal |
| Promotion adds ceremony to the owner's gesture | medium | Article V/XI.4 review: accept IS approval; only model generation admits | A confirmation dialog on accept/promote |
| Process window invents state | medium | render only projected states; no age heuristics | A "failed" row the journal never emitted |
| Schema migration bites the archive | medium | additive-only migration; backfill idempotent on the real archive before merge | Any destructive migration step |
| Spine drift | low | no story touches the kernel; process window is a pure consumer | Any diff under `holdspeak/kernel/` spine files |

## Decisions made (this phase)

- 2026-07-29 - Chartered by owner direction ("Phase 109 fully
  delivered") from the Phase-107-close synthesis: Project Memory is
  the phase, the process window is its one cheap rider; Phase 108 is
  reserved for The Locked Room (§5b confinement) whose audited work
  list keeps in BACKLOG candidate Y - orchestrator, owner-directed.
- 2026-07-29 - Decision records are DERIVED, not rival: backfilled
  and reconciled from the existing `decisions` artifacts the plugins
  already produce; the plugin chain does not learn a new store -
  orchestrator, from the substrate scout's findings.
- 2026-07-29 - FTS + ranking before vectors: the archive is text with
  strong structure; embeddings are a future phase only if FTS proves
  insufficient on real queries - orchestrator.
- 2026-07-29 - The Meetings-window search wire defect (`HistoryCore`
  sends `q`, the route reads `search`) is claimed by HS-109-04 as a
  substrate fix with a regression test - found during charter
  scouting.

## Decisions deferred

- **Phase 108 — The Locked Room** (RFC §5b confinement): the
  privileged executor process, warrants over IPC, A01-A10, T01/T02,
  C02/C03/C05, the "empty register" clause-6 question held for the
  owner. Work list machine-asserted in `effect_ledger.json`.
- **Process controls** (kill/retry from the process window) — needs
  the liveness reaper and a consent story; candidate for 108's
  successor or a rider once the reaper exists.
- **Vector retrieval** — only if FTS misses on real owner queries.
- **Retention/backup tooling** — semantics stated this phase; tooling
  deliberately unscoped.

## Where we are

**2026-07-29 — scaffolded.** Eight stories chartered; HS-109-01 is
next. Nothing has shipped; the story table above is the truth.
