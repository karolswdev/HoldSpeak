# Phase 151 — The Live Intelligence Proof

**Status:** in progress (2/6).

**Last updated:** 2026-08-30.

## Owner mandate

The owner's pick from the post-150 menu (the value frame leads:
"a Senior Software Architect, who now manages 3 people").
Everything 147-150 built — record → transcribe → intel →
action_items → Door → person brief — has NEVER fired against a
real model end-to-end; every walk ran on seeded intel (the honest
list is in [audit-loop-census.md](./assets/audit-loop-census.md)
§faked). This phase makes the manager suite REAL on real metal.

Two owner rulings folded at charter (2026-08-30, verbatim intent):
"we can simulate it. I can certainly put up a youtube recording of
a 1:1" (real-speech audio through the real import door = the
honest headless treatment; the mic hop is the one attended leg),
and "you do have ssh keys to log in there... test the meetings
adapter please" (the vision probe ran pre-charter and PASSED —
[metal-probes.md](./assets/metal-probes.md)).

Branch `feat/hs151-live-intel-proof` from main `3a37e484`.

## Evidence base (pre-charter, all live)

- [`assets/metal-probes.md`](./assets/metal-probes.md) —
  orchestrator probes: .43 recon (8080 resident Qwen3.6-35B WITH a
  server-level `--json-schema {"line"}` pin; disk 98% — never
  download to the box); the 8081 vision server STOOD UP from the
  shelf (Qwythos-9B + mmproj) and PROVEN (4/4 events off a week
  grid at temp 0, first try; relaunch line recorded); the decisive
  schema probe — bare requests get `{"line": ...}`, request-level
  response_format overrides cleanly AND the model emits real named
  owners.
- [`assets/audit-metal-census.md`](./assets/audit-metal-census.md)
  — mlx-whisper 0.4.3 ready; the audio-file import door
  (meeting_import.py:201) shares the production persistence +
  intel-enqueue tail; the modern dispatch = profile + assignment
  on `meeting.deferred_analysis` (P55/P57 harnesses STALE); real
  multi-speaker meeting WAVs already in dogfood/_audio/.
- [`assets/audit-loop-census.md`](./assets/audit-loop-census.md)
  — the chain hop-by-hop; capture strictly needs a live input
  device (no file AudioSource); fresh intel items land PENDING in
  the UNASSIGNED lane; the intel prompt is PERSON-BLIND by design
  (steers to Me|Remote|null — pre-150); action-item identity =
  sha256(task:owner); the control-vs-treatment design.

## The two latent defects already found

1. **The bare-dispatch defect** (engine.py:294-303): cloud intel
   sends NO response_format — against the owner's actual resident
   server the pin swallows the JSON plea and intel parses nothing.
   Story 01.
2. **The person-blind prompt** (parsing.py:16-46): the intel
   schema forbids the very thing the 150 delegation lane exists
   for — named owners. Story 02.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-151-01 | The honest dispatch (structured output + the wiring recipe) | done | [story-01](./story-01-honest-dispatch.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-151-02 | The named-owner intel (the prompt learns people) | ready | [story-02](./story-02-named-owners.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-151-03 | The headless metal proof (control vs treatment) | ready | [story-03](./story-03-metal-proof.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-151-04 | The vision proof (the snapshot adapter on real metal) | done | [story-04](./story-04-vision-proof.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-151-05 | The record book | ready | [story-05](./story-05-record-book.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-151-06 | The walk, the attended leg, and the close | ready | [story-06](./story-06-walk-and-close.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

**2/6.** HS-151-01 (the honest dispatch) is DONE — the first
latent defect dies: cloud intel now sends request-level
structured output built from INTEL_SCHEMA, the ONE source of
truth the prompt stringifies, the response_format wraps, and the
adapter references (named-owner shape from birth). The pin-server
regression test reproduces the owner's real server's {"line"}
swallow against the old shape and proves the new one; the
response_format-400 fallback is a NAMED signal and a SECOND
admitted child (the max_completion_tokens compat pattern — never
two physical requests under one receipt); the _extract_json
line-recovery heuristic proven still live. scripts/
wire_metal_intel.py wires a fresh HOME through the REAL adoption
machinery (resolve-proof pinned; first live fire in story 03).
Census drift (18 entries) remapped 1:1 by the orchestrator with
dual attribution; the builder stopped at the red guard per the
law. Earlier — **1/6.** HS-151-04 (the vision proof) is DONE — the snapshot
adapter met a real vision model for the first time and the 146
"no real-vision-model probe" ledger line CLOSES: the truth image
4/4 with the anchor EXACT (visible_header, never guessed); the
messy image 3/4 with the all-day banner-row miss recorded as a
model limitation WITH its frame; the refusal leg clean (zero
invented events from a non-calendar image); both 146 counsel
riders (422 by-name surfacing; the vision pre-filter) verified on
real metal; JSON reliability clean (zero retries, zero malformed —
fences the only quirk). The phase's THIRD latent defect found and
fixed: parse_extraction_json had never met a fence
(bare json.loads → perfect model output refused as
unreadable_screenshot) — fence-strip per house precedent,
three-direction pin. LEDGER added: the ROUTED vision path stays
unproven (legacy profiles lack vision manifests —
inference_assignment_incompatible; the DIRECT DISPATCH fallback is
the 146-designed lawful path and carried the proof). Rig re-run
green by the orchestrator's own hand against live 8081; the rail
frame wears the real egress badge. Stories 01+02 hold in their
lane; 03 next.
Earlier — chartered 0/6 on the day 150 merged. The pre-charter probes
already de-risked the two scariest unknowns (vision metal EXISTS
and reads calendars; the schema pin is overridable) and found two
real latent defects before a single story ran.

## Decision log

- **2026-08-30 — owner pick:** the Live Intelligence Proof over
  JIRA Desk Sync, the Honest CI arc, and Desk Chat.
- **2026-08-30 — owner rulings:** simulate the meeting with a real
  1:1 recording (YouTube or shelf WAVs) — the attended leg plays
  real speech at the real mic, everything else headless; use ssh
  to .43 to stand up and test the vision model (done pre-charter).
- **2026-08-30 — orchestrator rulings (the spec):**
  (a) treatment audio enters by the REAL import door — sync/push
  is BANNED from every 151 proof rig (it is the fake this phase
  retires); (b) intel dispatch gains request-level structured
  output derived from the intel schema — local provider untouched;
  (c) the prompt evolves to named owners
  (`"owner": "<name>|Me|Remote|null"`) — parsing already passes
  strings; reserved handling stays exactly the 150 contract;
  (d) the modern wiring only (profile + assignment via the
  Phase-143 system) — no resurrection of the stale P55 kwargs;
  (e) 8081 is the vision route; 8080 stays the intel route with
  the override proving itself against the REAL pinned server (the
  harshest honest environment we have); (f) control-vs-treatment
  per audit B's design: same WAV, isolated HOMEs, artifacts =
  action_items rows / intel_snapshots / board JSON / brief
  sections / frames.

- **2026-08-30 — counsel design ruling: RATIFY-WITH-CONCERNS
  ("the charter is thorough; the pre-charter probes de-risked the
  scariest unknowns"). SIX must-fixes ABSORBED into the story specs
  before any builder:** M1 the response_format-400 fallback is a
  NAMED signal → a SECOND admitted child (the dictation runtime's
  ProviderCompatibilityRetry pattern; never two physical requests
  under one receipt — counsel verified the egress warrant shape is
  untouched by the new kwarg); M2 ONE schema source of truth in
  parsing.py (prompt stringifies it, response_format wraps it, the
  adapter references it); M3 the prompt declares Me/Remote as the
  ONLY reserved tokens, all others literal names; M4 the schema
  constant carries the named-owner shape from story 01, story 02
  updates prompt+constant together; M5 the grounded-owner
  assertion is case-insensitive SUBSTRING (an ungrounded owner is
  a recorded finding, not a rig failure); M6 the attended-leg
  evidence header states verbatim "simulated meeting (played
  recording), real capture path, real transcription, real intel"
  — never "real meeting". Should-fixes absorbed: S1 the pin test
  also proves the _extract_json line-recovery heuristic; S2 the
  vision rig exercises the refusal path (a non-calendar image →
  zero events or a named refusal). Counsel also VERIFIED: every
  downstream owner consumer treats owner as an opaque string (no
  Me|Remote assumption anywhere — lanes, overlay, aftercare,
  exports, cadence all safe); intel-disabled is the correct
  control; the import door shares zero DNA with sync/push (the ban
  is grep-enforceable). Ledgered: L1 identity churn (charter),
  L2 8081 JSON reliability recorded as a finding, L3 a bounded
  intel timeout (~15 min) at builder discretion.**

## Risk register

- The resident 8080 server is the owner's — proofs never restart
  or reconfigure it; the 8081 server dies on reboot (relaunch line
  in metal-probes.md); the box disk is 98% full — nothing is ever
  downloaded to it.
- Real model output is nondeterministic even at temp 0 across
  llama.cpp versions — proofs assert SHAPE and grounded content
  (owners that appear in the transcript), never exact strings.
- Messy owner reality ("Ewa S." vs "Ewa"; "myself"/"I" are not
  reserved): multiple aliases per person is the designed answer;
  the walk records what the real model actually emits.
- The intel queue worker and the import door run in the hub
  process — rigs must use the production worker path, not private
  shortcuts.
- 35B on cpu-moe is slow — intel legs need generous timeouts and
  the detached-run law (nohup + done-file) if a rig exceeds the
  10-min tool window.

## Ledger (charter-time, carried openly)

- Action-item identity sha256(task:owner) means a re-extraction
  with a drifted owner string creates a sibling row (not a
  delegated_at restamp) — observed at census, not this phase's
  fight.
- "myself"/"I" as model-emitted owners are mappable (not in the
  reserved set) — watch in the walk; rule only if it bites.
- The 393 reachability family and the CI-red family carry from
  150 untouched.
