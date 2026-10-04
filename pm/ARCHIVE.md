# The evidence archive

Owner ruling 2026-10-04: the evidence leaves the working tree. Nothing is
deleted. Every file is on the archive branch and the tag.

- Branch: `archive/evidence-2026-10-04` (on `origin`)
- Tag: `evidence-2026-10-04`
- Both point at commit `91dca1ed9`, the last `main` that held the evidence.
- The list of every file that moved: `pm/archive-manifest.txt` (16,389 paths).
- Manifest SHA-256: `90f9a67642392e41305539842843672274affb39eabce8175e22405de79ef753`
  (`tests/unit/test_evidence_archive.py` checks the hash, that no entry is in
  the tree, and that every entry is on the tag).

## Get a file back

Read one file:

    git show archive/evidence-2026-10-04:<path>

Put one file or one directory back in your tree:

    git checkout archive/evidence-2026-10-04 -- <path>

If the branch is not local: `git fetch origin archive/evidence-2026-10-04:archive/evidence-2026-10-04`.
Find a path: `grep <word> pm/archive-manifest.txt`.

## The numbers

| | Files | MB |
|---|---|---|
| Tracked tree before | 26,990 | 2,517.3 |
| Tracked tree after | 10,612 | 171.5 |
| Moved to the archive | 16,389 | 2,348.1 |

## What moved

| Group | Files | MB |
|---|---|---|
| `pm/**/assets/`: shots and run dumps (PNG, JPG, JSON, JSONL, logs, HTML canvases) | 13,482 | 1,562.2 |
| `pm/roadmap/holdspeak-mobile`: screenshots and assets (dormant track) | 204 | 409.2 |
| `pm/**/attempts/`: failed tries | 830 | 95.1 |
| `pm/`: other `screenshots/` and `evidence/` directories, loose images | 396 | 92.2 |
| `docs/internal/philo/phase-*`: shots, JSON, logs, HTML canvases | 854 | 70.2 |
| `pm/`: SQLite proof databases | 17 | 61.8 |
| `docs/internal/surface-inventory-2026-09-20`: shots, CSV, JSON | 402 | 41.0 |
| `docs/internal/philo/graph`: observation shots | 206 | 16.6 |

## What stays, and why

- `pm/STATUS.md`, this file, the manifest.
- All Markdown under `pm/`: story files, `current-phase-status.md`,
  `final-summary.md`, READMEs, design docs, settled designs and plans in
  `assets/`. Small text; tests and docs cite it.
- `evidence-story-*.md` (1,462 files, 10.7 MB). The product reads them: the
  Roadmap window shows `hasEvidence` for each story
  (`holdspeak/web/routes/roadmaps.py`), the pull-request review reads the
  story evidence (`holdspeak/delivery/pr_receipts.py`), and `dw check`
  reports a done story with no evidence file as an error.
- Source code under `pm/**/assets/` (`harness/` directories, proof programs
  in `.py` and `.sh`). Live tests import some of it.
- `pm/roadmap/holdspeak-mobile/contracts/` (a CI workflow validates it).
- The two real-send ledgers (`phase-10-the-channels/assets/story-06-real-sends.json`,
  `phase-11-more-documents-on-the-channels/assets/story-07-real-sends.json`).
  They are operational inputs: `scripts/philo10_send_job.py` and
  `scripts/philo11_send_job.py` read them and refuse a second real send.
- `docs/internal/philo`: all Markdown and text, the graph and atlas JSON
  (the doc generators and the test rig read them), `visuals/`, two fixtures
  that live tests read (`phase-5/residual-set.json`,
  `phase-4/headline/fixture.json`), and six observation shots that the graph
  cites as claim evidence.

## Known effects

- A Markdown file that stays can link a shot that moved. The link check
  (`tests/unit/test_doc_drift_guard.py`) accepts a link whose target is in
  the manifest. All other dangling links still fail.
- `dw check` on the command line reports about 120 more errors ("broken asset
  reference", "broken evidence link") for old evidence files that name shots
  that moved. The Roadmap window does not show them: the route
  (`holdspeak/web/routes/roadmaps.py`) drops a broken link whose target is in
  the manifest. A link to a file that is in no list is still an issue.
- Tests that read archived evidence are parked in `tests/_parked/history/`
  (see its README). They do not run.
- Old scripts under `scripts/` that read archived run directories need the
  files back first (`git checkout archive/evidence-2026-10-04 -- <path>`).

## New evidence

Tests write shots to `.tmp/evidence-shots/` (`tests/_evidence.py`).
`.gitignore` keeps images, databases and `attempts/` out of `pm/`.
