# HS-79-06 — closeout

- **Project:** holdspeak
- **Phase:** 79
- **Status:** todo — the gate.
- **Depends on:** 01–05.

## The bar

Full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`) green; web
build green (`cd web && npm run build`) — route modules feed the pages;
`swift test` green (the iPad client consumes the moved routes; paths must be
byte-identical); the manifest byte-stable on a fresh regen; `final-summary.md`
with the line-count ledger (before/after per file, verbatim-move accounting).
One PR, merged on conclusion-checked green.
