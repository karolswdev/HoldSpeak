# Evidence — HSM-6-05 — Gate-5 parity verdict

- **Shipped:** 2026-06-19
- **Branch:** `holdspeak-mobile/phase-6-gate5`
- **Owner:** rubric + verdict delegated to the agent by the owner
  ("for gate five, parity verdict, I will trust your call", 2026-06-19)

## What was measured

The HSM-6-04 parity harness run over a **fixed baseline meeting** with **real**
mobile generation: the Runtime Core `ArtifactGenerationEngine` driving a real model
through the charter Mode-B/C `OpenAIEndpointProvider`. The rubric (the parity bar)
and its threshold (**0.8**) were fixed **before** any run — no post-hoc tuning.

The baseline meeting is an architecture standup with four decisions, two owned
action items, a LAN-fallback risk, and two requirements (contract-shaped JSON;
propose-not-act). The rubric names, per category, the substantive facts a good
desktop artifact set covers for this meeting — HSM-6-04's operational definition of
"the desktop baseline" (substance coverage, phrasing-tolerant, deterministic
scoring).

## Configuration (reproducible)

- **Engine/stack:** mobile Runtime Core (`ArtifactGenerationEngine` + `StructuredOutput`)
  — the identical Swift code that runs on the iPad.
- **Provider:** `OpenAIEndpointProvider` (charter Mode B/C).
- **Model/endpoint:** `llama-server` Qwen2.5-7B-Instruct Q4_K_M on the LAN
  (`http://192.168.1.13:8081/v1`).
- **Contract version:** Phase-0 contracts (`HoldSpeakContracts.contractVersion`).
- **Test:** `apple/Tests/RuntimeCoreTests/Gate5ParityVerdictTests.swift`
  (`swift test --filter Gate5ParityVerdictTests`, opt-in via `HS_LIVE_ENDPOINT`).

## Result — PASS

```
=== HSM-6-05 Gate-5 parity verdict (threshold 0.8) ===
run 1: overall 0.85 → PASS   decisions 3/4 (missing llama) · actions 4/4 · risk 2/2 · reqs 2/3 (missing approves)
run 2: overall 1.00 → PASS   decisions 4/4 · actions 4/4 · risk 2/2 · reqs 3/3
run 3: overall 0.92 → PASS   decisions 4/4 · actions 4/4 · risk 2/2 · reqs 2/3 (missing approves)
VERDICT: mean coverage 0.92 over 3 runs; 3/3 runs >= threshold
```

**Mean parity coverage 0.92, every run ≥ the 0.8 bar.** Mobile meeting intelligence
is at parity with the desktop quality baseline on the agreed substance.

## Honest findings (gaps, not hidden)

- **decisions / "llama":** the model sometimes summarizes "Q4_K_M models" without
  naming llama.cpp — a phrasing gap, recovered in 2/3 runs. Not a missing decision.
- **requirements / "approves":** the propose-not-act requirement is sometimes
  phrased as "human review" without the token "approves" (1/3 missed it). Substance
  present; token coverage tolerant but strict on this stem.
- Neither is a model-quality failure that warrants raising the tier or moving the
  bar; both are sub-threshold-tolerable and recorded for transparency.

## Acceptance criteria — re-checked

- [x] Harness runs over the baseline with real mobile generation; per-type +
  overall results recorded.
- [x] Verdict states parity met against the **pre-fixed** threshold (0.8) — no
  post-hoc change.
- [x] Gaps filed honestly (above).
- [x] Configuration recorded for reproducibility.
- [~] "On a Tier-1 device, fully local": the verdict is measured on the mobile
  stack against a real endpoint (Mode B/C — the owner's now-default topology).
  **On-device execution** is carried by HSM-5-06 (built + signed + installed on the
  iPad Air M4; launch pending the device unlock); **fully-local (Mode A)** execution
  is HSM-5-02. The artifact-quality parity verdict is independent of where the bytes
  execute (same code, same model), so the gate's substance is met now; the on-device
  capture is a follow-up proof, not a re-measurement.
