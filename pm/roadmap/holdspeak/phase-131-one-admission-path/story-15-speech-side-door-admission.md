# HS-131-15 — Speech side doors become sessions or stay lexical

- **Project:** holdspeak
- **Phase:** 131
- **Status:** done
- **Depends on:** HS-131-02, HS-131-09
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

The dictation dry-run route and `holdspeak dictation` command can construct the
model-bearing pipeline without the authenticated speech-session parent and
frozen capability plan established by HS-131-09. Dry-run and CLI topology does
not exempt transcription, classification, rewrite, or punctuation from
Constitution Articles V.2–3 and XI.1–3.

## Scope

### In

- Begin with a design beat, ruled by Sol before implementation, that decides for
  each entry point whether it needs provider work or can truthfully remain
  lexical-only.
- If provider work remains, define the authenticated principal, parent operation,
  bounded session lifetime, frozen ordered capability revisions, cancellation
  boundary, and publication owner before construction. A route body or CLI flag
  may not fabricate an owner principal or ambient session.
- Route each retained Whisper, classification, rewrite, punctuation, local,
  cloud, compatibility, and mesh attempt through `InferenceRunner` as an
  `inference.invoke@1` child of that parent with one immutable terminal receipt.
- If an entry becomes lexical-only, make provider construction unreachable and
  keep the limitation honest at the route/command boundary without a quiet
  model fallback.
- Reuse the HS-131-09 speech plan, provider adapter, revision rebinding,
  publication fence, and journal hygiene. Do not create dry-run-specific or
  CLI-specific provider machinery.
- Preserve content ownership outside the kernel: audio, dictated text, prompts,
  tokens, and rewritten bodies never enter operation, event, or receipt fields.
- Remove `dictation-dry-run` and `dictation-command` from `NAMED_FINDINGS` only
  after both entry points prove the chosen design mechanically.

### Out

- Dictation UI redesign, mic gesture changes, or new pipeline blocks.
- A blanket local/CLI/preview exemption from model admission.
- Authentication by caller-supplied owner identity.
- Persisting dry-run or CLI content in the kernel journal.

## Acceptance criteria

- [x] A Sol-ruled design records the admit-versus-lexical decision for each
  entry point and names principal, authority basis, parent, frozen plan,
  cancellation, and publication boundaries for every retained provider path.
- [x] Neither entry point can construct a model-bearing pipeline before its
  authenticated parent and immutable plan exist.
- [x] Every retained physical model attempt has one causally linked invocation
  child and one immutable terminal receipt; lexical-only paths mint none.
- [x] Missing authentication, authority, session liveness, or exact revision
  refuses by name before provider construction or dispatch.
- [x] Cancellation, expiry, route disconnect, or command interruption prevents
  late transcript/rewrite output from landing.
- [x] Kernel rows contain no audio, dictated text, prompt, token stream, or model
  response body.
- [x] The one-path census removes both speech findings with no product scope in
  `ADAPTER_ALLOWLIST` and zero unregistered execution.

## Test plan

- Design: adversarial state/transition review covering admit and lexical-only
  alternatives, authority derivation, interruption, and publication ownership.
- Unit: route and CLI principal/session tests; every provider capability;
  lexical-only zero-child controls; forged/stale context; cancellation;
  cardinality; hygiene; and one-path census.
- Mutation: restore direct `build_pipeline` construction in each entry and prove
  the exact named fence failure before returning to green.
- Integration: execute both production entry points with isolated HOME and one
  retained provider capability, then inspect parent, child, revision, receipt,
  and publication rows.
- Manual / device: n/a; HS-131-12 performs the assembled live-model proof.

## Notes / open questions

The design beat chooses behavior rather than weakening the invariant. If dry-run
or CLI cannot establish honest authority cheaply, lexical-only is the correct
product limitation under Article VI.
