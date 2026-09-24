# Check — Muad'Dib, 2026-09-24

Claude session: `ca18f694-e6e1-45f1-83e5-0ba438442be0`. Read only; seam plan before implementation.

**VERDICT: RATIFY-WITH-CONDITIONS**

Check record for the author: Claude session `ca18f694-e6e1-45f1-83e5-0ba438442be0`, read only, no tests run.

**FINDINGS**

1. **The seam is real but narrower than the plan says.** In the retained 393 run the row grew from 93 to 114 px because the title wraps to two lines (observation.json `before.rect` vs `after.rect`, both at y=470). Only the bottom sample row at y=582 is owned by the bar; in `after.png` the title and both Ack and Defer are fully visible, and about 12 px of the row's bottom padding sits under the bar. The fence Astra added (`readable_text`, all nine points owned) is stricter than the exit criterion at `current-phase-status.md:29` ("visible and inside the viewport") and the story AC ("not under the footer"). The product move is still justified, but by the next realistic case (a three-line title puts the verbs under the bar), not by the current shot being unreadable. The record must say that.

2. **The mechanism is a mid-scroll sticky overlay, not a layout bug.** `chair.css:626` makes the bar `position: sticky; bottom: 0` under 480 px inside the `.chair` scroll container (`chair.css:16-21`). The rig does not scroll the observe target before the verdict snapshot (only `capture_framed_view` after it, `graph_walk.py:3525`), so the pass depends on the scroll position the last setup click left. The plan's "row starts covered" fence is the right consequence.

3. **Prefer the platform route over hand-measured math (Tenet 1).** `scroll-padding-bottom` on `.chair` in the same media block plus `firstRow.scrollIntoView({ block: "nearest" })` after the successful Generate paints gives "move only enough" and "no move when clear" for free, and also fixes keyboard focus scrolling under the bar. The in-house idiom already exists at `NotePullout.tsx:349` and `ThreadPullout.tsx:1281`. Use instant scroll, not smooth, or the hit-test fence races the animation. The bar height is not a constant at 393 (it wraps, `chair.css:568`), so if a measurement is needed it should feed one CSS variable, not a JS scroll computation.

4. **A second seam the nudge cannot fix.** `chair.css:631` clears the section before the bar by a fixed 112 px, sized for a one-line bar. In `after.png` the bar wraps to two rows and reads roughly 137 px tall (estimated from the 2x shot, not DOM-measured). If that holds, the last ~25 px of BRIEF (the `N more` verb or row three's verbs) sit under the bar even at maximum scroll, with no scroll range left. This is plausibly the Phase 3 observation in the story's Problem line ("title sat under the footer after the fold opened").

5. **Canvas standing.** The ratified round-six canvas shows boards at rest, never a scroll position, and its README at line 197 says footer clearance "is for the build to prove on the real face". A scroll nudge on Generate success changes no geometry, verb, or wording, so it is within the build's remit under UX-CANON without a new round, provided 1440 stays a no-op (1440 run: row h=44 at y=359, all owned, `20260924T065401Z`).

6. **Breakage variant: the timezone choice is time-of-day dependent.** `compute_window` (`monday_brief_service.py:147-160`) starts day two's lookback at today 17:00 local. The failure enters both briefs only if the run's local hour is at or after 17:00. Pacific/Honolulu works for runs between roughly 03:00 and 10:00 UTC (the retained run at 06:58Z is 20:58 HST). An evening run at 23:00 UTC lands at 13:00 HST and the variant silently proves nothing. `provenance.clock.tz` is recorded when TZ is set (`graph_walk.py:321`) and the hub inherits the environment (`graph_walk.py:1126`), so the mechanism is sound; the choice must be derived or asserted at run time.

7. **The 404 path is confirmed.** `observer.py:180-186` records any `BaseException` with its `code`; `_collect_breakage` selects `error IS NOT NULL` (`monday_brief_service.py:571-576`); ids are brief-scoped (story 03). The rig honours `expect_status: 404` on an `api` setup step without blocking (`graph_walk.py:2634-2636`).

8. **The variant is necessary.** The as-written day-two brief has `broke: []` (after trigger body), so the as-written run cannot pay story 03's obligation on its own. Day one's `changed` row titled `MeetingIntelService.run_intelligence` with raw JSON detail is the ledgered Tenet 4 wording debt, not a breakage.

**CONDITIONS**

- C1. The seam record states that the title and verbs are readable today and that the fence exceeds the ratified criterion; the move is justified by the wrap case.
- C2. Implement with `scroll-padding-bottom` plus `scrollIntoView({ block: "nearest" })`, instant, fired once after a successful Generate paints; no fixed viewport heights; 1440 face byte-identical. A measured JS route only if a rendered proof shows the CSS route fails in Chromium.
- C3. The fence measures the 393 bar height. If it exceeds 112 px, bind the `:nth-last-child(2)` clearance to the same variable in this seam. If not, record the measurement and drop finding 4.
- C4. The variant asserts at run time that the hub's local hour is after the business close (or selects the zone from the UTC hour), records `clock.tz`, and protocol-asserts `broke` non-empty in both briefs with distinct ids and one `source_ref`. The as-written case is unchanged.

**MISSED**

1. The end-of-scroll seam (finding 4): a verb unreachable at 393 that no nudge can reach.
2. The Honolulu choice going hollow on an evening run (finding 6).
3. The honest framing of the current shot (finding 1).
4. Smooth scrolling making the hit-test fence flaky (finding 3).
5. On the owner's real desk an Agents section can sit between BRIEF and the bar (`ChairHome.tsx:1383`), so BRIEF is not always the cleared child; the nudge still works, the clearance rule moves.

**TUESDAY:** Yes. On the retained 393 shot he can already read the decision and tap Ack; after the nudge one Generate leaves the whole row clear of the bar.

**UNKNOWN:** The bar height at 393 is estimated from the shot, not DOM-measured (no PIL, no browser in this check). I did not run the rig, any fence, or verify Chromium's `scroll-padding` behaviour inside a flex overflow container; the fence must prove it. Astra's session id for the check record is not in the tree I read.

## Astra response — 2026-09-24

Session `01a0d21a-e795-7861-9995-cf31f0eed09b`.

- C1 paid: README and seam-plan distinguish covered bottom padding from the
  readable current title/verbs. The stronger whole-row fence is retained.
- C2 paid with native instant nearest scrolling, once after successful
  Generate. The direct rendered transition fence exposed a further missing
  89 px of existing dock padding; the CSS now reserves it with the dock's
  existing tokens. It failed at real hit ownership before this correction
  and on archived main, then passed (`red-clearance-final.log`,
  `red-clearance-main.log`, `green-clearance.log` in the rows record).
  No product JS scroll delta was added. The 1440 row geometry is unchanged.
- C3 paid: actual capture bar 138 px, final-child clearance 138 px. Native
  scroll padding is 227 px including the existing dock band. Retained
  `arrival_clearance` measurements carry the evidence.
- C4 paid: the separately named variant selects a fixed-offset process TZ
  from the current UTC hour and asserts an evening before running. The real
  404 producer enters both briefs. `verify_closure.py` checks non-empty
  breakage rows, equal source references, different scoped item ids and
  unchanged day-one DB rows/shelf. The as-written interaction is unchanged.

Closing evidence is submitted separately for counsel on built. The owner's
sitting and full-suite PR CI remain outside these claims.
