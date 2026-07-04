# Phase 80 — Artifacts for the Archive (imports run the plugin chain)

**Status:** **CLOSED — 4/4 (2026-07-04, same day).** The F-05 fix landed and was re-proven on the same real `.43` sandbox that filed it (the addendum in `dogfood/results/2026-07-04.md`) — the Phase-67 dogfood run's headline
finding (F-05), promoted to a phase the same day it was filed.

**Last updated:** 2026-07-04 (**CLOSED, all four the same day.** `meeting_plugins.py`
is the seam: score → route → a standalone `PluginHost` (built-ins + project detector,
actuators proposal-only, heavy plugins inline) → one full-transcript window + per-plugin
run records + synthesized artifacts, with DB-backed idempotency on the window's
transcript hash (unchanged reruns dedup; artifact ids stay stable instead of stacking
per-execution LLM variance). The deferred-intel processor runs it after a successful
analyze — gated on `intent_router_enabled`, honest status detail either way, a chain
failure never fails the job; `--reroute` executes the rerouted chain against its own
window. RE-PROVEN on real metal: the same arch-review import that had ZERO artifacts in
the dogfood run now yields 4 (an accepted ADR with real context, a mermaid flowchart of
the discussed system, requirements, project association), and the delivery reroute
executes to 10 — the profile visibly changes the artifact set. 6 new tests (the seam,
idempotency, override, empty-raises, queue-on, queue-off byte-identical); the
import/queue/primitives battery 93 green. One lesson re-learned: `intel_queue` binds
`get_database` at module level — patch the lookup site, the Phase-63 rule.)

## Why this phase exists

The recorded dogfood run (`dogfood/results/2026-07-04.md`) proved it precisely:
**imported meetings never receive typed plugin artifacts.**

- The import path and the deferred-intel queue run base `MeetingIntel.analyze` only
  (`intel_queue.py:190-230`): summary, topics, action items — never the MIR router +
  plugin host that produce the typed artifacts (ADR drafts, mermaid diagrams,
  incident timelines, milestone plans, requirements…).
- `hs intel --reroute` records the intent window (`commands/intel.py
  _persist_cli_reroute`) but executes no chain — a route on paper.
- The plugin host runs ONLY on live meeting windows (`runtime/routing_glue.py`).

Half of the dogfood Tier 2's expectations (T2-01..06 artifact lists, T2-09 segment
probe, T2-10 plugin disabling, aftercare's decisions lane) rest on a capability the
archive path does not have. Meanwhile every building block already exists at library
level: `extract_intent_signals` (pure scoring), `preview_route` (pure routing),
`PluginHost.execute_chain` + `register_builtin_plugins`, `record_intent_window` /
`record_plugin_run`, and `synthesize_meeting_artifacts` → `record_artifact` — the
live path's own persistence recipe, currently reachable only from inside the web
runtime's mixins.

## The load-bearing design call

**One seam, host built on demand, the live path untouched.** A pure module
(`holdspeak/meeting_plugins.py`) exposes `run_meeting_plugin_chain(db, meeting, *,
profile, override_intents=None, threshold=None)`: build the transcript from the saved
segments → score → route → construct a standalone `PluginHost` (builtin plugins +
project detector; actuators stay proposal-only) → `execute_chain` over one full-
transcript window → persist the window + runs → synthesize + persist artifacts.
Idempotent by construction (the host's idempotency key is
meeting/window/plugin/transcript-hash; re-running a clean meeting dedups instead of
duplicating). The deferred-intel processor calls it after a successful base analyze
(gated on `intent_router_enabled`, honest status detail either way); `--reroute` and
the API override call it so a reroute finally *does* something. Live meetings keep
their windowed path byte-identical.

## Stories

| Story | Title | Status | Depends on |
|---|---|---|---|
| HS-80-01 | The persisted-meeting plugin-run seam (`run_meeting_plugin_chain`) — **leads** | done (6 tests; DB-backed idempotency) | none |
| HS-80-02 | Imports get artifacts (the deferred-intel processor runs the chain) | done (gated, honest detail, never fails the job; router-off byte-identical test-locked) | HS-80-01 |
| HS-80-03 | Reroute executes (CLI `--reroute` runs the chain against its window) | done (executed:true + statuses + artifact count on the payload) | HS-80-01 |
| HS-80-04 | Docs + the dogfood re-proof (the F-05-blocked rows re-driven on real `.43`) | done (CHANGELOG entry; the results addendum re-scores T2-01 + T2-07 PASS and unblocks the rest) | HS-80-01..03 |

## Where we are

CLOSED, opened and shipped in one sitting — the dogfood run filed F-05 in the morning
and the archive had its artifacts by night. The recorded run's addendum is the proof:
T2-01 re-scored PASS with the exact artifact list the protocol always expected, and
`--reroute` finally executes. Scope note kept honest: the live windowed path is
byte-untouched; the API override on live meetings already had its own surface — the
CLI reroute was the persisted-meeting gap and is the one closed here.
