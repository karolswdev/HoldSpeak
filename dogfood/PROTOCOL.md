# HoldSpeak Dogfood Protocol

> **Superseded by the UAT rig.** UAT is now run through the web-based framework
> at [`../uat/`](../uat/README.md): `uv run python -m uat.conductor` boots an
> isolated HoldSpeak, stages named idempotent state recipes, and walks you
> through a pack beat by beat with a verdict per surface landing in a run DB — a
> guided site instead of this fillable checklist (which sat on the shelf, the
> exact failure mode UAT exists to prevent). This file's **substrate is reused**
> by the rig — the isolated `_home` recipe (ported to `uat/conductor/home.py`),
> the mock repos under `repos/`, the committed transcripts under `transcripts/`,
> and `make_fixtures.py` — so nothing here is dead; it is the conductor's
> foundation. Keep this document as the manual fallback and the substrate's home;
> **run UAT from `../uat/`.**

The end-to-end exercise. You drive a real, isolated HoldSpeak against believable
data — three mock repos with `.hs/` context and completed-stage history, plus
meetings and dictation rendered through the macOS `say` voices — and you check
off what works. The point is to feel every surface the way a user does, on
real metal, and to keep a fillable record you can re-run each release.

**How to use this file**

1. Run the preflight (section 0).
2. Copy this file to a dated run: `cp dogfood/PROTOCOL.md dogfood/results/$(date +%F).md`
   (the `results/` copies are gitignored — fill those in, leave this master clean).
3. Work top to bottom. For each check, set **Result** to `PASS` / `FAIL` /
   `PARTIAL` / `SKIP` and jot a **Note** (what you saw, screenshot path, the bug).
4. Roll the run up in `dogfood/RESULTS-TEMPLATE.md`'s header (env, tier, score,
   top failures) at the top of your dated copy.

**Two tiers** (you chose both):

- **Tier 1 — Plumbing.** No LLM, no microphone. Fast, deterministic, run it
  every iteration. Catches dead routes, broken imports, config drift.
- **Tier 2 — Real metal.** Real `say` → Whisper → intel on `.43`. The truth
  tier: proves the LLM-shaped features actually produce output, not just plumb.

Legend: `hs` = the isolated launcher (`dogfood/hs`, or `hs` after `source
dogfood/env.sh`). Web routes are on the URL `hs web` prints. "Expect" is the
pass bar; if reality disagrees, that's a `FAIL` and a finding.

---

## 0 · Preflight

- [ ] **P-01 · Build the sandbox.** `dogfood/setup.sh` (tier-2 config, intel → `.43`).
  - Expect: writes `_home/.config/holdspeak/config.json`; links HF cache + Models.
  - Result: ___  · Note:

- [ ] **P-02 · Isolated doctor is green.** `dogfood/hs doctor`
  - Expect: runtime deps OK; config loads; DB at the sandbox path (not your real `~`).
  - Result: ___  · Note:

- [ ] **P-03 · `.43` reachable.** `curl -s http://192.168.1.43:8080/v1/models` (use `dangerouslyDisableSandbox` if scripting).
  - Expect: a model list comes back. If not, Tier 2 is blocked — do Tier 1 only.
  - Result: ___  · Note:

- [ ] **P-04 · Render fixtures.** `python dogfood/make_fixtures.py` (macOS `say`).
  - Expect: `_audio/*.wav` for 6 meetings + 6 dictation sets; `MANIFEST.json`; `*.script.txt` ground truth.
  - Result: ___  · Note:

- [ ] **P-05 · Plumbing e2e green.** `HOLDSPEAK_DOGFOOD=1 uv run pytest -q tests/e2e/test_dogfood_plumbing_e2e.py`
  - Expect: all pass (scenarios well-formed, repos load, transcripts parse).
  - Result: ___  · Note:

---

## 1 · Tier 1 — Plumbing (no LLM, no mic)

> Optionally swap to the lean config first: `dogfood/setup.sh --tier1 --force`.
> Everything here must work with intel and the dictation pipeline off.

### 1.1 CLI surface

- [ ] **T1-01 · doctor variants.** `hs doctor --strict` then `hs doctor --connectors`
  - Expect: `--strict` exits non-zero only on real warnings; `--connectors` lists packs + discovery errors.
  - Result: ___  · Note:

- [ ] **T1-02 · Help for every subcommand.** `hs --help`, then `--help` on `web meeting history actions import doctor backup restore dictation agent-hook device-psk intel`.
  - Expect: each prints usage, no traceback.
  - Result: ___  · Note:

- [ ] **T1-03 · Backup / restore round-trip.** `hs backup`; note the `.bak`; `hs restore` (list); `hs restore <file> --yes`.
  - Expect: timestamped backup created; restore confirms then swaps; DB intact.
  - Result: ___  · Note:

- [ ] **T1-04 · device-psk.** `hs device-psk show` then `hs device-psk rotate` then `show`.
  - Expect: a PSK shows; rotate changes it; persisted in sandbox config.
  - Result: ___  · Note:

### 1.2 Import — transcript path (deterministic, no Whisper)

- [ ] **T1-05 · Import all three committed transcripts.**
  `hs import dogfood/transcripts/pylon-incident.vtt --title "Pylon cert outage" --tag incident`
  then the `.srt` and `.txt`.
  - Expect: three meetings created fast (no model load); segments carry speakers (Jordan/Wei/Priya; Priya/Mara/Sam; Dana/Ravi/Meaghan).
  - Result: ___  · Note:

- [ ] **T1-06 · History CLI.** `hs history`; `hs history -s cert`; `hs history --from 2026-01-01 --to 2026-12-31`; `hs history <id>`; `hs history <id> --export markdown` (also `json`, `txt`).
  - Expect: list, search hit, date filter, detail, and all three export formats render.
  - Result: ___  · Note:

- [ ] **T1-07 · Actions CLI.** `hs actions --all`; `hs actions --owner Priya`; `hs actions --done <id>`; `hs actions --dismiss <id>`.
  - Expect: cross-meeting action items list; owner filter works; done/dismiss change state.
  - Result: ___  · Note:

### 1.3 Web surface — every page loads

- [ ] **T1-08 · Launch web isolated.** `hs web` (note the URL/port).
  - Expect: server binds 127.0.0.1; `/health` returns OK.
  - Result: ___  · Note:

- [ ] **T1-09 · Walk every page.** Open `/`, `/welcome`, `/setup`, `/history`, `/settings`, `/activity`, `/dictation`, `/commands`, `/companion`, `/presence`, `/docs/dictation-runtime`.
  - Expect: each renders with content (no blank tab, no console error, no 500). Note any that look unstyled or empty.
  - Result: ___  · Note:

- [ ] **T1-10 · History UI + facets.** On `/history`: the 3 imported meetings show; filter by speaker facet, by tag, by date.
  - Expect: faceted search narrows the list server-side.
  - Result: ___  · Note:

### 1.4 Config cockpit

- [ ] **T1-11 · Read + write settings.** On `/settings`: change the hotkey display, the model name, the transcription language, toggle presence. Save.
  - Expect: changes persist to `_home/.config/holdspeak/config.json` (verify by reading the file); reload shows them.
  - Result: ___  · Note:

- [ ] **T1-12 · Settings is sectioned + searchable.** Search the settings page for "wake", "macro", "intel".
  - Expect: the search surfaces the right sections; every knob from `config.json` is reachable.
  - Result: ___  · Note:

### 1.5 Dictation plumbing

- [ ] **T1-13 · dry-run with pipeline off.** `hs dictation dry-run "claude add idempotency to the charge endpoint"`
  - Expect: prints the pipeline trace + final text; works with no LLM backend (stages skipped honestly).
  - Result: ___  · Note:

- [ ] **T1-14 · blocks + runtime.** From inside `dogfood/repos/ledgerline`: `hs dictation blocks ls`; `hs dictation blocks show agent_task_buildout`; `hs dictation blocks validate`; `hs dictation runtime status`.
  - Expect: the repo's `blocks.yaml` resolves; the block shows; validate passes; runtime status reports the resolved backend.
  - Result: ___  · Note:

- [ ] **T1-15 · Journal records even without typing.** After a couple of dry-runs, confirm rows in the journal (DB `dictation_journal`, or the journal view).
  - Expect: raw + final text + warnings stored; retention cap honored.
  - Result: ___  · Note:

- [ ] **T1-16 · Spoken-symbol mapping (text path).** `hs dictation dry-run "email me at sign ledgerline dot dev"` with the tier-config symbol table.
  - Expect: "at sign" → `@`; check `hash`/`dash`/`percent sign` and that attach modes control spacing.
  - Result: ___  · Note:

- [ ] **T1-17 · Voice macros dry-fire.** On `/commands`: the 4 macros (open inbox / launch editor / list files / paste quote) list; use the test-fire button (`/api/commands/test`) on each.
  - Expect: keyword match is whole-utterance + normalized; each action kind (open_url/launch_app/shell/type_text) reports a correct dry-fire; nothing fires on a non-match.
  - Result: ___  · Note:

### 1.6 Audio import plumbing (Whisper, intel off)

- [ ] **T1-18 · Import a rendered meeting with intel off.** `hs import dogfood/_audio/meeting-questline-balanced-sync.wav --title "Balanced sync"`
  - Expect: meeting goes `importing` → transcribes via Whisper → persists; transcript is recognizable against `meeting-questline-balanced-sync.script.txt`. No artifacts (intel off) — that's correct.
  - Result: ___  · Note:

- [ ] **T1-19 · Bad-format import is honest.** `hs import dogfood/PROTOCOL.md`
  - Expect: a clear "unsupported format" error, no crash, no empty meeting.
  - Result: ___  · Note:

---

## 2 · Tier 2 — Real metal (`say` → Whisper → `.43` intel)

> Use the tier-2 config (`dogfood/setup.sh` default). Each meeting import below
> runs the full intel pipeline. Compare artifacts against the scenario's
> `description` and the repo's completed-stage docs. Intel is non-deterministic —
> judge on substance (did it surface the decision, the owners, the risk?), not
> exact wording.

### 2.1 Meetings — one per MIR profile

- [ ] **T2-01 · Architect review (ledgerline).** `hs import dogfood/_audio/meeting-ledgerline-arch-review.wav --title "Scaling the write path"` with `mir_profile=architect`.
  - Expect artifacts: an **ADR draft** (event-sourced write log), a **mermaid** component diagram, a captured **decision** (adopt event sourcing + hourly snapshots, defer sharding), a **dependency map** (snapshot ← append log; reconcile ← snapshot+tail), **action items** with owners (Alex=ADR, Mara=property test, Priya=migration).
  - Result: ___  · Note:

- [ ] **T2-02 · Incident retro (ledgerline).** Import `meeting-ledgerline-incident-retro.wav`, `mir_profile=incident`.
  - Expect: an **incident timeline** (14:02 retry storm → 14:11 23 double-posts → 16:40 made whole), a **runbook delta** (over-billing remediation + duplicate-key alert), a **risk** (no concurrency/load test), a **decision** (don't close LL-118 until both tests green), owners (Mara/Priya/Sam).
  - Result: ___  · Note:

- [ ] **T2-03 · Product review (questline).** Import `meeting-questline-product-review.wav`, `mir_profile=product`.
  - Expect: **requirements** for guilds v1 (create/invite-link/shared quest/leaderboard; non-goal no public directory), **customer signals** (accountability-with-friends demand), a **risk** (moderation/abuse surface; activation leak), a **decision** (defer guilds, fix activation, run a flagged shared-quest experiment to measure WAQC).
  - Result: ___  · Note:

- [ ] **T2-04 · Delivery standup (questline).** Import `meeting-questline-delivery-standup.wav`, `mir_profile=delivery`.
  - Expect: a **milestone plan** (M1 onboarding fix → M2 streak tz → M3 shared-quest experiment; guilds v1 → Q4), a **scope-guard** flag (onboarding revamp must not grow into a full redesign), a **decision** + owners.
  - Result: ___  · Note:

- [ ] **T2-05 · Incident war-room (pylon).** Import `meeting-pylon-incident-warroom.wav`, `mir_profile=incident`.
  - Expect: a **timeline** (09:14 page → 09:18 TLS errors → 09:52 mitigated, ~38m SEV-2), root-cause chain (PI-198 net-policy → ACME solver blocked → silent renewal fail), a **runbook delta** (break-glass reissue; ACME-path validation), a **risk** (no synthetic ACME test), a **decision** (14-day headroom alert + synthetic ACME CI test), owners.
  - Result: ___  · Note:

- [ ] **T2-06 · Balanced sync (questline).** Import `meeting-questline-balanced-sync.wav`, `mir_profile=balanced`.
  - Expect: the buried **decision** (monthly opt-in product-update email) is captured despite the small talk; **action items** with owners (Meaghan=draft email, Tom=watch staging, Dana=tell marketing + leadership note); maybe a **stakeholder update** draft. Brief intents are not dropped.
  - Result: ___  · Note:

### 2.2 Routing controls

- [ ] **T2-07 · Profile changes the artifacts.** Re-route T2-01 under `delivery` then `incident`: `hs intel --route-dry-run <id> --profile delivery` and `--reroute <id> --profile architect`. Or via `/api/intents/profile`.
  - Expect: the plugin chain (and artifacts) differ by profile; dry-run shows the plan without persisting; reroute persists.
  - Result: ___  · Note:

- [ ] **T2-08 · Manual intent override.** `hs intel --reroute <id> --override-intents incident,architecture --threshold 0.5`; or `/api/intents/override`; or `/api/intents/preview` on a snippet.
  - Expect: the override forces those intents; preview simulates a route for arbitrary text.
  - Result: ___  · Note:

- [ ] **T2-09 · Segment probe surfaces buried intents.** With `intent_segment_probe_enabled` off, import the balanced sync; then on, re-import. Compare.
  - Expect: with the probe on, the brief/buried decision in T2-06 is less likely to be dropped.
  - Result: ___  · Note:

- [ ] **T2-10 · Plugin disabling.** Set `disabled_plugins=["mermaid_architecture"]`, re-run T2-01.
  - Expect: the diagram plugin is **skipped** (visible in plugin-runs), not failed; other artifacts unaffected.
  - Result: ___  · Note:

### 2.3 Deferred intel queue

- [ ] **T2-11 · Queue + process + retry.** With `.43` briefly unreachable, import a meeting (job queues); `hs intel` (list), `hs intel --process`, `hs intel --retry <id>`, `hs intel --retry-failed`; `/api/intel/summary`.
  - Expect: jobs queue when realtime is down, process on demand, retry with backoff; summary reports failed % / backoff.
  - Result: ___  · Note:

### 2.4 Aftercare

- [ ] **T2-12 · Aftercare digest + jump + draft.** On a finished meeting: `/api/meetings/<id>/aftercare`, `/followup-draft`; in the UI use the transcript-moment jump.
  - Expect: an open/decided/changed digest; jumping lands on the right transcript moment; a local follow-up email draft reads sensibly. Read-only — nothing executes without approval.
  - Result: ___  · Note:

### 2.5 Actuators — propose → approve → execute

- [ ] **T2-13 · Approval is the gate.** With `allow_actuators=false`, open a meeting's aftercare.
  - Expect: the dashboard/UI offers no un-gated execute affordance; nothing runs without an explicit approval. (Per the ratified aftercare design, approving a proposal IS the execution gate on that route — approval executing is correct, not a failure.)
  - Result: ___  · Note:

- [ ] **T2-14 · GitHub issue actuator.** Set `allow_actuators=true`, `allowed_actuators=["github_issue_actuator"]`. From an accepted action item, propose → approve → `/aftercare/file-issue`.
  - Expect: a proposal with target + preview; approval gates execution; the result carries an **egress badge** (cloud + target). (Use a throwaway repo or a dry path.)
  - Result: ___  · Note:

- [ ] **T2-15 · Slack send.** Set `slack_webhook_url` (a real incoming webhook, or observe the refusal when empty). `POST /api/meetings/<id>/export/slack`.
  - Expect: with a URL set, the digest/draft posts to Slack via propose→approve→execute; the egress badge shows `cloud` + the Slack target; the URL never appears in any stored payload.
  - Result: ___  · Note:

- [ ] **T2-16 · Webhook host allowlist.** Enable `webhook_post_actuator`, set `webhook_allowed_hosts=["example.com"]`, try a proposal targeting a non-listed host.
  - Expect: the unlisted host is **refused**; a listed host is allowed.
  - Result: ___  · Note:

### 2.6 Dictation — real voice, grounded rewriting

> Render the dictation clips (P-04). Feed each clip through the real pipeline
> (hotkey capture, or the dictation runtime against the rendered audio). The
> rewriter must ground in the repo's `.hs/` + KB. Run from inside each repo dir
> so project detection fires.

- [ ] **T2-17 · ledgerline grounding.** Speak/feed `dictation-ledgerline` from `dogfood/repos/ledgerline`.
  - Expect: rewrite names concrete files (e.g. `src/ledgerline/api/charges.py`, `db/idempotency.py`), adds an **acceptance-criteria checklist**, and calls out the **append-only / double-entry / idempotency** invariants from `.hs/memory.md`. Not a paraphrase.
  - Result: ___  · Note:

- [ ] **T2-18 · questline grounding.** From `dogfood/repos/questline`, feed `dictation-questline`.
  - Expect: rewrite requires a **feature flag** + a **tracked event**, references the north-star **WAQC**, names files (`src/server/streaks.ts`, etc.).
  - Result: ___  · Note:

- [ ] **T2-19 · pylon grounding.** From `dogfood/repos/pylon-infra`, feed `dictation-pylon`.
  - Expect: rewrite requires a **rollback plan**, honors **progressive rollout** + **no manual kubectl**, names files (`terraform/cluster.tf`, runbooks).
  - Result: ___  · Note:

- [ ] **T2-20 · Multi-pass + latency budget.** With `rewrite_passes=2`: dry-run a ledgerline task and watch timing.
  - Expect: the 2-pass output is tighter than 1-pass; the latency budget is respected (stages abort if over `max_total_latency_ms`).
  - Result: ___  · Note:

- [ ] **T2-21 · LLM target detection.** With `target_detect_llm_enabled=true`, dictate an ambiguous target.
  - Expect: low-confidence heuristic targets get re-classified by the LLM; final target is sensible.
  - Result: ___  · Note:

### 2.7 Languages

- [ ] **T2-22 · German dictation.** Set `model.language="de"`, feed `dictation-german` (voice Anna).
  - Expect: clean German transcription. Then set `model.language="auto"` and confirm it still works (the one-knob behavior). Compare quality.
  - Result: ___  · Note:

- [ ] **T2-23 · Spoken symbols in real speech.** Feed `dictation-spoken-symbols` (real audio).
  - Expect: after transcription, "at sign"→`@`, "hash"→`#`, "dash"→`-`, "percent sign"→`%`, with correct spacing per attach mode.
  - Result: ___  · Note:

### 2.8 The learning loop

- [ ] **T2-24 · Correct in the moment → it learns.** Dictate a ledgerline task, correct the result in the UI (e.g. fix a term), then dictate a similar task.
  - Expect: the correction persists (`dictation_corrections`); the later, similar dictation shows a **"learned from N similar"** chip; the learning digest reflects it. Honest at N=0.
  - Result: ___  · Note:

### 2.9 Wake word

- [ ] **T2-25 · Arms, doesn't type.** Enable `wake_word` (preview), say the wake word then a phrase.
  - Expect: it **arms** an 8s window and shows a preview (does not auto-type); one-shot "Type it" types it once and won't re-type. Ordinary speech does not false-accept.
  - Result: ___  · Note:

### 2.10 Activity intelligence + pre-briefing

- [ ] **T2-26 · Connectors + nudges.** On `/activity`: configure a connector (GitHub/JIRA preview/run), generate nudges.
  - Expect: source-cited nudge cards appear; dismiss + select work; `/api/activity/briefing` returns nudges + artifacts before a meeting.
  - Result: ___  · Note:

- [ ] **T2-27 · Meeting candidates.** Preview candidates, add one manually, start a meeting from it.
  - Expect: candidate → live meeting; the pre-briefing "dictate with this" loop grounds the meeting in the record.
  - Result: ___  · Note:

### 2.11 Presence + Qlippy

- [ ] **T2-28 · Presence HUD + Qlippy.** Enable `presence.enabled` (and `presence.mascot`) in `/settings`; open `/presence`; run a meeting/dictation.
  - Expect: the native HUD appears (focus-safe, off by default); cards update live (decision/result/learned/aftercare); Qlippy mascot toggles; a card **Approve** equals the dashboard action (audit parity).
  - Result: ___  · Note:

### 2.12 Speakers / diarization

- [ ] **T2-29 · Diarization + speaker management.** With `diarization_enabled=true`, import a multi-voice meeting; on `/history` open speakers.
  - Expect: distinct speakers separated; merge/rename works; `cross_meeting_recognition` links the same voice across meetings.
  - Result: ___  · Note:

---

## 3 · Cross-cutting

- [ ] **X-01 · Egress / quiet-trust badges.** Across the run, confirm the badge scope is correct: `local` (no LLM), `local+cloud` (intel on `.43`), `cloud + target` (Slack/GitHub). No privacy prose paragraphs — just the badge.
  - Result: ___  · Note:

- [ ] **X-02 · Export formats everywhere.** Export a meeting as `txt`, `markdown`, `json`, `srt` (CLI + UI).
  - Expect: all four are well-formed and contain transcript + artifacts.
  - Result: ___  · Note:

- [ ] **X-03 · Schema / version safety.** `hs doctor` reports `config_version`; `hs backup` before any migration; `hs restore` recovers. Try opening the sandbox DB note the refuse-newer behavior if you bump the version.
  - Result: ___  · Note:

- [ ] **X-04 · First-run journey (fresh sandbox).** `rm -rf dogfood/_home && dogfood/setup.sh`, then `hs web`: the `/welcome` wizard fronts the dashboard; walk it; complete a first dictation.
  - Expect: guided fresh-clone → verified first dictation with zero file edits; the `first_run` milestone flips and `/welcome` stops fronting.
  - Result: ___  · Note:

- [ ] **X-05 · It stayed isolated.** Confirm your real `~/.config/holdspeak` and `~/.local/share/holdspeak` were never touched during the run.
  - Expect: all writes landed under `dogfood/_home`.
  - Result: ___  · Note:

---

## Tier C · The Cadence Engine (CAD-8)

> Off by default. These run under the isolated sandbox `hs` (HOME=`dogfood/_home`).
> No external side effect should ever occur without an approval.

- [ ] **C-01 · Projection.** Import a meeting (or run a `say`-pipeline scenario), then
  `hs cadence run-now`.
  - Expect: open loops are projected from the meeting's action items + any pending
    proposals, scored, ordered by staleness; re-running does not duplicate them.
  - Result: ___  · Note:

- [ ] **C-02 · Brief + closeout.** `hs cadence brief` then `hs cadence closeout`.
  - Expect: the brief leads with the single highest-leverage move; the closeout lists
    every open loop with a recommended close/file/snooze/kill/delegate.
  - Result: ___  · Note:

- [ ] **C-03 · Decisions stick.** Kill a loop, then `hs cadence run-now` again.
  - Expect: the killed loop does NOT reappear.
  - Result: ___  · Note:

- [ ] **C-04 · No egress.** `hs cadence audit --out /tmp/audit.json`.
  - Expect: `egress.scope = "local"`; the audit JSON is complete (loops + nudges +
    policies) and nothing left the machine during C-01..C-03.
  - Result: ___  · Note:

- [ ] **C-05 · Master off-switch.** With `cadence.enabled = false` (default), start
  `hs web`.
  - Expect: no cadence thread runs; the runtime is byte-identical to a build without
    cadence; the read commands still work on demand.
  - Result: ___  · Note:

---

## Findings

Log every `FAIL` / `PARTIAL` here as you go, so the run produces a worklist:

| # | Check | Severity | What happened | Repro | Filed? |
|---|-------|----------|---------------|-------|--------|
|   |       |          |               |       |        |
