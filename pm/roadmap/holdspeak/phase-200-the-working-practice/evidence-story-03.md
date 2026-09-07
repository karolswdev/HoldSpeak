# Evidence - HS-200-03

- **Story:** HS-200-03 - Make release checks isolated and actionable
- **Status:** done
- **Date:** 2026-09-06

## Proof

### Captured run — 2026-09-06T19:30:25Z

- **Command:** `bash -c set -o pipefail; T=$(mktemp -d); echo "--- critical journeys (isolated HOME)"; HOME=$T uv run pytest -q -m critical tests/critical -p no:cacheprovider 2>&1 | tail -1; echo "--- the isolation guard + the formerly inherited twelve + the CI-only cluster"; HOME=$T uv run pytest -q -p no:cacheprovider tests/unit/test_phase200_ci_isolation.py tests/unit/test_ask_grounding_claims.py tests/unit/test_ask_runner_migration.py tests/unit/test_desk_seed.py tests/unit/test_hs173_nudge_wire.py tests/unit/test_kernel_effect_fence.py tests/unit/test_product_copy.py tests/unit/test_project_mcp_commands.py tests/unit/test_project_mcp.py tests/unit/test_hs175_calendar_wire.py tests/integration/test_web_activity_api.py tests/unit/test_api_surface.py tests/unit/test_ux_canon_ratchet.py 2>&1 | tail -1; echo "--- the same under TZ=Pacific/Auckland"; TZ=Pacific/Auckland HOME=$T uv run pytest -q -p no:cacheprovider tests/unit/test_hs175_calendar_wire.py tests/unit/test_hs173_nudge_wire.py 2>&1 | tail -1; echo "--- web"; cd web && npm run check 2>&1 | tail -2; cd ..; uv run python scripts/check_docs.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c10b90f83545342c48329973981a89f007ac2d5a

```text
--- critical journeys (isolated HOME)
11 passed in 9.79s
--- the isolation guard + the formerly inherited twelve + the CI-only cluster
226 passed in 74.66s (0:01:14)
--- the same under TZ=Pacific/Auckland
44 passed in 8.20s
--- web

bundle gate passed (Desk JS 1275040 B; Desk CSS 306679 B; source maps 0)
Documentation navigation: 38 files checked; local targets and Markdown headings resolve.
```
