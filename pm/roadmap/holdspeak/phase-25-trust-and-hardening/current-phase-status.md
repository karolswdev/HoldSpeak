# Phase 25 — Trust & Hardening

**Last updated:** 2026-05-31 (HS-25-01..06 done; HS-25-07 closeout + HS-25-08 web badge remain).

## Goal

Close the correctness, privacy, and security gaps that stand between HoldSpeak
and being safely operated by someone other than its author — and that block any
future cross-network reach (Phase 15). No transcript should leave the machine
without explicit consent; the web runtime should be defensible the moment it
stops binding loopback-only; the data-at-rest and trust boundaries should be
written down; and the latency-sensitive paths should fail safe instead of
hanging or racing.

## Scope

### In

- Make every path that could send a transcript off-machine explicit and
  opt-in; eliminate silent cloud egress when a local intel model is
  missing/misconfigured.
- Add an authentication gate to the FastAPI web runtime and a guard for
  non-loopback binding (prerequisite to Phase 15).
- Write the threat model + encryption-at-rest stance (data classes, trust
  boundaries, egress points) as canon.
- Make LLM-runtime concurrency safety explicit at the runtime layer rather than
  relying on the controller's undocumented `_transcription_lock`.
- Bound Whisper transcription with a timeout so a hung model cannot freeze the
  pipeline.
- Audit half-wired knobs (`eviction_idle_seconds`, `intel_cloud_store`) and
  resolve each to proven-working or removed.

### Out

- The `web_server.py` decomposition / maintainability refactor — that is
  **Phase 26** (fast-follow).
- Cross-network transport itself (TLS, tunnels, per-device PSKs) — that remains
  **Phase 15**; this phase only unblocks it.
- Product-strategy "front door" / positioning work.
- Encryption-at-rest *implementation* if the recorded decision is to document
  the stance instead (story 03 settles which).
- New features in meeting, dictation, activity, or companion surfaces.

## Exit criteria (evidence required)

- [ ] A missing/misconfigured local intel model causes **no** transcript to
      leave the machine; proven by a test that exercises the
      no-local-model path and asserts no cloud call, plus a dogfood note.
- [ ] The web runtime rejects unauthenticated requests to data and mutation
      endpoints when a token is configured, and refuses to bind a non-loopback
      host without one; proven by `tests/` cases over the FastAPI app.
- [ ] `docs/SECURITY.md` exists, enumerates data classes (transcripts, speaker
      embeddings, activity ledger, config secrets), trust boundaries, and every
      egress point, states the encryption-at-rest decision, and is linked from
      `pm/roadmap/holdspeak/README.md` source canon + `README.md`.
- [ ] LLM-runtime concurrent `classify`/`rewrite` calls are serialized at the
      runtime layer and covered by a test exercising concurrent calls; the
      controller's prior reliance is documented.
- [ ] A hung/slow transcription is bounded by a configurable timeout and
      recovers gracefully (user notified, pipeline returns); covered by a test
      with a slow mock transcriber.
- [ ] No config knob silently no-ops: `eviction_idle_seconds` and
      `intel_cloud_store` are each proven-working by a test or removed with a
      recorded rationale.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` is green and the
      output is captured in the closeout evidence.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-25-01 | Loud cloud-path consent — no silent transcript egress | done | [story-01-loud-cloud-consent.md](./story-01-loud-cloud-consent.md) | [evidence-story-01.md](./evidence-story-01.md) |
| HS-25-02 | Web-runtime auth token + non-loopback bind guard | done | [story-02-web-runtime-auth.md](./story-02-web-runtime-auth.md) | [evidence-story-02.md](./evidence-story-02.md) |
| HS-25-03 | Threat model + encryption-at-rest stance doc | done | [story-03-threat-model-doc.md](./story-03-threat-model-doc.md) | [evidence-story-03.md](./evidence-story-03.md) |
| HS-25-04 | LLM runtime thread-safety made explicit | done | [story-04-llm-runtime-thread-safety.md](./story-04-llm-runtime-thread-safety.md) | [evidence-story-04.md](./evidence-story-04.md) |
| HS-25-05 | Whisper transcription timeout | done | [story-05-transcription-timeout.md](./story-05-transcription-timeout.md) | [evidence-story-05.md](./evidence-story-05.md) |
| HS-25-06 | Runtime-lifecycle knob audit (eviction, cloud_store) | done | [story-06-runtime-lifecycle-audit.md](./story-06-runtime-lifecycle-audit.md) | [evidence-story-06.md](./evidence-story-06.md) |
| HS-25-07 | Trust hardening dogfood + closeout | backlog | [story-07-trust-dogfood-closeout.md](./story-07-trust-dogfood-closeout.md) | — |
| HS-25-08 | Web egress-posture badge (split from HS-25-01) | backlog | [story-08-web-egress-badge.md](./story-08-web-egress-badge.md) | — |

## Where we are

Phase opened 2026-05-31, prioritized ahead of Phase 24 (now paused) following a
full-system analysis. The analysis found the engineering broadly strong but
flagged a cluster of trust gaps: a silent local→cloud fallback for meeting
intel, a web runtime with no auth whose safety rests entirely on binding
`127.0.0.1`, LLM runtimes whose thread-safety depends on an undocumented
controller lock, an unbounded transcription call, and a couple of config knobs
that may silently no-op. None are individually fatal; together they are what
stops the tool from being handed to anyone else — and they gate Phase 15's
cross-network plans.

HS-25-01 is in progress. Read-before-fix corrected its premise: the default
`provider="local"` is already structurally incapable of cloud egress (the
resolver is local-only and the OpenAI client is only built for non-local
providers), so there was no live leak at the default — but nothing *tested* that
guarantee. `tests/unit/test_intel_egress_invariant.py` (5 cases, green) now locks
the invariant and simultaneously proves `cloud`/`auto` still reach the cloud, so
the consent boundary is pinned from both sides. Remaining HS-25-01 work is
transparency: surface the active egress posture in `doctor` + the web
intel-status surface, and make `auto`'s fallback visible.

HS-25-01 is **done**: `tests/unit/test_intel_egress_invariant.py` locks the
invariant, `doctor` + `/api/runtime/status` (`intel_egress`) + the meeting guide
surface the posture. The web dashboard badge was split to **HS-25-08**.

**Repo finding (surfaced during HS-25-01):** the full suite has **9 pre-existing
failures on `main`**, confirmed unrelated to this work (reproduced on `HEAD` with
changes stashed). Six are page-content tests against a **stale committed
`holdspeak/static/_built/`** Astro bundle; three are `test_activity_history`
cases needing a Safari fixture absent from this checkout. The `_built` staleness
overlaps HS-25-08 (rebuild) and Phase 26 (web work); worth a dedicated cleanup if
it persists.

HS-25-02 is **done**: `holdspeak/web_auth.py` adds the token primitives;
`web_server.py` enforces a token gate **only off-loopback** (loopback stays open
— user decision) plus a bind guard that refuses a non-loopback bind without a
token; `doctor` reports the posture. The gate is dormant at today's `127.0.0.1`
default and activates the instant Phase 15 introduces a non-loopback host — so
**Phase 15 is now unblocked on the auth front**. Two small follow-ups are noted
on the story (off-loopback `/ws` gating; browser token injection) — neither is
reachable while host is loopback-only.

HS-25-03 is **done**: `docs/SECURITY.md` records data classes, trust boundaries,
egress points, and the encryption-at-rest decision (document the stance, defer
implementation, recommend full-disk encryption; revisit if multi-user/server).
Linked from README + roadmap canon.

HS-25-04 is **done**: `CountingRuntime` (the wrapper `build_runtime` always
applies) now serializes `load`/`classify`/`rewrite` on a per-instance `RLock`, so
the non-thread-safe MLX/llama.cpp adapters are single-flight intrinsically rather
than by the controller's external lock. Concurrency test proves
`max_in_flight == 1`.

HS-25-06 is **done**: audit found both knobs real (not dead). `eviction_idle_seconds`
genuinely unloads the model (config→assembly→adapter→`_maybe_evict`);
`intel_cloud_store` is forwarded as `store=True` and now documented as advisory
(endpoint-dependent). Both pinned by `tests/unit/test_runtime_knob_audit.py`.

**All six engineering/security stories (HS-25-01..06) are done.** Remaining:
- **HS-25-07** — phase closeout + dogfood. The three dogfood scenarios
  (misconfigured-local-model shows no egress; web token gate; transcription
  timeout recovery) want a **live/manual** run — needs the user (or a hardware
  session). Code-level proof already exists in each story's tests.
- **HS-25-08** — web egress badge: needs an Astro `web/` edit + `_built` rebuild
  (large bundle churn); also a chance to clear the stale-`_built` pre-existing
  failures.

## Product problems to solve

| Problem | Why it matters | First likely move |
|---|---|---|
| Silent cloud fallback for intel | "Local-first & private" is the pitch; a misconfigured model path can quietly queue transcripts for cloud. | Gate all egress behind an explicit consent flag; warn in `doctor` + web when config would send transcripts off-machine. |
| Web runtime has no auth | Whole security model is "binds localhost"; Phase 15 deliberately breaks that assumption. | Add a token gate mirroring `device_audio.verify_psk` (`hmac.compare_digest`); refuse non-loopback bind without it. |
| Trust boundaries are undocumented | No one can reason about exposure (transcripts, voiceprints, browser-derived ledger) without reading the source. | Write `docs/SECURITY.md`; decide + record the encryption-at-rest stance. |
| LLM concurrency safety is implicit | `runtime_mlx`/`runtime_llama_cpp` aren't thread-safe; only `controller._transcription_lock` serializes them. | Move serialization into the runtime layer; test concurrent calls. |
| Transcription can hang | A stuck model blocks the transcription thread with no timeout. | Wrap `Transcriber.transcribe` with a configurable timeout + graceful fallback. |
| Dead-feeling config knobs | `eviction_idle_seconds` defaults off; `intel_cloud_store` rides `extra_body` and may no-op. | Audit each: prove it works (test) or remove it (rationale). |

## Pickup order

1. HS-25-01 — kill silent cloud egress (highest-trust item).
2. HS-25-02 — web auth + bind guard (unblocks Phase 15).
3. HS-25-03 — threat-model doc + at-rest decision (can run in parallel).
4. HS-25-04 — runtime thread-safety.
5. HS-25-05 — transcription timeout.
6. HS-25-06 — runtime-knob audit.
7. HS-25-07 — dogfood + closeout.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Auth gate breaks the local web/menubar/TUI clients that assume open access | Medium | Default token auto-generated + auto-applied for the local client; loopback stays frictionless | A local client can no longer reach the runtime after the gate lands |
| Tightening the deferred-intel path changes existing meeting-intel behavior | Medium | Story 01 verifies current behavior first, then makes egress opt-in without removing local/explicit-cloud paths | A meeting that previously got cloud intel silently stops getting any intel with no surfaced reason |
| Runtime-level mutex serializes calls that were already serialized, adding no value or causing deadlock | Low | Confirm the contention path before adding a lock; prefer a documented single-flight assertion if the controller already guarantees it | Added lock changes latency or deadlocks under the existing single-threaded transcription path |
| "Audit and remove" deletes a knob that is actually load-bearing | Low | Story 06 requires verifying real usage (`eviction` logic exists at `runtime_mlx.py:180`) before any removal | Removing a knob breaks a test or a documented config workflow |

## Decisions made (this phase)

- 2026-05-31 — Phase 25 prioritized ahead of Phase 24 — trust gaps gate Phase 15 and external use — user.
- 2026-05-31 — `web_server.py` decomposition split into a separate Phase 26 fast-follow — keep security work and a large refactor in different blast radii — user.

## Decisions deferred

- Encryption-at-rest: implement vs. document-the-stance — trigger: settled in HS-25-03 — default: document the stance and filesystem-permission posture, defer implementation unless the threat model demands it.
- Auth scheme (static config token vs. per-client PSK like the device link) — trigger: HS-25-02 design — default: static config token with `hmac.compare_digest`, reusing the device-PSK pattern.
