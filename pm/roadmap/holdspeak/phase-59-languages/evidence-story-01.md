# Evidence — HS-59-01: The language knob, end to end

**Date:** 2026-06-11
**Branch:** `phase-59-languages`

## 1. What shipped

- **`holdspeak/languages.py`** (new, pure — import-statement-locked): the
  vendored Whisper registry (99 codes incl. `yue`), `normalize_language`
  (accepts `auto`/codes/English names, case/space-tolerant, actionable
  `ValueError` otherwise), `language_choices` (Auto-detect first, names
  A-Z). No whisper import can ever run at config time.
- **`ModelConfig.language: str = "auto"`** — older config shapes coerce
  forward to the default (tested).
- **`Transcriber(language=…)`**: the facade normalizes once and threads to
  BOTH backends. The byte-identical invariant is structural: a pinned code
  adds `language=<code>` to the backend call; auto adds **nothing** (the
  kwarg is conditionally built, so the auto call shape is exactly the
  pre-knob call — asserted per backend with fake modules). The mlx warm-up
  call now warms in the pinned language when set.
- **All four construction sites threaded** (web_runtime, `main.py`, the
  import route factory, the import CLI) — locked by a source-marker test
  so a fifth site or a regression is caught.
- **The settings boundary**: PUT `/api/settings` validates via the
  registry (a typo fails the write with the actionable message, and the
  bad write changes nothing — asserted), stores the normalized code.
- **The settings UI**: a "Spoken language" select in the Voice typing
  section (Auto-detect + 99 names), with the honest hint ("Auto-detect
  works well for longer speech; pin your language if short utterances get
  misdetected"). The page's option list is locked in lockstep with the
  Python registry by a set-equality test, so UI and backend cannot drift.

## 2. A find + a fix along the way

The `web_runtime` test fixtures stub `config` with `SimpleNamespace`, so
the strict attribute read exploded four tests; the site now reads the knob
defensively (`getattr(..., "auto")`, the same style as the other three
sites) and the five `FakeTranscriber` stubs learned the kwarg.

## 3. Live screenshot

`screenshots/story01-language-setting.png` — the Voice typing section with
the Spoken language select (Auto-detect) and the hint, zero page errors.

## 4. Tests

```
$ uv run pytest -q tests/unit/test_language_knob.py tests/integration/test_settings_language_ui.py
18 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2663 passed, 17 skipped
```

(2645 → 2663: 14 unit + 4 integration.) `npm run build` clean.
