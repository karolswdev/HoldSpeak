# HS-S23 · Classify Program path coverage changes correctly

**Proposed detailed exemplar, not implementation permission.** Epic: [HS-E20](../epics/HS-E20-program-contracts.md). Owner decision: D23 in [Decisions](../DECISIONS.md). Source pin: `80b641fa41c7352280cfa52e933acf6dbe8d3857`, main rechecked 3 November 2026 at 19:34 UTC. Product/source tests have not run during planning.

## Job and current evidence

When an authorized writer edits a Program's `within` text, a change that admits new planning paths should be visible to the existing owner-confirmation mechanism. Night planning accepts a union of paths, with an empty list meaning repository-wide. The text classifier currently flags removal of old strings instead: adding `docs/` to `src/` is not lower-bar; removing `docs/` from `src/, docs/` is.

This is a source-derived mismatch in one text guard, not a filesystem sandbox escape. `within` is explicitly limited to night planning in `docs/programs.md`; manual step ownership, direct `ProgramService.update` and post-change diff checks have distinct contracts. Some paths can run without a planner. This story must not advertise universal path prevention or all-API owner confirmation.

Evidence: [bounded path review](../NEXTGEN-JOURNEYS-AND-NAVIGATION.md#program-path-bounds-one-meaning-for-planning-and-text-changes-1200-follow-up). Current source: [program_text.py](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_text.py), [program_service.py](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_service.py), [program_night.py](https://github.com/karolswdev/HoldSpeak/blob/80b641fa41c7352280cfa52e933acf6dbe8d3857/holdspeak/services/program_night.py).

## Proposed contract and G23 decision

**Recommendation, pending:** `within` lowers the guard when the new allowed set contains **any** path the old set did not (`after` is not a subset of `before`). This includes a replacement that both adds and removes coverage. A three-label expands/narrows/equivalent API is unnecessary for this Boolean guard.

G23 must explicitly accept or redirect:

1. Newly admitted coverage, including mixed replacements, uses the existing lower-bar mechanism; narrowing/equivalent coverage does not. This deliberately changes today's partial-removal test expectation.
2. Classification follows the existing night-planning lexical, slash-delimited coverage on validated repository-relative names. Empty means repository-wide. Ordinary nonempty bounds cover themselves and descendants even without a trailing slash. Preserve case, literal glob/backslash/dot spellings and internal separators; do not resolve paths, fold case, inspect existence or turn this into a glob matcher.
3. Only classification changes. Parser/printed/stored list representation, nightly/canon consumers, direct update, manual plans and diff enforcement remain unchanged. A shared consumer migration or broader authority change needs another decision.

A small **proposed** private coverage helper adjacent to `_lowers_head` in the existing `program_text.py` is sufficient; no new module or API is needed. Its exact private name is not an existing contract. Do not import stateful night/canon modules into the pure text module just to share a few lines.

For ordinary accepted names, compare each new bound with old bounds using equality or a slash-delimited descendant relation. Strip only surrounding entry whitespace and trailing separators as needed for the agreed night-coverage comparison; do not rewrite the stored values. Any unmatched new bound adds coverage. Empty-before is already universal; empty-after makes coverage repository-wide. Characterize unusual accepted spellings in HS-T23-01 before finalizing the helper, not by guessing filesystem semantics.

## Acceptance matrix

The results below are the **proposed G23 behavior**, not tests already executed. Rows compare coverage, not whether a text diff row exists.

| Case | Before → after | `lowers_bar` |
| --- | --- | --- |
| C01 | empty → empty | false |
| C02 | empty → `src/` | false; narrows repository-wide coverage |
| C03 | `src/` → empty | true |
| C04 | `src/` → `src/, docs/` | true |
| C05 | `src/, docs/` → `src/` | false; deliberate current-expectation change |
| C06 | `src/api/` → `src/` | true |
| C07 | `src/` → `src/api/` | false |
| C08 | `src/` → `src/, src/api/` | false; redundant child |
| C09 | `src/, src/api/` → `src/` | false; equivalent removal |
| C10 | `src/, docs/` → `docs/, src/` | false; order only |
| C11 | `src/` → `docs/` | true; mixed removal/addition |
| C12 | `src/` → `src2/` | true; not a raw string-prefix match |
| C13 | `src` ↔ `src/` | false under proposed night-coverage comparison; representation need not normalize |
| C14 | duplicates added/removed with unchanged union | false; preserve parser/storage behavior |
| C15 | `src/a` → `src/ab` | true; slash boundary matters |

Additional parser characterization: missing `within` means empty; `within none` means literal `none`; comma-only nonempty rest produces empty; bare `within` is not that spelling. The validator rejects leading `/`, `~` and `..` path parts. It does not canonicalize `.`/`./`, internal repeated slash, case, globs or backslashes. Night and canon differ at edge normalization (`path='src', bound='src/'`); preserve both consumers unchanged. Do not claim full equivalence between them.

## Required observed behavior after an authorized implementation

- Stable row ID `program.within`, current diff/preview fields and ordinary revision/storage behavior remain.
- Owner dry-run writes nothing; owner expansion without the specific allowed row is held; explicit owner `allow_lower=['program.within']` applies it.
- A creator-agent expansion remains refused by the existing head lower-bar rule. Agent-supplied `allow_lower` stays `owner_required`; unrelated agents cannot write. A preview is not a write grant.
- Narrowing/equivalent edits use the ordinary authorized path, without changing other guard fields or current syntax refusals.
- Stale-base conflict remains `text_conflict` and cannot be bypassed by a changed classification.
- Generated expansion at YOLO remains withheld, including owner-invoked shaping. A mixed answer may apply its independent allowed row while retaining expansion for a separate owner action. Preserve existing refreshed-base/partial-write behavior.
- Actual returned `changes`/`lowers`/`allowed_text`, stored `within`, revision and applicable checkpoint/announce behavior are asserted using existing rigs. A helper Boolean alone is insufficient.
- Unchanged night/canon tests pass. No new enforcement or parser normalization is introduced.

## Exact existing context and editable ownership

Read named symbols/sections, not whole research files. Line anchors refer to the pin and must be rechecked.

| Existing path | Exact concern | Edit status |
| --- | --- | --- |
| `holdspeak/services/program_text.py` | `Head.within`; `program_line`; `head_value`; `_lowers_head` at 1196; `diff_program_text` at 1280 | **Only production editable file**, limited to `within` classification and a cohesive private helper |
| `holdspeak/services/program_service.py` | `_require_writer` 1720; `update`/`_update_language_fields` 2017–2157; `_check_text_rows` 4056; `text_apply` 4129; `_agent_bar_rows` 4199; `_apply_text` 4249; `_within` 5547 | Read-only behavior/authority/storage consumer |
| `holdspeak/services/program_shaper.py` | `guard`, `_rows_for`, `shape`, `shape_program`; YOLO allowed-row filtering 539–573 | Read-only consumer |
| `holdspeak/services/program_night.py`, `program_canon.py` | `_inside_within` / `read_item` and `_within` / `file_items` | Read-only planning semantics and known normalization difference |
| `holdspeak/services/program_runner.py` | `diff_facts` 1605–1627 compares step `owns`, not Program bounds | Read-only scope boundary |
| `holdspeak/web/routes/programs.py`, `holdspeak/mcp/families/program.py` | REST text forwarding 318–325; MCP text dispatch 466–469; direct-update surface separately exists | Read-only public adapters; no new route/schema |
| `holdspeak/db/programs.py`, `holdspeak/principals.py` | Existing storage and authenticated principal model | Read-only; no schema, identity or wire changes |
| `tests/unit/test_program_text.py`, `test_program_agent_bar.py`, `test_program_shaper.py` | Matrix, actual service/principal and generated-text integration | **Editable existing tests** |
| `tests/unit/test_program_night.py`, `test_program_night_canon.py` | Unchanged consumer regression tests | Read-only; named execution budget |
| `tests/integration/program_rig.py`, `program_night_seed.py`, `program_shape_seed.py`, `tests/conftest.py` | Existing fake adapters, isolated DB/tmp paths and test opt-outs | Read-only; do not change fixture behavior to mask a failure |
| `docs/programs.md`; `docs/internal/betterment/programs/PROGRAM-LANGUAGE-2026-10-31.md` | Relevant Text/Apply/Night and language §3.6/§4.5/§4.6/§5.5; distinguish old target names from actual paths | Read-only. Report contradictory normative text; a necessary doc edit requires explicit owned-path amendment |

## Tasks and verification

[HS-T00](../tasks/HS-T00-baseline.md) → [HS-T23-01](../tasks/HS-T23-01-contract.md) → [HS-T23-02](../tasks/HS-T23-02-implementation.md) → [HS-T23-03](../tasks/HS-T23-03-verification.md).

Use exactly the five files in [V23](../VALIDATION.md#v23-first-slice-verification). Existing named tests and proposed additions are distinguished there. No browser/provider test is needed to prove this classifier's scoped behavior; integration-owner quick check still follows current repo rules. Do not invent a lint gate from an installed dependency.

## Rollback and stop conditions

Expected compatibility impact: changed classification and test expectations only; no new wire/storage format, new module, import contract or data migration. A reviewed reverse patch to these owned lines can restore the old behavior, but would restore the additive-expansion limitation. Do not change stored Programs to make rollback pass, and do not use reset/restore/clean on a shared tree.

Stop for unresolved G23, unassigned code lane, material source drift, a helper requiring planner/canon normalization changes, a need to guard direct update/manual/diff paths, a new schema/API or unsafe fixture, unavailable isolated test environment, unexplained baseline failure or conflicting dirty files. Report the smallest amendment/decision, not an opportunistic broader fix. Invariants: [I16/I18/I19/I20](../INVARIANTS.md).
