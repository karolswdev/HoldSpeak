# Counsel brief — Phase D slice 1 blocked rulings (HS-143-08)

Prepared 2026-08-24 by the orchestrator for ONE capped Sol ruling round.
All factual claims below were verified against the CURRENT worktree
(`.tmp/worktrees/hs143-08`, HEAD `35dfa709` + uncommitted slice-1 edits)
by a read-only verification pass on 2026-08-24. File:line references are
current-tree.

## The owner's bar (state this in your ruling; it is law)

**OWNER'S BAR — hard, twice-reasserted, once HARD-OVERRULED into law
(2026-08-24):** the product always runs YOLO mode. Findings count ONLY
when a normal product action reproduces damage. Crash-window /
sleep-resume / takeover-race / adversarial scenarios are LEDGER NOTES by
default, even when a probe reproduces them. **Counsel loops hard-cap at
ONE ruling round + at most ONE fix round, then RATIFY-WITH-NOTES and
ship.** The five-round C1 loop is the never-again example.

Also standing: migrations stay minimal (single-user reality); HoldSpeak
is not really released (no backwards-compat ceremony); this is one
owner's laptop.

## Governing design

`assets/story-08-phase-d-speech-design.md` — the ruled Phase D design
with six binding amendments. Relevant here: Amendment 2 (closed
`wake-capture@1` policy; "cross-bind the configured wake revision in
immutable parent and principal evidence"), Amendment 3 (ONE bounded P=1
preload sequence), Amendment 6 ("focused tests must cover local, mesh,
and private-network transcription and prove that none is mislabeled").

## R1 — Mesh/private-network speech execution is not implemented

Verified state: the routed transcription callback receives the
controller-selected engine as `_engine` and ignores it, invoking the
captured LOCAL `Transcriber.run()` regardless of selected leg
(`speech_session/transcription.py:285-305`). Frozen construction derives
only engine/model/language strings for a local constructor
(`speech_session/session.py:526-537`). Yet route eligibility ADVERTISES
non-local legs: `inference_capabilities.py:1058` and
`services/inference_service_route_policy.py:197-200` both declare
`boundaries=("local","mesh","private_network")` for `speech.transcribe`.
There is NO admission-time local-only guard. A conventional mesh leg
(`node_runtime` engine) fails local constructor validation
(`transcribe.py:66-69`) BEFORE a transcription child — so it does not
silently run local — but any non-local leg whose frozen engine string
passes the local allowlist would execute locally while the receipt
names the remote deployment (a receipt lie).

Ruling needed: (a) scope `speech.transcribe` to `("local",)` at the
policy/capability level now, refuse honestly, and LEDGER the remote leg
as future work (the orchestrator's recommended yolo answer — no remote
audio transport exists and inventing one is not slice-1 scope); or
(b) require a remote audio transport/semantic adapter design now. If
(a): rule how Amendment 6's "local, mesh, and private-network" test
clause is narrowed (e.g. tests prove the local badge + prove a
non-local leg is refused at admission, not mislabeled).

## R2 — Cold MLX wake capture fails on the ordinary path (must resolve)

Verified state: `wake-capture@1` permits only `speech.transcribe`
(`services/inference_service_route_policy.py:185-200`); the derived
preload member exists ONLY for OWNER principals
(`speech_session/session.py:654-662`); an unloaded MLX backend requests
preload work before the transcribe child (`transcribe.py:197-218`,
`518-521`) and the wake session's `preload_child` refuses with
`speech_preload_not_admitted` (`speech_session/transcription.py:318-320`).
Net: fresh app boot + wake enabled + MLX + model not yet loaded → wake
capture fails without dispatching speech. This is an ORDINARY-path
defect under the owner's bar (a normal product action breaks) — it must
be resolved, not noted. The current wake test fakes `loaded=True`
(`tests/unit/test_dictation_session_admission.py:88-105`, wake test at
`346-369`) and cannot cover this; the fix round must add a real
cold-path proof (production objects, no decorated fakes — this story's
named sin, caught twice).

Options to rule between: (i) extend `wake-capture@1` with a narrowly
authorized wake lifecycle/preload member (derived exactly like the
owner's, from the frozen transcription route, per the existing
derived-preload contract — keeps Amendment 3's ONE bounded P=1 shape);
(ii) a lawful parentless warm prerequisite before wake sessions;
(iii) explicit cold-wake refusal surfaced honestly (rejected by the
orchestrator as an ordinary-path regression: wake worked cold before
Phase D). Orchestrator recommends (i).

## R3 — Wake's configured revision has no ruled principal-evidence field

Verified state: the configured wake revision IS cross-bound in the
immutable parent snapshot (`speech_session/session.py:619-626`,
persisted via `services/inference_parent_route_bundle_service.py:447-457`)
but the shared `InferenceFeaturePrincipalPolicyEvidence@1` payload has
no field for it (`services/inference_service_route_policy.py:127-140`)
and the schema is EXACT/CLOSED — reconstruction validates
`set(policy) != fields` (`services/inference_route_plan_service.py:1727-1745`).
Amendment 2 says "cross-bind the configured wake revision in immutable
parent and principal evidence". Extending the generic schema touches
owner evidence construction (`inference_route_plan_service.py:591-628`),
every service policy, and strict reconstruction for all existing
adopters.

Ruling needed, schema-level, pick one: (a) amend Amendment 2 narrowly —
parent-evidence cross-bind suffices (it is immutable and durable), the
principal-evidence leg is satisfied by the fixed policy identity, no
schema change (orchestrator's recommendation: cheapest honest answer,
zero blast radius, single-user reality); (b) add an OPTIONAL closed
`policy_context_revision`-style field to
`InferenceFeaturePrincipalPolicyEvidence@1` with exact-set validation
updated everywhere; (c) mint `...@2` for wake only. If (b) or (c),
state the exact field name and validation rule so the fix round is
mechanical.

## R4 — Partial marker cutover mixes bundled and legacy work (review stream, verified)

Verified state: with the speech marker on and the provider marker off,
transcription rides the bundle but configured classify/rewrite runs as
LEGACY plain children under the SAME parent
(`speech_session/session.py:594-604`, `645-653`;
`speech_session/provider.py:264-280` routed vs `306-318` legacy
fallthrough; `speech_session/child.py:170-186` same parent
operation/context). Those legacy children sit outside the route bundle
and consume the parent's global child capacity reserved for bundle-era
work (can exhaust the bundle parent).

Ruling needed: is this a lawful TRANSITIONAL state (the design's
two-marker cutover contemplates it; slice 2 / Phase F removes it) that
gets a ledger note + a capacity guard, or must slice 1 couple the
markers (speech marker implies provider members in the bundle) before
commit? Orchestrator note: Amendment 6 already preserves provider
classify/rewrite behavior "not migrated by Phase D" — a ruling that the
markers ship coupled-by-default (one cutover switch) may be the
smallest honest fix.

## R5 — Frozen faster-whisper constructor loads WhisperModel pre-child (review stream, verified)

Verified state: `_FasterWhisperTranscriber.__init__` eagerly constructs
`WhisperModel` (`transcribe.py:385-392`); its `ensure_loaded` is a
documented no-op ("faster-whisper loads its weights in its own
constructor", `transcribe.py:398-402`); construction happens on the
pre-child path (`runtime/dictation_capture.py:117-122`,
`runtime/transcriber_state.py:92-96`) after parent/bundle admission but
BEFORE any routed transcription child. A matching cached instance skips
reconstruction. Only MLX has the separable admitted load (the ruled
Amendment-3 lifecycle).

Ruling needed: (a) explicit local-only exception — faster-whisper's
load is constructor-inseparable, local, no egress; record the exception
in the design and ledger it (orchestrator's recommendation); or
(b) require wrapping construction in an admitted `speech.preload@1`
lifecycle like MLX. If (b), note it re-opens Amendment 3's shape for a
backend whose library API cannot separate load from construction.

## What the ruling must produce

For each of R1-R5: a one-paragraph ruling with the chosen option and
any binding amendment text (exact words if design text changes). Cap:
this is the ONE ruling round; at most ONE fix round follows, then
RATIFY-WITH-NOTES and ship. Do not expand scope; do not order full-suite
runs (orchestrator owns sweeps); do not order probes for
crash-window/adversarial scenarios — those are ledger notes by law.
