# Check — Astra, 2026-09-24, on built: PHILO-4-01 (PR #625 @ 8ff1e0a8)

VERDICT: BOUNCE — do not merge #625 at `8ff1e0a8`. The Generate implementation is sound; the active atlas contracts and generated graph need correction.

FINDINGS:

1. **Blocking: three executable atlas cases still assert retired behavior.** Empty generation and reload expect `Nothing material changed.` at `docs/internal/philo/graph/atlas.json:4934` and `docs/internal/philo/graph/atlas.json:5003`. I generated and reloaded an empty brief through the real service, then evaluated those actual predicates: both returned false against `No changes`. Generation failure still observes `.write-receipt-label` and expects `Generate brief FAILED` at `docs/internal/philo/graph/atlas.json:5652`, although the implementation correctly retired that channel. This repeats scar 1. **Tenets 3/4; Articles VI.3 and IX.3.** Sealed passes and earlier observations may retain historical words; the active atlas may not.

2. **Blocking: graph consistency is red.** `philo_graph_reference.py --check` exits 1 with `graph join drift`. The difference is currently the atlas input hash; substituting the base atlas in memory restores exact agreement with the committed graph. This is branch-introduced drift. Atlas claims also need correction: the empty-face claim still names the old sentence at `docs/internal/philo/graph/atlas.json:8290`, and the quiet/reload state points to the populated branch at `docs/internal/philo/graph/atlas.json:8334`. Passing symbol-anchor tests does not establish those claims. **Tenet 3; Article IX.3.**

3. **The face follows story 01’s ratified behavior.** `web/src/desk/chair/ChairHome.tsx:695` supplies the badge and library Generate Button to all five branches, disabled during reads/generation. The label stays unchanged; generating/failure use the 12 px receipt species. Generation failure has no Retry; read failure retains it. Captions and successful receipts remain in the populated and quiet branches. No raw button was introduced. The A3 reversals and write-recovery rewrite are lawful consequences of `pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-canvas/README.md:124`, not weakened requirements. The wording fence changed with the label.

4. **The scoped fences and triage evidence hold.** Retained logs show vitest **13 failed / 7 passed**, including the `docs/internal/philo/phase-4/generate/prefix-red-vitest.txt:229`, and pytest **2 failed / 17 passed**. My reruns passed **398 web tests and 134 Python tests**, including atlas tests; `dw check holdspeak-philo` passes. The `tests/unit/test_philo_4_01_generate.py:56` uses real generation, persistence and shelf methods with a stubbed collector. Passing before the fix is lawful: it verifies an unchanged invariant. The rendered test independently forbids `/shelf` calls. Calibration’s two string changes are lawful fixture maintenance, but prove no live atlas case.

5. **The retained walks support the narrow story claim.** Both runs have isolated HOME/DB paths, one terminal Generate click, POST 200, a new next-day brief ID containing the decision, and no `/shelf` reference. Both correctly remain **FAIL** because the decision is outside the three rendered rows. The `pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/20260924T053019Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-1440/after.png` shows Generate, caption, receipt and `1 more`. The `pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/20260924T053350Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-393/after.png` shows Generate reachable, but lower content covered by fixed chrome. Story 02 remains necessary; this is not a completed morning.

CONDITIONS:

Correct the three active case contracts and stale claims, add fences that exercise those actual contracts, then regenerate the graph and obtain a green `--check`. Retain historical passes unchanged. Supply real atlas runs for the corrected cases at both widths; calibration alone does not discharge them. Record this check beside the artifact before merge.

MISSED:

1. The distinction between sealed historical JSON and the executable atlas allowed the exact wording-fence scar to recur.
2. At 393, `in_viewport: true` coexists with `all_owned: false`: the capture bar/dock cover ledger content. Story 02 must prove unobscured readability, not rectangle containment alone. `pm/roadmap/holdspeak-philo/phase-4-the-morning/assets/story-01-shots/20260924T053350Z-case.closure.chain.s5_next_day_brief_has_it-muaddib-393/observation.json:2250`.
3. The canvas README still opens “UNRATIFIED”; the phase status records ratification. Update the current status without rewriting its historical rounds.

TUESDAY: He can Generate without acknowledging yesterday’s rows; he still cannot read the new decision directly in the morning view.

UNKNOWN: The claimed **422-test** run is absent from the named evidence pack. Full-suite/CI results and built failure-state geometry were not independently verified. Retained walks identify base revision `1c39294c`, dirty; their capture index is the base tree, so it does not bind the unstaged build exactly to HEAD. No rig or real-desk run performed; the worktree remains unchanged.