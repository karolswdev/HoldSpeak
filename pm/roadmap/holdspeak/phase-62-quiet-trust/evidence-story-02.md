# Evidence — HS-62-02: The sweep

**Date:** 2026-06-12
**Verdict:** done. Every reassurance tail in the operational web UI is cut
or shortened to its functional core; only the dedicated trust surfaces and
the one onboarding pitch line still say it, once.

## What changed (nine files)

- `history.astro`: draft notes → "Send to Slack creates a proposal;
  approve it below." / "Preview and copy only."; file-issue loop-note →
  "Creates a proposal; approve it below (execution needs actuators
  enabled)."; proposal-note → "Review the preview, then approve or
  reject."; guard copy → "Approving sends this message to Slack." /
  "Approving records the decision; execution is a separate step.";
  import-notes lost the "Everything stays on this machine." tail (the
  functional "source file isn't kept" truth stays).
- `index.astro` (dashboard): the rail note shortened; the guard copy made
  per-target like history — which also fixed a real lie: the dashboard
  guard still said "only records your decision", untrue for slack since
  HS-61.
- `history-app.js` / `dashboard-app.js`: flashes shortened ("Proposal
  approved." / "...created — approve it below."); the dashboard toast now
  says "Approved — sent." when the decision response reports `executed`.
- `welcome.astro`: the wizard rail foot is "Local · 127.0.0.1" (it
  repeated on every step).
- `settings.astro`: the lead lost its "nothing here leaves your machine
  unless…" clause (the Cloud section's targeted warn-note stays — that
  one is behavioral and placed where it matters); the wake copy lost
  "after that everything runs locally"; the Qlippy note lost "— nothing
  runs without your click"; the Slack hint shrank to three functional
  clauses.
- `LocalPill.astro`: the tooltip is now "Everything stays on this
  machine." (was a 25-word inventory sentence).
- `ContextSection.astro`: "The drafting stays on your machine." deleted.

## What deliberately remains (the explain-once set)

- The TrustChip surfaces (`trust-view.js`, the `AppLayout` popover
  footer, the LocalPill tooltip): one short line each — explaining trust
  is that surface's entire job.
- `welcome.astro` step lead: the single first-run pitch sentence.
- Behavioral warnings untouched: the Cloud-section warn-note, the wake
  type-action false-detection warning, `commands.astro` shell danger
  copy, the journal's "Preview only" state string.
- Two code comments (not user-facing).

The post-sweep residue grep ships above as the audit; it returns exactly
that set.

## Proof

- Locks updated in place: `test_history_slack_surfaces.py` (notes, flash,
  per-target guard on BOTH pages, settings copy),
  `test_web_history_import_ui.py`, `test_presence_mascot_gate.py`.
- `cd web && npm run build` clean (13 pages); 0 `_built/` tracked.
- Full suite: **2768 passed, 17 skipped**.
