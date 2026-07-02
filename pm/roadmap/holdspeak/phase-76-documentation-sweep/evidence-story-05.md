# Evidence — HS-76-05 — Closeout: the tail + coherence

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-76-documentation-sweep`)

## The tail, fixed (each maps to a ledger row)

- **SECURITY.md** (first in line): the stale module refs corrected
  (`db.py` → `db/` with `core.py` named; `intel.py` → `intel/providers.py`;
  the imprecise line anchor dropped for the mechanism description), and
  **the three missing egress rows added** — the desk Slack relay, the
  desk webhook connector (any configured endpoint), and the desk GitHub
  issue write — each with its trigger, exact payload posture, and gate,
  in the table's own voice.
- **The trust boundary mirrors SECURITY again**: ARCHITECTURE's diagram
  gains the two new crossing shapes (the companion webhook and the
  gh-issue write; the desk Slack relay rides the existing Slack
  crossing). Render guard re-run green.
- **docs/README.md (index)**: the front-door paragraph speaks the Desk;
  the Desk doc moved into Start here; the duplicate Extend row removed.
- **MEETING_MODE_GUIDE**: the live dashboard is `/live` (both spots);
  the always-on runtime phrasing fixed.
- **CHANGELOG**: a populated `[Unreleased]` covering the three shipped
  features (in user words, schema v6 and the backup posture named) and
  the fixes.
- **DICTATION_PIPELINE_GUIDE** names `preview_before_type`;
  **USER_GUIDE** disambiguates the two preview mechanisms.

## Verification artifacts

- Doc guards **85 passed** (one dash of mine caught and fixed en route);
  Mermaid render guard **2 passed** after the trust-diagram edit; full
  suite **3088 passed, 37 skipped, 0 failures**.
- Coherence pass: the four front-door narratives (README, GETTING_STARTED,
  the index, WEB_DESK) now tell one story — arrive on the Desk, the rooms
  hang off its menu, the badge is the one trust answer.

## Left for the owner (surfaced, not taken)

- The six dead root strays (`CODEX_IDEAS.md`, `IDEAS.md`, `TODO.md`,
  `INTEGRATION_NOTES.md`, `HOLDSPEAK_REFACTORING.md`,
  `PLAN_TEST_FRAMEWORK.md`) — recommend delete or archive/.

## Acceptance criteria — re-checked

- [x] All ledger rows fixed or explicitly routed; guards green; the
      mirror check done AFTER SECURITY's fix, as planned.
