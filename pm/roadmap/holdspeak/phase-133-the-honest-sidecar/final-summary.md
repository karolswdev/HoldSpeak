# Phase 133 — The Honest Sidecar: final summary

**Verdict sought:** complete (11/11), one session (2026-08-16), zero
regressions. Owner sitting pending; counsel opinion recorded alongside.

## What shipped

The MCP sidecar went from 52 tools to **82** across eight new families —
ask (5), settings (2), coder (3), cadence (11), sequence (2),
workflow (2), memory (1), plugin_job (4) — plus one new resource
(`holdspeak://cadence/status`), with **zero new provider-reaching side
doors**: all four model-invoking tools (`ask.run`,
`cadence.get_loop` conditional, `sequence.run`, `workflow.run`) ride
the existing admitted `InferenceRunner.invoke()` paths. The honesty
sweep paid every audited debt: `auth.py` tells the truth (dead
`HOLDSPEAK_URL`/`url` removed, process-boundary-as-trust-boundary
docstring), the Phase-122-promised `holdspeak-mcp` console script
exists, `.mcp.json` sits at the repo root (holdspeak-only per counsel),
list resources are bounded at 100, the 6-vs-17 kind gap is named in
every `desk.*` description, and `pipeline_events_query` died in favor
of `pipeline.events` with zero grep hits remaining.

## The method

Audit → design → ruling → charter → waves → walk, one day:

1. **Three parallel Opus audits** (structural census, static+live MCP
   surface, canon/backlog) on `d4acbbe7` produced the evidence base;
   reports summarized in the charter, full session records with the
   orchestrator.
2. **The design beat**: the full surface spec (every tool name, schema,
   dispatch anchor, invariant) drafted against real service signatures,
   then **ruled by a fresh Opus counsel** — verdict "implementation may
   begin" under four conditions, all folded into
   [assets/surface-spec.md](./assets/surface-spec.md) before any
   implementation.
3. **Waves**: a keystone (per-family modules + registry) landed first
   so seven parallel workers touched disjoint files; serialized SHIP
   through the DW gate — eleven story commits, every one contracted and
   evidence-paired.
4. **The walk**: `scripts/mcp_walk.py` boots the real subprocess over
   real stdio — 26 assertions, full JSON-RPC transcripts committed, and
   a live `.43` proof: receipt model == endpoint's loaded model
   (`Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf`), control-vs-treatment.

## Judgment calls the orchestrator made alone (for review)

1. **Spec amendment at wave open** (committed `4ee6e69e`, visible in
   the spec): per-family test files instead of one shared
   `test_mcp_phase133.py`, and REQUIRED_TOOLS extensions serialized to
   SHIP time — pure contention avoidance; the test-law intent
   unchanged.
2. **Counsel condition 1 resolution**: ruled ADD for
   `cadence.run_now`/`cadence.apply_closeout` (counsel had verified
   both local-DB-only), taking the count from 28 to 30.
3. **Keystone rider** (`b42b8796`): family routing changed from
   catch-LookupError to ownership-by-name-membership after the Ask
   worker's guard exposed the class (a service `KeyError` would read as
   "not mine" and misreport as Unknown tool). Regression test added.
4. **Walk seam fixes** (in the walk commit): the `.43` profile needed
   `kind: "private_endpoint"`; the live leg boots with
   `--extra meeting` because the OpenAI-compatible provider is an
   optional extra. Both diagnosed live; the pre-fix refusals were
   themselves honest, named errors (Article VI behaving as designed).

## The ledger

- Two distinct single-run timing flakes under xdist load
  (`test_device_recording_tick::test_sender_exception_does_not_kill_thread`,
  `test_mesh_receiver_authority::test_an_expiry_on_another_connection_wins_the_settlement`),
  each 3/3 green serially, both untouched by this phase → recorded for
  BACKLOG Candidate Z.
- Suite verdicts: wave-A gate 5781 passed, final gate 5799 passed,
  zero regressions against the green pre-phase baseline.

## Held for the owner sitting

1. **Resource observer asymmetry** (spec Q5): tool reads observed,
   resource reads not — ratify under Article XI.5 or fix in a future
   story. Orchestrator default: future story.
2. **`companion_github_repo` writable via `settings.update`** (counsel
   C.iii): not in SECRET_PATHS; redirectable destination, no new egress
   channel. Orchestrator default: acceptable, documented.

## Deferred (named, not waived)

Coder write verbs, `cadence.reply`, `plugin_job.process` (live-runtime
delivery paths the stdio sidecar does not own — absences named in tool
descriptions); the unselected One Chokepoint items (kernel admission
for non-inference writes, observer holes, runner dedup); issue #450
Wave 1 remains the owner-named next product slice.

## Evidence pack

Eleven evidence files (`evidence-story-01..11.md`), the ruled spec with
its counsel-ruling record, two committed JSON-RPC walk transcripts in
`assets/`, and the suite logs referenced from the evidence. The walk
harness is reusable: `uv run python scripts/mcp_walk.py [--live-43]`.
