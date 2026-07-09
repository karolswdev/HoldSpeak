# Evidence - HSU-1-05

- **Story:** HSU-1-05 - The debrief + the triage protocol
- **Status:** done
- **Date:** 2026-07-09

## What shipped

`uat/conductor/debrief.py` + `uat/TRIAGE.md` + debrief/triage routes + a site
sitting-end panel:

- **The packet** (`debrief.md` + `debrief.json` into `uat/_runs/<run>/debrief/`):
  the header, the score **per surface and overall** (a surface never sat is
  named, not averaged away), coverage % against the ledger, and every non-pass
  finding with note + screenshot link + a product-log slice windowed around the
  step's timestamp. `debrief.json` is the stable agent-side contract.
- **Findings** — each `fail`/`partial` verdict → a finding with a stable id
  (`UAT-<run>-<n>`), a triage state, and a disposition that survives
  regeneration (upsert preserves the human's call). A cross-surface split
  (passed on web, failed on iPhone) is one finding carrying both — the parity
  break is the signal.
- **The ritual** (`uat/TRIAGE.md`) — the four steps + the disposition vocabulary
  (`untriaged|fix|wont-fix|by-design|duplicate`).
- **The BACKLOG feed** — a `fix` renders a paste-ready block in BACKLOG's
  candidate-table format citing finding id + debrief path (proposes, never edits).
- Routes: `POST/GET /api/sittings/{id}/debrief`, `PATCH /api/findings/{id}`,
  `GET /api/sittings/{id}/findings/backlog-block`. The site's sitting-end screen
  renders findings + triage buttons + the BACKLOG block.

## Sample `debrief.md` (a scripted sitting: web fail, iPad/iPhone pass)

```markdown
# UAT debrief — smoke

## Score per surface
- **web** — 0 pass · 1 fail · 0 partial · 0 skip
- **ipad** — 1 pass · 0 fail · 0 partial · 0 skip
- **iphone** — 1 pass · 0 fail · 0 partial · 0 skip

## Findings (1)
### UAT-965c77-1 — A seeded desk, read on all three surfaces — step 1, web: fail
- **Verdict:** fail  ·  **Surface:** web  ·  **Triage:** untriaged
- **Note:** the badge read cloud on a local desk
- **Cross-surface split:** passed on ipad, iphone but fail on web — a parity break.
```

## Proof

### Captured run — 2026-07-09T07:52:07Z

- **Command:** `uv run pytest -q tests/uat/ --ignore=tests/uat/test_induction_integration_43.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b3526e9057ef30f01a3e0042f25a3b2bb1e8f3b4

```text
........................................................................ [ 88%]
.........                                                                [100%]
81 passed in 17.18s
```
