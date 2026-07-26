# Evidence - HS-104-04

- **Story:** HS-104-04 - PR receipts — paying the candidate-Y deferral
- **Status:** done
- **Date:** 2026-07-26

## The live walk — real gh, real PRs, the real desk

Staged hub (`uat.stage --recipe seeded-desk`, port 8789); THIS repo
registered as a delivery source through the product's own
`POST /api/delivery/sources`; a manual Work attempt attached for
HS-104-03. Screenshots in assets/story-04/, read before the flip.

1. **The real rows.** `POST /api/delivery/prs/refresh` ran ONE
   batched `gh pr list` and served 50 receipts: `#377 open ·
   ci=pending · heuristic ("branch name resembles HS-104-03 (name
   match only)")`, `#378 draft · exact ("branch matches a registered
   worktree")`, every merged PR quiet and unattributed — all three
   epistemic labels visibly distinct on glass
   (pr-rows-desktop-1440.png, pr-rows-phone-393.png), needs-you
   ordering holding (open above draft above merged), `observed
   2026-07-26T18:44:27Z` printed on the section.
2. **See diff, honestly.** #378's base SHA (origin/main's tip) was
   not in the local checkout: the verb rendered the honest absence
   with the explicit "Fetch them (network)" offer
   (pr-diff-absent-desktop-1440.png); the fetch — the one named
   git-network act — then rendered the REAL local `base...head`
   diff inline (pr-diff-desktop-1440.png).
3. **The stale path, real network yank.** Wi-Fi off →
   refresh → `stale | gh exited 1 | last observed
   2026-07-26T18:44:27Z | rows retained: 50` — never a silent
   freeze; Wi-Fi on → refresh → `live` with a fresh observed_at.
   (Earlier, the isolated run-home's unauthenticated gh degraded to
   `unavailable | gh exited 4` — the typed-failure path seen live
   too.)
4. **Poll economy.** Reads never shell (unit-pinned); the cadence is
   per-source `pr_refresh_seconds`, explicitly set, absent by
   default; the egress census pins `gh` to `pr_receipts.py` alone.

## Proof

### Captured run — 2026-07-26T18:46:20Z

- **Command:** `uv run pytest -q tests/unit/test_pr_receipts.py tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c8b3bdd9b56f6a8f07f017a7b26c9444cc154509

```text
................                                                         [100%]
16 passed in 1.03s
```
