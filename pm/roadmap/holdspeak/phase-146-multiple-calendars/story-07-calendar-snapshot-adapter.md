# HS-146-07 — The Calendar Snapshot adapter (screenshot → reviewed events → a file source)

- **Project:** holdspeak
- **Phase:** 146
- **Status:** ready
- **Depends on:** HS-146-01, HS-146-02, HS-146-03
- **Unblocks:** HS-146-05, HS-146-06
- **Owner:** unassigned

## Problem

Owner direction (2026-08-28, ruled INTO this phase over a Phase-147
deferral): *"most of the time I will certainly not have access to the
server my work's O365's… I take a screenshot of my whole week, and
the adapter essentially translates that into individual .icses."* The
locked-down-work-machine case has no feed URL to subscribe to; the
Phase-135-era OWA/Playwright idea is brittle and
credential-adjacent. A screenshot is the one artifact the owner can
always produce.

## Settled direction (backlog candidate AE, ruled at fold-in)

1. Screenshots of the O365/OWA week view enter HoldSpeak.
2. A vision-capable model — through the intelligence router's
   assignments, local-first, the egress badge honest if a cloud model
   reads the owner's work calendar — extracts events {title, weekday,
   start, end, location}.
3. **Week anchoring is never guessed silently**: read the date header
   when visible, else one confirm field ("week of …").
4. **Review before commit** (preview-before-type doctrine): the
   extracted events render as an editable list; the owner confirms;
   no silent writes from a model read, ever.
5. The confirmed events are written as a local `.ics`; a file-based
   `CalendarSource` (label "O365 SNAPSHOT") is registered or updated.
   From there the 146 machinery is the whole backend: the bounded
   parser stays the ONE trust boundary (model output parsed like any
   hostile feed), replace-on-success per snapshot batch, provenance
   chips, per-source last-good.

## Design beat (required BEFORE implementation)

This story carries a concurrency-light but judgment-heavy flow; per
the design-beat law a read-only plan round settles, with
[ORCH-CALL]s the orchestrator rules:

- which surface hosts the flow (an affordance beside the story-03
  calendar list editor vs the desk drop matrix vs the Hopper) and
  which existing review surface the confirm step reuses;
- which router capability names the vision assignment and what the
  extraction schema/refusal looks like (unreadable screenshot = a
  named in-flow refusal, never an empty success);
- where the generated `.ics` lives on disk and its lifecycle
  (regenerate-in-place per confirm);
- multi-screenshot handling for one week (merge before review).

## Scope

### In

The five settled beats above; the plan's ruled edit map; focused
tests (extraction schema validation with a fixture screenshot →
deterministic fake model in tests, ICS generation round-trip through
the REAL parser, source registration, refusal paths); the egress
truth on the confirm surface.

### Out

- OWA/browser automation; live O365 APIs; recurring background
  re-capture (a snapshot is a manual act).
- Real-model extraction quality tuning beyond one honest
  control-vs-treatment probe on `.43` if a vision-capable local model
  exists there (else the cloud path with badge, owner-visible).

## Acceptance criteria

1. A week-view screenshot becomes rail EVENTs only after the owner
   confirms the reviewed list; cancel writes nothing.
2. The generated `.ics` passes the production parser (round-trip
   test); a hostile/garbled model output is refused by the parser
   exactly like any bad feed — no bypass path exists.
3. Week anchor: wrong-guess is impossible by construction (visible
   anchor, owner-editable) — proven in the review-surface test.
4. A second snapshot of the same week replaces the source's
   projection (no stacking duplicates from re-imports).
5. Egress truth visible wherever the vision assignment is remote.

## Test plan

Named at plan time; at minimum: unit (extraction schema + ICS
round-trip + registration), lane/UI tests for the review surface,
one e2e glass leg (fixture screenshot → fake vision model →
confirm → rail), folded into story 05's walk shots.
