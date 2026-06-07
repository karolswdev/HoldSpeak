# Phase 49 — Meeting Aftercare ("close the loop")

**Status:** IN PROGRESS (1/6). Opened 2026-06-07 on user direction, right after
Phase 48 closed (PR #30). Picked from the [project backlog](../BACKLOG.md)
candidate A (user-favored): make the meeting side close its own loops instead of
just displaying artifacts.

**Last updated:** 2026-06-07 (HS-49-01 done — the aftercare digest: a read-only
`compute_meeting_aftercare` + `GET /api/meetings/{id}/aftercare` over open items
(by owner), decisions, and a real since-last-meeting diff, surfaced as a "Your
next move" panel above the artifacts. Quiet when nothing's open/decided/changed.
9 new tests + 477-passing sweep; screenshot captured. Next: HS-49-02 provenance.)

## The thesis — why this phase

**The meeting side has 14 real plugins, artifacts, proposals, history, and action
review. What it lacks is follow-through.** The strategic review
(`.guru_meditation.md`, bet #5) put it plainly: *"A beautiful artifact that never
changes the user's next action is decoration."* Grounded in the live tree:

- **The result is display, not action.** A meeting produces artifacts
  (`decisions`, `action_items`, ...) and a user reads them, then goes elsewhere to
  do the work. The history meeting-detail view renders artifacts + proposals, but
  there is no "here's your next move."
- **There is no cross-meeting view.** `MeetingRepository.list_meetings` /
  `list_action_items` exist, but there is **no** "what changed since last meeting"
  query and **no** "what's still open for me across meetings" rollup. That is
  genuinely new work, not a re-skin.
- **The loop-closer already exists, unused for this.** The Phase 37/38 actuator
  system (propose -> approve -> execute, audited, off by default) and the GitHub
  issue / gated connector can turn an accepted action into a filed issue. Aftercare
  wires the meeting result into that path.
- **Provenance is half-built.** Action items carry `source_timestamp` (a real
  link back to the transcript moment); artifacts mostly do not. "Show me the
  moment that justifies this" is a trust win waiting to be surfaced.

## Goal

Make a meeting's afterlife **close loops**: surface what's open / decided /
changed (read-only, honest), let the user jump to the transcript moment that
justifies a result, turn accepted actions into issues through the existing
human-approved actuator flow, and draft a copyable follow-up. Without changing how
meetings are captured, how plugins run, or how synthesis works, and without ever
acting on the user's behalf without explicit approval.

## Scope

- **In:** a **cross-meeting aftercare aggregation** + surface (open-by-owner,
  decisions, since-last-meeting diff) (HS-49-01); a **transcript-moment provenance
  jump** (HS-49-02); **accepted actions -> actuator proposals** reusing the
  existing propose/approve/execute flow (HS-49-03); a **local follow-up draft**
  (preview + copy) (HS-49-04); a **docs** story (HS-49-05); a **closeout**
  (before/after, dogfood, final-summary, PR) (HS-49-06).
- **Out:** new artifact types or new plugins (reuse what synthesis produces);
  changing meeting capture / plugin execution / synthesis; auto-execute or
  auto-send anything (every external effect stays human-approved + audited; drafts
  are preview-only); the public release contract + schema-migration policy (backlog
  C, a separate gate); dictation-side work.

## Exit criteria (evidence required)

- A read-only aftercare aggregation + surface show honest, real counts: what's
  open (by owner), what was decided, and what changed since the previous meeting.
  (HS-49-01)
- A "jump to the transcript moment" affordance appears only where a real timestamp
  exists and opens the transcript there. (HS-49-02)
- Accepted action items become actuator proposals through the existing
  propose -> approve -> execute flow (off by default, human-approved, audited; no
  new write primitive). (HS-49-03)
- A local follow-up draft (decisions + open actions + owners) is preview + copy,
  never auto-sent. (HS-49-04)
- The docs tell aftercare end to end and frame "close the loop"; guards green.
  (HS-49-05)
- Before/after captured; dogfood green; `final-summary.md`; phase CLOSED; PR to
  `main` merged on green. (HS-49-06)

## Invariants

- **Never act without approval.** Closing a loop reuses the actuator system as-is
  (off by default, per-action human approval, audited, payload-parity holds);
  drafts are preview + copy, never auto-sent. No new write primitive.
- **Honest over hype.** "Since last meeting" diffs and "what's open" are computed
  from real data; surfaces stay quiet with no prior meeting / no change; the
  transcript jump shows only when a real timestamp exists. No fabricated changes,
  no fake 0:00.
- **Local-first & private.** Aggregation + drafting are local; anything that could
  leave the machine (issue creation, webhook) goes through the gated connector +
  approval, with the source/egress made clear.
- **Behavior-preserving.** Meeting capture, plugin runs, and synthesis stay
  byte-identical; actuators stay off by default. Existing tests green.
- **Page density.** Do not pile more onto `history.astro` / `history-app.js`
  without factoring into a partial / behavior module (the standing warning).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-49-01 | The aftercare digest (open / decided / changed) | done | [story-01-aftercare-digest.md](./story-01-aftercare-digest.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-49-02 | Transcript provenance ("show me the moment") | backlog | [story-02-transcript-provenance.md](./story-02-transcript-provenance.md) | — |
| HS-49-03 | Close the loop: accepted actions to issues | backlog | [story-03-actions-to-issues.md](./story-03-actions-to-issues.md) | — |
| HS-49-04 | Draft the follow-up (preview + copy) | backlog | [story-04-followup-draft.md](./story-04-followup-draft.md) | — |
| HS-49-05 | Docs: meeting aftercare, end to end | backlog | [story-05-docs.md](./story-05-docs.md) | — |
| HS-49-06 | Closeout — before/after + dogfood + PR | backlog | [story-06-closeout.md](./story-06-closeout.md) | — |

## Where we are

**HS-49-01 is done** — the aftercare digest is built and shipped. The foundation
the rest of the phase presents: `holdspeak/meeting_aftercare.py`
(`compute_meeting_aftercare`) aggregates what's open (by owner), what was decided
(the `decisions` artifact), and a real since-last-meeting diff (new decisions /
new actions / closed actions vs the chronologically prior meeting). It's served
read-only by `GET /api/meetings/{id}/aftercare` and surfaced as a "Your next move"
panel at the top of the meeting-detail side column, above the artifact dump. The
panel and the diff stay quiet when there's nothing open, decided, or changed
(`is_empty`). 9 new tests (unit + API), the 477-passing relevant sweep, and a
screenshot (`screenshots/story-01-aftercare-digest.png`) back it.

Next: **HS-49-02** (transcript provenance — the "jump to the moment" affordance
off the `source_timestamp` the digest already threads through). The
[`AGENT-BRIEF.md`](./AGENT-BRIEF.md) has the mission, the mapped code seams, and
per-story success criteria. Sequence: 01 ✓ -> 02 -> 03 -> 04 -> 05 -> 06.

## Active risks

- **Acting without approval.** Mitigation: reuse the actuator approval + audit (off
  by default); drafts preview-only; the never-act-without-approval invariant.
- **Fabricated "changes".** Mitigation: diffs computed from real prior-meeting
  data; quiet at no-change; honesty-over-hype invariant.
- **Page-file bloat.** Mitigation: the page-density invariant; factor `history.astro`
  aftercare UI into a partial / behavior module.
- **Provenance gaps.** Action items have `source_timestamp`; artifacts mostly do
  not. Mitigation: surface the jump only where a real timestamp exists; thread it
  through where the data already supports it rather than backfilling everything.

## Decisions made (this phase, from user)

- **Build meeting aftercare next.** The user picked backlog candidate A ("I do
  like 4") as the next phase, and asked to keep the other bets alive (now in
  [`../BACKLOG.md`](../BACKLOG.md)).
- **Not one mega-phase.** The other backlog bets ship as their own focused phases.

## Decisions deferred

- **Aftercare home.** A dedicated tab vs. a section inside the meeting-detail view
  vs. a cross-meeting "for me" rollup. Settle in HS-49-01, favoring the lightest
  thing that reads as "your next move" and does not bloat `history.astro`.
- **Follow-up draft: local-only vs LLM-assisted.** Start local (assemble from
  artifacts); an LLM polish pass is a candidate, not required. Settle in HS-49-04.
- **Provenance for artifacts.** Whether to backfill a transcript-moment link onto
  decisions (a schema touch) or only surface it where data already exists. Settle
  in HS-49-02, favoring the no-schema-churn path first.
