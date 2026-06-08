# HS-51-01 — Leak inventory + vocabulary policy (the map)

The complete, classified list of roadmap-vocabulary leaks in the user/operator-facing
docs, the scope decision, and the banned-pattern + allowlist that HS-51-02 (scrub)
and HS-51-03 (guard) both follow. Produced 2026-06-07.

## How this was found

```
grep -rInE '\bHS-[0-9]{2}-?[0-9]*\b|\bPhase[ -][0-9]+\b|\bPMO\b|\bcloseout\b|the current roadmap' \
  README.md docs/ --include='*.md' | grep -v 'docs/internal/' | grep -v 'docs/evidence/'
```

This surfaced more than the AGENT-BRIEF's scaffold-time list. `SECURITY.md`,
`PLUGIN_AUTHORING.md`, and `docs/assets/pixellab/README.md` also leak. The root
`README.md` is clean (only legitimate `actuator` product nouns).

## Scope decision (fixed)

- **IN (scrub + guard):** the root `README.md` and the top-level guides `docs/*.md`.
  These are what a user or operator actually reads.
- **OUT (never scrubbed, never scanned):**
  - `pm/roadmap/**` — the PMO corpus, the historical record, kept verbatim.
  - `docs/internal/**` — internal planning + `DOCS_STYLE.md`; exempt by design (it
    must be able to quote the banned tokens as examples).
  - `docs/evidence/**` — frozen evidence snapshots.
  - `docs/assets/**` — asset-provenance readmes, not a user reading-journey doc. The
    one leak there (`docs/assets/pixellab/README.md:9`) is an **optional courtesy
    scrub** in HS-51-02 and is **out of the guard's scan scope** (the guard scans
    top-level `docs/*.md`, non-recursive).
- **KEEP everywhere (not leaks):** product nouns (`actuator`, `connector`,
  `artifact_generator`); named architecture specs `MIR-01` / `DIR-01` / `WFS-01`
  (these are spec names, not phase tags, and do not match the banned patterns).
  `docs/README.md:78-79` references `DIR-01` / `MIR-01` on purpose: keep.

## The inventory (banned hits + proposed rewrite)

Every line below is **banned** unless marked KEEP. The rewrite is product-tense:
the meaning survives for a reader who has never heard of a "phase". HS-51-02 applies
these.

### docs/RELEASING.md  (in scope, maintainer-facing guide)
- **L102** `See the captured example in the Phase 50 evidence.`
  -> `See the captured example in the release evidence.`

### docs/CONNECTOR_DEVELOPMENT.md  (in scope)
- **L5-6** `Phase 9 shipped the first three first-party connectors; phase 11 generalises the contract so anyone can author a local one.`
  -> `HoldSpeak ships first-party connectors, and the contract is general enough that anyone can author a local one.`
- **L316** heading `## Phase 13 additions — runtime gates, pipelines, user packs, run history`
  -> `## Runtime gates, pipelines, user packs, and run history` (drops the phase tag and the em dash)
- **L318-320** `Phase 11 shipped the contract; phase 13 turns it on. The four surfaces below are what changed in the runtime — read these before authoring a pack against the current main.`
  -> `Beyond the base contract, the runtime adds four surfaces. Read these before authoring a pack.` (drops phase tags, "the current main", em dash)
- **L452-454** `Phase 11 ships the *contract* and the *first-party packs*. Any external distribution mechanism is a separate phase, not on the current roadmap.`
  -> `HoldSpeak ships the *contract* and the *first-party packs*. Any external distribution mechanism (a remote publishing flow, a marketplace, a third-party loader) is out of scope today.`

### docs/DEVICE_PROTOCOL.md  (in scope)
- **L310** table cell `**Periodic tick during meeting (HS-17-05, currently every 1 s)**`
  -> `**Periodic tick during meeting (currently every 1 s)**`
- **L311** table cell `**Finalized transcript segment (HS-17-08 / HS-17-13)**`
  -> `**Finalized transcript segment**`
- **L315** `The periodic Recording-tick (HS-17-05, 2026-05-10) fires every 1 second ...`
  -> `The periodic Recording-tick fires every 1 second ...` (drop the `(HS-..., date)` parenthetical)
- **L387** heading `## 8. What phase 15 will need to revisit`
  -> `## 8. What cross-network reach will need to revisit`
- **L389-390** `Phase 14 is plain `ws://` on loopback. Phase 15's tunnel layer (Tailscale / Cloudflare Tunnel / WireGuard) terminates TLS somewhere; ...`
  -> `The device link is plain `ws://` on loopback today. A future tunnel layer (Tailscale / Cloudflare Tunnel / WireGuard) terminates TLS somewhere; ...`
- **L400-403** `**Per-device PSKs.** Phase 14 uses a single shared secret. Phase 15+ should issue per-device PSKs once HoldSpeak ships to a second install ...`
  -> `**Per-device PSKs.** HoldSpeak uses a single shared secret today. Per-device PSKs become worthwhile once HoldSpeak ships to a second install or the user wants to revoke a single device.`

### docs/INTELLIGENT_TYPING_GUIDE.md  (in scope)
- **L135** `Known-good local dogfood profile from HS-19 closeout:`
  -> `A known-good local profile:`

### docs/SECURITY.md  (in scope; the story IDs are used as decision provenance, meaningless to a reader)
- **L3** `**Status:** living document (HS-25-03, Phase 25 "Trust & Hardening").`
  -> `**Status:** living document.`
- **L45** heading `### Encryption-at-rest decision (HS-25-03)`
  -> `### Encryption-at-rest decision`
- **L75** `... gated by an auth token (HS-25-02): required to bind and on every request ...`
  -> drop `(HS-25-02)`: `... gated by an auth token: required to bind and on every request ...`
- **L79** `Same-LAN scope today; cross-network is Phase 15.`
  -> `Same-LAN scope today; cross-network reach is planned.`
- **L92** `... surfaced by `doctor` + `intel_egress` in the runtime status (HS-25-01).`
  -> drop `(HS-25-01)`.
- **L95** `Loopback by default; token-gated off-loopback (HS-25-02).`
  -> drop `(HS-25-02)`.
- **L130** `... owned by **Phase 15** (TLS, tunnels, per-device PSKs), which this phase unblocks.`
  -> `... planned as future work (TLS, tunnels, per-device PSKs).`

### docs/PLUGIN_AUTHORING.md  (in scope)
- **L631-632** `The Phase-37 `outbox` reference writes a local file; the Phase-38 references reach real systems (GitHub, a webhook) under that manifest.`
  -> `The `outbox` reference writes a local file; the GitHub and webhook references reach real systems under that manifest.`

### docs/assets/pixellab/README.md  (OUT of guard scope; optional courtesy scrub)
- **L9** heading `## Brand identity (HS-33-05, 2026-06-03)`
  -> `## Brand identity (2026-06-03)`

### KEEP (not leaks, do not touch)
- **docs/README.md:78-79** `DIR-01` / `MIR-01` spec names. Architecture spec names,
  referenced on purpose. Keep.

## Banned pattern + allowlist (for the HS-51-03 guard)

**Banned (the guard fails on these in user-facing docs):**
- `\bHS-\d{2}(-\d+)?\b`  (e.g. `HS-25`, `HS-17-05`, `HS-17-08`)
- `\bPhase[ -]\d+\b`  (e.g. `Phase 15`, `Phase-37`, `Phase 9`)
- `\bPMO\b`
- the literal phrase `the current roadmap`
- `\bcloseout\b`

**Allowlist (must NOT trip the guard):** `MIR-\d+`, `DIR-\d+`, `WFS-\d+`, and product
nouns. None of these match the banned patterns, so no special-casing is needed;
the requirement is just to keep the patterns this narrow (never a bare `\bphase\b`).

**Honest limitation:** the regex catches *numbered/tagged* leaks. Bare process-speak
with no number (`a separate phase`, `which this phase unblocks`) is NOT caught by the
regex; it is removed by the human scrub (HS-51-02) and discouraged by the codified
`DOCS_STYLE.md` rule (HS-51-04). The guard is the backstop against the high-signal
tags returning, not a full prose linter.

## Verification

Re-running the grep above over the **in-scope** docs after HS-51-02 must return
empty (excluding `docs/assets/`, which is out of scope). At inventory time it
returns the 20 banned hits listed above (plus the 1 optional assets hit and the 2
KEEP `MIR/DIR` lines).
