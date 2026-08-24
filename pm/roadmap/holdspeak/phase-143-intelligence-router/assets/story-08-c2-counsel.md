# Story 08 · Phase C slice C2 counsel (Sol, capped pass)

Reviewed at `f3546f8d`, 2026-08-24, under the owner's capped protocol
(one ruling round + at most one fix round; findings must reproduce on
an ordinary product action; adversarial/timing exotics = recorded
notes). Fresh counsel session, scoped to C2 only.

## Verdict: DO-NOT-RATIFY → fixed in the single permitted fix round

**The one blocker (ordinary-path, reproduced):** C2 ignored the
owner-facing **Disabled plugins** setting. The disabled/skipped gate
read `host.disabled_plugins`, an attribute production `PluginHost`
never defined, and the production bound-host construction never loaded
`MeetingConfig.disabled_plugins` (`holdspeak/config/meeting.py:86-90`,
the persisted authority behind
`web/src/pages/cores/SettingsCore.tsx:865`). Counsel's probe: disable
`requirements_extractor`, process a normal saved Meeting → the disabled
plugin executed (`success`), five children, four artifacts, Meeting
`ready`. Unwanted execution and lying glass from a routine owner
action. The committed test had masked the omission by setting the
synthetic attribute on its fake host — proof of the fake, not the
product (report-inflation, named as such).

**Everything else PASS under counsel's own production probes:** frozen
registry authority + exact bundle membership (`db/intel.py:284-342`,
`:802-868`; binder `:61-165`); runtime-string planning dead for new
jobs with terminal visible refusals; pre-child descriptor/capability/
host/bundle agreement with honest drift refusal (live probe: drifted
plugin minted no child, base analysis survived, glass showed the named
refusal); inner-output-only semantics; receipt-gated projection under
C1's transcript/executor-epoch fences; no parallel executor/retry/
preflight machinery. Ordinary-path probes 1 (install→process) and 3
(drift) passed live.

## The fix (same day, single round)

Production bound host loads and normalizes persisted
`MeetingConfig.disabled_plugins` (`meeting_plugins.py:458-478`);
`PluginHost` formally owns an immutable `disabled_plugins` disposition
(`plugins/host.py:141-160`); the gate reads it before host/member/
bound-child admission (`meeting_plugins.py:604-608`). Design choice,
stated: disabled plugins remain frozen bundle members at claim time and
resolve `skipped` at execution before admission — preserves the
immutable built-chain descriptor; the precomputed allowance goes
unused; zero children, zero artifacts. The proof is production-shaped:
real persisted config, real `Config.load()`, real
`build_bound_meeting_plugin_host()`, no synthetic attributes
(`test_meeting_deferred_admission.py:1676-1718`) — disabled plugin
`skipped` with the truthful disposition, unaffected plugin succeeds,
Meeting `ready`. Full files green: deferred admission 39, meeting
plugins 8, plugin disable 12, host idempotency 3.

Confirming sweep: **6414 passed / 68 baseline-inherited / zero
branch-new** (two delivery-campaign load flakes serial-green ×2).

## Orchestrator disposition

Blocker accepted and fixed within the capped protocol; the disable fix
is verified against the counsel's own probe recipe by the
production-shaped test plus the sweep — per the owner's protocol, no
second counsel round is convened. C2 is CLOSED. The lesson recorded
for worker briefs: proofs must construct the production object, never
decorate a fake with the attribute under test.
