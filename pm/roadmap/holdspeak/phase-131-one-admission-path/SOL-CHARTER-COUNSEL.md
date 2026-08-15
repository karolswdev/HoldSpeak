# Sol charter counsel — Phase 131 One Admission Path

**Date:** 2026-08-09

**Verdict:** ratify as amended.

Sol read the current `0fc14aca` tree, issue #450, Constitution Articles V, IX,
and XI, the Phase-130 counsel/handoff, both current-tree Terra execution maps,
the authored 12-story charter, and Terra's hostile charter review. The fleet did
not certify its own plan. Every surviving blocker below was resolved in the
charter before this verdict.

## Terra findings and disposition

1. **Native transcription was unowned and the fence was too SDK-shaped —
   sustained.** Shared local Whisper in `holdspeak/transcribe.py`, meeting
   transcription, core dictation capture, and configured-wake transcription are
   now explicitly assigned to HS-131-09. HS-131-10 scans model execution forms,
   including `.transcribe()` and local runtimes, not only provider SDK calls.
2. **A session could cache authority past revocation — sustained.** Session
   parents carry immutable authority basis and a frozen deployment plan. Every
   child admission and claim still validates current session/authority
   liveness, expiry, and revocation through the kernel. Per-session admission
   removes repeated owner decisions; it does not remove live authorization.
3. **Schedule expiry could contradict "until changed or disabled" — sustained
   in principle, already amended.** Default delegation has no timer. Expiry is
   enforced only when the owner explicitly chooses it. Exact work, target,
   cadence, device, change/disable, and revocation remain the ordinary bounds.
4. **HS-131-07 depended circularly on a later census — sustained.** Two
   pre-charter current-tree audits are now the bounded execution census, with
   every known family assigned before implementation. A new site found by the
   closing fence blocks and requires an explicit charter amendment/new owner
   story. It cannot silently expand HS-131-07. No separate read-only census story
   was added because the standing owner rule rejects pre-implementation
   measurement gates; the research is already complete and recorded.
5. **"One physical dispatch boundary" was the wrong invariant — sustained.**
   The charter now requires one authorized runner/gateway interface with a
   finite reviewed adapter allowlist for heterogeneous local, cloud, streaming,
   fallback, mesh, and transcription implementations. Each adapter dispatch
   must have exactly one preceding invocation admission and one terminal
   invocation receipt.
6. **Dictation latency had no decidable bar — sustained.** HS-131-09 now names
   `scripts/measure_dictation_latency.py`, the fixed 16 kHz fixture, identical
   machine/model/backend/driver sink, 2 warmups, 20 measured runs, median and
   p95, a contemporaneous clean-fork control, and a maximum regression of
   `max(25 ms, 5%)` at either statistic.
7. **The top README still called Phase 129 newest — sustained.** The first
   update block now names and links Phase 131. The canonical `Current phase`
   pointer also resolves to the Phase-131 status file.

## Verification-pass blocker and disposition

Terra's amendment verification sustained the original seven fixes, then found
one additional P0: `Transcriber` preloads MLX Whisper by invoking it on silent
audio before a meeting/dictation/wake session necessarily exists
(`holdspeak/transcribe.py:201-225`). The first amendment had named ordinary
transcription but accidentally excluded this real invocation.

**Sustained and fixed.** HS-131-09 now owns every shared Whisper call, including
preload/warmup. When warmup occurs during session opening it is that session's
invocation child. A pre-session preload is admitted as the authenticated runtime
service under the owner's explicit configured local-model/preload authority
basis and exact deployment revision; it never impersonates the owner. Without a
valid basis, warmup defers until first-session admission or refuses before model
execution. HS-131-10 explicitly fences preload, and the live walk proves its
actor, authority basis, operation, and terminal receipt.

## Sol amendments beyond the hostile review

- A session freezes a routing/deployment **plan**, not necessarily one model.
  Transcription, classification, rewrite, intelligence, and plugins may use
  distinct exact revisions; each child names the revision it executes.
- Schedule delegation is device-local. Synced schedule configuration cannot
  grant a peer authority or start work there.
- Remote inference retains its separately admitted egress effect and receipt.
  Egress evidence neither substitutes for nor double-counts the model invocation
  child and invocation receipt.
- Retry and fallback cardinality follows actual dispatch. Two provider calls
  mean two admitted invocation children and two terminal invocation receipts.
- `Transcriber` and configured wake are inside Article XI. Local execution and
  previously accepted low latency do not create a constitutional exemption.

## Final charter judgment

The phase is now bounded and implementable:

- 12 PMO-sized stories, one ready and eleven dependent backlog stories;
- every known Python model execution family has one named owner;
- deployment revisions and the sync registry remain in the same phase;
- session and schedule authority match the owner's rulings without fabricating
  principal identity or caching revoked rights;
- the fence tests one admission interface, not one physical SDK expression;
- Swift remains entirely out of implementation scope;
- docs land after features and before the real-model walk;
- Terra verifies focused stories, while Sol reads code, evidence, and full-suite
  output before every final done decision.

No constitutional or delivery blocker remains in the charter. The nine
`dw check` errors are the same inherited historical roadmap errors captured
before Phase 131; this charter adds none.
