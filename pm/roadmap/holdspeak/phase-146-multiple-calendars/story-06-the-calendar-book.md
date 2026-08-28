# HS-146-06 — The calendar book (thorough feature documentation)

- **Project:** holdspeak
- **Phase:** 146
- **Status:** ready
- **Depends on:** HS-146-02, HS-146-03, HS-146-04, HS-146-07
- **Unblocks:** HS-146-05
- **Owner:** unassigned

## Problem

Owner order (2026-08-28): document this feature thoroughly — a
dedicated story, not the close's afterthought. Today the calendar's
entire public story is one paragraph in the Door section
(`docs/USER_GUIDE.md:487-497`), one egress row (`docs/SECURITY.md:355`),
and a passing mention in `docs/MCP_SIDECAR.md:87`; `docs/ARCHITECTURE.md`
says nothing about the calendar pipeline at all. Multi-calendar ships
with real semantics (per-source last-good, provenance, no-dedupe,
orphan cleanup, one-shot migration) that a cold reader must be able
to learn from the docs alone.

## Scope

### In

- **USER_GUIDE** — a proper "Calendars" section (not a paragraph):
  connecting the first calendar (file path and HTTPS, from the Door's
  Connect-calendar affordance AND from Settings→Meetings); adding a
  second (labels, the enable toggle, remove); what the rail shows
  (EVENT rows, STARTS times, the provenance chip appearing only when
  more than one source is configured); why a duplicated event shows
  twice (cross-feed UIDs, no silent merge); what happens when a
  calendar breaks (last-good events stay, the refusal is named);
  refresh cadence (boot + 15 minutes); what disable/remove do to
  projected events. Voice: the POSITIONING canon, no prose in
  screenshots' place, labels stated exactly as the UI renders them.
- **SECURITY** — the egress row rewritten for many sources: exactly
  what is fetched (each enabled HTTPS url), when, the wire posture
  (no redirects, 10s, no credential headers), the per-source egress
  chips as the visible truth, what never leaves the machine; file
  sources = zero egress.
- **ARCHITECTURE** — a compact calendar-pipeline section: config
  shape (`CalendarSource`), the one-shot migration, the conductor's
  per-source refresh + per-source last-good law + orphan cleanup, the
  revision namespace (`calendar_source_revision(source_id, url)` →
  projection ids), the bounded parser limits (5 MiB / 14-day /
  128 occurrences), the projection store columns, and how the Door
  aggregate consumes it (`calendar_configured` = ≥1 enabled valid).
- **MCP_SIDECAR** (:87 + the settings tool description truth) and
  **README** / **GETTING_STARTED** entry points: the multi-calendar
  sentence where the Door is described; only where these surfaces
  already speak of the Door/calendar — no new marketing prose.
- **The six "one subscription" sites** from the plan §7 (moved here
  from story 05 by the 2026-08-28 amendment): USER_GUIDE:486-497,
  SECURITY:355, `mcp/families/settings.py:28`, and the three
  docstrings (`integrations.py`, `calendar_ingest_conductor.py`,
  `db/calendar_events.py`).
- **Retirement guard**: extend the doc-drift guard (the 143/144
  precedent) so the singular "calendar subscription" claim cannot
  creep back into the user-facing docs once retired — only if the
  existing guard mechanism accommodates it cleanly; otherwise record
  the tie-break in evidence.

- **The Snapshot adapter chapter** (amended 2026-08-28 at the
  HS-146-07 fold-in): USER_GUIDE covers the screenshot import
  end-to-end (what to screenshot, the week anchor, the review step,
  what "O365 SNAPSHOT" on the rail means, re-importing a week);
  SECURITY covers where the screenshot goes (the vision assignment's
  egress truth — local vs cloud) and that the generated `.ics` rides
  the same bounded parser; ARCHITECTURE covers the adapter's
  trust-boundary claim (model output is hostile input).

### Out

- Shots/walk/close (story 05). Marketing rewrites of unrelated
  sections. New public doc files beyond what the entry points need.

## Acceptance criteria

1. A cold reader can set up two calendars, predict the rail's
   behavior (chips, duplicates, breakage), and answer the egress
   question from the docs alone.
2. `grep -ri "calendar subscription" docs/ README.md` (singular
   claims) returns zero user-facing hits; grep proof in evidence.
3. ARCHITECTURE teaches the per-source last-good law and the
   revision namespace with file anchors that are real.
4. Every touched doc renders truthfully against the shipped UI
   labels (checked against the story 03/04 glass, not memory).

## Test plan

- Doc guards: `uv run --python 3.13.11 pytest -q
  tests/unit/test_doc_drift_guard.py tests/unit/test_product_copy.py
  tests/unit/test_product_language.py` (isolated HOME) — read
  against the known baseline failures honestly.
- The greps from acceptance criteria captured in evidence.
