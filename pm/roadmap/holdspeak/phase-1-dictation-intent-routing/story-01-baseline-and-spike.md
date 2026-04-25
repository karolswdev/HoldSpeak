# HS-1-01 — Step 0: Baseline + llama-cpp/Qwen spike

- **Project:** holdspeak
- **Phase:** 1
- **Status:** ready
- **Depends on:** HS-0-01, HS-0-02
- **Unblocks:** HS-1-02 (contracts), HS-1-04 (LLM runtime)
- **Owner:** unassigned

## Problem

Before any pipeline code is written, we need three measured facts:

1. The current typing-path latency (hotkey release → keyboard injection)
   on the reference Mac, so DIR-R-005 (≤250ms median pipeline overhead)
   is meaningful relative to a real number.
2. Whether `llama-cpp-python` is installed with Metal support on this
   machine. The existing `intel.py` path uses GGUF models but the
   Metal-enabled wheel is not guaranteed by `pip install`.
3. Whether `Qwen2.5-3B-Instruct-Q4_K_M.gguf` with a fixed GBNF grammar
   actually meets §7.2's first-token ≤250ms / sustained ≥40 tok/s
   targets on this machine.

Per the spec (§12.1), this is the entry-criteria spike for the rest of
the phase. If the targets fail, we drop the default to Qwen2.5-1.5B
*before* designing around the wrong number.

## Scope

- **In:**
  - `scripts/bench_baseline_typing.py` — captures hotkey-release-to-typing latency over a 50-utterance fixture (uses existing `Transcriber` + mocked `TextTyper`). Output appended to evidence as `00_baseline_typing_latency.txt`.
  - Verify `llama-cpp-python` is installed; if not, install via `uv pip install 'llama-cpp-python>=0.2.90'` (Metal-enabled wheel — re-build with `CMAKE_ARGS="-DGGML_METAL=on"` if the prebuilt wheel isn't Metal).
  - Download `Qwen2.5-3B-Instruct-Q4_K_M.gguf` from `bartowski/Qwen2.5-3B-Instruct-GGUF` (manual download, place at `~/Models/gguf/`).
  - `scripts/spike_qwen_grammar.py` — loads the model, compiles a fixed GBNF grammar for a 4-block taxonomy, runs a 10-prompt classification fixture, records first-token latency, total latency, output, and grammar-compliance for each.
- **Out:**
  - Any code under `holdspeak/plugins/dictation/` (that's HS-1-02 onward).
  - Block-config schema parsing (HS-1-05 — the spike uses a hard-coded grammar string).
  - Multi-tier benchmark across 1.5B / 3B / 7B — that's HS-1-10. This story only validates the proposed default (3B).

## Acceptance criteria

- [ ] `scripts/bench_baseline_typing.py` exists and runs to completion against the 50-utterance fixture; median + p95 reported.
- [ ] `scripts/spike_qwen_grammar.py` exists and runs end-to-end on the reference Mac; per-prompt first-token + total latency recorded.
- [ ] `llama-cpp-python` reports `n_gpu_layers > 0` after model load (Metal active). If not, evidence file documents the rebuild command and re-run.
- [ ] All 10 spike prompts return JSON conforming to the GBNF grammar (zero malformed outputs — that's the whole point of grammar-constrained decoding).
- [ ] First-token latency on Qwen2.5-3B-Q4_K_M, warm: median ≤250ms (DIR-R-001). If exceeded, story does NOT close as `done`; the next story flips to "block reduction" mode and the default-tier decision in phase-status is revised.
- [ ] Evidence file `docs/evidence/phase-dir-01/<TS>/00_baseline_typing_latency.txt` exists.
- [ ] Evidence file `docs/evidence/phase-dir-01/<TS>/51_model_tier_benchmark.md` contains an initial entry for the 3B tier with raw numbers.

## Test plan

- **Unit:** n/a (this is a measurement spike, not production code).
- **Integration:** Run both scripts on the reference machine. Capture stdout + return codes.
- **Manual:** Spot-check that the 10 spike prompts cover the four taxonomies in the spec (`ai_prompt_buildout`, `code_exercise`, `documentation_exercise`, plus one no-match case).

## Notes / open questions

- Model download is **manual**. DIR-01 explicitly forbids auto-download (spec §13 risk #7). The story closes only after a human downloads the file and re-runs the spike.
- If the Metal wheel rebuild is needed, capture the rebuild stdout in evidence — future contributors will hit the same step.
- The 10-prompt fixture is intentionally small. HS-1-10 expands to a larger labeled set across all three tiers; this story is "is the proposed default in the right ballpark?" only.
- If Qwen2.5-3B fails the latency target, the resolution is to revise the default to 1.5B in `current-phase-status.md` decision log, NOT to abandon the phase.
