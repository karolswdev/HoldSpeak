# Evidence — HS-48-03: Frictionless correction ritual (right / wrong, in flow)

Write-once record. Correcting is now a one-tap decision on the dictation result
*and* on every journal entry, reusing the existing correct path. No new write
primitive; the dictation bundle stays focus-safe.

## What shipped

**One reused ritual** (`web/src/scripts/dictation-app.js`)
- `correctionRitual(opts)` renders a single inline component; `wireFixit(root)`
  wires every `.fixit` inside a container (idempotent via `data-wired`). It is
  used by both the dry-run moment (`renderMomentOfTruth` -> `wireFixit(host)`)
  and every journal entry (`renderJournalEntry` -> `renderJournal` calls
  `wireFixit(list)`). Reuse, not duplication — the existing `submitMomentFix`
  seam was extended, not forked (it now resolves the closest `.fixit` instead of
  global ids, so many entries coexist).
- "Right" is a calm client-only acknowledgement ("Glad it landed. Nothing to
  teach.") — no server call, no write churn, routing untouched.
- "Wrong" opens the existing correct path pre-scoped: with a target present you
  pick block vs target in one tap; with only one teachable dimension it jumps
  straight to that form. The routed value is the placeholder, so a fix is one
  decision, not a blank kind/value form. Submit reuses
  `POST /api/dictation/journal/{id}/correct` and shows the HS-48-02 honest
  coverage line (`correctionDoneText`), then flags the card corrected and
  refreshes the digest hero.
- Corrected entries show no ask (the "✓ corrected" badge already speaks); avoids
  re-teach churn.

**Styling** (`web/src/pages/dictation.astro`, `<style is:global>`)
- `.fixit-*` rules (global, because the ritual DOM is JS-injected). On a journal
  card it reads as a quiet footer rule; on the dry-run it sits in the accent
  `.moment` card. Reuses `.moment-q` / `.moment-done` / `.moment-check`.
- Fixed a latent bug: an author `display` rule was overriding the `[hidden]`
  attribute, so the scope/form panels leaked open. Added
  `.fixit-*[hidden] { display: none }` so `[hidden]` wins. (Same shape would have
  affected the old `.moment-form`; now correct.)

## Focus-safe (the standing invariant)

Zero `.focus()` in the dictation script bundle — panels reveal on click and
keyboard focus stays where the user put it. (My explanatory comment was reworded
so it no longer trips the literal-string guard.)

## How to verify

- `(cd web && npm run build)` — completes; 0 `_built/` tracked.
- Screenshots (`uv run python scripts/screenshot_learning_digest.py`):
  `docs/assets/screenshots/trust-signals-journal.png` (each uncorrected entry
  shows "Was that right? · Right · Fix it →"; the corrected entry shows none) and
  `correction-ritual.png` (one tap opens the pre-scoped block fix inline).

## Tests run (read the output)

- `uv run pytest -q tests/integration/test_web_dictation_correction_ritual.py` —
  7 passed: the ritual ships (`correctionRitual`/`wireFixit`, the right/wrong +
  scope markers, reuse of `/correct` and `submitMomentFix`); it is wired into
  both the dry-run host and the journal list; it is focus-safe (no `.focus()`);
  the CSS is global; the `#dry-moment` host is present with no autofocus; and the
  correct path the ritual posts to teaches + marks the entry corrected.
- `uv run pytest -q tests/integration/test_dictation_moment_of_truth.py` —
  6 passed (the existing moment guard still holds: `submitMomentFix` present,
  zero `.focus()`).
- Slice: `uv run pytest -q -k "dictation or journal or corrections or learning or moment" --ignore=tests/e2e/test_metal.py` — 396 passed, 6 skipped.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — 2401 passed, 18 skipped.

## Invariants held

- No new write primitive: the ritual posts to the existing correct endpoint;
  secret-filter + `corrections_enabled` honesty come for free (HS-48-02 copy).
- Behavior-preserving: "Right" makes no call; routing is untouched; corrected
  entries don't re-prompt. Full suite green.
- Focus-safe; local-first; 0 `_built/` tracked; no `--no-verify`, no `Co-Authored-By`.
