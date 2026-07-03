# Evidence — HSM-18-01 — The dictation pipeline client + authoring/preview screen

**Status:** done (2026-07-03), on `holdspeak-mobile/hsm-18-01-teleprompter`. The client spine
and the typed shell teleprompter landed in earlier increments (PR #150 lineage); this closes
the story: the voice teleprompter with an honest receipt, the readiness strip, and the flag
that makes the receipt true.

## 1. The receipt was a lie — `raw` fixes it

`/api/dictation/remote` always re-ran the pipeline on the sent text, so a client that
previewed a dry-run receipt and sent its `final_text` got it **processed twice** — the
rewrite is not idempotent, so what previewed was not what typed (a latent bug in the landed
shell screen). Now:

- **Hub:** `raw: true` on the remote route delivers the text VERBATIM — no pipeline, no
  macro dispatch. Absent/false stays byte-identical (locked by
  `test_raw_absent_stays_byte_identical`). 4 new tests in
  `test_web_routes_remote_dictation.py` (verbatim delivery, macro-skip, focused threading,
  default unchanged) — 15/15.
- **Client:** `IDesktopClient.sendRemoteDictation(text:target:raw:)` with source-compatible
  conveniences (every pre-18-01 call site unchanged); the wire carries `"raw": true` only
  when true (`testRawRidesTheWireOnlyWhenTrue`, body-capturing stub).
- **The shell teleprompter's Send now passes `raw: true`** — what previewed is exactly what
  lands.

## 2. The voice teleprompter (DictateView, the main app)

The Phase-15 voice surface (hold-to-talk → on-device WhisperKit → deliver) gains the
story's two missing pieces:

- **The readiness strip** — `GET /api/dictation/readiness` fetched on probe, rendered as
  chips: the hub's own `ready` verdict, the resolved backend, the live detected target.
  No snapshot renders no strip, never an error.
- **Preview first** (opt-in toggle, persisted, **off by default** — preview is never the
  default story): release runs the dry-run and arms a **receipt card** — exactly what will
  type, its destination, latency + blocks + warnings chips — with Discard / Send. Send
  commits verbatim (`raw`). If the hub can't preview mid-flight, the words fall back to the
  exact non-preview lane (never lost). Off = the historical direct flow, untouched.

Screenshots (iPad Air 13-inch (M4) simulator):
- [`hsm-18-01-receipt-armed.png`](./screenshots/hsm-18-01-receipt-armed.png) — the armed
  receipt over the read-back, "Preview first ON".
- [`hsm-18-01-readiness-strip.png`](./screenshots/hsm-18-01-readiness-strip.png) — the
  seeded strip.

## 3. The real-hub proof (live, not seeded)

A REAL `MeetingWebServer` (scratch DB, the owner's real config untouched on disk) served
`127.0.0.1:8123`; the simulator app connected to it live (`HS_DEMO_DICTATE=live`, peer env
pointing at the hub):

- [`hsm-18-01-live-hub-readiness.png`](./screenshots/hsm-18-01-live-hub-readiness.png) —
  "Connected · words land on Karol's Mac" + the strip rendered from the real readiness
  payload: **Pipeline ready ✓ / openai_compatible / → Claude Code** — the hub genuinely
  detected the live coding session as the dictation target.
- Real `POST /api/dictation/dry-run` receipts curled from the same hub: real project
  (`holdspeak`, git anchor), real blocks (3 global), real target detection, and the honest
  degraded state — the configured `127.0.0.1:8082` llama-server being down rides the
  receipt as `warnings` with verbatim `final_text` (the exact state the receipt card's
  warning chip renders).

## Honest boundaries

- **The spoken-word leg on real metal** (mic → WhisperKit → dry-run → receipt → raw send,
  on the device) rides the phase gate **HSM-18-06** — the voice pipeline itself is the
  proven Phase-15 path; what 18-01 added around it is sim-proven + live-hub-proven.
- A real LLM rewrite in the receipt was attempted and honestly failed three ways: the
  configured local llama-server is down, `.43`'s forced grammar corrupts the classifier
  JSON (`extra key 'ai_prompt_context'`), and in-process `llama_cpp` segfaults on the local
  Qwen3-4B GGUF (exit 139). The receipt's warning-path render is the honest outcome; a
  clean rewriter endpoint is an 18-06 runway item (owner's endpoint call).

## Suites

`uv run pytest -q tests/unit` **2401 passed** · `tests/integration` **685 passed** ·
`swift test` **417 passed** · meeting-capture app xcodebuild green · companion-shell app
xcodebuild green.
