# HS-3-01 — `detect_project_for_cwd()` pure function

- **Project:** holdspeak
- **Phase:** 3
- **Status:** backlog
- **Depends on:** HS-2-11 (MIR-01 closed; phase-3 scaffold landed)
- **Unblocks:** HS-3-02 (wiring needs the detector to exist)
- **Owner:** unassigned

## Problem

DIR-01 §8.1 says project-override blocks are "auto-discovered via
`project_detector`", and DIR-01 §6.4 declares
`Utterance.project: ProjectContext | None  # from project_detector`.
But `holdspeak/plugins/project_detector.py` is the **MIR-side
keyword scorer** that matches transcripts to project KBs — there is
no cwd-based project-root finder anywhere in the codebase. `grep`
for `find_project_root` / `detect_project` returns zero hits.
`holdspeak/plugins/dictation/blocks.py:150` accepts a
`project_root: Path | None` parameter but no caller passes a
non-None value. This story builds the pure detector function that
the rest of the phase wires through.

## Scope

- **In:**
  - New module-level function `detect_project_for_cwd(start: Path | None = None) -> ProjectContext | None` (location: `holdspeak/plugins/project_detector.py` alongside the existing class — keeps the spec's "via project_detector" wording honest, or a sibling `holdspeak/plugins/dictation/project_root.py` if the file gets crowded; pick at implementation time).
  - Walk strategy: from `start` (default `Path.cwd()`), walk up until one of the anchors is found, in priority order: `.holdspeak/` (strongest signal — explicit project opt-in), `.git/` (most projects), `pyproject.toml` / `package.json` / `Cargo.toml` (language hints, lowest priority). Stop at filesystem root or `$HOME`, whichever comes first; return `None` if no anchor matched.
  - Returned `ProjectContext` shape (matches the kb-enricher template surface in spec §8.4): `{"name": <derived>, "root": <abs path str>, "anchor": <which marker matched>}`. Optional: if `<root>/.holdspeak/project.yaml` (or similar canonical KB file) exists, load it and merge under a `kb` key — but only if the file exists. Don't invent KB content.
  - `name` derivation: prefer `[project].name` from `pyproject.toml` if present, else `[package].name` from `Cargo.toml`, else `"name"` from `package.json`, else the basename of `root`.
  - Pure function, no side effects beyond filesystem reads. Cheap (one stat per ancestor + at most one small file read for the name).
  - Unit tests at `tests/unit/test_project_detector_cwd.py` covering: (1) anchor priority (`.holdspeak/` beats `.git/` beats `pyproject.toml`), (2) walks up correctly from a nested dir, (3) returns `None` outside any project tree, (4) name derivation falls back through the priority chain, (5) `kb` key absent when no KB file present, (6) doesn't escape `$HOME`.
- **Out:**
  - Wiring it into `Utterance` or `blocks.py` — that's HS-3-02.
  - Caching across calls — premature; the function is cheap. Add only if profiling in HS-3-02 shows it matters.
  - Reading project KB content beyond a single optional file at the root.
  - Cross-platform path corner cases beyond what the existing `pathlib` usage handles.

## Acceptance criteria

- [ ] `detect_project_for_cwd(start: Path | None = None) -> ProjectContext | None` exists and is importable from a stable path (documented in the story's evidence).
- [ ] Returned dict, when non-None, contains at least `name`, `root`, `anchor` keys.
- [ ] Anchor priority is `.holdspeak/` > `.git/` > language manifests.
- [ ] All 6 unit-test scenarios pass.
- [ ] Function does not touch the filesystem outside the cwd→root walk and at most one name-source file read.
- [ ] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` PASS.

## Test plan

- **Unit:** `tests/unit/test_project_detector_cwd.py` — 6 cases, using `tmp_path` fixtures to construct synthetic project trees.
- **Regression:** documented full-suite command (metal excluded).

## Notes / open questions

- Module location is a small judgement call. Adding to the existing `project_detector.py` keeps the spec wording literal but mixes two distinct surfaces (MIR-side scorer + dictation-side cwd detector). The implementation should pick the location that minimizes confusion and document the choice in evidence.
- `$HOME` boundary protects against runaway walks if `holdspeak` is launched from `/` or similar.
- The optional `kb` key is deliberately additive: HS-1-06 (kb-enricher) reads `{project.kb.*}` placeholders; if no KB file exists, those templates correctly fall through to DIR-F-007's "skip injection" path.
