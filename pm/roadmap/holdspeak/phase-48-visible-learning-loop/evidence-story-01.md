# Evidence — HS-48-01: The learning digest ("What HoldSpeak learned")

Write-once record of what shipped for the digest. The phase rule that matters:
every number is real and comes from the same Jaccard matcher that nudges
routing. No second similarity, no inflation, quiet at N=0.

## What shipped

**Backend**
- `holdspeak/dictation_learning.py` — a pure `build_learning_digest()` over the
  journal + correction stores. It reuses `holdspeak.plugins.dictation.corrections.similarity`
  (the exact Jaccard function `best_match_in` thresholds on, default 0.5), so a
  correction's reported "N similar" is exactly the set of journal utterances the
  live pipeline would nudge. Read-only; no writes.
  - Window scopes the **activity** (corrections made, dictations corrected, the
    by-kind / by-block / by-target breakdowns) by `created_at` (ISO string
    compare). Per-correction **reach** is computed over the whole journal,
    because a correction nudges every matching utterance regardless of when it
    was said.
  - Total reach (`similar_nudged`) dedups: a transcript matched by two
    corrections counts once, so overlapping corrections never inflate it.
- `holdspeak/web/routes/dictation/pipeline.py` — `GET /api/dictation/learning-digest?window=week|all`.
  Fetches `ctx.corrections.list_for_display()` + the journal repo, hands them to
  `build_learning_digest`, returns the JSON. A bare server (no durable repos)
  returns a zeroed digest, never an error. The `enabled` flag carries the
  `corrections_enabled` posture so the view phrases coverage honestly ("now
  nudged" only when corrections actually route).

**UI** (`web/src/pages/dictation.astro` + `web/src/scripts/dictation-app.js`)
- A "What HoldSpeak learned" digest hero at the top of the Memory tab (the
  lightest home that reads as a reward; no new nav). Signal language: eyebrow +
  display headline, a week / all-time pill toggle, three stat cards (corrections
  made, dictations corrected, utterances nudged), an honest one-line summary,
  breakdown chips (routed-to-block / target-profile), and per-correction reach
  rows that show "learned from N similar" only when N > 0 (quiet at N=0).
- A teaching empty state ("Nothing learned this week / yet … correct a dictation
  and it shows up here").
- The digest body is JS-injected, so all its CSS lives in the page's
  `<style is:global>` block (the Astro-scoped-CSS trap). Verified the rules
  compiled global, not scoped.

## How to verify

- Build the bundle (Node 22.21): `(cd web && npm run build)` — completes; 0
  `holdspeak/static/_built/` tracked (gitignored).
- Screenshots (real server, seeded temp DB, no mic/LLM):
  `uv run python scripts/screenshot_learning_digest.py` →
  `docs/assets/screenshots/learning-digest-week.png`, `-all.png`, `-empty.png`.
  The populated shot shows reach chips; the empty shot shows the teaching state.

## Tests run (read the output)

- `uv run pytest -q tests/unit/test_dictation_learning_digest.py` — 7 passed.
  Asserts the reported "N similar" equals a direct `similarity()` computation,
  window scoping by `created_at`, by-kind/block/target breakdowns, the
  enabled-flag passthrough (counts unchanged), dedup of overlapping reach, and
  the bad-window fallback.
- `uv run pytest -q tests/integration/test_web_dictation_learning_digest.py` —
  6 passed. Endpoint over durable repos (real counts + reach), corrected-
  dictation count, bare-server zeroed digest, `corrections_enabled` posture, the
  page-content markers (`#learn-digest`, the window buttons, "What HoldSpeak
  learned"), and the is:global CSS guard (`.learn-stat{` present, no
  `learn-stat[data-astro-cid`).
- `uv run pytest -q tests/unit/test_dictation_routes_split.py` — 2 passed. Route
  table + count bumped to 36 (the new GET).
- **Real-speech e2e** (the phase's pitch, proven through actual voice):
  `tests/e2e/test_dictation_learning_digest_spoken_e2e.py` — opt-in
  (`HOLDSPEAK_SPOKEN_DICTATION_E2E=1`), auto-skips otherwise. macOS `say` →
  per-utterance `.wav` → Whisper (`Transcriber("base")`) → `/api/dictation/dry-run`
  (journals each run) → `/api/dictation/journal/{id}/correct` (teaches) →
  `/api/dictation/learning-digest`. Only the LLM is stubbed; the digest's counts
  come from the **real transcribed** journal. Observed run:
  - said "send the launch checklist to the team" → heard "Send the launch checklist to the team."
  - said "send the launch checklist to everyone" → heard "Send the launch checklist to everyone."
  - said "remember to book the conference room" → heard "Remember to book the conference room."
  - digest: `corrections_made=1`, `dictations_corrected=1`, `similar_nudged=2`
    (the two launch lines; the conference-room line stays out of reach),
    per-correction `similar=2`. 1 passed.
- Full slice: `uv run pytest -q -k "dictation or journal or corrections or learning" --ignore=tests/e2e/test_metal.py` — 380 passed, 5 skipped.
- Full suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — 2385 passed, 18 skipped.

## Invariants held

- Behavior-preserving: the digest is read-only; the correct path is untouched;
  routing stays byte-identical when corrections are off (no change to the
  pipeline). Full suite green.
- Honest over hype: one matcher (`corrections.similarity`), quiet at N=0,
  `corrections_enabled` posture surfaced, overlapping reach deduped.
- Local-first, no `_built/` tracked, no `--no-verify`, no `Co-Authored-By`.
