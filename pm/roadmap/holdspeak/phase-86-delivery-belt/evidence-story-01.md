# Evidence — HS-86-01 — The clean tree: fix the 31 triaged desyncs

- **Shipped:** 2026-07-07
- **Commit:** (this commit)
- **Owner:** agent (Claude), owner-directed

## What was fixed (the full triage, consumed)

Source list: delivery-workbench `phase-16-flagship-tree/evidence-story-04.md`
(the flagship dogfood triage). Every item:

1. **14 retrospective final summaries** — holdspeak phases 0, 1, 2, 3,
   4, 5, 6, 7, 8, 9, 10, 11, 12, 13. Each opens with the label
   *"Retrospective closeout (2026-07-07), reconstructed from evidence
   files + git history"* and claims nothing beyond the phase's own
   trail. Generation verified story/evidence pairing per phase — all
   14 phases have full 1:1 pairing (2..16 stories each).
2. **`phase-15-out-and-about/current-phase-status.md` backfilled** —
   goal + the Phase-25 gate recorded; zero stories invented.
3. **phase-4 `HS-4-06` evidence cell** linked a directory (the WFS
   evidence bundle); now links the bundle's `99_phase_summary.md`.
4. **phase-24 `HS-24-03/04/05`** — dash placeholders became real
   backlog story stubs (content from the phase doc's own
   descriptions, hardware-gating recorded), rows now link them.
5. **mobile phase-14 `HSM-14-02/04/05/06`** — bare `story-NN` cells
   became real story files (02 in-progress per its row; 04/05/06
   backlog), rows now link them.
6. **mobile phase-15 story-08/09/10 headers** — stale `backlog` /
   `in-progress` headers now lead with the table's own truth
   (`built + Simulator-proven …`), owner-gated walk beats preserved
   verbatim.
7. **mobile phase-5 `HSM-5-02`** — the TABLE was the stale side: the
   story header records the Mode A run on the iPad Air M4,
   owner-witnessed 2026-06-20. Cell reconciled to done with the
   provenance note.
8. **`docs/evidence/phase-wfs-01/20260426-1537` unreadable** — was
   the directory-link case in (3); no file content touched.

Upstream assist (delivery-workbench PR #2, follow-up commit):
`normalize_status` now reads only the decoration-cut head — the two
phase-15 narrative cells whose tails contained accidental keywords
("…saga closed…", "…never shipped)") stopped reading as done, which
resolved their two spurious evidence demands without touching the
cells' recorded receipts.

## Verification artifacts

```text
$ ~/dev/reusable-processes/pmo-roadmap/bin/dw --root . check
dw check: ok        (exit 0; was 397 errors on v1.12.0, 31 after upstream phase 16)
```

Full suite (docs-only change; doc-drift guards are the relevant
tests):

```text
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
3299 passed, 37 skipped, 2 warnings in 257.44s (0:04:17)
```

## Acceptance criteria — re-checked

- [x] `dw check` exits 0 with zero ERROR lines — output above.
- [x] Every new final summary carries the retrospective label and
      links only artifacts that exist (generator asserted 1:1
      story/evidence pairing before writing).
- [x] `dw state` reports current phase 85/closed for holdspeak (the
      README pointer's phase; 86 pointer move happens at this
      phase's own cadence), counts unchanged except corrected rows.
- [x] Full suite green — appended below.

## Deviations from plan

The story expected some drifts to resolve by editing headers only;
two resolved upstream instead (the head-only normalization fix) and
one resolved by correcting the TABLE (HSM-5-02, where the header was
the truthful side). Both deviations recorded above.

## Follow-ups

None — HS-86-02 is the next story by design.
