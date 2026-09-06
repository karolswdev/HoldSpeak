# HS-176-04 — The voice law

- **Project:** holdspeak
- **Phase:** 176
- **Status:** in-progress
- **Depends on:** HS-176-01
- **Unblocks:** HS-176-05
- **Owner:** unassigned

## Problem

Article IV.1: "Every text input can be spoken into. The mic is an
affordance of the OS, not of any one feature." UX-CANON.md rule B
lists MicButton as a species that lives on every text input. The
library species already carry it by default (StringGadget
gadgets.tsx:243, PadGadget gadgets.tsx:315, EditInPlace
Surface.tsx:1070) and 30 standalone MicButton placements sit across
26 faces. The census as of main `7a47904e`
(assets/mic-census-176.md) finds the law still unpaid at 17 sites:
8 raw `<input>`/`<textarea>` elements that take dictatable text with
no mic, and 9 gadget instances that opt out with `mic={false}` for no
reason (the onboarding dictation well among them). The scanner's
voice-law rule `mic` (scripts/ux_canon_scan.py:100) is file-scoped,
gated on face classification, and voided by a single opt-out per
file, so it cannot see the gap; its ceiling is 6.

## Scope

- In:
  - The census (assets/mic-census-176.md) is the ledger: every raw
    element and every opt-out with its disposition
    (ADD-MICBUTTON / MIGRATE-TO-GADGET / RESTORE-MIC / ALLOWLIST /
    PARK).
  - The 8 uncovered raw elements gain a mic following the placement
    rule from the HS-176-01 artboard (migrate to the gadget where the
    layout allows; an explicit MicButton beside it where it does not).
  - The 9 unjustified `mic={false}` opt-outs are restored.
  - The 4 justified opt-outs (a cron expression, two HH:MM fields, a
    glyph field) and the 19 non-text controls (password, file, radio,
    checkbox, number, range, date/time, two dead primitives) are named
    in the scanner's allowlist with reasons, as the A1 raw-button
    allowlist does today.
  - 170's four orphaned dictation components (UtteranceWell,
    InstrumentStrip, AimRow, ResultPanel: not in the barrel, zero
    importers) are parked under `_parked/`, never deleted.
  - The scanner's `mic` rule is extended to per-element with the named
    allowlist, un-gated from face classification; the ceiling drops to
    0; the ratchet prevents regression.
- Out:
  - MicButton on non-text controls (buttons, toggles, pickers).
  - Voice commands or wake-word integration (separate capabilities).
  - A new rule id (the rule is `mic`; `A14` is not added).

## Acceptance criteria

- [ ] Every dictatable text input across web/src renders MicButton;
      the census's after-count of uncovered sites is 0 (Article IV.1).
- [ ] The 9 opt-outs are restored; the 4 justified ones and the 19
      non-text controls are allowlisted by name with a reason.
- [ ] The four orphans are parked, not deleted (owner ruling).
- [ ] The scanner's `mic` rule counts per element with the allowlist;
      the ceiling is 0; the ratchet test passes.
- [ ] The face matches the HS-176-01 artboard's placement rule per
      species.
- [ ] Every MicButton placed is click-to-toggle (owner ruling; no
      hold).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_ux_canon_ratchet.py`
  and the scanner's own tests (`-k ux_canon`).
  - The `mic` rule reports per element; an allowlisted element with a
    reason is not a violation; an opt-out outside the allowlist is.
- Web unit: `uv run python scripts/check_web_baseline.py --run` (zero
  branch-new).
- Integration: `python scripts/ux_canon_scan.py` after the migration
  reports `mic: 0`.
- Manual: walk five surfaces at 1440 + 393; every visible text input
  has MicButton.

## Notes / open questions

- The MicButton placement for StringGadget inside a dense LedgerRow:
  the artboard decides whether the mic is inside the gadget (compact)
  or beside it (standard). Propose inside (consistent with the
  existing gadgets.tsx placement); the owner decides on the canvas.
- The eight raw sites: LedgerFilter.tsx:112, ThreadComposer.tsx:1060,
  ThreadPullout.tsx:211 and :1634, ThoughtContextPicker.tsx:191,
  ThoughtDocumentPane.tsx:90, ThoughtWorkspaceWindow.tsx:415,
  NotePullout.tsx:409 (line numbers as of `7a47904e`; the census
  file is the ledger).
