# PHILO-5-04 - The owner asks in his own words

- **Project:** holdspeak-philo
- **Phase:** 5
- **Status:** backlog
- **Depends on:** PHILO-5-03
- **Unblocks:** the phase close
- **Owner:** Astra (Luna); Muad'Dib checks
- **Council tag:** the owner's D3 and proof mode; Astra r2 Closing proof

## Problem

The owner ruled the closing use: Codex drives it (D3), rehearsed, the owner skims shots (proof mode). Until the loop runs from a normal-language request through Codex against an isolated hub, the catalogue is not shown to be client-neutral, and the owner has no evidence that the job lands on the Desk. Story 01 proves the path (`scripts/graph_walk.py:1494,1517`, `holdspeak/mcp/server.py:119,144`, `scripts/astra:20,50`); this story uses it for the whole job.

## Scope

- **In:** Astra drives the normal-language meeting job through Codex against an isolated hub (import, summary, decision, next-day brief, the Thought's save); the MCP transcript and the Desk shots at 1440 and 393 retained; Muad'Dib checks; the owner reviews the shots.
- **Out:** everything the phase status lists as out; a live sitting; the owner's own client; already-open brief refresh (the shots use a fresh/reopened Desk read for the brief).

## Acceptance criteria

- [ ] The request is ordinary words; no operation name, argument or test clock appears in the request, and the owner is never asked to operate them.
- [ ] Run against an isolated HOME via the story 01 Codex configuration; the effective HOME, lock and DB path retained; never the desk.
- [ ] The MCP transcript and the Desk shots at 1440 and 393 are retained: the summary, the decision, the dated next-day brief and the saved Thought on the Desk; summary delivery without manual refresh; the brief on a fresh/reopened Desk read.
- [ ] Real-engine and replayed runs, if both occur, are retained and labelled separately.
- [ ] Muad'Dib's check is recorded; the owner reviews the shots; the evidence reads "rehearsed, owner-reviewed shots" and never as an observed sitting.
- [ ] Fence law: every behavioural fence is red pre-fix through the real producers (real services, the real hub, the real lock and config paths — no test double that lies about the field the check reads); new structural invariants are proved by deliberate mutations that turn the fence red. An import failure or an unavailable symbol is not the required red.


## Carried in from story 03 (Muad'Dib's counsel C3 — work, not notes)

- [ ] SAVED shown on the Arrival while the durable state is `import_failed` (an empty VTT import): the face must not lie — fix the honest state (no design; the existing failure idiom) with a fence red pre-fix, or a named follow-up with a fence-as-observed if the fix needs a canvas.
- [ ] S4 at 393: after Done the reading view is blank — cause found; fixed if product-only, else ledgered with the shot.
- [ ] One missing HTTP decision read produces TWO broke rows (`holdspeak/web/routes/decisions.py:58-61` falls through from the registry NotFound to the lifecycle service): one cause, one row; fence red pre-fix.
- [ ] Shelf schema drift: the MCP tool enum refuses before dispatch while the descriptor says it will not pre-empt (`operations.py:421-431`) — align (descriptor or schema) with a schema-alignment fence.
- [ ] Structural fence: the rig (`scripts/graph_walk.py`, `philo5_pairs.py`) never imports `holdspeak.operations` in-process (a second composition); red by mutation.
- [ ] Ledgered: op observations carry a forced `viewport: 1440` label and a `-1440` run id — a reader can take an op run for a face; note it in the rig's observation schema or drop the label for op runs (small).

## Effort (council-style estimate, not a promise)

1 day (Astra r2)

## Test plan

- **Unit:** none new (the fences live in 01–03).
- **Integration:** the Codex → proxy → isolated hub run, transcript and shots retained under this phase's assets.
- **Manual / device:** the owner reviews the shots (rehearsed, owner-reviewed shots — not a sitting).

## Notes

- 2026-09-24 — chartered from draft r3 + Astra r2 (`checks/charter-astra-r2.md`, the Closing proof position and the story-04 amendment).
