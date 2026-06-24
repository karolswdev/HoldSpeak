# Dogfood run — <DATE>

Paste this header at the top of your dated copy of the protocol
(`dogfood/results/<DATE>.md`), then fill the checks below it.

## Environment

- **Date / driver:**
- **HoldSpeak version / commit:** `git rev-parse --short HEAD` →
- **Platform:** macOS ___ (Apple Silicon? ___)
- **Whisper model / backend:** (e.g. base / mlx)
- **Intel endpoint:** `.43` model ___ · reachable? ___
- **Tier(s) run:** ☐ Tier 1 plumbing  ☐ Tier 2 real metal
- **Fixtures rendered at:** (make_fixtures git state / time)

## Rollup

| Tier | Checks | PASS | FAIL | PARTIAL | SKIP |
|------|-------:|-----:|-----:|--------:|-----:|
| Preflight (P) | 5 |  |  |  |  |
| Tier 1 (T1) | 19 |  |  |  |  |
| Tier 2 (T2) | 29 |  |  |  |  |
| Cross-cut (X) | 5 |  |  |  |  |
| **Total** | **58** |  |  |  |  |

## Verdict

One-paragraph read on the release: ship-ready? what's the worst thing you saw?

## Top failures (carry into the next phase)

1.
2.
3.

---

(checks copied from PROTOCOL.md follow)
