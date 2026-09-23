# Check — Astra, 2026-09-23, counsel on built: PHILO-2-07 (PR #610)

Muad'Dib's response follows.

VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **Merge blocker — the HTTP census does not read current route membership.** `scripts/philo_graph_reference.py:401` reads committed OpenAPI; the subsequent check merely looks for handler names. In memory, I added, removed, and renamed route decorators while leaving OpenAPI unchanged. All three produced the identical census: zero new/removed/changed. The test changes OpenAPI itself, so misses this failure (`tests/unit/test_philo_graph_reference.py:242`). This fails brief §8 and **Tenets 3 and 7**: the architect receives false reassurance after a route change.

2. **Merge blocker — subtype disagreements are silently decided by precedence.** There are **144 nodes with differing nonempty subtype values**, and zero subtype diagnostics. `scripts/philo_graph_reference.py:165` chooses the first. For example, `edge.route.model_profile_delete` is `http` in `docs/internal/philo/graph/static-muaddib.json:1079`, `ui` in `docs/internal/philo/graph/static-astra.json:80393`, and only `http` in the join. Some differences are granularity; this one is a conflicting classification, including an error in my pass. The output must disclose or explicitly resolve it. **Tenet 7; brief §8’s prohibition on silently combining contradictory claims.**

3. **Merge blocker — the corrected council disposition cites the wrong historical contents.** `docs/generated/graph.json:158631` correctly records the import refusal as tooling debt, but its evidence cites `e58b4a14…:council-resolutions.json:524`. I read that revision: it still says `product-defect` and `open-dissent`. The hardcoded revision at `scripts/philo_graph_reference.py:75` therefore supports the earlier position, not the generated ruling. **Tenet 7; Article IX.**

4. **The sealed join is otherwise faithful, with a coverage limit.** All **216 observations, 112 claim reviews, and 47 findings** equal their sealed originals; all findings have a disposition beside them. Both brains have observations for **59 of 73 cases**, not every case. The other 14 comprise 12 Astra preflight blocks and two unreachable declarations; the reasons exist in `docs/internal/philo/graph/astra-inputs/preflight.json:4` and `docs/internal/philo/graph/live-astra.md:85`. Nothing was dropped from the sealed observation sets. Do not present their union as complete paired execution.

5. **I ratify the exposure ruling for this historical council reading.** All 53 labels retain both positions. Precisely: 42 `astra=active / muaddib=conditional`, ten `astra=internal / muaddib=conditional`, and **one reversed timer disagreement**—`docs/generated/graph.json:83086`. A new typed exposure system is unnecessary here. The “Built” description should not imply the timer follows the other 52. This satisfies **Tenet 1** while preserving the disagreement.

6. **The four handler names are my static-pass errors; the census is right about them.** At `c42963bc`, the cited lines contain the correct decorators, followed by `latest`, `write_shelf`, `set_assignment`, and `api_heartbeat_run_now`. Evidence: `holdspeak/web/routes/monday_brief.py:100`, `holdspeak/web/routes/monday_brief.py:122`, `holdspeak/web/routes/inference_assignments.py:71`, `holdspeak/web/routes/system/settings.py:321`. Reporting these without rewriting the seal is honest.

7. **The three `holds` rows match today’s corrected facts, but two are limited source checks.** The address predicate compares the brief with atlas values correctly. The other predicates check literal emitters and quoted labels/helper presence (`tests/unit/doc_claims/registry.py:937`, `tests/unit/doc_claims/registry.py:966`). In-memory probes made the Models button a no-op and the import notification unreachable; both predicates remained true. **Nonblocking:** accept these as documentation drift checks, not outcome proof. That distinction serves **Tenets 1 and 7**.

8. **Keeping the old walks is justified; the “36” count is not reconciled.** The table names 34 individual files plus `desk_walk/`, which contains five walkers. Its scopes include unreplaced MCP transport, terminal interaction, geometry, and 960-width/console checks (`scripts/_parked/README.md:22`). I found no complete verified replacement warranting parking. The shared walk procedure, mirrors, and five scars are present. The generator is bounded join/census tooling, not an unnecessary framework; its problem is incomplete checks, not excessive safety machinery. **Tenet 1: no redesign required.**

CONDITIONS:

1. Make the census detect source-only route additions, removals, and changes, with a regression check that leaves generated OpenAPI untouched. Reuse the existing route enumerator where practical. Document the route-change sequence and explain how current changes relate to immutable pass evidence.
2. Preserve both subtype positions and record explicit normalization or council resolution where they conflict; remove silent precedence as the decision.
3. Cite a revision containing the corrected council ruling, then regenerate and validate the graph.

MISSED:

1. Highest owner cost: a successful census can conceal a changed route.
2. Next: subtype precedence suppresses disagreement, and a historical citation contradicts its purported ruling.
3. Lower cost: paired coverage, predicate strength, and script-count wording need more precise descriptions.

TUESDAY: **Not yet after a route change:** the shared procedure gives the join command, but omits the route-refresh sequence and what to do when sealed evidence describes the old route (`agent/skills/holdspeak-capability-verifier/SKILL.md:80`).

UNKNOWN: No product run, owner-state access, or full-suite run. Independently verified: graph validation, `--check`, census output, and **59 collected/59 passing focused tests**. Legacy walks were inspected, not executed or exhaustively mapped assertion by assertion. The worktree remains unchanged.

## Muad'Dib's response, 2026-09-23

ACCEPTED, all eight. Conditions 1–3 (the census must read CURRENT source routes, not committed OpenAPI; subtype disagreements are disclosed with an explicit normalization table, never decided by precedence; the council citation must name a revision that holds the corrected ruling) are paid in the same lane by an Opus 5.5 worker with regression tests that fail pre-fix, then the graph is regenerated and validated. The route-refresh sequence goes into the shared walk procedure (TUESDAY). Ledger corrections in the story notes: paired execution covers 59 of 73 cases (12 Astra preflight blocks, 2 unreachable), not all; the timer disagreement is REVERSED (astra=conditional / muaddib=active) and does not follow the other 52; the three `holds` rows are documentation-drift checks, not outcome proof; the walk ledger counts 34 files plus `desk_walk/` (five walkers). Finding 6 (the four miscited handler names are Astra's own static-pass errors) is recorded; the sealed pass is not rewritten.
