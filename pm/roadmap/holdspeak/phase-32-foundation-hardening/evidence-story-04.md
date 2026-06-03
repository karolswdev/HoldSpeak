# Evidence — HS-32-04 (CI end-to-end smoke test, core path)

**Shipped:** 2026-06-02. The core promise — *real audio in → real transcript out
→ injected text* — now has an **ungated** test that runs on every push and
asserts on the **produced text**. Previously this was validated only behind the
`metal` / `spoken_e2e` markers, which never run in CI, so a transcription
regression left CI green.

## The fixture (generated once, committed, shared by both CI envs)

`tests/fixtures/core_path_smoke_16k.wav` — a 16 kHz mono 16-bit WAV (~93 KB,
2.79 s) of *"the quick brown fox jumps over the lazy dog"* (a pure-words pangram
— no digit-normalization ambiguity). Generated **once** on macOS with
`say -o … --data-format=LEI16@16000 --file-format=WAVE "…"` and **committed**, so
both CI environments and local runs read the same bytes — no `say`/TTS or
microphone at test time. (`.gitignore`'s `tests/fixtures/*.wav` rule got a
negation exception for this one small file.)

## The test — `tests/integration/test_core_path_smoke.py`

- `test_core_path_audio_to_injected_text`: loads the WAV (stdlib `wave` + numpy,
  no scipy), runs the **real** `Transcriber(model_name="tiny")` →
  `TextProcessor.process` → a capturing typer (the injection seam, recorded not
  sent to a keyboard), and asserts the produced text contains `"quick brown fox"`
  and `"lazy dog"` (normalized substring, tolerant — not exact equality). This is
  the exact transformation `WebRuntime._transcribe_and_type` performs to get the
  text it hands the typer.
- `test_core_path_smoke_assertion_is_not_vacuous`: a mutation guard proving the
  substring assertion *rejects* a wrong transcript (so a broken transcription
  path turns the smoke test red) — runs even with no backend.
- `_require_backend()` skips cleanly where no Whisper backend is installed (e.g.
  the Linux unit job), so the test is **not** gated behind a never-run marker —
  it runs for real where a backend exists.

## Where it runs in CI (ungated, every push)

The **macOS integration job** (`integration-tests`, `macos-14` Apple Silicon)
runs `tests/integration/` on every push, and `mlx-whisper` is a **core dependency**
on darwin arm64 — so the smoke test executes with real Whisper there (the model
`mlx-community/whisper-tiny-mlx`, ~75 MB, downloads on first use). Documented in
`.github/workflows/test.yml`. The ubuntu unit job (`tests/unit/`, no backend)
never sees it; it isn't a separate gated job, it's a normal test on a job that
already runs every push.

## Verification (run locally, real mlx Whisper)

- `uv run pytest -q tests/integration/test_core_path_smoke.py` → **2 passed in
  1.24s** (real `whisper-tiny-mlx` on the committed WAV → exact transcript "The
  quick brown fox jumps over the lazy dog.").
- **Mutation check (shown):** feeding silence (`np.zeros`) through the same path
  yields an **empty** transcript → `"quick brown fox" in normalized` is `False` →
  the assertion would go **red**. The test catches a broken transcription path.
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1948 passed, 14
  skipped** (+2). Test + workflow ruff/yaml clean.
- Phrase candidates were checked against `tiny` first: the pangram transcribes
  exactly; "testing one two three…" normalizes digits ("1, 2, 3"), so the
  pangram was chosen for robust word-substring matching.

## Decisions

- **Smoke model = `tiny`** (the deferred decision): smallest viable, deterministic
  greedy decode, transcribes the fixed fixture exactly; substring assertion with
  tolerance. (Resolves the phase's "which Whisper model" deferral.)
- **Seam-level, not full-`WebRuntime`.** Driving the real
  `WebRuntime._transcribe_and_type` was tried and rejected for CI: constructing
  the full runtime drags in the author's config and fires the DIR-01 dictation
  pipeline (LAN calls) + DB/plugin-host setup — non-deterministic and slow. The
  `_transcribe_and_type` *wiring* (transcript → typer) is already covered by
  `test_web_runtime` with a fake transcriber; this smoke fills the complementary
  gap (real audio → real transcript). Together they cover the full path in CI.

## Discovered (out of scope — flagged)

- Constructing the full `WebRuntime` logs `Could not load projects for detector
  at startup: 'Database' object has no attribute 'get_all_projects_for_detector'`
  — a Phase-31 db-decomposition miss (the method moved to a repo, e.g.
  `db.projects.…`). **Non-fatal** (caught + warned), but a real latent bug. Worth
  a follow-up (candidate for HS-32-05/06 or a separate fix).
