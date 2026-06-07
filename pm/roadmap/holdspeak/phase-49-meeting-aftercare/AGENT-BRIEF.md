# Phase 49 — Agent Brief (read this first)

You are picking up **Phase 49 — Meeting Aftercare ("close the loop")** for
HoldSpeak. This brief is self-contained: the mission, the exact code seams
(mapped against the live tree), the rules of the road, and a per-story definition
of success. Read it, then read [`current-phase-status.md`](./current-phase-status.md)
and the story you're working. If this brief disagrees with the live status docs
or the codebase, the **codebase wins** — re-verify before trusting any line or
number below.

---

## 0. Mission

The meeting side is strong: 14 real plugins, artifacts, proposals, history,
action review. But a meeting's afterlife is **display**, not **follow-through**. A
user sees beautiful artifacts and then has to go *do* the work somewhere else.
The strategic review's verdict: "A beautiful artifact that never changes the
user's next action is decoration."

Make the meeting **close its own loops**. After a meeting, answer the questions a
person actually has, on the surface where the meeting already lives:

- **What's still open for me?** (open action items, by owner, across meetings)
- **What did we decide?** (the decisions, surfaced, not buried in an artifact)
- **What changed since last meeting?** (a real cross-meeting diff)
- **Show me the moment that justifies this.** (jump to the transcript segment)
- **Turn accepted actions into issues.** (reuse the actuator propose -> approve
  -> execute flow; off by default, human-approved, audited)
- **Draft the follow-up.** (a local, copyable summary; preview + copy, never
  auto-sent)

This is a **follow-through + trust** phase on the meeting/history surface. It does
**not** add new artifact types or change how meetings are captured or how plugins
run. You are adding a read-only aggregation, an honest provenance jump, a
loop-closing path that reuses the existing actuator system, and a local draft.

---

## 1. The one thing you must not get wrong

**Nothing leaves the machine, and nothing changes state, without explicit
per-action human approval — and every "open / decided / changed" claim must be
real.** The whole point of aftercare is trust at the moment of action.

- **Closing a loop reuses the actuator system as-is.** "Accepted actions ->
  issues" creates `ActuatorProposal`s through the existing
  propose -> approve -> execute path (`plugins/actuators.py`,
  `plugins/actuator_executor.py`, `db/actuators.py`). It stays **off by default**
  (`allow_actuators` + per-project allow-list), every execution is **audited**,
  and the payload-parity (TOCTOU) gate holds. **No new write primitive. No
  auto-execute.**
- **The follow-up draft is preview + copy.** Like dictation replay: assemble it
  locally, show it, let the user copy it. Never auto-send, never open a connector
  to send it.
- **Diffs and "what's open" are computed from real data.** "Since last meeting"
  compares this meeting to the chronologically previous one over the real
  `decisions` / `action_items`; do not fabricate or pad changes. Stay quiet when
  there is no prior meeting or no change.
- **Provenance only when it's real.** The "jump to the transcript moment" affordance
  shows only when a real `source_timestamp` (or segment range) exists. No fake
  "0:00" jumps. (Same honesty discipline as Phase 48's quiet-at-N=0.)

---

## 2. Rules of the road (non-negotiable)

- **PMO commit gate.** Every commit needs a fresh `.tmp/CONTRACT.md` (template in
  `pm/roadmap/PMO-CONTRACT.md` §"Contract template", **7** checkboxes — the 8th
  "design handoff" box is a Pantrybot example, not this repo's hook); `mkdir -p
  .tmp` first, the pre-commit hook validates and deletes it. A story flipping to
  `done` **must** ship its `evidence-story-{n}.md` in the same commit; **one**
  done-flip per commit. The phase-exit story needs `evidence-story-06.md` **and**
  `final-summary.md` in the same commit. The story Status line is the list-item
  form `- **Status:** done`.
- **No `Co-Authored-By` trailer. No `--no-verify`.**
- **Operating cadence.** Every shipping commit updates: the story header status,
  the phase `current-phase-status.md` (row + Last-updated + "Where we are"), the
  project `README.md` (phase row + Current-phase + Last-updated), and any canon
  doc the story touched.
- **One PR per phase, merged when CI green.** Work on a phase branch; at close,
  push + open a PR to `main` + merge with a merge commit when all CI suites pass
  (Unit · Integration macOS · E2E macOS · Linux Smoke · Route screenshots).
  Memory `feedback_merge_phases_via_pr`.
- **Tests actually run.** Flip a story to `done` only after running the relevant
  tests and reading the output. Full suite:
  `uv run pytest -q --ignore=tests/e2e/test_metal.py` (the metal file hangs without
  a mic). Type-check is not validation.
- **Behavior-preserving.** Aftercare is read-only aggregation + the existing
  actuator path + a local draft. Meeting capture, plugin runs, and synthesis stay
  byte-identical. Actuators stay off by default.
- **Write like a human.** In any doc or UI copy you add: no em or en dashes, no
  emoji-decorated bullets, no rule-of-three padding, no "not X but Y". Plain,
  varied, direct. (`humanizer` skill available; `docs/internal/DOCS_STYLE.md` is
  the voice authority.)

---

## 3. The ground truth (code seams, already mapped + verified)

Backend (data):

- `holdspeak/db/meetings.py` — `MeetingRepository`. `list_meetings(limit, offset,
  date_from, date_to, tag)` (l.381), `get_meeting(id)` (l.253), `list_action_items(
  include_completed, meeting_id, owner)` (l.430). **There is no cross-meeting /
  "since last meeting" query — that is your new work (HS-49-01).** Meetings carry
  `started_at`/`ended_at`/`title`/`tags`/`segments`; segments carry
  `start_time`/`end_time`/`text`/`speaker`.
- `holdspeak/db/models.py` — `ActionItemSummary` carries `status`
  (pending|done|dismissed), `review_state` (**pending|accepted**, l.14
  `VALID_ACTION_ITEM_REVIEW_STATES`), `owner`, `meeting_id`, and
  **`source_timestamp`** (a float meeting-offset — the provenance link to the
  transcript). `ArtifactSummary` carries `artifact_type`, `structured_json`,
  `status` (draft|needs_review|accepted|rejected), `sources` (plugin-run lineage,
  **not** transcript moments).
- `holdspeak/db/plugins.py` — `PluginArtifactRepository.list_artifacts(meeting_id)`
  (l.749), `record_artifact(...)` (l.656), `artifact_sources` table (provenance).
- `holdspeak/plugins/synthesis.py` — plugin -> artifact_type map (`decisions`,
  `action_items`, `requirements`, `risk_register`, ...). Decisions live in the
  `decisions` artifact's `structured_json`.

Backend (actuators — the loop-closer you REUSE, do not reinvent):

- `holdspeak/plugins/actuators.py` — `ActuatorProposal` (target/action/preview/
  payload/reversible/required_capabilities), `ACTUATOR_PROPOSAL_STATUS="proposed"`.
- `holdspeak/db/actuators.py` — `ActuatorRepository`: `record_proposal`,
  `list_proposals(meeting_id, status)`, `transition_proposal(...)`, `list_audit`.
  Lifecycle proposed -> approved -> executed | rejected; approved -> failed ->
  approved (retry).
- `holdspeak/plugins/actuator_executor.py` — `ActuatorExecutor`: status gate ->
  policy gate (`allow_actuators` + allow-list) -> payload-parity hash -> injected
  `connector` -> audit. The invariant lives here.
- `holdspeak/plugins/builtin/github_issue_actuator.py` — the reference: proposes a
  GitHub issue for the first unowned action item (`GithubIssueActuator.run`, l.86;
  `GITHUB_ISSUE_MANIFEST`, l.64; gated `gh issue create`). Aftercare wants
  **accepted** action items -> proposals; this is the pattern to follow.
- `holdspeak/plugins/gated_connector.py` — `WriteConnectorManifest` (permission +
  allow-lists); refusal raises `ConnectorOperationRefused` before any egress.

Web routes (`holdspeak/web/routes/meetings.py`):

- `GET /api/meetings` (l.272), `GET /api/meetings/{id}` (l.431),
  `GET /api/meetings/{id}/artifacts` (l.596), `GET /api/meetings/{id}/proposals`
  (l.662), `POST /api/meetings/{id}/proposals/{pid}/decision` (l.689 — approve/
  reject). Action items: `PATCH /api/action-items/{id}` (status, l.130),
  `PATCH .../{id}/review` (accept, l.164), `GET /api/all-action-items` (l.733) +
  the `/all-action-items/{id}/review` (l.834) global variants.

UI (Astro; source in `web/src`, built bundle is **gitignored** under
`holdspeak/static/_built/` — run `(cd web && npm run build)`, Node >= 22.12, after
any `web/src` edit; page-content tests read the built JS):

- `web/src/pages/history.astro` (~2.4k lines) — Meetings / Action items / Speakers
  / Projects / Intel tabs; the meeting-detail view renders artifacts (l.705+) and
  proposals (l.936+). **Heed the page-density rule: factor aftercare UI into a
  partial / behavior module, do not just append.**
- `web/src/scripts/history-app.js` — `openMeeting(id)` fetches the meeting +
  artifacts + proposals; `setActionReviewState(...)` accepts an action;
  `api_decide_meeting_proposal(...)` approves/rejects a proposal. Runtime-injected
  DOM, so any new CSS for it must be `<style is:global>` (memory
  `reference_astro_scoped_css_js_dom`) and **screenshot-verified**.

Tooling you'll reuse:

- **Dogfood:** `scripts/dogfood_learning_loop.py` (Phase 48) + the meeting
  integration tests (`tests/integration/test_web_meeting_proposals_api.py`,
  `test_artifact_synthesis_pipeline.py`) are the models — HTTP-driven over a
  `TestClient` against a seeded temp DB, no mic/LLM.
- **Screenshots:** `scripts/screenshot_learning_digest.py` (Phase 48) is the
  model for before/after.
- **Real-speech e2e:** `tests/e2e/test_spoken_meeting_e2e.py` already does
  `say` -> Whisper -> plugins -> artifacts; the aftercare e2e can build on it.

---

## 4. Per-story definition of success

- **HS-49-01 — The aftercare digest.** A read-only aggregation
  (`GET /api/meetings/{id}/aftercare`, or `/api/aftercare?...`) over meetings +
  action items + artifacts: what's still open (by owner), what was decided, and a
  real "what changed since the previous meeting" diff (new/closed decisions +
  actions vs the chronologically prior meeting). A surface on the meeting/history
  view that reads as "here's your next move," quiet when there's nothing. The
  foundation everything else presents.
- **HS-49-02 — Transcript provenance ("show me the moment").** A "jump to the
  transcript moment" affordance wherever a real `source_timestamp` / segment range
  exists (action items already carry it; thread it through the aftercare surface
  and, where feasible, decisions). Shows only when the timestamp is real; opens
  the transcript at that segment. Honest, read-only.
- **HS-49-03 — Close the loop: accepted actions -> issues.** From the aftercare
  surface, turn **accepted** action items into actuator **proposals** (GitHub
  issue / connector) through the existing propose -> approve -> execute flow. No
  new write primitive; off by default; per-action human approval; audited;
  payload-parity holds. Reuses `github_issue_actuator` / the gated connector.
- **HS-49-04 — Draft the follow-up.** A local, copyable follow-up draft (decisions
  + open actions + owners) assembled from the aftercare data. Preview + copy, never
  auto-sent; LLM-optional (assemble locally first). Mirrors replay's stance.
- **HS-49-05 — Docs.** The Meeting Mode guide documents aftercare end to end
  (what's open / decided / changed -> jump to the moment -> accept -> file issue /
  draft follow-up); README/index frames "close the loop"; guards green; grounded
  in code; honest about off-by-default actuators + preview-only drafts.
- **HS-49-06 — Closeout.** Before/after (old artifact-only meeting view vs the new
  aftercare surface), a green dogfood, full suite green, `final-summary.md`, phase
  CLOSED, PR to `main` merged on green.

---

## 5. Gotchas that will bite you

- **Never auto-act.** (See §1.) Reuse the actuator approval + audit; off by
  default; drafts are preview + copy. A surface that files an issue or sends a
  message without explicit approval fails the phase.
- **Real diffs only.** "Since last meeting" must compare real prior-meeting data;
  stay quiet with no prior meeting or no change. No fabricated "what changed."
- **Provenance must be real.** Only offer the transcript jump when a real
  timestamp exists; never a fake 0:00.
- **Astro scoped CSS dies on JS-injected DOM.** The history meeting-detail DOM is
  JS-rendered; any aftercare CSS must be `<style is:global>` (or static markup
  toggled by JS) and **screenshot-verified**. Memory
  `reference_astro_scoped_css_js_dom`.
- **Page density.** `history.astro` (~2.4k lines) is already large. Factor the
  aftercare UI into a partial / behavior module; do not just append.
- **`created_at` / `started_at` are ISO text.** Order meetings by `started_at` to
  find "the previous meeting"; window/compare carefully. Seed deterministic
  timestamps in tests.
- **Actuator policy is real.** Execution needs `allow_actuators` + the per-project
  allow-list + a host-injected connector; in tests, inject a stub connector and
  set the policy explicitly (see `tests/integration/test_web_meeting_proposals_api.py`
  + `tests/unit/test_actuator_executor.py`).

---

## 6. Where to start

`HS-49-01` (the aftercare digest) is the entry point — every other surface
presents or feeds the aggregation it adds. Read `story-01-aftercare-digest.md`,
build the read-only cross-meeting aggregation over meetings + action items +
artifacts (open-by-owner, decisions, since-last-meeting diff), then the aftercare
surface, run
`uv run pytest -q -k "meeting or aftercare or action_item or artifact or proposal"`
+ `npm run build` + a screenshot, and ship it through the PMO gate. Sequence:
01 -> 02 -> 03 -> 04 -> 05 -> 06.

Keep it honest, keep it local-first, never act without approval, keep meeting
capture untouched. This is the phase that turns meeting intelligence from a pile
of beautiful artifacts into something that changes your next action.
