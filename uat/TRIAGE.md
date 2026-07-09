# The UAT triage ritual

A pile of verdicts is not the deliverable — the **joint review** is: the owner
and the agent looking at the same record and deciding, finding by finding, what
to fix, what to leave, and what was fine all along. This doc is the ritual, so
it happens the same way every sitting and its output lands somewhere durable.

## The four steps

1. **The human finishes the sitting.** Every applicable (step, surface) has a
   verdict. The site's sitting-end screen generates the debrief packet
   (`uat/_runs/<run_id>/debrief/debrief.md` + `debrief.json`).

2. **The agent reads `debrief.json` + the log slices** and annotates each
   finding with a first-pass hypothesis. The log slice is the head start: a
   `fail` arrives with the server's own words around that moment. Cross-surface
   splits (passed on web, failed on iPhone) are read as parity breaks, not two
   separate findings.

3. **Owner + agent walk the findings together** and set a disposition on each,
   from this vocabulary:

   | State | Meaning |
   |---|---|
   | `untriaged` | not yet decided (the default) |
   | `fix` | a real defect worth a backlog row |
   | `wont-fix` | real, but not worth fixing now (record why) |
   | `by-design` | the behaviour is correct; the expectation was wrong |
   | `duplicate` | the same defect as another finding (name it) |

   Set each via `PATCH /api/findings/<id>` with `{triage_state, disposition}`.
   The disposition note is the human's reasoning; it survives regeneration.

4. **Every `fix` is proposed into the backlog.** The harness generates a
   paste-ready block (`GET /api/sittings/<id>/findings/backlog-block`) in
   `pm/roadmap/holdspeak/BACKLOG.md`'s candidate-table format, citing the
   finding id and the debrief path. The harness **proposes**; the human pastes
   and the commit rides the normal PMO gate. A UAT finding feeds BACKLOG, and
   BACKLOG feeds phases — the harness never edits BACKLOG or files issues itself.

## What is a finding

Every `fail` and `partial` verdict becomes a finding with a stable id
(`UAT-<run>-<n>`). A `skip` is a deliberate non-answer, listed in the debrief
but not filed for triage. A `pass` is collapsed into the totals. An `n/a`
surface never produces a verdict, so it never produces a finding — but a pack
whose iPhone column is all `n/a` is a **partial sitting**, and the debrief's
per-surface coverage says so plainly.

## Keeping a sitting that mattered

Debrief packets live under gitignored `uat/_runs/`. When a `fix` finding ships
as a holdspeak phase, copy that sitting's `debrief.md` into the relevant
roadmap evidence dir — the debrief cites, the evidence file proves.
