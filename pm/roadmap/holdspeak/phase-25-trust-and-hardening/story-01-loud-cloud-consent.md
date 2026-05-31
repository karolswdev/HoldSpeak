# HS-25-01 — Loud Cloud-Path Consent: No Silent Transcript Egress

- **Project:** holdspeak
- **Phase:** 25
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-25-03, HS-25-07
- **Owner:** unassigned

## Problem

HoldSpeak markets itself as local-first and private, but meeting intel defaults
make a transcript reach the cloud without an explicit, informed choice.
`config.py` ships `intel_enabled=True` (`:53`), `intel_provider="local"`
(`:54`), and `intel_deferred_enabled=True` (`:57`). When the configured local
model is missing or its path is wrong, the deferred path can resolve to cloud
processing of the transcript. A privacy-first tool must make any off-machine
transmission an explicit opt-in, not a silent consequence of a misconfigured
model path.

**This story does not remove cloud intel.** Cloud is a legitimate, fully
supported choice — if the user wants it, they get it. The goal is *consent, not
removal*: cloud should happen because the user chose it (`provider="cloud"`, or
`"auto"` understood and accepted as "use cloud when local can't"), never as a
silent side effect of a broken `provider="local"` setup. The explicit-cloud and
`auto` paths stay first-class; we only close the accidental one and make the
active posture visible.

## Verification finding (2026-05-31) — premise corrected

Read-before-fix turned up that the worst-case framing above is **not** a live
bug at the default setting. Both the live analyzer (`meeting_session.py:620,651`)
and the deferred queue (`intel_queue.py:99-123,415-435`) pass the user's
configured `intel_provider` straight through to `resolve_intel_provider`, and
that resolver (`intel.py:199-201`) returns local-only for `provider="local"` —
it never falls back to cloud. `MeetingIntel._ensure_runtime_loaded`
(`intel.py:548-564`) only constructs the OpenAI client when the resolved
provider is not `local`. The shipped default is `intel_provider="local"`
(`config.py:54`, `DEFAULT_INTEL_PROVIDER="local"`), so **out of the box a
missing/garbage local model fails closed — no transcript egress.** Cloud is
reached only via explicit `cloud` or `auto` (documented "local-first then cloud
fallback").

So the real gap is not a leak to plug but an **unguarded invariant**: nothing
tested that `local` stays local, so a future refactor could regress it silently.
The story is rescoped accordingly:

1. **Lock the invariant** with a regression-guard test (shipped first). ✅
2. **Transparency**: surface the active egress posture in `doctor` + the web
   intel-status surface, and make `auto`'s cloud-fallback visible (not silent).
3. Keep explicit `cloud`/`auto` first-class (the same test proves they still
   reach cloud).

## Scope

### In

- Verify and document the *current* behavior of `intel.py` +
  `intel_queue.py` when no local model is available across
  `intel_provider` ∈ {`local`, `cloud`, `auto`} and `intel_deferred_enabled`
  ∈ {true, false}.
- Introduce/clarify an explicit cloud-consent gate so a transcript is sent
  off-machine **only** when the user has affirmatively chosen cloud (e.g.
  `intel_provider="cloud"` or `"auto"` with a present cloud key) — never as a
  fallback from a broken local config under `provider="local"`.
- Surface the egress posture: `holdspeak doctor` and the web intel-status
  surface state plainly whether the current config can send transcripts off
  the machine, and why.
- When `provider="local"` and the local model is unavailable, fail visibly
  (queue stays local / clear "no local model" state) rather than silently
  routing to cloud.

### Out

- Encryption-at-rest (HS-25-03).
- Changing the cloud provider/endpoint integration itself.
- Removing the legitimate explicit-cloud and `auto` paths.

## Acceptance criteria

- [x] A test exercises `provider="local"` + missing local model and asserts
      **no** cloud client is constructed (live analyzer + deferred queue) —
      `tests/unit/test_intel_egress_invariant.py`, 5 cases green.
- [x] A test confirms explicit `provider="cloud"` (and `auto` with key) still
      reaches the cloud path — same file.
- [x] `holdspeak doctor` reports an explicit line stating whether the active
      config can transmit transcripts off-machine — `_check_meeting_intel_egress`
      in `doctor.py` ("Meeting intelligence egress").
- [x] The egress posture is exposed for the web surface — `intel_egress` block
      in the `/api/runtime/status` payload (`web_runtime.py`). The visual
      dashboard badge is split to **HS-25-08** (needs an Astro `_built` rebuild).
- [x] Behavior/posture documented in `docs/MEETING_MODE_GUIDE.md`
      ("Where your transcripts go (egress posture)").

## Test plan

- Unit: `uv run pytest -q tests/ -k "intel or deferred"` — add no-local-model
  egress assertions over `intel.py` / `intel_queue.py` (mock the cloud client,
  assert not-called).
- Integration: doctor intel-check reflects the egress posture for each provider
  setting.
- Manual / device: dogfood with a deliberately wrong local model path; confirm
  doctor + web both say "no transcript leaves this machine" and intel reports a
  clear no-local-model state. (Recorded in HS-25-07.)

## Notes / open questions

- Confirm exactly where the local→cloud resolution happens
  (`intel.resolve_intel_provider` per analysis) before changing it.
- `intel_cloud_store` (`config.py:71`) interacts with this — its audit is
  HS-25-06; keep the two stories from overlapping by limiting this one to the
  egress *decision*, not the store flag.

## Closeout

Shipped 2026-05-31. See [evidence-story-01.md](./evidence-story-01.md).

Key outcome: the feared "silent egress" was **not** a live bug at the default
(`provider="local"` is structurally local-only); the value delivered is the
regression guard that locks that invariant, plus making the posture visible in
`doctor`, the runtime-status API, and the meeting-mode docs. No production
behavior changed — `local` already failed closed; `cloud`/`auto` still reach the
cloud by explicit choice. The dashboard badge is the only remainder, tracked as
HS-25-08.
