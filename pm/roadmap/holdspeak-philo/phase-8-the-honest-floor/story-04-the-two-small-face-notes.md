# PHILO-8-04 - The two small face notes (OPTIONAL)

- **Project:** holdspeak-philo
- **Phase:** 8
- **Status:** done
- **Depends on:** the owner keeps one or both notes (Q3); removed if he drops both
- **Unblocks:** PHILO-8-03 (its shots include the kept notes)
- **Owner:** Muad'Dib's lane (Fedaykin, Opus 5.5); Astra role (Opus 5.5 stand-in; Codex Astra on return) checks
- **Closure finding:** Phase 7 final summary, THE LEDGER row 13; BACKLOG "PHILO-7-04 follow-ups" rows 1–2 (`pm/roadmap/holdspeak/BACKLOG.md:1280-1281`); `checks/charter-astra-role-r1.md` F9
- **Canvas:** none for (a) (a heading removed); the words for (b) are the owner's

## Problem

(a) The decision window draws its "Decision context", "Decision" and "Consequences" headings with nothing under them when those fields are empty (`web/src/desk/pullouts/DecisionPullout.tsx:113-115`). UX-CANON: no empty labels. The BACKLOG homes this to the Floor lane (`BACKLOG.md:1280`). (b) On a fresh hub the brief reports the people sections as "unavailable", a word for a state that is only "none yet" (BACKLOG row 2, homed to the Arrival lane, `BACKLOG.md:1281`; the producer line is not yet traced — the story traces it first). (b) is not a Floor item; the charter recommends dropping it from this phase (Q3).

## Scope

- **In:** only the notes the owner keeps: (a) each of the three headings shows only when there is text under it; (b) the brief says the true state for empty people sections, in the owner's words.
- **Out:** any other section of the decision window or the brief.

## Acceptance criteria

- [x] (a, KEPT) A decision with an empty context, decision or consequences field shows no heading for that field; with text, the heading and text show; at 1440 and 393. Red on main. Edit still offers all three fields.
- (b) DROPPED by the owner at ratification (2026-09-26, Q3: "keep (a), drop (b)"); it stays in the Arrival lane (`pm/roadmap/holdspeak/BACKLOG.md:1281`). Not built, not verified here.

## Effort (not a promise)

PROVISIONAL: about 0.25 engineering days for (a); (b) about 0.25 more if kept.

## Test plan

- **Unit:** the pullout render with and without consequences; the brief service's people sections on an empty store.
- **Integration:** a glass shot of each at both widths.

## Notes

- 2026-09-26 — drafted by the Fedaykin docs lane for Muad'Dib; OPTIONAL by the brief; the owner keeps or drops each note at ratification.
- 2026-09-26 — round two: the Astra-role check (`checks/charter-astra-role-r1.md` F9) paid: (a) covers all three empty headings; (b) is an Arrival-lane item, offered for dropping.
- 2026-09-26 — the owner kept (a) and dropped (b) at ratification.
- 2026-09-26 — (a) BUILT (Fedaykin lane, Opus 5.5, `feat/philo-8-04-empty-headings`). `DecisionPullout.tsx` draws each of the three read-view sections with the library `SurfaceSection` species only when its field has text after trim; the editor is unchanged (three fields). `surface.css`: in the decision window (scoped to `.desk-decision-card`) the section head does not draw a second hairline (the pullout section already draws one). Fences: the glass `tests/e2e/test_philo8_04_empty_decision_heads_glass.py` (title only, context only, the Phase 7 story 04 case context + decision; Edit on the title-only case) at 1440 and 393, red on main (the three headings with nothing under them), green after; three vitest cases in `philo301DecisionFace.test.tsx` (two red on main). `philo605DecisionBodyDiagnosis.test.tsx` now finds the "Decision" section by its heading, not by position. Atlas `atlas-phase7.json` line anchors moved (+1, +11). Shots: `assets/story-04-shots/`.
- 2026-09-26 — round two: the Astra-role check on built (`checks/story-04-built-astra-role-r1.md`, RATIFY-WITH-CONDITIONS): C1 paid (the negative control anchors on the read view; the Done-never-leaves-Edit mutant turns it red), F3 and F4 paid; the Follow-through doubled hairline filed in BACKLOG "PHILO-8-04 follow-ups".
