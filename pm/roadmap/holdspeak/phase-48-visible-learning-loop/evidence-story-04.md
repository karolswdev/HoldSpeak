# Evidence — HS-48-04: Docs, the learning loop end to end

Write-once record. The docs now tell the loop as one story (dictate, correct in
one tap, learn, see what it learned, replay), the README and docs index frame it
as the local-first differentiator, and every claim is grounded in shipped code
with an honesty note about the bounded Jaccard learning.

## What shipped

**The guide tells the whole loop** (`docs/INTELLIGENT_TYPING_GUIDE.md` §12)
- Reframed the section intro as the five-step learning loop (dictate, correct,
  learn, see it, replay), then walked the steps in order.
- Rewrote "the moment of truth" into **Step 2: correct it in one tap** matching
  the shipped HS-48-03 ritual: Right (a no-write acknowledgement) vs Fix it
  (pre-scoped block/target in one tap, routed value pre-filled), on the dry-run
  result and every journal entry; honest, focus-safe confirmation. Screenshot:
  `assets/screenshots/correction-ritual.png`.
- Added **Steps 3 and 4: see what it learned** documenting the "What HoldSpeak
  learned" digest (window toggle, the three counts, by-block/target, per-correction
  "learned from N similar") and the inline trust chips on the dry-run result,
  journal entries, and Memory list. Screenshots:
  `assets/screenshots/learning-digest-week.png`, `trust-signals-journal.png`.
- Reworded the replay subsection as **Step 5**.
- Added **How the learning works, and its limits**: it is Jaccard token overlap
  (not retraining, no embeddings), off by default for routing until
  `corrections_enabled`, and local + gist-only + secret-filtered. No over-claim.

**README + index hooks frame it as the differentiator**
- Root `README.md`: the "Why it's different" bullet is now "It gets better at
  your voice, and shows you the proof" (digest + honest count + replay, local,
  off by default, no hidden retraining); the "See it learn" section gained the
  digest screenshot + an honest caption.
- `docs/README.md`: the dictation index entry now points at the full loop and the
  "What HoldSpeak learned" digest ("the proof, not the promise").
- `docs/DICTATION_COPILOT.md`: a "See also" entry ties feature ② (correction
  memory) to what it becomes over time (the loop + digest).

**Voice:** the new copy follows `DOCS_STYLE.md` / the phase humanizer rule (no em
or en dashes, no rule-of-three padding, no "not X but Y"); plain and direct.

## How to verify

- The digest + ritual + trust screenshots are real captures from
  `scripts/screenshot_learning_digest.py` (a real server over a seeded temp DB,
  no mic/LLM); all referenced image paths resolve (guarded below).
- Read §12 top to bottom: a newcomer learns that correcting teaches the tool and
  exactly where to see the proof.

## Tests run (read the output)

- `uv run pytest -q -k "doc_drift or link or doc_guard or doc"` — 65 passed,
  2 skipped. Covers: no stale DeterministicPlugin claims; **no dangling relative
  links** (the new index/See-also links resolve); the README **built-in-plugin
  count** still matches the registry (my README edits left it intact); and
  **every embedded image reference resolves** (the three new screenshots in the
  guide + the digest image added to the README).
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — 2401 passed,
  18 skipped (docs-only change; nothing in code moved).

## Invariants held

- Grounded in code: the loop description matches `db/journal.py`,
  `plugins/dictation/corrections.py`, `dictation_learning.py`, and the
  `learning-digest` / `journal/{id}/correct` routes shipped in HS-48-01..03.
- Honesty over hype: the limits note states Jaccard + local + off-by-default
  explicitly; no implied silent retraining.
- No `_built/` touched; no `--no-verify`, no `Co-Authored-By`.
