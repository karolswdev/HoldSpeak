# Phase 146 — Multiple Calendars — final summary

**Verdict:** complete (7/7). Close counsel (opus):
**RATIFY-WITH-CONCERNS** — one should-fix (the snapshot timezone bug,
caught by the counsel READING the delivered shots against each other)
FIXED in-round with photographic proof, its fix exposing and killing a
second latent ICS-offset defect; two factless strings + one docs
cosmetic FIXED; two structural items ledgered. All seven judgment-call
clusters ruled lawful. Full verdict + dispositions in the
`current-phase-status.md` decision log.

## What shipped

One ICS subscription became many, and a locked-down work calendar
became importable without ever touching its server:

1. **Multi-source plumbing (01).** `CalendarSource {id, label, url,
   enabled}` with a one-shot minimal migration; per-source last-good
   projections (a broken calendar never wipes a healthy one);
   end-of-tick orphan cleanup; per-source revision namespaces.
2. **The sources wire (02).** `{calendar: {sources: [...]}}` with
   per-entry refusals that NAME the offending entry; the
   `_calendar_sources` per-source egress fact.
3. **The list editor (03).** The joy surface: + ADD SOURCE, label/
   url/on rows with mics, in-world REMOVE?, per-source egress chips,
   an empty state that leads a cold owner to one obvious act.
4. **Rail provenance (04).** Snug mono source chips ONLY when >1
   calendar; label → hostname → LOCAL stamped server-side; a
   cross-feed duplicate shows twice, distinguishable by chip — no
   silent merge, ever.
5. **The calendar book (06, owner-ordered).** A real USER_GUIDE
   Calendars section, SECURITY's two-row egress truth, an
   ARCHITECTURE pipeline section, entry points, and a doc-drift
   retirement fence on the singular-subscription vocabulary.
6. **The Calendar Snapshot adapter (07, owner-ruled fold-in).**
   Screenshot → vision extraction through the router (routed when
   assigned; ask-template direct dispatch when not; no vision model
   = a NAMED refusal) → the anchor-gated review window (the week is
   never silently guessed; CANCEL writes nothing) → a generated
   `.ics` that rides the SAME bounded parser as any hostile feed →
   the rail under O365 SNAPSHOT. Routes 538→540.

## Proof

- **Cold walk** (`scripts/door_walk_hs144.py`, leg 5 rewritten for
  the sources wire): 7/7 PASS, run twice by the orchestrator.
- **Close sweep**: 12 failed / 6796 passed / 53 skipped in 8:29 —
  eleven names baseline-exact; the twelfth is the handover-NAMED
  hs143 assignments s5 flake sibling (glass-under-load family),
  serial ×2 green. **Baseline-exact, zero branch-new.** Stamped
  `dw evidence capture` pair in evidence-story-05.
- **Glass, all orchestrator-eyeballed** (`assets/story-0304-shots/`,
  `assets/story-07-shots/`): the editor empty/one/two-sources at both
  widths; the rail chips two-sources/one-source; the review window
  anchored and editable at both widths; the final rail exhibit
  (Team sync [WORK] beside Glass Standup [O365 SNAPSHOT]).
- Per-story focused closes: 66 (01), 37 (02), 12+16 (03), 14+7+20+
  9e2e+2e2e+walk (04), 25-guard+greps (06), 23+8+2+5+censuses (07).

## The round-by-round honesty ledger

- Story 04: the orchestrator's eye caught the provenance chip
  stretching full-row, and the shot rig photographing a window OVER
  the chair while assertions passed behind it — both fixed, both
  recorded.
- Story 07 took TWO rounds: round 1 left production extraction a
  stub (a real drop would refuse as "unreadable"); the flip was
  refused and round 2 wired the real dispatch with an
  engine-factory-level proof.
- Three code-law censuses each caught the new vision seam and forced
  deliberate registrations (routing-census adopter; one-path vision
  leaf 102→103; capability-census entrance with capability + owner).
- Story 06's baseline-guard check surfaced a branch-new factless
  failure string sheltered inside a baseline failure — fixed to
  carry the four failure facts.
- Cross-arc: the routing census drifted on hot files four times; all
  remapped 1:1 with attributes and classifications byte-unchanged.

## Ledger (carried)

- The Phase 144/145 ledgers stand. New ledger items from the close
  counsel: the IMPORT SCREENSHOT button's swallowed 422 refusals
  (narrow surface); the direct-dispatch fallback not pre-filtering
  vision-capable profiles (named-refusal failure mode).
- Backlog candidates unchanged; AE (the snapshot adapter) GRADUATED
  into HS-146-07 and shipped.

## Owner gates (open)

1. Shot verdicts on the phase exhibit — a flinch is a redo.
2. The merge word — one PR of `feat/hs146-multi-calendar` → main.
   CI is dead; local verification is the record.
