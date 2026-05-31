# HS-25-03 — Threat Model + Encryption-at-Rest Stance

- **Project:** holdspeak
- **Phase:** 25
- **Status:** done
- **Depends on:** HS-25-01
- **Unblocks:** HS-25-07
- **Owner:** unassigned

## Problem

HoldSpeak stores sensitive data — full meeting transcripts, speaker *voice
embeddings* (biometric-adjacent), a browser-history-derived activity ledger,
and references to cloud API keys — in a plaintext SQLite DB protected only by
filesystem permissions. There is no written threat model, so no one (including
the author) can reason about exposure, and the encryption-at-rest question has
never been explicitly decided. A privacy-first tool needs its trust boundaries
on paper.

## Scope

### In

- Write `docs/SECURITY.md` covering:
  - **Data classes**: transcripts/segments, speaker embeddings, activity ledger
    + connector annotations, config + cloud API-key handling, device PSK.
  - **Storage posture**: SQLite location, filesystem-permission reliance, temp
    snapshots used for browser-history reads.
  - **Trust boundaries**: local process, the loopback web runtime + its new
    token (HS-25-02), the device PSK link, and the local-vs-cloud egress line
    (HS-25-01).
  - **Egress points**: every place data can leave the machine and what gates it.
  - **Encryption-at-rest decision**: implement vs. document-the-stance, with the
    rationale and (if documented-only) the residual risk and the trigger that
    would flip the decision.
- Link `docs/SECURITY.md` from `README.md` and add it to the
  `pm/roadmap/holdspeak/README.md` source-canon list.

### Out

- Implementing encryption-at-rest unless this story's decision selects it (then
  spin a follow-up story; do not bundle).
- The auth mechanism itself (HS-25-02) — reference it, don't build it here.

## Acceptance criteria

- [x] `docs/SECURITY.md` exists and enumerates data classes, storage posture,
      trust boundaries, and egress points (§§1–6).
- [x] The encryption-at-rest decision is recorded with rationale + residual risk
      + revisit trigger (§2 — document-the-stance; recommend full-disk encryption).
- [x] `README.md` links to `docs/SECURITY.md` ("Where to go next" table).
- [x] `pm/roadmap/holdspeak/README.md` source-canon list includes
      `docs/SECURITY.md`.
- [x] Claims cross-checked against code: egress sites verified
      (`intel.py` OpenAI client, `intel_queue.py:345` webhook, connector
      subprocesses, `device_audio.py` PSK); `activity_history.py` confirmed to
      make no network calls; DB/config paths from `db.py`/`config.py`.

## Test plan

- Unit: n/a (docs).
- Integration: n/a.
- Manual: cross-check each documented egress point against the cited source
  file; confirm no undocumented network call exists in `activity_*` (read-only)
  and `intel*` paths.

## Notes / open questions

- Depends on HS-25-01 so the egress section describes the *hardened* (no silent
  fallback) behavior, not the old one.
- Default stance (per phase decision-deferred): document the
  filesystem-permission posture and defer implementation unless the model
  demands it. The author may override.

## Closeout

Shipped 2026-05-31. See [evidence-story-03.md](./evidence-story-03.md).

Encryption-at-rest decision: **document the stance, defer implementation** (per
the recorded default; user steered "proceed on the default"). `SECURITY.md`
recommends full-disk encryption and records the revisit trigger (multi-user /
server / third-party-data). App-level DB encryption (e.g. SQLCipher), if ever
wanted, is a new story — not a reopen of this one.
