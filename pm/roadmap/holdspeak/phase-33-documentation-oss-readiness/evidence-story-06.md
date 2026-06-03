# Evidence — HS-33-06 (Phase closeout + final-summary)

**Shipped:** 2026-06-03. Phase 33 verified end-to-end and closed; the
`final-summary.md` is written and the project README phase row flipped to `done`.

## Link-check sweep

- **Doc link-check** (`tests/unit/test_doc_drift_guard.py::
  test_no_live_doc_has_a_dangling_relative_link`) → green; scans every live
  `docs/**/*.md` (incl. the new `docs/README.md`, `docs/MODELS.md`, and the
  pixellab provenance README) for dangling relative markdown links.
- **Root docs** — extracted every relative link + HTML `<img src>` from
  `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`: **no missing links** (incl. the
  HS-33-03-moved `docs/internal/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`, the brand mark,
  and the spot-art assets).

## Doc-truth re-verify

- The HS-32-06 drift guard (no live doc claims a `DeterministicPlugin` stub) →
  still green.
- **Pre-release positioning made consistent** — fixed the one remaining
  contradiction: the roadmap README's project-metadata line said "`v0.2.0` is
  released"; updated to "pre-release… not a published tag… not on PyPI," matching
  the README banner + `CHANGELOG`.

## OSS checklist (all satisfied)

| Item | State |
|---|---|
| `LICENSE` (Apache-2.0) | ✅ present |
| `pyproject` metadata (license/authors/classifiers/urls/keywords) | ✅ `license = "Apache-2.0"`, builds clean (HS-33-02) |
| README badges | ✅ license / Tests CI / Python / platform (URLs against the real repo) |
| Honest pre-release status | ✅ README banner + CHANGELOG + roadmap metadata |
| `docs/README.md` index navigable | ✅ user journey + internal pointer |
| `docs/MODELS.md` bring-your-own contract | ✅ |
| Assets wired (mark + social card) | ✅ README header + committed social card |
| `CHANGELOG.md` + `CONTRIBUTING.md` | ✅ present |

## Tests ran

- `uv run pytest -q tests/unit/test_doc_drift_guard.py` → **3 passed**.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1954 passed, 15 skipped**.

## Done-when

- [x] No broken links; drift guard + doc-truth green.
- [x] OSS checklist satisfied (LICENSE / metadata / README / docs / assets /
      CHANGELOG / CONTRIBUTING).
- [x] `final-summary.md` written; project README phase row = `done`; full suite
      green.

## Notes

- The phase is the local branch `phase-33/hs-33-01-model-framing` (6 story
  commits), unpushed — open a PR to `main`.
- Manual, non-repo follow-up recorded in `final-summary.md`: set
  `social-card.png` as the GitHub social preview (repo Settings UI).
