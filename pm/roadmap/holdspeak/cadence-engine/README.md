# The Cadence Engine — program chart

> **HoldSpeak Cadence Engine: a local-first technical chief-of-staff that turns meetings,
> activity, dictation, and coding-agent state into evidence-backed nudges and nearly-complete
> next actions.** Qlippy does not merely remind. Qlippy pushes — with receipts, restraint, and a
> ready-made next move.

**Status:** Phase 0 (architecture hardening) complete — this chart IS its output. **Phases 1–6 are
COMPLETE** — the substrate, the `/cadence` web coach, agent-blocker push, Telegram remote presence,
the daily push brief, and now **stale-loop escalation + the end-of-day closure ritual** (every open
loop with a recommended cheap decision; batch-apply; a history view). Off by default throughout.
**Phase 7 (LLM next-best-action) is next** — the one phase with real-metal LLM proof (which also
lights up the Phase-5 brief polish). Phase 8 (hardening + dogfood) closes it.

**Last updated:** 2026-06-28 (Phase 6 shipped — escalation + EOD closeout across CLI/web/Telegram +
batch-apply + history; 171 cadence/web tests green. Phases 1–5: substrate + web coach + agent push +
Telegram + the daily brief. Program authored from the owner's rough design + a grounded seam map; §15
resolved below).

---

## 0. The one sentence

Continuously convert existing HoldSpeak knowledge into:

```
Open Loop → Next Best Action → Suggested Artifact → Nudge → Decision
```

…and never nudge without a prepared next step. **Bad:** "Reminder: file the GitHub issue."
**Good:** "I drafted the issue (title + body + source). [Approve] [Edit] [Snooze] [Kill loop]."

This is a **pressure system**, not a chatbot. The promise: *Qlippy interrupts only when he has done
enough work that your next decision is cheap.*

## 1. The product principle — pushy, never reckless

1. Notice important unfinished work. 2. Make a concrete suggestion. 3. Cite the evidence.
4. Offer one-tap decisions. 5. Respect snooze/dismissal. 6. Escalate stale loops *gradually*.
7. Never perform an external side effect without explicit approval. 8. Never nag without a useful
prepared step.

## 2. The non-negotiables (the trust boundary)

These are hard rules, enforced structurally, not by good intentions:

- **No external side effect without the existing actuator approval path.** Every outbound action
  (issue, Slack, webhook) is an `ActuatorRepository.record_proposal(...)` that the user approves;
  cadence **never** calls a connector directly and **never** bypasses `transition_proposal`.
- **No raw shell, no network egress** from cadence except via approved/gated connectors.
- **Off by default.** `CadenceConfig.enabled = False`. When off, the runtime is byte-identical to
  today (the thread never starts). No hidden cloud fallback.
- **Every nudge is explainable** — it carries `EvidenceRef`s (a meeting segment, an artifact, an
  agent session, an activity record, a proposal) with deep links.
- **Every generated action is editable or rejectable.** Dismissal and snooze are respected and
  audited. A **killed** loop stays killed unless its source materially changes.
- **Quiet hours default-on.** The only opt-in exception is an urgent agent-blocker.
- **One badge, never a privacy sentence** ([[feedback_no_privacy_novels]]): every nudge carries an
  egress badge (`local` / `mixed` / `cloud + target`).
- **All source text is data, never instructions** — transcripts, browser titles, issue titles,
  agent output never alter policy or trigger tool calls; all generated proposal payloads are typed
  and preview-gated (prompt-injection defense).

## 3. Phase-0 architecture decisions (the §15 open questions, resolved)

| # | Question | Decision | Why |
|---|----------|----------|-----|
| 1 | Loops: DB entities or computed views? | **First-class DB entities, source-projected.** The collector idempotently upserts loops from sources (key = `source_type:source_id`); user lifecycle state (snoozed/killed/nudge_count) lives only on the row. | A "killed" loop must stay killed even while its source action item still exists — a view can't remember a decision. |
| 2 | Agent sessions: JSON or SQLite? | **Keep the JSON capture file; the collector *mirrors* awaiting-response sessions into loops.** No migration in this program. | Don't destabilize the agent-hook capture path; mirror, don't move. |
| 3 | Telegram second confirm for high-risk? | **Yes — tied to the actuator's `reversible` flag.** `reversible=False` or external egress ⇒ a two-step confirm; reversible/local ⇒ one tap. | A remote surface has higher accidental-tap risk; reuse the safety signal the actuator already carries. |
| 4 | Personality: gentle/normal/aggressive? | **Yes — `CadenceConfig.pressure` scales policy *timings* only**, never *what* is nudged or any safety gate. Default `normal`. | Cheap (a multiplier on delays/repeats/max-per-day), high perceived value, safety-invariant. |
| 5 | Daily brief: scheduled or on activity? | **On first user activity after a configured earliest time** (not before ~7am). | A 6am push while you sleep is noise; "first touch after quiet hours" respects presence. |
| 6 | Low-confidence extractions → loops? | **Yes, as quiet `needs_review` loops** — surfaced in the queue, never a push until confirmed. | Honest at low confidence; never nags on a hallucinated action. |
| 7 | Project identity normalization? | **One `resolve_project()` helper** — prefer explicit `project_id` (activity), the `.hs/` project via `repo_root` (agents), the meeting linkage; fall back to repo-root basename / domain. Loops store a `project` string. | Good-enough grouping now; one function to sharpen later. |
| 8 | Plugin-pack later or first-party? | **First-party, in-tree `holdspeak/cadence/`.** | Cadence is core product surface; the actuator system is already the extension seam for outbound actions. |

**Cross-cutting (corrections to the rough design, from the grounded seam map):**

- **Threading, not asyncio.** `WebRuntime` runs background work as **daemon threads on a shared
  `runtime_stop_event`** (`web_runtime.py:169,477–482,537,564`), e.g. `PluginQueueMixin`. The
  cadence loop follows that exact pattern — a `CadenceMixin` daemon thread — **not** the rough
  design's "periodic async task."
- **No new infrastructure.** In-process thread + SQLite. No Celery/Redis/Temporal (design §6.3).
- **Reuse, never rebuild.** Cadence is a *layer* over seams that already ship; §4 maps each.

## 4. The seams we reuse (verified `file:line`)

| Seam | Where | How cadence uses it |
|------|-------|---------------------|
| **Runtime hub** | `WebRuntime` `holdspeak/web_runtime.py:138` (8 mixins); daemon-thread pattern `:477–482`, stop `:418/:564` | A `CadenceMixin` (`holdspeak/runtime/cadence.py`) owns `self.cadence_thread`, started in `run()`, joined in cleanup. |
| **SQLite** | `Database` `holdspeak/db/core.py:810`; `SCHEMA_SQL:142`, `SCHEMA_VERSION=2 :39`; `BaseRepository(connection, container)` `holdspeak/db/base.py` | New `cadence_*` tables in `SCHEMA_SQL`, bump to `3`; `CadenceRepository` in `holdspeak/db/cadence.py`, registered in `Database.__init__:816`. |
| **Aftercare** | `holdspeak/meeting_aftercare.py` (read-only digest: open_items/decisions/changes); routes in `web/routes/meetings.py` (aftercare read, file-issue, export/slack) | Strongest signal source: open/accepted actions → loops. |
| **Activity ledger** | `activity_records` `db/core.py:496`; `ActivityRepository` `db/activity.py`; `Nudge`/`compute_nudges()` `holdspeak/activity_nudges.py`; `/api/activity/briefing` | "Is this loop still alive?" — recent-activity suppression/boost. |
| **Action items** | `action_items` `db/core.py:200` (status pending/completed/dismissed, `review_state`, `owner`); in `MeetingRepository` | Source loops; owner/assign moves. |
| **Agent hooks** | `AgentSession` `holdspeak/agent_context/models.py` (`awaiting_response`, `last_assistant_text`, `tmux_pane`, `cwd`, `repo_root`); file `~/.config/holdspeak/agent_sessions.json` | Awaiting-response → blocker loop; reply via tmux or `/api/dictation/remote`. |
| **Actuators** | `ActuatorRepository.record_proposal(...)` → `transition_proposal(...)` `holdspeak/db/actuators.py:42`; audit table; idempotency key; gates `allow_actuators=False`/`allowed_actuators`/`webhook_allowed_hosts` `config.py` | The ONLY path to an external side effect. |
| **Routes** | `build_*_router(ctx)->APIRouter`; registered `web_server.py:556–567`; `WebContext` `web/context.py` | `build_cadence_router` → `/api/cadence/*`. |
| **Web UI** | Astro `web/src/pages/*.astro` + `web/src/scripts/*.js`; build to `_built/`; `egress-badge.js` (scope local/mixed/cloud) | A `/cadence` coach page. |
| **CLI** | `main.py` subparsers + `holdspeak/commands/*.py` (`run_*_command`) | `holdspeak cadence …`. |
| **Presence** | `desktop_presence.py` `_STATE_META`, `_set_runtime_activity()` | A cadence nudge rides the desktop presence overlay. |
| **Dogfood** | `dogfood/PROTOCOL.md` (Tier-1 plumbing / Tier-2 real-metal); `tests/e2e/test_dogfood_plumbing_e2e.py`; `HOLDSPEAK_DOGFOOD=1` | A cadence protocol section + fixtures. |
| **Egress / Intel** | `egress-badge.js`; `intel_egress_posture()` `holdspeak/intel/providers.py:225`; providers local/cloud/auto + structured-JSON validation | Badge every nudge; LLM next-actions are fail-closed JSON. |
| **Config gate** | `config.py` dataclasses, off-by-default booleans (`meeting.allow_actuators=False`) | `CadenceConfig(enabled=False, pressure="normal", …)`. |

## 5. The core concepts (data model)

`OpenLoop` (id, source_type, source_id, project, title, summary, status [open/snoozed/closed/
killed/delegated], priority, due_at, snoozed_until, owner, stale_score, last_nudged_at,
nudge_count) · `EvidenceRef` (kind, id, label, timestamp, deep_link) · `NextBestAction` (loop_id,
kind, title, body_markdown, confidence, reversible, proposal_id) · `Nudge` (loop_id, action_id,
surface, severity, message, actions, status) · `CadencePolicy` (source_types, quiet_hours,
delays, escalation, max/day, surfaces). Full SQL in `phase-1-cadence-core/story-01`.

## 6. The phases (build in dependency order)

Phase 1 leads and is fully storied. Each later phase is storied when it becomes the lead.

| Phase | Title | The crux | Depends on |
|-------|-------|----------|------------|
| **1 ✅** | **Cadence core** | *Done.* The loop/nudge/policy substrate: models, migrations, collector (meeting actions + pending proposals), stale-scoring v1, policies + quiet hours, CLI, unit tests. No external side effects, off by default. | — |
| **2 ✅** | Web coach surface | *Done.* `/api/cadence/*` + a `/cadence` page: loops, evidence deep-links, snooze/kill/close, deterministic next-action, egress badges. | 1 |
| **3 ✅** | Agent-blocker push | *Done.* Awaiting-response agent sessions → top loops + a reply composer; the typed reply is delivered into the agent's tmux pane (`send_text_to_pane`, in the route — never autonomous). | 1 |
| **4 ✅** | Telegram remote presence | *Done (hermetic; live walk = owner).* Pairing + a Telegram surface (`holdspeak/cadence_telegram.py`, a sibling of the core); `/brief` `/loops` `/status`; inline-button decisions (snooze/done + kill-confirm); unpaired-chat rejection; push-on-tick; token never logged/stored. | 2, 3 |
| **5 ✅** | Daily push brief | *Done.* A deterministic morning brief (`build_brief`, first-activity trigger) across CLI/web/Telegram with prepared moves; the LLM-wording-polish seam is tested + fail-closed (live wiring deferred to a real-metal follow-up). | 2 |
| **6 ✅** | Stale-loop + EOD closure | *Done.* `escalation_severity` (nudges/age) + `build_closeout` (a recommended decision per loop) + batch-apply + kill/delegate/snooze/close semantics + a history view, across CLI/web/Telegram. | 2, 5 |
| **7** | LLM next-best-action | Structured-JSON next-action generator (issue/Slack drafts, dedupe clustering), fail-closed validation, preview/approval-gated. | 6 |
| **8** | Hardening + dogfood | A cadence dogfood protocol + fixtures + e2e, telemetry-free local audit export, docs, and the master off-switch proven. | all |

**Anti-goals** (design §14): not a chatbot, not an autonomous shell executor, not a second runtime,
not a cloud-first memory, not an MCP free-for-all, not a surveillance daemon, not a vague-reminder
nag machine, not a separate product.

## 7. Operating cadence (per the repo)

Every shipping commit: branch off `main`, write `.tmp/CONTRACT.md` (8 honest `[x]`), run the
relevant tests (`uv run pytest -q …`), open a PR, **merge on green** ([[feedback_merge_phases_via_pr]]).
Each phase updates its `current-phase-status.md` story-status row + "Where we are", this chart's
"Last updated", and any canon doc the story names. A **dedicated docs story** closes each
user-facing phase ([[feedback_dedicated_docs_story]]). Prove LLM-shaped features on real metal,
control-vs-treatment, not just a no-LLM plumbing pass ([[feedback_prefer_real_metal_proof]]).

## 8. Pointers

- **Owner's rough design:** the source brief (this chart refines it into implementation-ready work).
- **Phase 1 (lead):** `phase-1-cadence-core/current-phase-status.md` + `story-01..06`.
- **The first agent prompt** the owner supplied (design §16) is satisfied by this chart + Phase 1.
- **Memories:** [[feedback_no_privacy_novels]], [[feedback_merge_phases_via_pr]],
  [[feedback_dedicated_docs_story]], [[feedback_prefer_real_metal_proof]],
  [[feedback_author_pmo_directly]], [[project_phase37_actuators]], [[reference_lan_llm_endpoint]].
