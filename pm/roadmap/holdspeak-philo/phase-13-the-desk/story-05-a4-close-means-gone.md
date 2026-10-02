# PHILO-13-05 - A4 Close means gone

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** done
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** PHILO-13-07 (B2 builds on a lifecycle that closes)
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** A4 (PROPOSAL §3, Wave A)
- **Closure finding:** `grounding/faces-jobs.md` F1 (`:167`); `grounding/faces.md:24`; `grounding/checks/faces-astra.md` finding 1; `grounding/checks/proposal-astra.md` conditions
- **Canvas:** none

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

After Close, the window is gone: nothing invisible stays on top and catches his taps.

## Problem

After Close, the card fades to opacity 0 and stays (`pointer-events: auto`, ≥ 4 s, until reload). At 393 the closed Intelligence window covers the whole Chair: `Retry` and every row tap go nowhere until a reload (`grounding/probes/faces-jobs-ghost-1440.out.txt`, `-393.out.txt`; `grounding/shots/jobs/J1-10-retry-swallowed-393.png`). **The cause is source-backed, not proven:** `openPullout` stores the qualified id it is given (`decision:decision_…`, `intelligence:desk`; `web/src/desk/store/compositorSlice.ts:137-152`), the card closes with the bare `o.id` (`web/src/desk/components/Pullout.tsx:68`), `closePullout` filters by equality (`compositorSlice.ts:177-189`), and the faded element (`web/src/desk/components/DeskWindow.tsx:645-668`) is never unmounted (`grounding/faces.md:24`).

## Scope

- **In:**
  - **First, reproduce through the real path:** open each object window through its real opener (qualified ids: a decision from the brief or palette, `intelligence:desk`; bare ids: a list row), close it, and fail a test on what the browser renders. Only then fix.
  - The fix at its seam (the id the store keeps versus the id the card closes with), in `web/src/desk/store/**` and `Pullout.tsx`.
  - A rendered fence for every opener that passes a qualified id.
- **Out:** window memory (B2); the close animation's look (C1).

## Acceptance criteria

- [ ] A failing test, written first, reproduces the ghost through the real open-and-close path for at least one qualified-id opener; it is red on main.
- [ ] After Close, `elementFromPoint` at the old window centre hits the Desk (not the closed card), at 1440 and at 393 (touch), for every opener that passes a qualified id, and for a bare-id opener.
- [ ] The closed card leaves the DOM (or holds `pointer-events: none`) after its animation; the next tap at its old place reaches what is under it (the J1 `Retry` at 393 works without a reload).
- [ ] If the reproduction shows a different cause, the story records it and fixes that cause; the fence stays on the rendered result.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-muaddib.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_muaddib_atlas.py`.
- **Focused:** web unit on the store (open qualified → close → the instance is gone); `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** Playwright through the real hub: open → close → `elementFromPoint` at both widths, touch at 393.
- **Atlas:** one case (open the decision from the brief, close, tap `Retry`), at 1440 and 393, one case per `scripts/graph_walk.py run` invocation.
- **Shots:** before Close, after Close, the next tap's effect, both widths.

## Worker-brief scars

- **Doubles that lie:** jsdom does not render opacity or hit tests; the unit test alone does not prove the face. The rendered fence is the proof.
- **Never rewrite a guard to match a removal:** an existing close test that passes on main is not loosened; it gains the qualified-id case.

## Effort (not a promise)

Grounding size: not sized as a move. PROVISIONAL.

## Notes

- 2026-10-01 — `web/src/desk/components/Pullout.tsx` is not named in PROPOSAL §4's map; assigned to this lane (status file, "File ownership").
- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
