# Phase 151 — The Live Intelligence Proof: the exit record

Written 2026-08-30 at the close. The phase where the manager suite
stopped being a beautifully-pinned theory: for the first time in
the product's history, the record → transcribe → intel → Door →
person-brief loop ran end-to-end against real models, and every
walk that ever faked it with seeded intel is now obsolete.

## The Tuesday answer

Import (or record) a real meeting. Real mlx-whisper transcribes it
in seconds; the production queue dispatches to your own pinned
llama.cpp box; ~8 seconds later real action items land PENDING in
the Unassigned lane with the owners the model actually heard; you
triage, map an owner once, and the chips, staleness, and the
brief's People section light up — the whole 150 grammar fed by
genuine intelligence instead of test fixtures. A screenshot of a
locked-down O365 week goes through the same honesty: a real vision
model reads it 4/4 and the events ride the rail.

## The thirteen latent defects real metal found (the phase's argument)

| # | Defect | Fate |
|---|---|---|
| 1 | Cloud intel sent NO response_format — the owner's real pinned server swallowed the prompt's JSON plea into `{"line": …}`; production intel parsed NOTHING | FIXED (01): INTEL_SCHEMA one source of truth; request-level structured output; 400-rejection = named signal, second admitted child |
| 2 | The intel prompt was PERSON-BLIND by design (`owner: Me\|Remote\|null`) — the delegation lane's purpose suppressed by its own pipeline | FIXED (02): named owners; Me/Remote the only reserved tokens |
| 3 | The snapshot adapter had never met a markdown fence — a real model's PERFECT extraction refused as unreadable_screenshot | FIXED (04): fence-strip per house precedent, three-direction pin |
| 4 | Multi-window audio import broken in production — every 30s+ recording died on idempotency_payload_mismatch (the legacy admission never learned models are reusable across windows) | FIXED (03): loaded_artifact_reusable on TranscriptionAdmission |
| 5 | Core intel HARD-FAILED when an optional plugin capability couldn't freeze an assignment — one wired model yielded ZERO intel for every meeting | FIXED (03, focused-counsel-ruled Design A): unassignable meeting.plugin.* members skip WITH the plugin_chain_skipped receipt; core capabilities stay terminal; the binder stays strict |
| 6 | DeploymentRevision.from_artifact hardcodes kind="this_device" for remote endpoints | FIXED (06 ladder, #13 below closes it) |
| 7 | The conductor fire wiring referenced an out-of-scope name since HS-136-01 — every production scheduled-recording fire died on a NameError under a precedence-swallowed guard | FIXED (06): the routes' own contract + the wired-lambda pin |
| 8 | The lambdas probed runtime-private names the callbacks contract never carried — the fire silently no-opped | FIXED with #7 |
| 9 | SCHEDULER principals can never hold a parent route bundle — fired recordings captured audio and dropped every transcription interval | FIXED (06): the wake-shaped SERVICE lane + the sealed scheduled-recording@1 policy |
| 10 | Live sessions could not freeze speech.transcribe on ANY head-less HOME — owner included; fresh-install meetings persisted EMPTY, silently | FIXED (07, focused-counsel-ruled): the admission pre-check + honest record_only |
| 11 | RoutedMeetingTranscriptionAdmission never implemented frozen_preload_material — every routed meeting transcription interval failed silently | FIXED (06 finisher) + P7/P8 pins |
| 12 | admit_on_frozen_route call sites omitted parent_operation_id — SERVICE-admitted children refused | FIXED (06 finisher) |
| 13 | The wire path's remote deployments dressed as this_device (closes #6) + the wire script wrote to a DATABASE THE HUB NEVER OPENS (~/.holdspeak vs DEFAULT_DB_PATH) — the story-03 "cross-process invisibility" demystified | FIXED (06) |

Every one of these lived happily under green seeded tests — and
the last seven were found by ONE leg: the owner played a YouTube
1:1 at the machine and the product's entire fired-capture chain
turned out never to have worked. Fourteen takes descended the
ladder layer by layer; the fifteenth ran green end-to-end. That is
the phase's thesis, proven thirteen times.

## The arc

| Story | What shipped | Commit |
|---|---|---|
| Charter | live pre-charter probes (the 8081 vision server stood up from the .43 shelf and read a week grid 4/4; the decisive 8080 schema probe) + two censuses → design counsel RATIFY-W-C, six must-fixes absorbed pre-build | the charter commits |
| 04 vision proof | the snapshot adapter's first real model — full product path, refusal leg clean, both 146 riders verified live, the 146 vision ledger CLOSES | `story-04 commit` |
| 01 honest dispatch | structured output surviving the real pinned server; the wiring recipe | `story-01 commit` |
| 02 named owners | the prompt learns people; the 150 contract holds untouched | `story-02 commit` |
| 03 metal proof | THE LOOP IS REAL — control-vs-treatment on real speech; the messy-reality record verbatim; two production fixes ridden in; a focused counsel round mid-story (Design A, five pins) | `story-03 commit` |
| 05 record book | the metal truth reads cold; the .43 operator runbook; guards unfiltered ×2 | `story-05 commit` |
| 06 walk + close | the walk pair stamped; the sweep on both baselines; this counsel; THE ATTENDED LEG | the close |

## The messy-reality record (kept verbatim in evidence-story-03)

The ground-truth script names Priya/Wei/Jordan; the TTS-synthesized
WAV transcribed the audible name as "CREO", and the model grounded
HONESTLY in what it heard — owners ["CREO","Me","Me","Me"] one run,
["CREO","CREO","Me","Me"] the next; "break-glass" arrived as "brake
glass". Real nondeterminism, real transcription artifacts, zero
ungrounded owners — the shape-grounded assertion law vindicated on
its first outing.

## Close verification

- The walk pair (story-03 + story-04 rigs) each ×2 green across
  builder + orchestrator runs; the stamped 06 capture carries both
  tails; sync/push appears in NEITHER rig (grep-verified).
- Close sweep (both baselines): see evidence-story-06.
- Close counsel: see the decision log.
- THE ATTENDED LEG, GREEN: 22 real segments of the owner's chosen
  recording ("Sample one on one meeting with Ms. Rachel Peller and
  Dr. Peter Bakken") transcribed from the LIVE MIC through the
  production conductor's fire; the 35B's summary describes the
  actual conversation (the Wisconsin Early Childhood Association
  grant; the "color of the day" tradition); one grounded action
  item; the no-named-owner finding recorded honestly instead of
  faked. The honesty header on every artifact per counsel M6:
  simulated meeting (played recording), real capture path (live
  mic), real transcription (mlx-whisper), real intel (.43).
  The full fourteen-take forensic ladder is in the phase log and
  the commit messages — the leg's failures ARE its product.

## The consolidated ledger (owner-visible)

| Item | Class |
|---|---|
| The ROUTED vision path unproven (legacy profiles carry no vision manifest; direct dispatch — the 146-designed fallback — carried the proof) | carried, named |
| disabled_plugins is dispatch-time only; claim-time planning ignores it (Design A makes the failure mode moot; the setting's semantics stand) | counsel-deferred, ruled at close |
| project_detector unconditionally in every chain | counsel-deferred, ruled at close |
| no_assignment terminal at settlement (a later-wired user's errored jobs) | counsel-deferred, ruled at close |
| The stop-handoff "routes=0" observation (live windows execute; displaced work enqueues regardless; deferred processes) | ledger, counsel-addendum question |
| Live intelligence now runs under the delegated SERVICE lane for fired recordings (the owner armed the schedule) | counsel-addendum question |
| Action-item identity churn (sha256(task:owner)) + the 8081 server dies on reboot (runbook carries the relaunch line) | carried |

## Owner gates

The exhibit rides the close: story-03-shots (the first real
intelligence on the Door and in the brief) + story-04-shots (the
vision rail). The branch HOLDS for the owner's shot verdict and
merge word — no pre-given word this arc.

## The standing questions

**Tuesday?** ~10 s to transcribe two minutes of meeting, ~8 s to
extract, and the week's delegation flows from what was actually
said. **Joy?** The desk now tells the truth about where its
intelligence came from — and the six defects it took to get here
are the proof nobody else had ever asked it to.
