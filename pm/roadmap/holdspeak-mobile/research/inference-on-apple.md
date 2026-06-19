# Hosting 4B–12B LLMs on iPhone and iPad (research canon)

**Status:** source canon for Phase 5 (Local Inference, Track F) and an input to
Phases 3 (Whisper device defaults) and 11 (thermal/sustained behavior).
**Provenance:** captured from the owner's research brief on 2026-06-18 — the
"information around the inference engine" promised before Phase 5. Inline
citation tokens from the source tool were stripped for legibility; the
engineering content is preserved verbatim in substance. **Every performance
number here is a planning estimate, not a vendor benchmark** — HSM-5-01 replaces
them with on-device measurement before the engine is picked.

---

## Executive summary

For **inference only**: **4B and 6B dense decoder LLMs are practical on modern
iPhones and iPads**; **7B is practical on A17 Pro and M-series with aggressive
quantization**; **12B is an iPad-first target wanting 16GB-class memory or a
hybrid/offload architecture**. The gating constraints are not nominal parameter
count but a combination of **available RAM, quantized weight size, KV-cache growth
with context length, runtime workspace overhead, storage budget, and sustained
thermal headroom**.

Apple's on-device stack is strongest with **Core ML** (shipped apps), **Core ML
Tools** (conversion/optimization), and **Metal/MPSGraph or BNNSGraph** (custom
execution). Among third-party runtimes, **llama.cpp** and **MLC-LLM** are the
relevant embedded iOS/iPadOS runtimes; **Ollama** and **vLLM** are **server-side
companions, not in-app iOS runtimes**.

Production rules of thumb: **quantized weights dominate static memory**, **KV
cache dominates long-context growth**, **mobile UX is limited by sustained
power/thermal behavior more than peak benchmarks**. Apple's `Foundation Models`
framework and the newer `Core AI` are **not** drop-in replacements for hosting
arbitrary GGUF/Core ML open-weight models inside an app.

**Defensible recommendation today:**
- **iPhone baseline:** A17 Pro / 8GB-class or newer for 4B–7B local chat at 4-bit/3-bit.
- **iPad baseline:** M1/M2/M3/M4, preferring **16GB** SKUs for 12B-class.
- **Quantization default:** 4-bit PTQ for shipping; 3-bit only when 7B/12B must fit tighter budgets and you can tolerate quality loss.
- **Architecture default:** on-device for privacy-sensitive, low-latency, short-context tasks; secure offload when prompts are long, concurrency matters, or 12B quality is needed on phones.

---

## Hardware envelope

Three hard walls, in order:

1. **RAM** — the first wall. Apple Intelligence floor is iPhone 15 Pro / iPad mini
   (A17 Pro) / iPad M1+, and Apple's own on-device models use **~7GB storage** —
   a useful sanity check that multi-GB assets are normal and must be budgeted
   explicitly, not silently absorbed into the app bundle.
2. **Memory bandwidth** — the second wall, dominant during token decode (decode is
   bandwidth-bound once weights fit). M2 ≈ 100GB/s, M4 ≈ 120GB/s; unified memory
   lets engines share one pool without copies. The A-series → M-series jump often
   feels larger in practice than NE TOPS marketing suggests.
3. **Thermals + battery** — the third wall. "Works in a short demo" is not enough;
   validate **sustained** decode, repeat-chat cadence, and charging-vs-battery on
   real devices.

### SoC fit (practical targets)

| SoC class | Representative | RAM | NE | ~Bandwidth | Practical local LLM target |
|---|---|---|---|---|---|
| Pre-A17 / pre-M1 | older iPhone; pre-M1 iPad | 4–6GB | older | n/a | **not a 4B–12B target**; tiny models or hybrid |
| **A17 Pro** | iPhone 15 Pro; iPad mini A17 Pro | ~8GB | 16-core | n/a published | 4B–6B comfortable q4; 7B feasible q4/q3; 12B hybrid |
| **M1** | iPad Pro M1 | 8GB / 16GB (1TB+) | 16-core | <100GB/s | 7B q4 good; 12B q4 only on 16GB |
| **M2** | iPad Pro M2 | 8GB / 16GB (1TB+) | 16-core | 100GB/s | 7B q4 strong; 12B q4 serviceable on 16GB |
| **M3** | iPad Air M3 | 8GB | 16-core | ~100GB/s | 4B–7B excellent; 12B only with careful q3/q4 |
| **M4** | iPad Pro M4 | 8GB / 16GB (1TB+) | 16-core, 38 TOPS | 120GB/s | 7B q4 very good; 12B q4 viable on 16GB |

---

## Software stack

### Apple-native

| Component | Role | Note |
|---|---|---|
| **Core ML** | shipping inference in apps | mainstream app-facing runtime; spans CPU/GPU/NE |
| **Core ML Tools** | convert/optimize/quantize | direct PyTorch/TensorFlow conversion recommended |
| **ML Program** | preferred model representation | typed tensors + precision control |
| **Stateful models / MLState** | KV-cache persistence | **iOS 18 / iPadOS 18+** |
| **MPSGraph** | custom graph execution | WWDC24 transformer improvements |
| **BNNSGraph** | CPU/real-time graph execution | ahead-of-time compile, no runtime alloc |
| **ML Compute** | older accel layer | not the primary new-app path |
| **Create ML** | train small models on Mac | not the path for hosting 4B–12B open weights |
| **Core AI** | newest Apple on-device AI framework | promising; ecosystem newer than Core ML |
| **Foundation Models** | Apple's own models + PCC variants | not embedding arbitrary external weights |

Takeaway: **Core ML + Core ML Tools** is the conservative shipping choice;
**MPSGraph** is the custom-kernel escape hatch; **BNNSGraph** is the CPU/real-time
option; **Core AI** is the one to watch.

### Third-party runtimes

- **llama.cpp / GGML / GGUF** — most relevant lightweight embedded path. Apple
  Silicon is first-class (NEON/Accelerate/Metal), 1.5–8-bit quantization, GGUF is
  a single-file **mmap-friendly** format, ships an **XCFramework** for iOS.
- **MLC-LLM** — the most "mobile-app-minded" path: iOS/iPadOS via Metal, a real
  `mlc_llm package` flow, Swift integration, compiled model libraries.
- **Ollama** — great desktop/server serving; **not** an iOS embedded runtime →
  treat as a Mode-B companion on a nearby Mac/LAN box.
- **vLLM** — high-throughput server (PagedAttention, continuous batching, prefix
  caching); maps to **server/offload** (Mode B/C), not in-app.

---

## Model sizing, quantization, memory budgeting

**Inference memory buckets:** weights + activations/workspace + tokenizer/runtime
overhead + **KV cache**. (Training adds gradients + optimizer states + saved
activations — which is why on-device fine-tuning of 4B–12B is not a plan; adapt
offline, ship an inference artifact.) KV cache grows ~linearly with sequence
length (attention compute is quadratic). Core ML `MLState` (iOS 18+) exists to
persist KV cache across decode steps.

**Quantization (Core ML Tools paths):** data-free PTQ (round-to-nearest),
activation quantization with calibration, **GPTQ** layerwise, QAT, and
**palettization** (weight clustering). Hierarchy: 8-bit (easy, often too big for
7B+ on phones) → **4-bit PTQ (deployment default)** → 3-bit (rescue for fitting
7B/12B, noticeable quality loss on coding/instruction-following) → GPTQ (stronger
at 3–4 bits) → QAT (best low-precision quality, offline only). **Prefer Core ML
Tools optimization APIs over "quantize elsewhere and hope"** — Core ML defaults
are tuned for Apple hardware.

### Budgeting (engineering estimate; single-stream, ~2K–4K ctx, 0.3–0.8GB overhead, 15–30% headroom)

| Size | FP16 | INT8 | 4-bit | 3-bit | Est. peak RAM (q4 / q3) | Recommended |
|---|--:|--:|--:|--:|--|--|
| **4B** | ~8.0GB | ~4.0GB | ~2.0GB | ~1.5GB | q4 ~2.7–4.0 / q3 ~1.9–3.0 | q4 default; q3 tighter phones |
| **6B** | ~12.0GB | ~6.0GB | ~3.0GB | ~2.25GB | q4 ~4.0–5.3 / q3 ~3.0–4.2 | q4 default |
| **7B** | ~14.0GB | ~7.0GB | ~3.5GB | ~2.6GB | q4 ~4.6–6.0 / q3 ~3.3–4.7 | q4 on A17/M; q3 if tight |
| **12B** | ~24.0GB | ~12.0GB | ~6.0GB | ~4.5GB | q4 ~7.5–9.5 / q3 ~5.8–7.8 | q4 on 16GB iPad; q3/hybrid else |

### Feasibility by device class

| Device class | 4B | 6B | 7B | 12B |
|---|---|---|---|---|
| A17 Pro / 8GB iPhone | good q4/q3 | good q4 | feasible q4/q3, careful ctx | usually hybrid/offload |
| A17 Pro / iPad mini | good | good | feasible | marginal unless aggressive |
| M1/M2/M3 8GB iPad | very good | very good | good | borderline; prefer server |
| M1/M2/M4 16GB iPad Pro | excellent | excellent | excellent | viable q4; watch thermals/ctx |

---

## Conversion, packaging, deployment

### Core ML pipeline (preferred Apple-native)

```
PyTorch/TensorFlow → Core ML Tools direct conversion → ML Program
  → Core ML optimization → KV-cache states / flexible shapes → iOS/iPadOS app
```

`torch.jit.trace` → `ct.convert(convert_to="mlprogram",
minimum_deployment_target=ct.target.iOS18, compute_precision=FLOAT16)`. TorchScript
tracing is the stable path; `torch.export` is newer/beta. **`onnx-coreml` is
frozen** — ONNX is interchange only, not the preferred modern Core ML path.

Pitfalls: dynamic control flow + unsupported ops are the main friction;
`EnumeratedShapes` preserves the NE path better than overly-dynamic reshapes;
model KV cache **as state** (MLState), not manual tensor I/O; float16 is the sweet
spot (forcing float32 can exclude the NE path).

### MLC-LLM pipeline

`mlc_llm convert_weight --quantization q4f16_1` → `mlc_llm gen_config` →
`mlc_llm package` (builds runtime + tokenizer + model libs; can bundle weights or
download at runtime; exposes `estimated_vram_bytes` as a budget proxy).

### llama.cpp / GGUF pipeline

`cmake -B build -DGGML_METAL=ON` → `llama-cli` / `llama-bench`; iOS via the
published **XCFramework** as a Swift Package binary target; GGUF mmap suits
memory-mapped weight loading. `convert_hf_to_gguf.py` flags evolve per release.

### Deployment checklist

1. Choose architecture (Core ML / MLC-LLM / llama.cpp+GGUF).
2. Freeze the target device class.
3. Set a memory budget (table above) incl. context-length assumptions.
4. Quantize **offline**; devices are not quantization/fine-tuning hosts.
5. Model KV cache intentionally (MLState iOS 18+ or runtime-native).
6. Prefer weight **download after install** unless offline-first first launch is required.
7. Secure storage / file protection for weights and any retained prompts.
8. Benchmark on **physical devices**, not Simulator/tethered-only.
9. Profile power/memory/background with Instruments + XCTest metrics.
10. Add a **server fallback** before shipping 12B broadly on phones.

---

## Performance expectations (planning ranges, NOT vendor benchmarks)

Methodology when exact benchmarks are absent: measure a representative artifact
(`llama-bench`); treat decode throughput as tied to quantized weight size +
bandwidth once it fits; treat prefill latency as sensitive to sequence length; cap
optimism by **sustained thermal** behavior on passively-cooled devices.

| Device class | 4B q4 | 6B q4 | 7B q4 | 12B q4 |
|---|--:|--:|--:|--:|
| A17 Pro / 8GB phone | ~8–18 tok/s | ~6–12 | ~4–10 | ~2–5 if it fits |
| 8GB M-series iPad | ~12–25 | ~8–16 | ~7–14 | not a good default |
| 16GB M-series iPad Pro | ~15–30 | ~10–20 | ~8–18 | ~3–8 |
| 16GB M4 iPad Pro | ~20–40 | ~14–28 | ~12–24 | ~5–12 |

Use these to judge **instant / interactive / marginal**, then replace with
device-lab measurement before release.

---

## Architecture options (map directly onto charter Modes A/B/C)

- **On-device only (charter Mode A)** — best for privacy-core, short prompts,
  modest context, single session. Strongest fit for **4B–7B** on A17 Pro /
  M-series. Core ML, MLC-LLM, llama.cpp all match.
- **Split execution (charter Mode B, "Hybrid recommended")** — simple replies /
  local classification / drafting on device; escalate long-context synthesis,
  retrieval-heavy reasoning, codegen, or 12B-quality to a server / nearby desktop.
  The most practical mass-market architecture. (Apple's own PCC pattern mirrors
  this for its model ecosystem.)
- **Secure offload (charter Mode C, "Endpoint")** — when you want vLLM features
  (PagedAttention, continuous batching) or a nearby Mac running Ollama. Best
  quality/concurrency, weakest offline story.

---

## Security, licensing, validation

- **Privacy:** on-device keeps user data local (Core ML is local by design); use
  `NSFileProtectionComplete`-class protection for stored weights/prompts/caches;
  ATS/HTTPS with narrow exceptions when offloading. Sending a prompt to any
  backend changes the privacy boundary regardless of how local the fallback is.
- **Background:** do **not** assume continuous background inference. `BGProcessingTask`
  is system-scheduled/idle-only; iOS/iPadOS 26 adds continuous background tasks +
  background GPU access but it's still constrained. Treat backgrounded model work
  as best-effort, checkpoint aggressively.
- **Licensing (redistribution is redistribution):** Llama 3 → Meta Llama 3
  Community License; Gemma → Gemma Terms + Prohibited Use Policy; Qwen → often
  Apache-2.0 but verify per model card. Keep a **license manifest** (upstream id +
  revision, conversion script revision, quant method, original license text,
  redistribution + prohibited-use obligations).
- **CI:** Xcode Cloud + XCTest metrics (`XCTMemoryMetric`, `XCTCPUMetric`,
  `XCTStorageMetric`, timing/signpost) + Instruments Power Profiler. Matrix:
  cold-start load, first-token latency (short + long prompts), sustained decode
  tok/s over minutes, peak memory, storage writes during cache growth, battery
  regressions, fallback-switch correctness, airplane-mode offline behavior.

---

## Open questions / limitations

- No official Apple token/s tables for arbitrary 4B–12B open weights on iPhone/iPad
  → the perf tables are planning estimates; replace with a runtime-specific
  physical-device suite using the exact shipped artifact.
- `Core AI` is new; the public ecosystem for arbitrary mobile LLM deployment is
  newer than Core ML's.
- Current App Store app-size constraints not re-verified here — check App Store
  Connect before bundling multi-GB weights.
- Some current iPhone RAM disclosures are partly secondary (Apple support pages are
  not uniform).

**Core conclusion:** 4B/6B are the phone sweet spot, **7B is the practical
upper bound for wide local-only mobile apps**, and **12B is an iPad-Pro-16GB or
hybrid/offload target** unless latency/context/quality are traded aggressively.
