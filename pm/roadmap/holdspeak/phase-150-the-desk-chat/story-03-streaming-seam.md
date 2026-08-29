# HS-150-03 - The streaming seam (invoke_stream + typed deltas + frames)

- **Project:** holdspeak
- **Phase:** 150
- **Status:** backlog
- **Depends on:** HS-150-02
- **Unblocks:** HS-150-04
- **Owner:** unassigned

## Problem

No LLM call in HoldSpeak streams to a client: `InferenceRunner.invoke`
returns a blob; `MeetingIntel._chat_completion_stream`
(`holdspeak/intel/engine.py:337`) exists but only meeting analysis
consumes it. A thread turn must stream inside the same admission /
frozen-plan / receipt envelope (settled-design D3).

## Scope

### In (D3)

- `InferenceRunner.invoke_stream(request, adapter, *, on_delta, …)`
  beside `invoke`: same envelope; fallback ONLY before the first
  delta; receipt `succeeded` at done, `indeterminate` on cancel/error
  after first delta; cancellation via the existing `threading.Event`.
- Typed `Delta(kind ∈ text|reasoning|usage|done|error, text, meta)`
  yielded by the extended `_chat_completion_stream` (reads
  `delta.content`, `delta.reasoning_content`, final `usage`); the
  non-streaming path byte-untouched.
- A `StreamingProviderAdapter` (or a `dispatch_stream` on the existing
  adapter protocol) so the runner stays driver-blind.
- Frames `thread_turn_started`, `thread_delta`, `thread_turn_done`
  appended to `RUNTIME_FRAME_TYPES` and `web/src/runtime/frames.ts`.
- The persistence cadence helper (2 s / 500 chars / done) as a small
  pure class the service (HS-150-04) drives.

### Out

The HTTP route and the assembler (HS-150-04); any UI.

## Acceptance criteria

- [ ] Against a recorded SSE fixture (llama.cpp and OpenRouter
      shapes): deltas arrive in order with `seq`; `usage` lands in
      the final receipt evidence; the receipt is `succeeded`.
- [ ] Cancel mid-stream: `on_delta` stops within 250 ms, receipt
      `indeterminate`, no exception escapes.
- [ ] Provider error BEFORE first delta → fallback to the next
      assignment (existing disposition); AFTER first delta →
      `indeterminate`, no fallback.
- [ ] Frame drift test green; the three frames documented in
      `realtime_frames.py` comments.
- [ ] Cadence helper: flushes at 500 chars, at 2 s, and at done; never
      twice for the same text.

## Test plan

- **Unit:** `tests/unit/test_inference_runner_stream.py` (fixture SSE
  server via a fake adapter), `tests/unit/test_realtime_frame_registry.py`,
  cadence helper test.
- **Integration:** n/a until HS-150-08 (real `.43`).
- **Manual / device:** n/a.

## Notes / open questions

Keep the OpenAI SDK client (already the engine's HTTP layer); do not
introduce httpx streaming in parallel.
