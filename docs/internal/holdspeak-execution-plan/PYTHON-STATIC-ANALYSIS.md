# Python static analysis — measured first pass

**Publication note, 4 November 2026:** `${ANALYSIS_ARTIFACTS}` is a placeholder for the original external analysis directory. Its scripts and data are not bundled. The historical commands below are not runnable from this documentation checkout alone. Only path notation changed; the findings and execution claims remain historical.

Status: source analysis completed; owner review pending. This report authorizes no removal or implementation.

## Scope and provenance

- Repository: `karolswdev/HoldSpeak`, pinned commit `80b641fa41c7352280cfa52e933acf6dbe8d3857`.
- Executed 2026-11-02 at approximately 20:07 UTC in the cloud workspace with Python 3.12.14.
- Materialized source from the official GitHub commit archive. Extracted only regular `holdspeak/**/*.py` files, never symlinks, with path traversal checks.
- **916 of 916 hub Python files analyzed.** Each file's Git blob SHA-1 was recomputed and compared with the connector's nontruncated pinned Git-tree manifest: **0 mismatches; 0 missing files**.
- This is the complete Python hub package, not every Python file in the monorepo. Tests, scripts, AIPI bridge and historical documents were outside the AST census.
- Used an original standard-library `ast` analyzer. No HoldSpeak modules imported, no setup/build/test scripts executed, no third-party package installation, no source changes.

## Measurements

| Measurement | Result | Meaning |
|---|---:|---|
| Parsed files | 916 | All hub Python files parsed under Python 3.12 |
| Syntax failures | 0 | Parsing only; not import/runtime/version-compatibility proof |
| Synchronous function definitions | 13,085 | Includes methods and nested definitions |
| Async function definitions | 628 | Includes methods and nested definitions |
| Class definitions | 1,316 | Includes nested definitions |
| Resolved local import-site target-edge records | 6,844 | 5,234 unique directed module pairs; 6,387 distinct source module/line locations; includes deferred and type-guarded imports |
| Same-suite repeated declaration candidates | 3 | Two legitimate property setters; one duplicated function |
| Statements after a direct unconditional terminal statement | 0 | Narrow syntactic check only |
| Recognized dynamic import Call nodes | 27 | 26 distinct path/line locations; 20 literal arguments, 7 nonliteral arguments |
| Modules with zero recorded explicit-target inbound edges | 39 | Not a static reachability or dead-module count |
| Multi-module strongly connected component sizes | 382, 5, 5, 2 | Syntactic all-context import graph, not import-time crash findings |

These measurements are not file-size caps, bloat scores or a reason to split cohesive modules. A module should be split when responsibilities, ownership or reasons to change diverge—not because it crosses a number.

## One confirmed redundant declaration

`holdspeak/db/primitives.py` defines `_backfill_directory_name_normalized` twice:

- [First definition, lines 1421–1492](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/primitives.py#L1421-L1492)
- [Second definition, lines 1497–1568](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/db/primitives.py#L1497-L1568)

Their ASTs are identical with source-location attributes excluded. The definitions are unconditional, undecorated and adjacent apart from comments. Ordinary module execution therefore replaces the first function binding with the second before downstream importers use it. This is stronger evidence than an unused-symbol grep: **the earlier declaration is shadowed by identical code**.

The surviving helper is not unused: `tests/unit/test_directory_name_uniqueness.py` imports it at line 18 and calls it at 209, 243, 280, 311, 313, 345 and 385. A bounded text search of all archive `.py`/`.md` regular files of at most 2 MB found those test references and the two declarations, but no production call. That search does not prove absence of dynamic access or other consumers. No migration behavior was exercised or changed.

The other repeated declarations are intentional getter/setter pairs:
- `holdspeak/hotkey.py:94,100`, `HotkeyListener.hotkey`, second decorated `@hotkey.setter`.
- `holdspeak/services/thread_tools.py:664,668`, `ThreadToolExecutor.on_decided`, second decorated `@on_decided.setter`.

## Why the 39 low-reference candidates are not a deletion list

The graph excludes non-import roots and dynamic resolution. It also omits implicit parent-package initialization: six zero-inbound packages have imported descendants (`cadence`, `commands`, `memory`, `plugins`, `plugins.dictation.builtin`, `privileged_effects`). It flags `holdspeak/cli_entry.py`, despite its declared CLI entrypoint. **21 of the 39 candidates are MCP family modules named in `_FAMILY_MODULE_NAMES` and loaded by `importlib.import_module` in `holdspeak/mcp/families/__init__.py:29–69`.**

Other candidates include package initializers, SDK modules, a parked route and plugin-related files. Each needs classification against entrypoints, registries, runtime configuration, tests and supported external use. No candidate was classified dead from inbound count alone.

The 27 recognized dynamic-import Call nodes (26 distinct path/line locations) include recipe/module-path loading and configured runtime imports. Two calls occur on the same line. The analyzer records nonliteral arguments as uncertainty; it does not invent edges. Aliased imports, custom loaders, reflective dispatch and decorator registrations need further analysis.

## Architectural signal, not automatic diagnosis

The import inventory supports investigating responsibility boundaries identified in the manual review:
- `web_server.py`: 133 distinct local dependencies; broad bootstrap fan-out is partly expected.
- `program_service.py`: 42 distinct local dependencies and 68 inbound import sites.
- `project_service.py`: 34 distinct local dependencies and 31 inbound import sites.

Those numbers are not defects. The stronger evidence remains mutual service composition, shared contracts located inside orchestrators, and unrelated read/command/Ask-task responsibilities. The 382-module component is a union of top-level, deferred and type-guarded explicit-target edges, including package aggregation but missing implicit parent-initializer semantics. It must not be presented as 382 modules that crash on import, nor as a runtime cycle finding. **No runtime import was performed.**

## Artifacts and reproduction

Analysis artifacts are outside the repository at `${ANALYSIS_ARTIFACTS}/`:

- `manifest.json`: pinned tree paths and expected Git blob hashes.
- `source.tar.gz`: official source archive, approximately 269 MiB; not part of the review package.
- `source/holdspeak/`: extracted Python source, unchanged.
- `materialize.py`: safe source-only extractor.
- `analyze.py`: original standard-library analyzer.
- `report.json`: detailed modules, import edges, candidates and components.
- `summary.json`: aggregate counts.

To repeat in the same analysis directory, without executing application code:

```sh
python ${ANALYSIS_ARTIFACTS}/materialize.py
python ${ANALYSIS_ARTIFACTS}/analyze.py
```

Source archive acquisition, if needed:

```sh
curl -L --fail --max-time 180 \
  -o ${ANALYSIS_ARTIFACTS}/source.tar.gz \
  https://github.com/karolswdev/HoldSpeak/archive/80b641fa41c7352280cfa52e933acf6dbe8d3857.tar.gz
```

The analyzer's suite walker was separately checked against synthetic snippets for a repeated function definition, a statement following `return`, and a conditional-return branch that does not make the following statement unreachable. These checks were of the analysis tool, not product tests.

## Limits and next evidence

Static analysis cannot establish everything that never executes. This pass does not model whole-program control flow, exceptions/finally behavior, runtime values, call targets, dispatch tables, reflection or external SDK clients. Zero terminal-tail findings does not mean there is no unreachable code. Parsing with Python 3.12 does not certify the declared minimum Python version.

Import edges form a syntactic all-context graph with both overapproximation and omissions. `from package import name` can add both package and submodule edges; conditional imports are not evaluated, and implicit parent-package initialization edges are absent. Context tags are heuristics: function descendants are tagged deferred, a TYPE_CHECKING substring tags its entire if subtree, and ordinary conditional imports retain the module tag. The module tag does not guarantee eager execution. The reviewer inspected all 21 TYPE_CHECKING tests in this snapshot: plain TYPE_CHECKING conditions, with no else-import misclassification found. Cycles and inbound counts are exploratory signals, not runtime reachability proofs. An independent read-only artifact review recomputed all 916 blob hashes and sizes with no mismatches, missing or unexpected files, reparsed all files, and reproduced definition counts and component sizes.

Next useful work is to add explicit entrypoint/registry roots and separate eager/deferred/type graphs before reviewing the remaining low-reference candidates. The downloaded source also makes a complete frontend AST graph feasible; this pass did not run one. No deletion, migration or refactoring task is approved by this report.
