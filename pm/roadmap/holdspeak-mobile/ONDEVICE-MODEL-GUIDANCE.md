# On-device model guidance — iPhone 17 Pro Max (and the 12GB tier)

**Researched 2026-07-05.** Three parallel investigations (hardware limits, the model
landscape, quant + KV-cache math) cross-checked against the app's own inference code
(`OnDeviceBudget.swift`, `LlamaProvider.swift`, the vendored `LLM.swift` v2.1.0 +
llama.cpp xcframework). This is the standing answer to "what model, quant, context, and
config should we run on the phone."

## The verdict (one line)

**Qwen3-4B-Instruct-2507, Q5_K_M (imatrix), 16K context** — on Metal, non-thinking. It is
the convergent winner for HoldSpeak's workload (meeting summarize/extract + dictation
rewrite) on a thermally-constrained 12GB phone, and it is already the model witnessed
running on the iPad.

## Why the 4B, not the 8B (the counter-intuitive part)

A phone is **heat-bound, not RAM-bound**, for multi-minute work. Measured A18/A19-class
behavior: sustained inference throttles **~40% within a couple of minutes**; peak is
~10–14 tok/s for an 8B Q4 vs ~20–30 tok/s for a 4B Q4. Generation is memory-bandwidth
bound (~77 GB/s on A19), so a smaller model that **finishes before it cooks** beats a
bigger one that throttles mid-summary. The 8B's marginal quality edge does not survive
the thermal tax on a phone.

And the decisive feature for *meetings*: **Qwen3-4B-Instruct-2507 has a 256K native
context** (no YaRN/RoPE surgery) — so the model is never the context bottleneck; the app
is. It is an explicit **non-thinking instruct** model (no `<think>` blocks), so no latency
is wasted on hidden reasoning for straightforward extract/summarize calls. Top-of-class
instruction-following for its size (IFEval 83.4, MMLU-Pro 69.6), and ~2.5–3 GB of weights
leaves generous room for the KV cache.

The 8B (Qwen3-8B) stays the **A/B fallback** if we ever want more raw capacity and don't
mind the throttle: it beats Llama-3.1-8B across the board but only has 32K native context
(needs YaRN for long meetings) and must be pinned to non-thinking mode. **Gemma 3 12B-it
(QAT)** is the quality ceiling (IFEval 88.9, superb clean summaries) but at ~7–8 GB Q4 it
is tight on a phone once the KV cache grows — a desktop-hub model, not a phone model.

## Quant: Q5_K_M imatrix (with the trade spelled out)

At 4B the weights are cheap, so quant quality matters more per byte and we can afford to
spend it:

| Quant | 4B weights | Quality (vs Q8) | Gen speed | Use when |
|---|---|---|---|---|
| Q4_K_M (imatrix) | ~2.5 GB | sweet spot; small PPL bump | fastest | max speed/battery/headroom |
| **Q5_K_M (imatrix)** | **~2.9 GB** | **~60% of the way back to Q8** | ~10% slower | **the pick — near-top quality, still fast** |
| Q6_K (imatrix) | ~3.3 GB | within ~0.02 PPL of Q8 (near-lossless) | ~25% slower | quality-first, don't mind slower gen |
| Q8_0 | ~4.3 GB | lossless | slowest | overkill on a phone |

Always prefer an **imatrix** build (unsloth / bartowski) over a plain quant — same size,
measurably better, biggest effect at Q4–Q5. Never go below Q4 for extraction accuracy.

## Context: 16K is the shipped ceiling (and it's fine)

The app computes a safe context from live free memory and **clamps it to 16,384 tokens**
(`OnDeviceBudget.contextTokens(... ceiling: 16_384)`, `ReviewUI.contextCeiling`). 16K
(~12K words) covers most meetings in one pass; longer ones fall to the chunked map-reduce
(HSM-8-07). fp16 KV at 16K for a 4B ≈ 2.25 GB — comfortable inside the ~9–10 GB app budget
the increased-memory entitlement affords on a 12GB device.

**Optional tune:** because Qwen3-4B-2507 natively supports 256K and the 12GB phone has
headroom, we could raise `contextCeiling` to **32K** (fp16 KV ≈ 4.5 GB; 2.9 GB weights +
1 GB overhead ≈ 8.4 GB, still inside budget) so a two-hour transcript fits one pass. Safe
on this device; keep 16K as the cross-device default.

## Engine findings that matter as much as the model

1. **Sampling isn't tuned for extraction.** LLM.swift defaults to temp 0.8 / topK 40 /
   topP 0.95 / repeatPenalty 1.2. Qwen3 non-thinking's own recommended settings are
   **temp 0.7, topP 0.8, topK 20, minP 0** — and for *factual* extraction/summarization
   a lower temp (~0.3–0.5) is better still. This is a cheap, high-leverage quality win and
   is model-choice-independent.
2. **Verify Metal offload on the A19.** Metal is compiled into the xcframework and the
   code only forces CPU on the simulator (implying device offloads by default), but
   `n_gpu_layers` isn't explicitly pinned. Worth a one-line os_log on the real device to
   confirm all layers land on the GPU — the difference between seconds and minutes.
3. **KV-cache quantization + flash attention are NOT exposed by LLM.swift v2.1.0**
   (`contextParams` only sets `n_ctx`/`n_batch`). So the "q8_0 KV → 32K in 8 GB" lever
   from the quant research is unavailable without patching the engine. Not needed for the
   4B at 16K; relevant only if we ever chase 64K+ context on-device.
4. **Templates are handled per family now** (Gemma/Qwen/Llama-3/Phi/Mistral auto-picked in
   `LlamaProvider.autoTemplate`) — the old "ChatML for everything" caveat is dead. Model
   choice is unconstrained by templating.

## The download

In-app: **Settings → Models**. `Qwen3 4B Instruct 2507` is already in the curated list at
Q4_K_M; for this device prefer a **Q5_K_M imatrix** build via the HF search
(`unsloth/Qwen3-4B-Instruct-2507-GGUF` → `Qwen3-4B-Instruct-2507-Q5_K_M.gguf`, or the
bartowski equivalent). Q4_K_M is the safe cross-device default the list already ships.

## If we do engine work next (ranked)

1. Tune the on-device sampling for extraction (temp/topP/topK per Qwen3 non-thinking).
2. Confirm +, if needed, pin Metal `n_gpu_layers` on device.
3. (Optional) raise `contextCeiling` to 32K for the 12GB tier.
4. (Later) patch LLM.swift for `--flash-attn` + q8_0 KV if 64K+ on-device context is ever
   wanted.
