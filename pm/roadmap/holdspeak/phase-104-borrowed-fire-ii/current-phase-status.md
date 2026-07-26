# Phase 104 - Borrowed Fire II: The Watched Hand

**Status:** SCAFFOLDED (0/7, 2026-07-25). Chartered from a second
external-research pass in the Phase-103 mold: a study of
`SirAllap/agentglass` (an MIT-licensed mission-control dashboard for
AI coding agents — Claude Code hooks + OTel ingestion, a PreToolUse
approval gate, cost/latency radar, and a git/PR/Docker cockpit),
followed by an adversarial council review (Codex CLI, read-only
against this repo, no shared context with the proposer). The council
cut two of five proposed stories, invalidated the gate's fail-open
design, and grounded the owner-mandated PR watch in a deferral this
roadmap had already recorded (Phase 94's candidate-Y "real GitHub
PR/CI receipt rows"). **Re-sequenced 2026-07-25 behind Phase 105
(Workbench)** by owner direction: the world layer is polished to
OS-grade first; this phase's shade cards and receipt lines land on
the icon/state/Info grammar Phase 105 installs. Activation order:
Phase 103 close → Phase 105 → this phase.

**Last updated:** 2026-07-25 (scaffolded; no story started).

## Why this phase exists

AgentGlass validates the exact thesis of Phases 87–90: the machine
that hosts your agents is a first-class surface. But its instincts are
the mirror of ours — it *watches* everything and intervenes at one
gate; HoldSpeak *steers* through one audited chokepoint and observes
as receipts. This phase borrows the half we lack: the ability for a
steered agent's own risky action to stop and ask the desk first, and
for the desk to answer honestly about what a session did and cost.

The council's synthesis rejected most of AgentGlass, as Phase 103
rejected most of researchmind:

- **Rejected: the cockpit sprawl** (git panel, PR review threads,
  Docker, Electron shell, in-app updater). Fleet-operator and
  IDE-adjacent scope; the desk grammar would drown under it.
- **Rejected: OTel/multi-provider ingestion breadth.** One owner's
  desk, not a telemetry platform.
- **Cut by council: the machine-wide agent census as desk objects.**
  `~/.claude/projects` is an archive, not a live census; transcript
  presence proves neither liveness nor attachability. Parked as a
  backlog candidate (an opt-in "observed archives" adapter with
  last-seen + confidence, materializing nothing until correlated).
- **Cut by council: context-radar-as-physics.** Objects that drift
  with context consumption violate Article I's sacred-arrangement
  clause — the very clause HS-103-01 just repaired. Parked: a quiet
  Reduce-Motion-safe gauge on the selected session, honestly labeled
  `reported`/`estimated`/`unavailable`, paired with a real
  compact/handoff verb.
- **Kept, redesigned: the tool-call gate** (fail-closed when armed,
  proposal persisted — never authority; see HS-104-02).
- **Kept, owner-mandated, narrowed: the PR watch** (HS-104-04 pays
  Phase 94's candidate-Y deferral at its minimal honest scope).
- **Kept, honesty-labeled: session receipts** (HS-104-05).

## Constitutional grounding

- **Article V (Consent is the spine of action):** the gate is a new
  vertebra on the existing spine — propose → approve → execute,
  default-off, double opt-in, every decision audited. It never mints
  a new consent mechanism; it rides Attention + the shade.
- **Article VI (Honest by construction):** capability declarations
  (HS-104-01) make the system state what it actually knows per agent
  adapter — authoritative, inferred, or unavailable — before any
  surface renders a number derived from it.
- **Article III (Local first, honest egress):** the gate is
  loopback-only plumbing (hook → hub). The PR watch is the one story
  with egress and wears the `local+cloud` badge; polling is manual or
  explicitly enabled, never ambient.
- **Article IX (Proof over claim):** the gate ships with its own
  threat-model story (HS-104-03) — restart, replay, TOCTOU, expiry —
  proven against a real Claude Code session, and the phase closes on
  an owner sitting.

## Goal

A steered agent's risky tool call can stop and ask the desk (armed
explicitly, fail-closed, decided from the shade, audited); the PRs
its work produces appear as honest receipt rows on the delivery
surfaces; and a session's card tells the truth about time, calls,
tokens, and estimated cost — with every number labeled by its
provenance.

## Scope

- In: the seven stories below and their evidence.
- Out: everything in the rejected/cut list above; any write action
  against GitHub (comments, reviews, merges — a merge actuator is a
  future phase on the actuator spine); ALL iPad/HSM work (standing
  owner direction, 2026-07-25: the web Desk OS is polished to the
  atom FIRST, becoming the spec a Swift recreation is later built
  from — contracts here are authored as spec artifacts, not as an
  active handoff, and no HSM leg rides or gates this phase).

## Exit criteria (evidence required)

- [ ] HS-104-01 through HS-104-05 shipped with evidence, each proven
      live against a real staged hub (and the gate against a real
      Claude Code session, real metal per standing practice).
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green (any
      pre-existing unrelated failures documented per-story).
- [ ] `cd web && npx tsc --noEmit -p . && npx vitest run && npm run
      build && npm run tokens:gate` green.
- [ ] The voice/vocabulary guards green, including the HS-103-02
      dash-in-glass rule, on every new surface string.
- [ ] HS-104-06 docs shipped touching the real entry points.
- [ ] HS-104-07 closeout: the walk passed live, the parked candidates
      recorded in BACKLOG.md, and the owner's sitting verdict recorded
      per Article IX.4.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-104-01 | The capability ledger — what each adapter actually knows | backlog | [story-01-capability-ledger](./story-01-capability-ledger.md) | — |
| HS-104-02 | The tool-call gate — a held hand, not a watched one | backlog | [story-02-tool-call-gate](./story-02-tool-call-gate.md) | — |
| HS-104-03 | The gate under attack — restart, replay, TOCTOU | backlog | [story-03-gate-threat-model](./story-03-gate-threat-model.md) | — |
| HS-104-04 | PR receipts — paying the candidate-Y deferral | backlog | [story-04-pr-receipts](./story-04-pr-receipts.md) | — |
| HS-104-05 | Session receipts — honest numbers on the card | backlog | [story-05-session-receipts](./story-05-session-receipts.md) | — |
| HS-104-06 | Docs — the gate and the watch at the entry points | backlog | [story-06-docs](./story-06-docs.md) | — |
| HS-104-07 | Closeout — the walk and the sitting | backlog | [story-07-closeout](./story-07-closeout.md) | — |

## Decisions deferred (parked, not committed)

- **Observed-archives adapter** (the census salvage): opt-in scanner
  over `~/.claude/projects` exposing last-seen + confidence, no desk
  objects until correlated with a live pane or Work attempt.
- **Context gauge on the selected session**: `reported` /
  `estimated` / `unavailable`, Reduce-Motion-safe, with a real
  compact/handoff verb. Blocked on HS-104-01 declaring context
  reporting per adapter first.
- **The merge actuator**: bound to PR + head SHA + merge method,
  stale-head refusal, receipt — a clean future story on the Phase
  37/61 executor spine once PR receipts exist.

## Where we are

**2026-07-25 — scaffolded, then re-sequenced.** The AgentGlass study
and the council critique are recorded in this charter; seven
implementation-grade stories drafted. Later the same day the owner
chartered Phase 105 (Workbench) and ordered it first; this phase
activates after 105 closes. Nothing started.
