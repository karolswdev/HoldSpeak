# Evidence - HS-105-06

- **Story:** HS-105-06 - Docs — the bench at the entry points
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T16:44:07Z

- **Command:** `sh -c uv run pytest -q tests/unit/test_doc_drift_guard.py tests/unit/test_web_vocabulary_guard.py tests/unit/test_interior_canon_guard.py 2>&1 | tail -1 && uv run python scripts/judgment_census.py 2>&1 | tail -1 && uv run python scripts/mockup_census.py 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 58d2393749bde6fb67c76d2b76df3108c25aaaed

```text
33 passed in 0.59s
census: every surface and component is judged — zero omissions
mockup census: every canon screen mocked at 1440 and 393
```

## What shipped (the narrative)

Entry points touched, every claim written from the SHIPPED tree:

- **USER_GUIDE.md** — a new "Using The Desk" section ahead of Mission
  Control: icons carry state at rest (each badge's meaning), select
  and open, drawers as directories with remembering windows, drop to
  compose (with the consent truth: a drop never runs a model), Info
  on everything, the menu bar with ghost-with-reason. The doc-drift
  guard caught six em-dashes in the first draft (the POSITIONING
  voice rule) — recomposed without them; guard green.
- **docs/internal/DESK_GRAMMAR.md** — NEW: the Style-Guide move. Six
  laws (icon, selection/open, drawer, drop, Info, verb) each citing
  its guard file, plus the standing remainders recorded rather than
  waived. AGENT_BRIEF.md §3 now points at it as required reading
  before touching the world.
- **ARCHITECTURE.md** — the desk-across-surfaces section grew the
  Workbench-grammar paragraph naming the contract files
  (dropMatrix/infoContract/verbRegistry) and the kernel deferral of
  the verb wire face.
- **README.md** — the public Desk paragraph now states the working-
  icon truth (state at rest, drawers, drop verbs, Info, the click
  grammar) instead of the tray-era description.
- **SECURITY.md unchanged, deliberately**: this phase added no new
  boundary — drops ride existing PUTs, the verb wire face was
  deferred precisely to avoid a consent-model shortcut.
- **UIUX_JUDGMENT.md** — the judgment census demanded the new
  components be judged: ZoneWindow / InfoWindow / DeskMenuBar rows
  added (plus two straggler components, SystemShade and
  GlassDropLayer, judged while there); census reads "zero omissions".

Captured above: doc-drift + vocabulary + interior-canon guards green
(the run INCLUDES the dash rule that bit the draft), judgment census
zero omissions, mockup census green.
