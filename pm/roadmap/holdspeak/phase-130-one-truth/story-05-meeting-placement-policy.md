# HS-130-05 — One meeting placement policy

- **Project:** holdspeak
- **Phase:** 130
- **Status:** backlog
- **Depends on:** HS-130-01
- **Unblocks:** —
- **Owner:** unassigned

## The thesis (the bar)

Meeting intelligence has two owners and one silent no-op. `intel_provider`
(config/meeting.py:33) and `intel_profile_id` (config/meeting.py:59) both steer
the meeting leg with no stated precedence: `effective_intel_cloud`
(providers.py:359-377) resolves the pointer, `build_configured_meeting_intel`
(providers.py:220-237) *also* passes `provider=intel_provider`. With
`intel_provider` defaulting to `"local"`, **selecting a Meetings destination
under Models does nothing** (audit-2 claim 10, corrected from the issue's
"duplicate control" framing), and neither surface says so. Separately, a
`meshNode` pointer returns `MeshRelayIntel` *regardless* of
`intel_provider="local"` (providers.py:222-225) — the pointer silently
overrides a local-only setting and egresses. And `mir_profile` /
`plugin_profile` (config/meeting.py:68,79): the runtime reads the first
(web_runtime.py:182, intel_queue.py:272, session.py:116/185/721), doctor
reports the second (doctor.py:1098-1138).

### What changes

1. One meeting **placement policy** with an explicit fallback rule, resolved
   through HS-130-01's resolver — a selected destination is used, or the UI
   states why it is not (never a silent no-op).
2. `intel_provider` + `intel_profile_id` collapse to one placement decision;
   the local/auto/cloud intent and the destination pointer stop being two
   independent owners with no precedence.
3. `mir_profile` and `plugin_profile` converge to one `meeting.routing_profile`
   accessor; old values migrate once; doctor reports the field the runtime
   reads.
4. The chosen route's boundary is described by HS-130-04's one vocabulary.

## Acceptance criteria

1. Selecting a Meetings destination changes where meeting intelligence runs,
   or the surface states the effective placement and why the selection is
   overridden — no silent no-op.
2. A `meshNode` destination cannot be presented as "local"; its egress is
   named per HS-130-04.
3. One accessor owns the meeting routing profile; doctor and runtime name the
   same value; migration of legacy `mir_profile`/`plugin_profile` values runs
   once and is idempotent.
4. Meeting placement resolves through the one resolver, reporting effective
   target + source.

## Test plan

- Backend: a test that a selected Meetings destination is honored (or
  explicitly overridden with a stated reason); a mesh-not-local test; a
  routing-profile convergence + one-shot migration test; doctor/runtime
  agreement test.
- Web: the Meetings settings surface shows effective placement + source.
- Full backend suite read from file before flip.

## Out of scope

- Kernel admission of the meeting run and the per-utterance/per-session
  admission ruling (Phase 131 precondition — see the status doc's deferred
  decisions).
- Streaming/dictation placement (touched only where it shares the routing
  accessor).
