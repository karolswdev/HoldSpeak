# HSM-5-03 — Model packaging & per-device defaults

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** in-progress
- **Depends on:** HSM-5-01
- **Unblocks:** HSM-5-05
- **Owner:** unassigned

## Progress (2026-06-18)

The **per-device default policy** is done + host-tested: `InferenceModel`
(4B/8B/12B+) + `InferenceModelPolicy.defaultModel(for:)` (iPhone→4B, iPad→8B) and
`isAllowed(_:pluggedIn:)` (12B+ only when plugged in, never a default) —
`apple/Sources/Providers/Inference/InferenceModel.swift`, `swift test` green. The
**packaging/download** half (obtaining + storing the model artifacts, first-run
download) is device/dep work that lands with the engine pick (HSM-5-01) and the
chosen runtime — stays in-progress until then.

## Progress & evidence (2026-06-19) — both delivery paths host-proven

The packaging half is now built and host-proven; only the on-device clean-install
first-run is gated on the iPad unlock.

- **`ModelCatalog`** (`apple/Sources/Providers/Inference/ModelCatalog.swift`) pins
  the per-tier artifacts (repo + Q4_K_M + filename): 4B → `bartowski/Llama-3.2-3B-Instruct-GGUF`,
  8B → `bartowski/Meta-Llama-3.1-8B-Instruct-GGUF`, 12B+ → `bartowski/Mistral-Nemo-Instruct-2407-GGUF`.
  All three HF URLs verified live (HTTP 302 → CDN).
- **`ModelStore`** (Foundation) — the model manager: `installedModels`,
  `importModel(from:)` (the **Files sideload** copy), `delete`, and
  `resolveActive(for:)` (per-device default → installed path). Stored under
  Application Support / HoldSpeak / models, re-used across runs.
- **`ModelDownloader`** (Foundation, `apple/Sources/Providers/Inference/ModelDownloader.swift`)
  — the **Hugging Face download** path: builds the canonical
  `…/resolve/main/{file}?download=true` URL and streams it with real 0…1 progress.
  (Finding: LLM.swift's built-in HF downloader scrapes HF's HTML and is broken
  against the current site — so we download by pinned URL instead, which is also
  deterministic.)
- **Proof:** `swift test` **62/62** (6 opt-in skips) incl. 4 `ModelStore`/catalog
  tests (import, GGUF-only listing, per-device resolve, delete). The real download
  path is proven by the opt-in `ModelDownloadTests` (`HS_HF_DOWNLOAD=1`): TinyLlama
  downloaded 0→100%, then `LlamaProvider` loaded it and completed.
- **Dev loop:** `apple/scripts/push-model-device.sh` pushes a local GGUF to the app
  container via `devicectl` (the developer path alongside sideload + download).

**Remaining:** the on-device clean-install first-run on the iPad Air M4 (gated on
the device unlock). Real-time download progress is wired; richer UI lives in the
experience phases (8–9).

## Problem

A local model has to get onto the device and be the right size for that device.
The charter's local-model strategy is explicit: iPhone defaults to a 4B model,
iPad to 8B, and 12B+ is experimental and only when plugged in. Without a
packaging + default-resolution story, the app either ships a giant bundle or
loads a model the device can't sustain.

## Scope

- **In:** how the model artifacts are obtained (bundled vs first-run download) and
  stored; the per-device default resolution (4B iPhone / 8B iPad); the 12B+ path
  gated behind plugged-in only and never the default; first-run UX implications
  (download size, where it lives, re-use across runs).
- **Out:** the inference engine choice (HSM-5-01, pins the concrete artifacts).
  The provider implementation (HSM-5-02). Structured output (HSM-5-04). Thermal
  downgrade under stress (Phase 11 owns the hardening matrix; this story sets the
  defaults it will lean on).

## Acceptance criteria

- [~] On a clean install, the per-device default model is obtained and usable: 4B
      resolves on iPhone, 8B on iPad — host-proven (real HF download + per-device
      resolution); on-device hardware verification pending the iPad unlock.
- [x] 12B+ is never the device default — the resolver only ever returns the
      per-device default (4B/8B); `InferenceModelPolicy.isAllowed` keeps 12B+
      plugged-in-only as an explicit opt-in, not a default.
- [x] Models are stored once and re-used across runs (download no-ops when the file
      is present); storage location documented (Application Support / HoldSpeak /
      models).
- [x] The concrete model artifacts are pinned by name (`ModelCatalog`: repo +
      filename + Q4_K_M), not "latest".

## Test plan

- Unit: the default-resolution logic (device class + power state → model) tested
  across the matrix (iPhone/iPad × battery/plugged).
- Manual / device: clean-install model acquisition on an iPhone and an iPad;
  confirm 12B+ is blocked on battery and allowed plugged in.

## Notes / open questions

- **Sizing is grounded by [`../research/inference-on-apple.md`](../research/inference-on-apple.md)**
  — the budgeting table (4B q4 ~2–4GB peak / 8B q4 ~5–6GB / 12B q4 ~7.5–9.5GB) and
  the feasibility matrix. The defaults: **4-bit PTQ** is the shipping default
  (3-bit only to rescue a tight fit); **4B iPhone / 8B iPad** matches the charter;
  **12B is 16GB-iPad-only or hybrid**, with **7B the practical phone upper bound**.
  Confirm against HSM-5-01's measured numbers, which override the estimates.
- Apple Intelligence itself uses ~7GB on-device — multi-GB assets are normal but
  must be budgeted explicitly; prefer **download-after-install** over bundling.
- First-run download size is a real UX cost — note it for the onboarding the
  iPhone/iPad experience phases (8–9) will surface.
- Pin exact artifacts so Gate 4 (HSM-5-05) and Phase-6 parity are measured against
  a known model, not a moving target.
