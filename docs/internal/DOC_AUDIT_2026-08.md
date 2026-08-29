# Documentation truth audit — 2026-08

**Audit date:** 2026-08-29. **Code baseline:** `origin/main` at `16477660b`.
**Method:** inventory every Markdown file, separate maintained guidance from
historical evidence, check live claims against code/configuration/tests, run the
generated-contract and link guards, and verify publication facts against the
project's [PyPI page](https://pypi.org/project/holdspeak/0.4.0/) and
[GitHub releases](https://github.com/karolswdev/HoldSpeak/releases).

This is the current accuracy ledger. The
[June audit](./DOC_AUDIT_2026-06.md) is retained as a historical snapshot.

## Scope: all 3,294 tracked Markdown files at audit start accounted for

The inventory uses `git ls-files '*.md'`, so hidden fixture and diagnostic files
are included. The audit does not rewrite evidence as if it were current
guidance. That would destroy provenance. The corpus is divided by contract:

| Corpus | Files at audit start | Treatment |
|---|---:|---|
| `pm/**/*.md` | 3,038 | Historical planning and evidence. Preserve verbatim. |
| `aipi-lite/pm/**/*.md` | 63 | Historical device planning and evidence. Preserve verbatim. |
| `docs/evidence/**/*.md` | 41 | Generated proof snapshots. Preserve verbatim. |
| `dogfood/results/*.md` | 1 | Recorded run result. Preserve verbatim. |
| `dogfood/repos/**/*.md` | 38 | Deliberate fixture-repository content, including hidden `.hs/` context. Validate as fixtures; do not rewrite to match HoldSpeak. |
| `tests/fixtures/**/*.md` | 4 | Deliberate dictation fixture content. Preserve the test input. |
| Everything else | 109 | Maintained guides, contributor references, archived diagnostics, design records, UAT/device runbooks, prompt skills, and indexes. Audit for current purpose, links, commands, and truth. |

The maintained 109 comprise five root documents; 28 top-level user/operator
guides; 37 internal design records; one asset README; six active AIPI-Lite
documents; three Apple documents; five designer-handoff documents; three
dogfood harness documents; ten packaged skill documents; seven UAT documents;
and four Web documents.

Internal plans remain design records, not install instructions. A plan may
describe a superseded decision in past tense. Current operational advice in an
internal document is still subject to the global drift guards.

## Canonical facts at the baseline

| Surface | Current truth | Source of truth |
|---|---|---|
| Source package version | `0.4.0`; Python `>=3.10` | `pyproject.toml` |
| Published release | PyPI and GitHub latest are `0.4.0` (2026-07-04) | PyPI and GitHub Releases |
| Documentation version | The repository docs describe `main`, which contains unreleased work after `v0.4.0`; use a source install for exact parity | Git history from `v0.4.0..main` |
| Primary CLI commands | 19: `web`, `meeting`, `history`, `actions`, `intel`, `dictation`, `agent-hook`, `gate`, `cadence`, `control-mode`, `device-psk`, `memory`, `doctor`, `import`, `mesh`, `node`, `backup`, `restore`, `seed` | `holdspeak/main.py` |
| Browser shell routes | 19 canonical or compatibility routes, all served by one React shell | `holdspeak/web/routes/pages.py` |
| HTTP/WebSocket routes | 540; iOS consumes 89 and Web consumes 418 at this baseline | generated `docs/api-surface.json` |
| MCP surface | 135 tools across 30 domain families; 29 default non-owner resources, 32 owner resources | `holdspeak/mcp/tools.py`, `holdspeak/mcp/resources.py`, `docs/MCP_SIDECAR.md` |
| Meeting-intel plugins | 14 built-ins and zero deterministic fallbacks in the registry | `holdspeak/plugins/builtin/__init__.py` plus plugin tests |
| Dictation defaults | Pipeline on; correction memory on; journal on with last-500 retention | `holdspeak/config/dictation.py` |
| Authority defaults | YOLO; actuator execution on; wildcard actuator/host allow-lists. Hard identity, destination, payload, secret, audit, and schema invariants remain | `holdspeak/config/core.py`, `holdspeak/config/meeting.py`, `holdspeak/operation_policy.py` |
| Ambient defaults | Desktop presence, Qlippy, wake word, Cadence, and Telegram cadence are off | `holdspeak/config/device.py`, `holdspeak/config/integrations.py` |
| Database upgrades | Declarative, additive reconcile. Back up before a real shape change; no database-version refusal gate | `holdspeak/db/reconcile.py`, `tests/unit/test_db_schema_policy.py` |
| Apple floor | macOS 14 and iOS 17 in SwiftPM; native app sources exist under `apple/App/` | `apple/Package.swift`, `apple/App/` |
| Web build | Vite + React 19, Node.js 20.19+ or 22.12+ for build/test, FastAPI for the shipped runtime | `web/package.json`, `web/README.md` |

## Findings and dispositions

| ID | Finding | Disposition |
|---|---|---|
| A1 | The June audit still claimed `0.2.1`, nine CLI commands, old defaults, and no PyPI release. | Kept as a clearly labelled historical snapshot; this ledger replaces it as current canon. |
| A2 | PyPI `0.4.0` predates a large unreleased body of work documented on `main`. A bare PyPI quickstart implied feature parity. | Install docs now distinguish the published release from a source install matching `main`. |
| A3 | Root docs said the desktop refused a newer-stamped database. The current reconciler explicitly has no version gate. | README and release guidance now describe additive reconcile and shape-change backups. Apple keeps its separate version-gated store statement. |
| A4 | The roadmap-vocabulary guard recognized only one- and two-digit story numbers, so `HS-112` and `HS-139` leaked into user docs. | Guard widened to three digits; affected guides rewritten in product tense. |
| A5 | Plugin authoring still taught mandatory per-action human approval and default-off execution, while the default YOLO posture can authorize a fixed configured destination. | Actuator docs now distinguish proposal review, authorization, and execution and describe all three control modes. |
| A6 | The docs index reported 127 MCP tools and overstated approval requirements. | Counts and authority language aligned with the MCP registry and control policy. |
| A7 | The API generator opened the contributor's ambient database, so doc generation could fail on unrelated local state. | Generator now assembles routes against a disposable isolated database. |
| A8 | Source paths moved during module splits (`config.py`, `intel.py`, the runtime bus, workflow service), but several guides retained old paths. | Maintained references now point at the live modules. |
| A9 | Apple README still described the native host as a future placeholder. | README now describes the existing SwiftPM layers, app sources, device scripts, and current iOS floor. |
| A10 | The April Astro designer handoff called itself current after the React hard cut. | The handoff is explicitly archived; current design and implementation references are linked. |
| A11 | UAT census numbers and a few path examples drifted as campaigns grew. | Volatile hard-coded census prose was replaced with current generated inventory guidance; paths corrected. |
| A12 | The changelog's Unreleased section covered only two mobile changes despite extensive post-`0.4.0` work. | Added a grouped, user-visible summary and kept release-specific history unchanged. |

## Validation contract

Run these before merging documentation changes:

```bash
uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_api_surface.py
uv run pytest -q tests/unit/test_reconcile.py tests/unit/test_db_schema_policy.py
uv run pytest -q tests/uat/test_decks.py tests/uat/test_scenarios.py tests/uat/test_smoke_pack.py
npm --prefix web run check
cd apple && swift test
```

`scripts/gen_api_surface.py` now uses a temporary database. Regenerating the
API contract does not read or reconcile `~/.local/share/holdspeak/holdspeak.db`.

## Standing rules for the next sweep

1. Treat code, schemas, generated contracts, and tests as authority. Treat
   screenshots and prose as claims to verify.
2. Keep release docs and `main` docs distinct while `main` is ahead of the
   latest published tag.
3. Preserve roadmap/evidence records verbatim. Add a current pointer instead
   of rewriting history.
4. Prefer generated counts. If a count is worth publishing, pin it to its
   registry with a test.
5. Never run documentation generators against ambient user data.
6. Update this ledger when an externally visible default, command, route,
   platform floor, or release channel changes.

## See also

- [`DOCS_STYLE.md`](./DOCS_STYLE.md): voice, structure, and navigation rules.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md): current runtime map.
- [`../RELEASING.md`](../RELEASING.md): package and data-upgrade contract.
- [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md): contributor workflow and checks.
