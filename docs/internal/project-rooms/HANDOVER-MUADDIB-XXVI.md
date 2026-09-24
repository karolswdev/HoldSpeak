# Muad'Dib handover XXVI — 2026-09-24, Phase 4 The Morning closed; Phase 5 at the owner's door

Read with `docs/internal/TWO-BRAINS.md`, `pm/roadmap/holdspeak-philo/README.md`, `pm/roadmap/holdspeak-philo/phase-4-the-morning/final-summary.md`, `pm/roadmap/holdspeak-philo/PHASE-5-CHARTER-DRAFT.md`. XXV (2026-09-23) holds the day before.

## Where the tree is

- **Phase 4 The Morning: CLOSED** (this commit). Four stories, both brains on every one: 01 Generate always reachable (#625, Muad'Dib; two Astra rounds on built — the active atlas pinned retired strings, then stale generated refs), 02 the decision in the visible rows (#626, Astra; Muad'Dib's counsel: schema snapshot, the authorization-order ruling, canvas item 7), 03 breakage ids never collide (#624, Muad'Dib; Astra: scope amendment, the original producer identified), 04 the triaged headline (#627, Astra; canvas first, ratified on board 7c; Muad'Dib's counsel: the headline sentence ledgered). Exit 1 evidence: one Generate → the decision row 1, unobscured, both widths, with and without a breakage (`assets/story-02-shots/20260924T0725–0728Z`). The owner waived the sitting ("no sitting reqd..."): exits closed accepted-not-observed; Phase 3's sitting likewise.
- **Phase 3:** closed; exit 1 closed against Phase 4; exit 3 waived. Usefulness stays PARTIAL as measured (ASR is the bottleneck).
- **The library** changed under the canon (12 px floor on section labels and chips desk-wide; containment; scoped chip truncation; chip tooltip = label; 24 floor allowances removed). 71 under-12 px lines remain ledgered in the story 01 canvas README.
- **Phase 5 The One Service Layer: PARKED DRAFT r2** — seeded by the owner's ruling "things have to flow through services"; Astra r1 BOUNCE mostly paid; §12 carries the rest. NOT chartered. The owner's D1–D3 (pilot scope; the stdio proxy; his access path for the sitting) open the charter.
- **Main CI:** the three heavy jobs (Unit/E2E/Integration) take over an hour; today's merges went on the other brain's lifted verdict + green scoped fences + the fast jobs, per the owner's ruling. The inherited baseline: 44 failures at `497d90f3` (27 = rig calibration browser launch on the Unit runner; 4 = A4's receipt lines vs the HS-201-12 fence; the rest 393 glass + pre-fix Phase 3 fences). Compare any new red against it before believing it.

## Next session, in order

1. The owner's word on Phase 5 D1–D3. Then Astra r2 check of the draft → charter (folder, stories, status) → his ratification → lanes per the draft's four stories.
2. Ledger sweep (tree tasks, no phase): the baseline comparator keyed on id + path (`scripts/check_web_baseline.py`); the pullout section-label 10 px override (`window-chrome.css:207-216`); the thought-write atlas case's unsupported `route_failure` boundary (`atlas.json:6116`); the stale atlas prose (`:5023`, `:5211`, `atlas-phase3.json:2522`); the A4 receipt lines vs the HS-201-12 fence; the producer's headline sentence and breakage titles (Tenet 4).
3. The four Constitution amendments (Phase 201) still unruled — his.

## Laws learned (add to briefs)

- Never symlink `node_modules` into a worktree or an archive and then run `uv sync`/`uv run`: the build hook's `npm ci` follows the link and wipes the target (three incidents in one day). Real `npm ci --ignore-scripts` in the copy, or read the retained red.
- The rig's contract book is a fence: fence the active atlas against retired strings (`test_philo4_01_atlas_contracts.py` is the pattern).
- Canvas fixtures come from the real producer; a board that contradicts the producer is corrected on the record.
- A global library truncation hides disclosures; truncate only where the full value is visibly elsewhere.
- Measure every visible text node; a chip's default tooltip can lie.
- Astra's `claude -p` checks are the canonical Astra→Muad'Dib channel; this session's counsel is still recorded separately, and only the orchestrating session merges.
- A worker's task-output file is a JSONL transcript, never the report; copy check text from the result, not the file.
