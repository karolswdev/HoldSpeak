# Phase 151 — The Live Intelligence Proof

**Status:** in progress (6/7) — the rider is DONE; the close holds
for the attended replay + the owner's shot verdict + merge word.

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
| HS-151-02 | The named-owner intel (the prompt learns people) | done | [story-02](./story-02-named-owners.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-151-03 | The headless metal proof (control vs treatment) | done | [story-03](./story-03-metal-proof.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-151-04 | The vision proof (the snapshot adapter on real metal) | done | [story-04](./story-04-vision-proof.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-151-05 | The record book | done | [story-05](./story-05-record-book.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-151-06 | The walk, the attended leg, and the close | in-progress | [story-06](./story-06-walk-and-close.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-151-07 | The fired-session admission (the attended leg's rider) | done | [story-07](./story-07-fired-session-admission.md) | [evidence-story-07](./evidence-story-07.md) |

## Where we are

**6/7.** HS-151-07 (the fired-session admission) is DONE — the
attended leg's four-defect ladder ends at bedrock, fixed: the
meeting admission pre-checks the speech head (counsel-ruled,
~30 lines, one file, bundle service untouched); absent → honest
record_only with the reason and repair named, never a silent empty
transcript; present → the full four-route bundle for OWNER and the
new SERVICE scheduled-recording lane alike. Six pins green (95
focused under the orchestrator's hand). The startup speech
migration confirmed as the head's lawful source on any
whisper-capable HOME. Defects #7-#10 all landed or ledgered with
receipts. Remaining: the attended REPLAY through the whole fixed
chain, then story 06's close.
Earlier — **5/6.** HS-151-05 (the record book) is DONE — the metal truth
reads cold: MODELS.md speaks the INTEL_SCHEMA shape and the
Me/Remote-only reserved law verbatim from parsing.py; the
architecture doc gained the structured-output and Design-A
sections; USER_GUIDE walks the named-owner triage loop with
latencies from evidence, not hope; and
docs/internal/OPERATOR_METAL_INTEL.md graduates the probe record
into a real runbook (the pin fact + do-not-touch law, the 8081
relaunch line, never-download-to-the-box, wire_metal_intel usage).
Guards unfiltered 33/33 twice (builder + orchestrator). Only 06
remains — the walk graduation and sweep run headless next; the
ATTENDED leg (the owner plays their 1:1 recording at the real mic)
is the one moment that waits for a human.
Earlier — **4/6, ALL FEATURE STORIES DONE.** HS-151-03 (the headless metal
proof) is DONE — THE LOOP IS REAL for the first time in the
product's history: real WAV → real mlx-whisper → the real import
door → the production queue (with the counsel-ruled Design-A skip
freezing only what resolves, receipted) → the REAL pinned resident
server → real pending action items on the Door → the real triage +
map gestures → the brief's People section; control leg all-zero on
the same audio; sync/push nowhere; extraction ~8 s on the 35B. The
messy-reality record is in the evidence verbatim (the TTS voice
transcribed the owner as "CREO" and the model grounded honestly in
what it heard; owners drift between runs — the shape-grounded
assertion law vindicated). The story shipped THREE product fixes
counsel-ruled or precedent-clean: the multi-window import
idempotency defect, the Design-A claim skip with all five pins,
and (recorded, not fixed) the remote DeploymentRevision kind
hardcoding. Six latent defects total now found by real metal.
Remaining: the record book (05), the walk + the ATTENDED leg +
close (06). Earlier — **3/6.** HS-151-02 (the named-owner intel) is DONE — the
person-blind prompt dies: intel now names owners when the
transcript does (Me/Remote declared the ONLY reserved tokens,
counsel M3 verbatim), the schema constant and prompt updated
together, and the canary round-trips "Ewa" and "Jan Kowalski"
through the pin server into pending action_items rows verbatim.
The interplay pins prove the 150 contract holds untouched: named
owners map through the real gesture, reserved strings refuse.
Counsel's verification stands — every downstream consumer treats
owner as opaque; only the prompt/schema changed. Next: story 03
(the headless metal proof) — both its dependencies are now on the
tree. Earlier — **2/6.** HS-151-01 (the honest dispatch) is DONE — the first
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

- **2026-08-30 — focused counsel (the Gap-2 claim fix):
  RATIFY-WITH-AMENDMENTS, Design A** — skip-unassignable-plugin-
  with-receipt at CLAIM PLANNING. Grounded in the C2 precedent
  ("disabled plugins remain frozen bundle members at claim time
  and resolve skipped at execution") and the dispatch path's
  existing containment vocabulary (skipped/refused/error while
  core analysis survives). Five pins: fix in
  _plan_installed_plugin_members (probe each plugin capability via
  the binder's own resolution; exclude on no_assignment), the skip
  RECORDED in the frozen route metadata (never silent), core
  capabilities NEVER skip (terminal stays terminal), the binder's
  prepare stays strict and untouched, router.py's chain stays
  honest. Config-absent boundary preserved (the probe reads
  persisted assignment heads only). Rejected: a claim-time
  disabled_plugins gate (violates the Config-absent principle and
  doesn't fix assignment-absence), wiring-side burden, chain
  surgery. Deferred to close counsel: project_detector's always-on
  status; binder defense-in-depth; whether no_assignment should be
  terminal at settlement.

- **2026-08-30 — CLOSE counsel: RATIFY-WITH-CONCERNS, ZERO
  must-fix, ONE should-fix (applied in-round), 228 focused green.**
  The no-fake law CLEAN (zero sync/push in any rig; treatment rides
  the real import door; assertions shape-grounded throughout; the
  CREO groundedness call ruled honest). All FIVE Design-A pins
  verified, incl. the negative test (core capabilities terminal)
  and the binder's own defense-in-depth (it independently
  re-validates reachability at prepare — it never trusts the
  planner blindly). The structured-output fallback mechanically
  correct: one physical request per admitted child, named signal,
  the follow-up child omitting the format. Idempotency fix SAFE
  (single bounded session; no mid-import config change possible);
  fence-strip SAFE (anchored non-greedy regex; the three pins).
  Tuesday + joy PASS ("the loop is real, the latencies are honest,
  the documentation prepares a cold reader"); no attended-demo
  embarrassment found beyond documented behaviors. S1 APPLIED
  IN-ROUND: the process-lifetime response_format downgrade now
  logs a warning (census re-remapped, 17 entries, attribution:
  the S1 lines). LEDGERED: S2 the plugin_chain_skipped receipt is
  DB/log-only — surfacing it is a P1 for a future
  settings/diagnostics story; L1 project_detector always-routed
  (now routinely skip-with-receipted by default — document or
  rule); L2 skipped plugin work unrecoverable without re-import (a
  "re-analyze" gesture is a future arc); L3 the dialect set has no
  TTL (same accepted shape as HS-131-10); L4 the remote
  DeploymentRevision kind hardcoding.

- **2026-08-30 — focused counsel (HS-151-07): RATIFIED — the
  admission pre-checks the speech head.** The meeting admission
  probes for a capability:speech.transcribe assignment head before
  declaring routes; absent → transcription+preload EXCLUDED from
  the bundle (which stays all-or-nothing for what it is given),
  raw capture continues, and the refusal is VISIBLE
  (transcription_status="record_only",
  reason_code=transcription_no_speech_assignment, the repair
  named) — Design-A spirit at the live bundle. The capability-only
  seam was REJECTED on evidence (it also requires a head — it only
  narrows scope); triggering the speech migration from the meeting
  path rejected as coupling. Six pins (P1-P6). ALL of tonight's
  groundwork KEPT (SERVICE principal, sealed scheduled-recording@1,
  the wiring, the fire contract). Open follow-through: P1/P3
  assume the SPEECH MIGRATION creates the head on configured
  HOMEs — the builder must find/trigger that mechanism for the
  attended HOME or surface the gap honestly.

## Risk register

- The resident 8080 server is the owner's — proofs never restart
  or reconfigure it; the 8081 server dies on reboot (relaunch line
  in metal-probes.md); the box disk is 98% full — nothing is ever
  downloaded to it.
- Real model output is nondeterministic even at temp 0 across
  llama.cpp versions — proofs assert SHAPE and grounded content
  (owners that appear in the transcript), never exact strings.
- Story-03's found-defect ledger (beyond the fixed ones): the
  wire-script cross-process DB visibility oddity (worked around
  in-process in the rig; needs a crisp repro before it earns a
  fix); disabled_plugins being dispatch-only remains a product
  truth the close counsel sees.
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
