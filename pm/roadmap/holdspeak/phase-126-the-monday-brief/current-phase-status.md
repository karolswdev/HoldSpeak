# Phase 126 — The Monday Brief

**Status:** done (9/9).

**Last updated:** 2026-08-07.

## The orchestrator

Opus 4.6 implements. Terra verifies against spec. The orchestrator
makes the done call.

## What we're building

Phase 125 gave the desk follow-through: meetings produce living boards,
decisions bridge into commitments, nothing gets lost. But the desk
still waits to be asked. It has the data — every service call observed,
every action tracked, every decision lifecycle recorded — but it doesn't
speak first.

Phase 126 changes that. At first desk-open each day (with a wider
Friday-to-Monday window on Monday), the desk reconstructs the operating
picture from observer data, follow-through boards, cadence loops, and
pending decisions. Four fixed sections: **Changed**, **Broke**,
**Waiting**, **Your Decisions**. The brief is deterministic and honest —
empty evidence yields "Nothing material changed," never invented content.

The result: the desk speaks first. Monday morning, before you ask
anything, the desk says what needs you.

## The architecture

```
pipeline_events ──┐
follow_through ───┤
cadence_loops ────┤──→ MondayBriefService.generate()
projections ──────┤         │
actuators ────────┤    ┌────┴────┐
decisions ────────┘    │  Brief  │
                       │         │
                  Changed / Broke / Waiting / Your Decisions
                       │
                  ┌────┴────────────────┐
                  │ monday_briefs table │
                  │ monday_brief_items  │
                  └─────────┬───────────┘
                            │
                  ┌─────────┴───────────┐
                  │  Desk pullout       │
                  │  MCP resource       │
                  │  Headline speech    │
                  └─────────────────────┘
```

## Why this phase exists

1. **The archaeology gap.** Monday morning, a tech lead spends 30-60
   minutes reconstructing what happened: checking Slack, tickets, CI,
   email, half-finished threads. The observer has the raw truth — but
   nobody assembles it into an operating picture.

2. **The attention gap.** Notifications and dashboards show everything.
   A brief shows what matters: what broke, what's waiting, and the
   decisions only this person can make.

3. **The honesty gap.** AI-generated summaries invent content when
   nothing happened. The brief is deterministic: empty sections say
   "Nothing material" and never call a model to fill silence.

## Constitutional grounding

- **Article V.2:** "Every attempt leaves a receipt." The brief is a
  receipt of the desk's own activity — what it did, what broke, what
  waits.
- **Article VI.2:** "No demo state, no seeded flattery, no fallback
  that hides a failure." Empty briefs are honest.
- **Article VII.1:** "No prose in the UI." The brief states what in
  the fewest words.
- **Article III.3:** "No telemetry." The brief is local-only.
- **Article IX:** "Proof over claim." The walk proves it.

## Story status

| ID | Story | Status | Story file | Evidence |
|----|-------|--------|------------|----------|
| HS-126-01 | Brief window and generation model | done | [story-01](story-01-brief-window-model.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-126-02 | Persist the brief | done | [story-02](story-02-persist-brief.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-126-03 | Collect changes | done | [story-03](story-03-collect-changes.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-126-04 | Collect breakage | done | [story-04](story-04-collect-breakage.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-126-05 | Collect waiting work | done | [story-05](story-05-collect-waiting.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-126-06 | Identify owner decisions | done | [story-06](story-06-owner-decisions.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-126-07 | Compose honestly | done | [story-07](story-07-compose-honestly.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-126-08 | Deliver and inspect (MCP + pullout) | done | [story-08](story-08-deliver-inspect.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-126-09 | The walk | done | [story-09](story-09-the-walk.md) | [evidence-story-09](./evidence-story-09.md) |

## Where we are

HS-126-01 through HS-126-06 are done. `MondayBriefService` computes local
17:00 windows (including the Friday-to-Monday span), persists one brief per
local date, and returns the existing identity on repeat generation. Its four
collectors now surface material changes, breakage, waiting work, and owner
decisions: authorization proposals rank ahead of unresolved decision reviews
and due-soon commitments. Brief items retain their source references through
the `brief_id` foreign key. HS-126-07 composes count-based headlines and the
honest empty state. HS-126-08 delivers the same persisted brief through MCP
(`monday_brief.get`, `monday_brief.generate`, and `holdspeak://briefs/latest`)
and FastAPI (`GET /api/brief/latest`, `POST /api/brief/generate`). HS-126-09
walks all four populated sections, the empty-window receipt, MCP delivery, and
same-day idempotence. The Follow-Through (Phase 125) is the prerequisite and
it shipped as PR #443.
