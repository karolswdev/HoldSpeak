# Sol counsel — Phase 130 "One Truth" CLOSE (2026-08-09)

Sol's acceptance pass on the FINISHED phase (distinct from the charter counsel
in SOL-COUNSEL.md). Verdict: **ratify with named reservations — one blocking.**
All three findings were adopted and resolved before merge.

## Sol's findings and their resolution

1. **[BLOCKING] Stale API-surface manifest.** The DecisionRecord rename added
   `/api/decision-records{,/search,/review,…}` routes but `docs/api-surface.json`
   / `docs/API_SURFACE.md` were never regenerated, so `test_api_surface` fails on
   HEAD — partly 130-caused drift that the ledger had homed under
   "still-inherited." **RESOLVED:** ran `scripts/gen_api_surface.py` (436 routes,
   decision-records now present); `test_api_surface` → 5 passed. The failure is
   reclassified **repaired-by-130** (not inherited); the ledger and final-summary
   are corrected accordingly. Sol was right — this was the "alias dies in the
   phase that establishes it" principle left half-done.

2. **[SITTING → fixed now] Tautological walk assertion.** `scripts/walk_one_truth.py`
   had a `_badge_host` helper that returned `{}` unconditionally, so its "no
   fabricated host" check could never fail. **RESOLVED:** deleted the fake helper
   and made the assertion real — it now calls the production `endpoint_egress(cloud=True,
   base_url=None)` and asserts the badge carries no `host` key (the DEFAULT_CLOUD_HOST
   fabrication is gone). Walk re-run: 19/19, the assertion now genuine.

3. **[SITTING → fixed now] Exhibit overstated "02 ships first."** The charter
   PLANNED secret slots first in the commit lane; the git log shows 02 landed
   FOURTH (after Wave A: 01, 08, 09). **RESOLVED:** final-summary corrected to
   state the plan vs the actual landing order honestly.

## What Sol cleared (clean bill on the engineering)

- All **7 charter reservations honored** (AC3→131, per-session ruling,
  revisions+registry same phase [131], secret-slot security cut, capability_ref
  + alias-boundary out, one-dial criterion replaced, Sequence/Workflow+Ask→131).
- The resolver (`inference_targets.py:485`) and egress classifier
  (`providers.py:346`) are **real single authorities exercised by real
  assertions** — deletion of duplicated authority, the owner's actual ask.
- The `.43` metal leg is **genuine** (probe returns the real model
  `Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`, not a fixture).
- The DecisionRecord migration is a proper in-place `ALTER TABLE … RENAME`
  (`migrations.py:95-101`) — rows preserved, not recreated.
- The secret-slot env rename is a real, properly-flagged operational finding;
  `doctor` prints the correct export line.
- The other three guard failures (`test_product_copy`, `test_web_vocabulary_guard`
  offender at FollowThroughView.tsx:162, a Phase-128 line) are genuinely
  inherited — correctly ledgered.

## Simplicity verdict (Sol)

> "Genuinely simpler to integrate against, not more machinery… this phase makes
> the product answer 'where did this run?' once instead of nine times. Real win."

## Final verdict

**Ratify with named reservations — one blocking, now resolved.** The blocking
manifest regen is done and committed with the walk; the two sitting-level items
were fixed rather than deferred. Two minds on the close; the owner sees both.
