# HS-98-03 — Meetings, native

- **Project:** holdspeak
- **Phase:** 98
- **Status:** backlog
- **Depends on:** HS-98-01
- **Unblocks:** HS-98-09

## Problem

The Meetings window (HistoryCore, 933 lines) is the intelligence
showcase — meetings, facets, artifacts, aftercare — rendered as
key-value dumps and stacked panels. This is where "confidence 0"-class
dishonesty lives.

## Scope

- In:
  - `HistoryCore` in the kit: meeting list as honest rows (title,
    humanized when, facet chips), detail as the split's second pane
    (artifacts, aftercare, moments), import verbs on the verb bar;
  - artifact cards keep their copy-as-markdown verbs but wear the
    surface grammar (sections, not nested Panels);
  - unknown/zero values omitted per the idiom; timestamps humanized;
  - HistoryCore off the guard allowlist.
- Out:
  - meeting pipeline/API changes; Live meeting (HS-98-04).

## Acceptance criteria

- [ ] HistoryCore off the allowlist; guard green.
- [ ] The meetings walk leg passes on the production bundle.
- [ ] Split collapses by window width; shots at both forms.
- [ ] No literal "unknown"/bare-zero renders in the meeting rows shown
      in shots; `npm run check` + python suite green.

## Test plan

- Existing meetings vitest + walk leg; reflow shots; `npm run check`.

## Evidence required

- Before/after shots, walk output, guard output, suite output.
